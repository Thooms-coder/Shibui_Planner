from flask_template.baseObject import baseObject

class task(baseObject):

    FLOW_SUBCATEGORIES = {
        'Deep Work': {'default_duration': 8, 'default_intensity': 7},
        'Meetings & Collaboration': {'default_duration': 6, 'default_intensity': 5},
        'Creative Work': {'default_duration': 7, 'default_intensity': 8},
        'Planning & Organization': {'default_duration': 5, 'default_intensity': 4},
        'Learning & Skill Development': {'default_duration': 6, 'default_intensity': 6}
    }

    MOTION_SUBCATEGORIES = {
        'Cardio & Endurance': {'default_duration': 7, 'default_intensity': 8},
        'Strength & Resistance': {'default_duration': 6, 'default_intensity': 9},
        'Flexibility & Recovery': {'default_duration': 5, 'default_intensity': 4},
        'Sports & Recreation': {'default_duration': 8, 'default_intensity': 7},
        'Outdoor & Active Lifestyle': {'default_duration': 7, 'default_intensity': 6}
    }

    def __init__(self):
        self.setup()

    # ──────────────────────────────────────────────────────────
    # Validation
    # ──────────────────────────────────────────────────────────
    def _validate_core(self, rec):
        """Validate TaskName, TaskCategory, TaskSubcategory, and defaults."""
        errors = []

        # TaskName required
        if not rec.get('TaskName') or not str(rec['TaskName']).strip():
            errors.append("Task name cannot be empty.")

        # Category must be Flow or Motion
        cat = rec.get('TaskCategory')
        if cat not in ['Flow', 'Motion']:
            errors.append("Task Category must be either 'Flow' or 'Motion'.")
            return errors    # stop here

        # Validate Subcategory
        sub = rec.get('TaskSubcategory')
        if cat == 'Flow':
            if sub not in self.FLOW_SUBCATEGORIES:
                errors.append(f"TaskSubcategory must be one of: {list(self.FLOW_SUBCATEGORIES.keys())}")
            else:
                self._assign_defaults_if_missing(rec, self.FLOW_SUBCATEGORIES[sub])

        elif cat == 'Motion':
            if sub not in self.MOTION_SUBCATEGORIES:
                errors.append(f"TaskSubcategory must be one of: {list(self.MOTION_SUBCATEGORIES.keys())}")
            else:
                self._assign_defaults_if_missing(rec, self.MOTION_SUBCATEGORIES[sub])

        return errors

    def verify_new(self, n=0):
        rec = self.data[n]
        self.errors = self._validate_core(rec)
        return len(self.errors) == 0

    def verify_update(self, n=0):
        rec = self.data[n]
        self.errors = self._validate_core(rec)
        return len(self.errors) == 0

    # ──────────────────────────────────────────────────────────
    # Helper for defaults
    # ──────────────────────────────────────────────────────────
    def _assign_defaults_if_missing(self, rec, defaults):
        """Assign default duration/intensity if empty or missing."""
        if not rec.get('DefaultDuration') or str(rec.get('DefaultDuration')).strip() == "":
            rec['DefaultDuration'] = defaults['default_duration']

        if not rec.get('DefaultIntensity') or str(rec.get('DefaultIntensity')).strip() == "":
            rec['DefaultIntensity'] = defaults['default_intensity']

    # ──────────────────────────────────────────────────────────
    # Update Task wrapper
    # ──────────────────────────────────────────────────────────
    def update_task_details(self, task_id, data):
        self.getById(task_id)
        if not self.data:
            self.errors.append("Task not found.")
            return False

        # Merge fields
        for k, v in data.items():
            if k in self.data[0]:
                self.data[0][k] = v

        # Validate
        if not self.verify_update(0):
            return False

        # Persist
        self.update(0)
        return True

    # ──────────────────────────────────────────────────────────
    # Delete
    # ──────────────────────────────────────────────────────────
    def delete_task_by_id(self, task_id):
        self.deleteById(task_id)
        return True
