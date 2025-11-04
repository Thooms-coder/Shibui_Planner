from flask_template.baseObject import baseObject
import datetime

class user_task(baseObject):
    def __init__(self):
        self.setup()

    def is_valid_status(self, status: str) -> bool:
        """Return True if status is one of the allowed literals."""
        valid = {'pending', 'in_progress', 'completed'}   # ← UPDATED
        return status in valid

    def verify_new(self, n=0):
        """
        Validate a new user_task assignment before insert.
        Checks required fields and status validity.
        """
        self.errors = []
        data = self.data[n]

        # Required fields for scheduling
        required_fields = [
            'UserID',
            'TaskID',
            'TaskStartTime',
            'Intensity',
            'ActualDuration',
            'TaskStatus'
        ]
        for field in required_fields:
            if not data.get(field):
                self.errors.append(f"{field} is required.")

        # Validate status value
        if not self.is_valid_status(data.get('TaskStatus', '')):
            self.errors.append('Invalid TaskStatus.')

        return len(self.errors) == 0

    def verify_update(self, n=0):
        """
        For updates, use the same validation as for new assignments.
        """
        return self.verify_new(n)

    def start_task(self, user_task_id):
        """
        Transition a task from 'Pending' to 'In Progress'.
        Record TaskStartTime if not already set.
        """
        self.getById(user_task_id)
        if not self.data:
            self.errors.append("User task not found.")
            return False
        if self.data[0]['TaskStatus'] != 'Pending':
            self.errors.append("Task is not in 'Pending' state.")
            return False
        self.data[0]['TaskStatus'] = 'In Progress'
        if not self.data[0].get('TaskStartTime'):
            self.data[0]['TaskStartTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.update()
        return True

    def complete_task(self, user_task_id):
        """
        Transition a task from any valid status to 'Complete',
        recording TaskEndTime if not already set.
        """
        self.getById(user_task_id)
        if not self.data:
            self.errors.append("User task not found.")
            return False
        self.data[0]['TaskStatus'] = 'Complete'
        if not self.data[0].get('TaskEndTime'):
            self.data[0]['TaskEndTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.update()
        return True

