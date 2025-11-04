# app.py
from flask import (
    Flask, render_template, request, session, redirect,
    url_for, flash, jsonify, g
)
from flask_session import Session
from datetime import datetime, timedelta, date
import time
import pymysql
import yaml
from pathlib import Path
from flask import current_app

# Model classes
from user import user
from task import task
from user_task import user_task
from feedback import feedback

# ─── App setup ───────────────────────────────────────────────────────────────
app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY']                 = '5sdghsgRTg'
app.config['SESSION_PERMANENT']          = True
app.config['SESSION_TYPE']               = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
Session(app)

BLOCK_LENGTH = 30  # fixed global block length

# ─── Utility filter ───────────────────────────────────────────────────────────
def format_datetime(value, fmt='%Y-%m-%d %H:%M:%S'):
    if not value:
        return ''
    try:
        return value.strftime(fmt)
    except:
        return 'NA'
app.jinja_env.filters['format_datetime'] = format_datetime

# ─── Before each request: auto‐transition + notifications ────────────────────
@app.before_request
def process_transitions():
    g.notifications = []
    if 'user' not in session:
        return
    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # Pending → In Progress
    rows = dbselect(
        "SELECT UserTaskID FROM mmungoshi_user_task "
        "WHERE TaskStatus='Pending' AND TaskStartTime <= %s",
        [now_str]
    )
    if rows:
        ids = [str(r['UserTaskID']) for r in rows]
        dbupdate(
            f"UPDATE mmungoshi_user_task "
            f"SET TaskStatus='in_progress' "
            f"WHERE UserTaskID IN ({','.join(ids)})"
        )
        for r in rows:
            g.notifications.append({
                'Type':       'started',
                'UserTaskID': r['UserTaskID'],
                'CreatedAt':  now_str
            })

    # In Progress → Completed
    rows2 = dbselect(
        "SELECT UserTaskID FROM mmungoshi_user_task "
        "WHERE TaskStatus='in_progress' AND TaskEndTime <= %s",
        [now_str]
    )
    if rows2:
        ids2 = [str(r['UserTaskID']) for r in rows2]
        dbupdate(
            f"UPDATE mmungoshi_user_task "
            f"SET TaskStatus='completed' "
            f"WHERE UserTaskID IN ({','.join(ids2)})"
        )
        for r in rows2:
            g.notifications.append({
                'Type':       'complete_reminder',
                'UserTaskID': r['UserTaskID'],
                'CreatedAt':  now_str
            })

# ─── Inject into templates ────────────────────────────────────────────────────
@app.context_processor
def inject_user():
    return {
        'me':            session.get('user'),
        'mode':          session.get('mode'),
        'notifications': g.get('notifications', [])
    }

@app.context_processor
def inject_now():
    # makes a now() function available in ALL templates
    return { 'now': datetime.utcnow() }

# ─── Authentication & mode ───────────────────────────────────────────────────
def checkSession():
    if 'active' in session:
        if time.time() - session['active'] > 1800:
            flash('Your session has timed out.')
            session.clear()
            return False
        session['active'] = time.time()
        return True
    return False

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = user()
        if u.tryLogin(request.form['Email'], request.form['Password']):
            session['user']   = u.data[0]
            session['mode']   = 'Flow'
            session['active'] = time.time()
            session.permanent = True
            return redirect(url_for('main'))
        flash("Incorrect username or password.", 'danger')
    return render_template('login.html')

