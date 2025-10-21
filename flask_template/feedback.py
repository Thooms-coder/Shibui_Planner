"""
feedback.py  –  model class for mmungoshi_feedback
Extends baseObject with:

• verify_new()      – validation for inserts
• verify_update()   – same rules, exposed for edits
• insert_feedback() – wrapper that validates then inserts
• update_feedback() – loads → merges → validates → updates
• delete_feedback_by_id()
• get_feedback_by_user()
"""

from baseObject import baseObject
import datetime


class feedback(baseObject):
    def __init__(self):
        self.setup()        # baseObject wires up .data, .errors, etc.

    # ──────────────────────────────────────────────────────────
    # Validation helpers
    # ──────────────────────────────────────────────────────────
    def verify_new(self, n: int = 0) -> bool:
        """
        Common validation rules:

        • UserID      required
        • Timestamp   required
        • Mood (optional) must be int 1-10
        • Comments    non-empty
        """
        self.errors = []
        data = self.data[n]

        # Required
        if not data.get('UserID'):
            self.errors.append('UserID is required.')
        if not data.get('Timestamp'):
            self.errors.append('Timestamp is required.')

        # Optional mood
        if 'Mood' in data and data['Mood'] is not None:
            try:
                mood_val = int(data['Mood'])
                if not 1 <= mood_val <= 10:
                    self.errors.append('Mood must be between 1 and 10.')
            except (TypeError, ValueError):
                self.errors.append('Mood must be an integer.')

        # Comments
        comments = data.get('Comments', '')
        if not comments or not comments.strip():
            self.errors.append('Comments cannot be empty.')

        return not self.errors

    def verify_update(self, n: int = 0) -> bool:
        """
        Edits currently follow the same rules as inserts.
        Extend here if you need special update-only constraints.
        """
        return self.verify_new(n)

    # ──────────────────────────────────────────────────────────
    # CRUD convenience methods
    # ──────────────────────────────────────────────────────────
    def insert_feedback(self, n: int = 0) -> bool:
        """Validate then insert a new record."""
        if not self.verify_new(n):
            return False
        self.insert(n)
        return True

    def update_feedback(self, feedback_id: int, data: dict) -> bool:
        """
        Steps:
        1. Load existing row
        2. Merge supplied fields
        3. Re-validate with verify_update()
        4. Persist
        """
        self.getById(feedback_id)
        if not self.data:
            self.errors.append('Feedback not found.')
            return False

        # merge
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
