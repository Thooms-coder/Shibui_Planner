"""
feedback.py  –  model class for mmungoshi_feedback
"""

from flask_template.baseObject import baseObject
import datetime

class feedback(baseObject):
    def __init__(self):
        self.setup()

    # ──────────────────────────────────────────────────────────
    # Validation
    # ──────────────────────────────────────────────────────────
    def verify_new(self, n: int = 0) -> bool:
        self.errors = []
        data = self.data[n]

        # Required: UserID + Timestamp
        if not data.get('UserID'):
            self.errors.append('UserID is required.')
        if not data.get('Timestamp'):
            self.errors.append('Timestamp is required.')
        else:
            # Normalize timestamp
            try:
                raw = data['Timestamp']
                dt = datetime.datetime.fromisoformat(raw.replace(" ", "T"))
                data['Timestamp'] = dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                self.errors.append("Invalid timestamp format.")

        # Validate MoodBefore and MoodAfter if present
        for mood_field in ('MoodBefore', 'MoodAfter'):
            val = data.get(mood_field)
            if val not in (None, '', ' '):
                try:
                    mv = int(val)
                    if not 1 <= mv <= 10:
                        self.errors.append(f"{mood_field} must be between 1 and 10.")
                except:
                    self.errors.append(f"{mood_field} must be an integer.")

        # Comments optional — validate type
        comments = data.get('Comments', '')
        if comments is not None and not isinstance(comments, str):
            self.errors.append("Comments must be text.")

        return not self.errors

    def verify_update(self, n: int = 0) -> bool:
        return self.verify_new(n)

    # ──────────────────────────────────────────────────────────
    # CRUD Convenience
    # ──────────────────────────────────────────────────────────
    def insert_feedback(self, n: int = 0) -> bool:
        if not self.verify_new(n):
            return False
        self.insert(n)
        return True

    def update_feedback(self, feedback_id: int, data: dict) -> bool:
        self.getById(feedback_id)
        if not self.data:
            self.errors.append('Feedback not found.')
            return False

        for key, value in data.items():
            if key in self.data[0]:
                self.data[0][key] = value

        if not self.verify_update(0):
            return False

        self.update(0)
        return True

    def delete_feedback_by_id(self, feedback_id: int) -> bool:
        self.deleteById(feedback_id)
        return True

    def get_feedback_by_user(self, user_id: int):
        self.getByField('UserID', user_id)
        return self.data