@app.route('/logout', methods=['GET','POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/set_mode')
def set_mode():
    m = request.args.get('mode')
    if m in ('Flow','Motion'):
        session['mode'] = m
    return redirect(request.referrer or url_for('list_user_tasks'))

# ─── Main dashboards ─────────────────────────────────────────────────────────
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/main')
def main():
    if not checkSession():
        return redirect(url_for('login'))
    if session['user']['UserType'] == 'Administrator':
        return render_template('main.html')
    return render_template('regular_main.html')

# ─── User Management (Admin) ─────────────────────────────────────────────────
@app.route('/users/manage', methods=['GET', 'POST'])
def manage_user():
    # admins only
    if not checkSession() or session['user']['UserType'] != 'Administrator':
        return redirect(url_for('login'))

    o      = user()
    action = request.args.get('action')
    pkval  = request.args.get('pkval')

    # ── safety: one admin can’t modify another admin ────────────────
    if action in ('delete', 'update') and pkval and pkval != str(session['user']['UserID']):
        o.getById(pkval)
        if o.data and o.data[0]['UserType'] == 'Administrator':
            flash("You cannot modify other administrators.")
            return redirect(url_for('manage_user'))

    # ───────────────────────── DELETE (POST) ───────────────────────
    if action == 'delete' and request.method == 'POST':
        conn = dbconnect()                      # ← same-file helper
        try:
            with conn.cursor() as cur:
                # 1) remove feedback and assignments first
                cur.execute("DELETE FROM mmungoshi_feedback   WHERE UserID = %s", (pkval,))
                cur.execute("DELETE FROM mmungoshi_user_task  WHERE UserID = %s", (pkval,))
            conn.commit()
        finally:
            conn.close()

        # 2) now delete the user
        o.deleteById(pkval)
        flash("User and related tasks/feedback deleted.", "warning")
        return redirect(url_for('manage_user'))

    # ───────────────────────── INSERT ──────────────────────────────
    if action == 'insert':
        if request.method == 'POST':
            o.set({
                'UserName':      request.form.get('UserName'),
                'UserEmail':     request.form.get('UserEmail'),
                'UserType':      request.form.get('UserType'),
                'UserPassword':  request.form.get('UserPassword'),
                'UserPassword2': request.form.get('UserPassword2')
            })
            if o.verify_new():
                o.insert()
                flash("User added.")
                return redirect(url_for('manage_user'))
        else:
            o.createBlank()
        return render_template('users/add.html', obj=o)

    # ───────────────────────── UPDATE ─────────────────────────────
    if action == 'update':
        if request.method == 'POST':
            o.getById(pkval)
            new_type = (
                'Administrator'
                if o.data[0]['UserType'] == 'Administrator'
                else request.form.get('UserType')
            )
            o.data[0].update({
                'UserName':      request.form.get('Username'),
                'UserEmail':     request.form.get('UserEmail'),
                'UserType':      new_type,
                'UserPassword':  request.form.get('UserPassword'),
                'UserPassword2': request.form.get('UserPassword2')
            })
            if o.verify_update():
                o.update()
                flash("User updated.")
                return redirect(url_for('manage_user'))
        else:
            o.getById(pkval)
        return render_template('users/manage.html', obj=o)

    # ───────────────────────── LIST / ADD / VIEW ──────────────────
    if not pkval:
        o.getAll()
        return render_template('users/list.html', obj=o)

    if pkval == 'new':
        o.createBlank()
        return render_template('users/add.html', obj=o)

    o.getById(pkval)
    return render_template('users/manage.html', obj=o)



# ─── Master Task Management (Admin) ──────────────────────────────────────────
@app.route('/tasks')
def list_tasks():
    if not checkSession() or session['user']['UserType']!='Administrator':
        return redirect(url_for('login'))
    t = task(); t.getAll()
    return render_template('tasks/list.html', tasks=t.data)

@app.route('/tasks/manage', methods=['GET', 'POST'])
def manage_task():
    action = request.args.get('action')
    pk     = request.args.get('pk')          # may be None

    # ───────────────────────── INSERT ─────────────────────────
    if action == 'insert':
        obj = task()
        if request.method == 'POST':
            obj.data = [{
                'TaskName':         request.form['TaskName'],
                'TaskCategory':     request.form['TaskCategory'],
                'TaskSubcategory':  request.form['TaskSubcategory'],
                'DefaultIntensity': request.form['DefaultIntensity'],
                'DefaultDuration':  request.form['DefaultDuration']
            }]
            if obj.verify_new():
                obj.insert()
                flash("Task added!", "success")
                return redirect(url_for('list_tasks'))
        else:
            obj.data = [{}]
        return render_template('tasks/add.html', obj=obj)

    # ───────────────────────── UPDATE ─────────────────────────
    if action == 'update' and pk:
        obj = task(); obj.getById(pk)
        if request.method == 'POST':
            obj.data = [{
                'TaskID':           pk,
                'TaskName':         request.form['TaskName'],
                'TaskCategory':     request.form['TaskCategory'],
                'TaskSubcategory':  request.form['TaskSubcategory'],
                'DefaultIntensity': request.form['DefaultIntensity'],
                'DefaultDuration':  request.form['DefaultDuration']
            }]
            if obj.verify_new():
                obj.update()
                flash("Task updated!", "success")
                return redirect(url_for('list_tasks'))
        return render_template('tasks/manage.html', obj=obj)

    # ───────────────────────── DELETE ─────────────────────────
    if action == 'delete' and pk and request.method == 'POST':

        conn = dbconnect()                     # <-- open a fresh connection
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM mmungoshi_feedback WHERE UserID = %s", (pk,))

                # 1) delete feedback rows linked to this task
                cur.execute(
                    """
                    DELETE f
                    FROM   mmungoshi_feedback  AS f
                    JOIN   mmungoshi_user_task AS ut
                        ON ut.UserTaskID = f.UserTaskID
                    WHERE  ut.TaskID = %s
                    """,
                    (pk,)
                )

                # 2) delete assignments for this task
                cur.execute(
                    "DELETE FROM mmungoshi_user_task WHERE TaskID = %s",
                    (pk,)
                )

            conn.commit()                      # commit both deletes
        finally:
            conn.close()                       # always close the connection

        # 3) delete the master task (now orphan-free)
        t = task()
        t.deleteById(pk)

        flash("Task and related assignments/feedback deleted.", "warning")
        return redirect(url_for('list_tasks'))


    # ───────────────────────── FALLBACK ───────────────────────
    return redirect(url_for('list_tasks'))

# ─── User-Assigned Tasks ─────────────────────────────────────────────────────
# app.py (or routes.py)  ───────────────────────────────────────────
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session
)
# import checkSession, user, task, user_task …

