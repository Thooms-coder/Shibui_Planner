from flask_template.baseObject import baseObject
import datetime

class user_task(baseObject):

    VALID_STATUSES = {'pending', 'in_progress', 'completed'}

    def __init__(self):
        self.setup()

    # ──────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────
    def normalize_status(self, s):
        """Convert any human-entered value into a DB-valid enum literal."""
        if not s:
            return 'pending'

        s = s.strip().lower().replace(" ", "_")
        return s if s in self.VALID_STATUSES else 'pending'

    # ──────────────────────────────────────────────────────────────
    # Validation
    # ──────────────────────────────────────────────────────────────
    def verify_new(self, n=0):
        self.errors = []
        data = self.data[n]

        required = ['UserID', 'TaskID', 'TaskStartTime', 'Intensity', 'ActualDuration']
        for field in required:
            if data.get(field) in (None, ''):
                self.errors.append(f"{field} is required.")

        # Normalize & validate status
        status = self.normalize_status(data.get('TaskStatus'))
        data['TaskStatus'] = status

        if status not in self.VALID_STATUSES:
            self.errors.append("Invalid TaskStatus.")

        return len(self.errors) == 0

    def verify_update(self, n=0):
        """Updates allow partial modification; only validate fields present."""
        self.errors = []
        data = self.data[n]

        if 'TaskStatus' in data:
            data['TaskStatus'] = self.normalize_status(data['TaskStatus'])
            if data['TaskStatus'] not in self.VALID_STATUSES:
                self.errors.append("Invalid TaskStatus.")

        return len(self.errors) == 0

    # ──────────────────────────────────────────────────────────────
    # State Transitions
    # ──────────────────────────────────────────────────────────────
    def start_task(self, user_task_id):
        self.getById(user_task_id)
        if not self.data:
            self.errors.append("User task not found.")
            return False

        row = self.data[0]
        if row['TaskStatus'] != 'pending':
            self.errors.append("Task is not in 'pending' state.")
            return False

        # Only change status
        row['TaskStatus'] = 'in_progress'

        # Only set start time if missing
        if not row.get('TaskStartTime'):
            row['TaskStartTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.update(0)
        return True

    def complete_task(self, user_task_id):
        self.getById(user_task_id)
        if not self.data:
            self.errors.append("User task not found.")
            return False

        row = self.data[0]

        row['TaskStatus'] = 'completed'

        # Only set end time if missing
        if not row.get('TaskEndTime'):
            row['TaskEndTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.update(0)
        return True