VALID_STATUSES = {'pending', 'in_progress', 'completed'}
def _clean_status(val: str, default: str = 'pending') -> str:
    """Normalise status coming from the form to a valid enum literal."""
    val = (val or default).strip().lower()
    return val if val in VALID_STATUSES else default


@app.route('/user_tasks/manage', methods=['GET', 'POST'])
def manage_user_task():
    if not checkSession():
        return redirect(url_for('login'))

    # ─── 1. determine whose assignments we’re viewing ────────────────
    filter_user = request.values.get('user_id') or None
    is_admin    = session['user']['UserType'] == 'Administrator'
    filter_user = int(filter_user) if (is_admin and filter_user) else session['user']['UserID']

    # allow admin to override target user on POST
    form_user   = request.form.get('UserID')
    target_user = int(form_user) if (is_admin and form_user) else filter_user

    action = request.args.get('action')          # new | insert | edit | delete
    pkval  = request.args.get('pkval')           # assignment id

    # ─── 2. dropdown choices ─────────────────────────────────────────
    tm = task();  tm.getAll();   all_tasks = tm.data or []
    um = user();  um.getAll();   all_users = um.data or []
    def _choices():
        return {'users': all_users, 'tasks': all_tasks}

    # ────────────────────────────────────────────────────────────────
    # INSERT  (action = new / insert)
    # ----------------------------------------------------------------
    if action in {'new', 'insert'}:
        obj = user_task();  obj.data, obj.choices = [{}], _choices()

        if request.method == 'POST':
            # datetime
            date_str = request.form.get('ScheduledDate', '').strip()
            time_str = request.form.get('ScheduledTime', '').strip() or '00:00'
            try:
                dt_start = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            except ValueError:
                flash('Invalid date/time.', 'danger')
                return render_template('user_tasks/add.html', obj=obj, user_id=filter_user)

            # master task (existing vs. new)
            if request.form['task_source'] == 'new':
                nt = task()
                nt.data = [{
                    'TaskName':         request.form.get('NewTaskName'),
                    'TaskCategory':     request.form.get('NewTaskCategory'),
                    'TaskSubcategory':  request.form.get('NewTaskSubcategory'),
                    'DefaultIntensity': request.form.get('NewDefaultIntensity'),
                    'DefaultDuration':  request.form.get('NewDefaultDuration')
                }]
                if not nt.verify_new():
                    flash('Error creating master task.', 'danger')
                    nt.choices = _choices()
                    return render_template('user_tasks/add.html', obj=nt, user_id=filter_user)
                nt.insert()
                master, master_id = nt.data[0], nt.data[0]['TaskID']
            else:
                master_id = request.form['TaskID']
                master    = next(t for t in all_tasks if str(t['TaskID']) == str(master_id))

                new_name = request.form.get('TaskName', '').strip()
                if new_name and new_name != master['TaskName']:
                    mt = task()
                    mt.getById(master_id)        # load the single master-task row
                    if mt.data:
                        mt.data[0]['TaskName'] = new_name
                        if mt.verify_new() or getattr(mt, 'verify_update', lambda: True)():
                            mt.update()          # commit the change
                            master['TaskName'] = new_name        # keep in-memory copy in sync

            # overrides / defaults
            intensity = request.form.get('Intensity') or master['DefaultIntensity']
            duration  = request.form.get('Duration')  or master['DefaultDuration']
            try:
                mins = int(duration)
            except ValueError:
                mins = int(master['DefaultDuration'])

            duration = str(mins)
            dt_end   = dt_start + timedelta(minutes=mins)
            status   = _clean_status(request.form.get('TaskStatus'))  # ← normalised

            ut = user_task()
            ut.data = [{
                'UserID':         target_user,
                'TaskID':         master_id,
                'TaskStartTime':  dt_start.strftime('%Y-%m-%d %H:%M:%S'),
                'TaskEndTime':    dt_end.strftime('%Y-%m-%d %H:%M:%S'),
                'Intensity':      intensity,
                'ActualDuration': duration,
                'TaskStatus':     status
            }]
            if ut.verify_new():
                ut.insert()
                flash(f'Task scheduled for {date_str} at {time_str}', 'success')
                return redirect(url_for('list_user_tasks', user_id=filter_user))

            obj = ut;  obj.choices = _choices()
            return render_template('user_tasks/add.html', obj=obj, user_id=filter_user)

        return render_template('user_tasks/add.html', obj=obj, user_id=filter_user)

    # ────────────────────────────────────────────────────────────────
    # EDIT  (GET + POST)
    # ----------------------------------------------------------------
    if action == 'edit' and pkval:
        ut = user_task();  ut.getById(pkval)

        if (not is_admin) and (str(ut.data[0]['UserID']) != str(session['user']['UserID'])):
            flash('You don’t have permission to edit that assignment.', 'danger')
            return redirect(url_for('list_user_tasks', user_id=filter_user))

        if request.method == 'POST':
            master_id = request.form['TaskID']
            master    = next(t for t in all_tasks if str(t['TaskID']) == str(master_id))

            date_str = request.form.get('ScheduledDate', '').strip()
            time_str = request.form.get('ScheduledTime', '').strip() or '00:00'
            try:
                dt_start = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            except ValueError:
                flash('Invalid date/time.', 'danger')
                ut.choices = _choices()
                return render_template('user_tasks/manage.html', obj=ut, user_id=filter_user)

            intensity = request.form.get('Intensity') or master['DefaultIntensity']
            duration  = request.form.get('Duration')  or master['DefaultDuration']
            try:
                mins = int(duration)
            except ValueError:
                mins = int(master['DefaultDuration'])

            duration = str(mins)
            dt_end   = dt_start + timedelta(minutes=mins)
            status   = _clean_status(request.form.get('TaskStatus'))

            ut.data = [{
                'UserTaskID':     pkval,
                'UserID':         target_user,
                'TaskID':         master_id,
                'TaskStartTime':  dt_start.strftime('%Y-%m-%d %H:%M:%S'),
                'TaskEndTime':    dt_end.strftime('%Y-%m-%d %H:%M:%S'),
                'Intensity':      intensity,
                'ActualDuration': duration,
                'TaskStatus':     status
            }]
            if ut.verify_new():
                ut.update()
                flash('Assignment updated.', 'success')
                return redirect(url_for('list_user_tasks', user_id=filter_user))

            flash('Validation failed — please correct the errors.', 'danger')

        ut.choices = _choices()
        return render_template('user_tasks/manage.html', obj=ut, user_id=filter_user)

    # ────────────────────────────────────────────────────────────────
    # DELETE  (called from a POST form button)
    # ───────────────────────── DELETE assignment ─────────────────────────
    if action == "delete" and pkval and request.method == "POST":
        pkval = int(pkval)              # ensure INT, not str

        conn = dbconnect()              # autocommit = False in helper!
        try:
            with conn.cursor() as cur:
                # 1) remove feedback rows
                cur.execute(
                    "DELETE FROM mmungoshi_feedback WHERE UserTaskID = %s",
                    (pkval,)
                )
            conn.commit()               # ---- FK now sees no children ----

            with conn.cursor() as cur:
                # 2) remove the assignment itself
                cur.execute(
                    "DELETE FROM mmungoshi_user_task WHERE UserTaskID = %s",
                    (pkval,)
                )
            conn.commit()               # final commit
        finally:
            conn.close()

        flash("Assignment and its feedback deleted.", "warning")
        return redirect(url_for('list_user_tasks', user_id=filter_user))


@app.route('/user_tasks/list', methods=['GET','POST'])
def list_user_tasks():
    # ─── Authentication ─────────────────────────────────────────────────────
    if not checkSession():
        return redirect(url_for('login'))

    is_admin       = (session['user']['UserType'] == 'Administrator')
    user_id_filter = request.args.get('user_id') or None
    action         = request.args.get('action')
    pkval          = request.args.get('pkval')

    ut = user_task()

    # ─── Handle deletion ────────────────────────────────────────────────────
    if action == 'delete' and pkval:
        if is_admin:
            ut.deleteById(pkval)
            flash("Assignment deleted.", "warning")
        else:
            flash("You don't have permission to delete assignments.", "danger")
        return redirect(url_for('list_user_tasks', user_id=user_id_filter))

    # ─── Show “New Task” form ───────────────────────────────────────────────
    if action == 'new' and request.method == 'GET':
        ut.createBlank()
        users = user();   users.getAll()
        tasks = task();   tasks.getAll()
        ut.choices = {'users': users.data, 'tasks': tasks.data}
        return render_template('user_tasks/add.html', obj=ut)

    # ─── Process insertion ─────────────────────────────────────────────────
    if action == 'insert' and request.method == 'POST':
        # parse schedule
        sched_dt = f"{request.form['ScheduledDate']} {request.form['ScheduledTime']}"
        try:
            dt = datetime.strptime(sched_dt, '%Y-%m-%d %H:%M')
        except ValueError:
            flash("Invalid date/time.", "danger")
            return redirect(url_for('list_user_tasks', user_id=user_id_filter))

        # master-task: either new or existing
        if request.form.get('task_source') == 'new':
            new_t = task()
            new_t.data = [{ 
              'TaskName':        request.form.get('NewTaskName'),
              'TaskCategory':    request.form.get('NewTaskCategory'),
              'TaskSubcategory': request.form.get('NewTaskSubcategory'),
              'DefaultIntensity':request.form.get('NewDefaultIntensity'),
              'DefaultDuration': request.form.get('NewDefaultDuration')
            }]
            if not new_t.verify_new():
                flash("Error creating master task.", "danger")
                new_t.choices = {'users': user().getAll() or [], 'tasks': []}
                return render_template('user_tasks/add.html', obj=new_t)
            new_t.insert()
            master = new_t.data[0]
        else:
            tm = task(); tm.getAll()
            master_id = request.form['TaskID']
            master    = next((t for t in tm.data if str(t['TaskID']) == master_id), {})

        # compute overrides or defaults
        intensity = request.form.get('Intensity') or master.get('DefaultIntensity')
        duration  = request.form.get('Duration')  or master.get('DefaultDuration')
        try:
            mins = int(duration)
        except:
            mins = int(master.get('DefaultDuration') or 0)
        dt_end = dt + timedelta(minutes=mins)

        ut.set({
            'UserID':         target_user,
            'TaskID':         master['TaskID'],
            'TaskStartTime':  dt.strftime('%Y-%m-%d %H:%M:%S'),
            'TaskEndTime':    dt_end.strftime('%Y-%m-%d %H:%M:%S'),
            'Intensity':      intensity,
            'ActualDuration': duration,
            'TaskStatus':     'pending'
        })
        if ut.verify_new():
            ut.insert()
            flash("Task scheduled.", "success")
            return redirect(url_for('list_user_tasks', user_id=user_id_filter))
        return render_template('user_tasks/add.html', obj=ut)

    # ─── Process edits ─────────────────────────────────────────────────────
    if action == 'edit' and pkval:
        ut.getById(pkval)
        owner = ut.data[0]['UserID']
        if not (is_admin or str(owner) == str(session['user']['UserID'])):
            flash("No permission.", "danger")
            return redirect(url_for('list_user_tasks', user_id=user_id_filter))

        if request.method == 'GET':
            users = user(); users.getAll()
            tasks = task(); tasks.getAll()
            ut.choices = {'users': users.data, 'tasks': tasks.data}
            return render_template('user_tasks/manage.html', obj=ut)

        # POST update
        ut.data[0].update({
            'TaskStatus':     request.form['TaskStatus'],
            'TaskStartTime':  request.form['TaskStartTime'],
            'TaskEndTime':    request.form['TaskEndTime'],
            'Intensity':      request.form['Intensity'],
            'ActualDuration': request.form['Duration']
        })
        ut.update()
        flash("Assignment updated.", "success")
        return redirect(url_for('list_user_tasks', user_id=user_id_filter))

    # ─── Final list of assignments ──────────────────────────────────────────
    # Decide user filter: None = ALL (admin), else a specific ID
    if is_admin:
        uid = None if not user_id_filter else user_id_filter
    else:
        uid = session['user']['UserID']

    # Build base query (no category filter)
    base_q = """
    SELECT
      ut.UserTaskID,
      ut.TaskStartTime,
      ut.TaskEndTime,
      CASE
        WHEN NOW() < ut.TaskStartTime THEN 'pending'
        WHEN NOW() >= ut.TaskStartTime AND NOW() < ut.TaskEndTime THEN 'in_progress'
        ELSE 'completed'
      END AS TaskStatus,
      t.TaskName,
      t.TaskCategory,
      t.TaskSubcategory,
      COALESCE(f.Intensity, t.DefaultIntensity)    AS Intensity,
      COALESCE(f.ActualDuration, t.DefaultDuration) AS ActualDuration
    FROM mmungoshi_user_task AS ut
    JOIN mmungoshi_task     AS t ON ut.TaskID = t.TaskID
    LEFT JOIN mmungoshi_feedback AS f ON f.UserTaskID = ut.UserTaskID
    """

    params = []
    if uid is not None:
        base_q += "\nWHERE ut.UserID = %s"
        params.append(uid)

    base_q += "\nORDER BY ut.TaskStartTime DESC"

    rows = dbselect(base_q, params)

    # Split into the two lists
    flow_tasks   = [r for r in rows if r['TaskCategory'] == 'Flow']
    motion_tasks = [r for r in rows if r['TaskCategory'] == 'Motion']

    # Build user list for admin dropdown
    users = []
    if is_admin:
        um = user(); um.getAll()
        users = um.data

    # Render
    return render_template(
        'user_tasks/list.html',
        flow_tasks=flow_tasks,
        motion_tasks=motion_tasks,
        users=users,
        user_id_filter=user_id_filter
    )

# ─── Planner ─────────────────────────────────────────────────────────────────
@app.route('/planner')
def planner():
    if not checkSession():
        return redirect(url_for('login'))

    uid  = session['user']['UserID']
    mode = session.get('mode')

    query = """
      SELECT
        ut.UserTaskID,
        t.TaskName,
        t.TaskCategory,
        t.TaskSubcategory,

        -- dynamic status based on now vs start/end
        CASE
          WHEN NOW() < ut.TaskStartTime THEN 'pending'
          WHEN NOW() >= ut.TaskStartTime
               AND NOW() < ut.TaskEndTime    THEN 'in_progress'
          ELSE 'completed'
        END AS TaskStatus,

        ut.TaskStartTime,
        ut.TaskEndTime,
        COALESCE(f.MoodBefore, 0) AS MoodBefore,
        COALESCE(f.MoodAfter,  0) AS MoodAfter,
        COALESCE(f.ActualDuration, t.DefaultDuration) AS ActualDuration,
        COALESCE(f.Intensity,       t.DefaultIntensity) AS FeedbackIntensity
      FROM mmungoshi_user_task ut
      JOIN mmungoshi_task      t ON ut.TaskID       = t.TaskID
      LEFT JOIN mmungoshi_feedback f ON f.UserTaskID = ut.UserTaskID
      WHERE ut.UserID = %s
        AND t.TaskCategory = %s
      ORDER BY ut.TaskStartTime
    """

    tasks = dbselect(query, [uid, mode])
    balance_score = compute_balance_score(tasks)

    return render_template(
        'planner.html',
        tasks=tasks,
        balance_score=balance_score
    )

# ─── Reporting APIs ──────────────────────────────────────────────────────────
@app.route('/api/daily_streak')
def api_daily_streak():
    if not checkSession():
        return jsonify(error='login'),401
    uid = session['user']['UserID']
    row = dbselect("""
      WITH days AS (
        SELECT DISTINCT DATE(TaskEndTime) d
        FROM mmungoshi_user_task
        WHERE UserID=%s AND TaskStatus='completed'
      ), runs AS (
        SELECT d, DATE_SUB(d, INTERVAL ROW_NUMBER() OVER (ORDER BY d) DAY) grp
        FROM days
      )
      SELECT COUNT(*) AS streak
      FROM runs
      WHERE grp=(SELECT grp FROM runs ORDER BY d DESC LIMIT 1)
    """, [uid])
    return jsonify(streak=row[0]['streak'] if row else 0)

@app.route('/api/mode_breakdown')
def api_mode_breakdown():
    if not checkSession():
        return jsonify(error='login'),401
    uid = session['user']['UserID']
    rows = dbselect("""
      SELECT t.TaskCategory AS mode,
             SUM(TIMESTAMPDIFF(MINUTE, ut.TaskStartTime, ut.TaskEndTime)) AS total_minutes
      FROM mmungoshi_user_task ut
      JOIN mmungoshi_task t ON t.TaskID=ut.TaskID
      WHERE ut.UserID=%s
      GROUP BY mode
    """, [uid])
    return jsonify(rows)

@app.route('/api/heatmap')
def api_heatmap():
    if not checkSession():
        return jsonify(error='login'),401
    uid = session['user']['UserID']
    rows = dbselect("""
      SELECT HOUR(TaskStartTime) AS hr,
             DAYOFWEEK(TaskStartTime) AS weekday,
             COUNT(*) AS cnt
      FROM mmungoshi_user_task
      WHERE UserID=%s
      GROUP BY hr,weekday
    """, [uid])
    return jsonify(rows)

@app.route('/api/weekly_balance')
def api_weekly_balance():
    if not checkSession():
        return jsonify(error='login'),401
    uid = session['user']['UserID']
    monday = (date.today() - timedelta(days=date.today().weekday())).isoformat()
    row = dbselect("""
      SELECT ROUND(AVG(
        (f.MoodAfter - f.MoodBefore)*f.Intensity*(f.ActualDuration/%s)
      ),2) AS score
      FROM mmungoshi_user_task ut
      JOIN mmungoshi_feedback f ON f.UserTaskID=ut.UserTaskID
      WHERE ut.UserID=%s
        AND f.Timestamp >= %s
        AND f.Timestamp < DATE_ADD(%s, INTERVAL 7 DAY)
    """, [BLOCK_LENGTH, uid, monday, monday])
    return jsonify(week_start=monday, score=row[0]['score'] if row and row[0]['score']!=None else None)

# ─── Feedback Management ─────────────────────────────────────────────────────
@app.route('/feedback/list', methods=['GET','POST'])
def list_feedback():
    if not checkSession():
        return redirect(url_for('login'))

    # ─── 1) Figure out raw filter from GET/POST ──────────────────────────────
    raw_filter = request.values.get('user_id')  # may be None or ''
    is_admin   = (session['user']['UserType']=='Administrator')

    # ─── 2) Normalize into user_id_filter ────────────────────────────────────
    if is_admin:
        # Admin + non-empty raw → that user; Admin + empty → None means “All Users”
        user_id_filter = int(raw_filter) if raw_filter else None
    else:
        # Regular users always only see themselves
        user_id_filter = session['user']['UserID']

    # ─── 3) On POST, allow admins to override via the form’s UserID dropdown ─
    form_user = request.form.get('UserID')
    if is_admin and form_user:
        target_user = int(form_user)
    else:
        target_user = user_id_filter

    fb     = feedback()
    action = request.args.get('action')
    pkval  = request.args.get('pkval')

    # ─── Build TaskName map ───────────────────────────────────────────────────
    tm = task(); tm.getAll()
    tmap = {t['TaskID']: t['TaskName'] for t in tm.data}

    # ─── Prepare the task‐assignment dropdown (scoped by user_id_filter) ────
    ut = user_task()
    if is_admin:
        if user_id_filter is None:
            ut.getAll()
        else:
            ut.getByField('UserID', user_id_filter)
    else:
        ut.getByField('UserID', session['user']['UserID'])

    fb.choices = {
        'tasks': [
            {
              'UserTaskID': r['UserTaskID'],
              'TaskName':   tmap.get(r['TaskID'], '')
            }
            for r in ut.data
        ]
    }

    # ─── Load user list for admin dropdown ───────────────────────────────────
    users = []
    if is_admin:
        um = user(); um.getAll()
        users = um.data

    # ─── DELETE feedback ─────────────────────────────────────────────────────
    if action == 'delete' and pkval:
        fb.delete_feedback_by_id(pkval)
        flash("Feedback deleted.")
        return redirect(url_for('list_feedback', user_id=user_id_filter))

    # ─── INSERT new feedback ─────────────────────────────────────────────────
    if action == 'insert':
        fb.set({
            'Timestamp':      request.form['Timestamp'],
            'MoodBefore':     request.form['MoodBefore'],
            'MoodAfter':      request.form['MoodAfter'],
            'ActualDuration': request.form['ActualDuration'],
            'Intensity':      request.form['Intensity'],
            'UserID':         target_user,
            'UserTaskID':     request.form['UserTaskID'],
            'Comments':       request.form.get('Comments','').strip()
        })
        if fb.verify_new():
            fb.insert()
            flash("Feedback submitted.")
            return redirect(url_for('list_feedback', user_id=user_id_filter))
        return render_template(
            'feedback/add.html',
            obj=fb,
            users=users,
            user_id=user_id_filter
        )

    # ─── UPDATE existing feedback ────────────────────────────────────────────
    if action == 'update' and pkval:
        fb.getById(pkval)
        fb.data[0].update({
            'Timestamp':      request.form['Timestamp'],
            'MoodBefore':     request.form['MoodBefore'],
            'MoodAfter':      request.form['MoodAfter'],
            'ActualDuration': request.form['ActualDuration'],
            'Intensity':      request.form['Intensity'],
            'Comments':       request.form.get('Comments','').strip()
        })
        # allow reassign for admins
        if is_admin and form_user:
            fb.data[0]['UserID'] = target_user

        if fb.verify_update():
            fb.update()
            flash("Feedback updated.")
            return redirect(url_for('list_feedback', user_id=user_id_filter))
        return render_template(
            'feedback/manage.html',
            obj=fb,
            users=users,
            user_id=user_id_filter
        )

    # ─── SHOW NEW-FEEDBACK FORM ──────────────────────────────────────────────
    if pkval == 'new':
        fb.createBlank()
        return render_template(
            'feedback/add.html',
            obj=fb,
            users=users,
            user_id=user_id_filter
        )

    # ─── SHOW EDIT-FEEDBACK FORM ─────────────────────────────────────────────
    if pkval:
        fb.getById(pkval)
        return render_template(
            'feedback/manage.html',
            obj=fb,
            users=users,
            user_id=user_id_filter
        )

    # ─── FINAL LISTING ────────────────────────────────────────────────────────
    if is_admin:
        if user_id_filter is None:
            fb.getAll()
        else:
            fb.getByField('UserID', user_id_filter)
    else:
        fb.getByField('UserID', user_id_filter)

    return render_template(
        'feedback/list.html',
        obj=fb,
        users=users,
        user_id_filter=user_id_filter
    )

# ─── Compute Balance Score ───────────────────────────────────────────────────
def compute_balance_score(tasks):
    if not tasks:
        return "NA"
    total = 0
    for row in tasks:
        mb        = row['MoodBefore']; ma = row['MoodAfter']
        mood_diff = (int(ma)-int(mb)) if (mb is not None and ma is not None) else 0
        intensity = int(row.get('FeedbackIntensity') or row['DefaultIntensity'] or 1)
        duration  = int(row.get('ActualDuration') or row['DefaultDuration'] or BLOCK_LENGTH)
        total    += mood_diff * intensity * (duration / BLOCK_LENGTH)
    return round(total/len(tasks),2)

# ─── DB Helpers ─────────────────────────────────────────────────────────────

def dbconnect():
    """
    Establishes a MySQL connection.
    - On Render: reads credentials from environment variables.
    - Locally: falls back to config.yml in the same folder.
    """
    if os.getenv("DB_HOST"):  # Render / production
        return pymysql.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PW"),
            database=os.getenv("DB_NAME"),
            autocommit=True
        )
    # Fallback for local development
    cfg_path = Path(__file__).parent / "config.yml"
    cfg = yaml.safe_load(cfg_path.read_text())["db"]
    return pymysql.connect(
        host=cfg["host"],
        port=cfg.get("port", 3306),
        user=cfg["user"],
        password=cfg["pw"],
        database=cfg["db"],
        autocommit=True
    )


def dbselect(query, params=None):
    conn = dbconnect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute(query, params or [])
    data = cursor.fetchall()
    conn.close()
    return data


def dbupdate(query, params=None):
    conn = dbconnect()
    cursor = conn.cursor()
    cursor.execute(query, params or [])
    conn.commit()
    conn.close()

# ─── Task History ────────────────────────────────────────────────────────────
@app.route('/task_history')
def task_history():
    if not checkSession():
        return redirect(url_for('login'))

    uid = session['user']['UserID']
    query = """
        SELECT
          ut.UserTaskID,
          t.TaskName,
          t.TaskCategory,
          ut.TaskStatus,
          ut.TaskStartTime,
          ut.TaskEndTime,
          f.MoodBefore,
          f.MoodAfter,
          f.ActualDuration
        FROM mmungoshi_user_task ut
        JOIN mmungoshi_task      t ON ut.TaskID = t.TaskID
        LEFT JOIN mmungoshi_feedback f
          ON f.UserTaskID = ut.UserTaskID
        WHERE ut.UserID = %s
        ORDER BY ut.TaskStartTime DESC
    """
    tasks = dbselect(query, [uid])
    return render_template('task_history_view.html', tasks=tasks)

if __name__ == '__main__':
    app.run(debug=True)
