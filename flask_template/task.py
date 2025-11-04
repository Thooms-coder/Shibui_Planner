from flask_template.baseObject import baseObject
import pymysql
import hashlib

class task(baseObject):
    # Define valid subcategories for each TaskCategory and their defaults.
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
    
    def verify_new(self, n=0):
        """
        Validate the task record before insertion.
         - Ensures TaskName exists.
         - Ensures TaskCategory is either 'Flow' or 'Motion'.
         - Validates that TaskSubcategory is one of the allowed ones for the given TaskCategory.
         - If valid, assigns default DefaultDuration and DefaultIntensity if missing.
        """
        self.errors = []
        
        # Check TaskName is provided
        if not self.data[n].get('TaskName'):
            self.errors.append('Task name cannot be empty.')
        
        # Check TaskCategory (should be 'Flow' or 'Motion')
        task_category = self.data[n].get('TaskCategory')
        if task_category not in ['Flow', 'Motion']:
            self.errors.append("Task Category must be either 'Flow' or 'Motion'.")
        else:
            # Get the provided TaskSubcategory
            task_subcategory = self.data[n].get('TaskSubcategory')
            if task_category == 'Flow':
                if task_subcategory not in self.FLOW_SUBCATEGORIES:
                    self.errors.append(
                        f"For Flow tasks, TaskSubcategory must be one of: {list(self.FLOW_SUBCATEGORIES.keys())}."
                    )
                else:
                    self.assign_defaults_if_missing(n, self.FLOW_SUBCATEGORIES[task_subcategory])
            elif task_category == 'Motion':
                if task_subcategory not in self.MOTION_SUBCATEGORIES:
                    self.errors.append(
                        f"For Motion tasks, TaskSubcategory must be one of: {list(self.MOTION_SUBCATEGORIES.keys())}."
                    )
                else:
                    self.assign_defaults_if_missing(n, self.MOTION_SUBCATEGORIES[task_subcategory])
                    
        return len(self.errors) == 0
    
    def verify_update(self, n=0):
        ...
        cat  = rec['TaskCategory'].lower().strip()
        sub  = rec['TaskSubcategory'].strip()

        if cat == 'flow' and sub not in FLOW_SUBCATEGORIES:
            self.errors.append(
                f"For Flow tasks, TaskSubcategory must be one of: {FLOW_SUBCATEGORIES}"
            )
        if cat == 'motion' and sub not in MOTION_SUBCATEGORIES:
            self.errors.append(
                f"For Motion tasks, TaskSubcategory must be one of: {MOTION_SUBCATEGORIES}"
            )

    def assign_defaults_if_missing(self, n, defaults):
        """
        Given a dictionary of defaults (with keys 'default_duration' and 'default_intensity'),
        assign DefaultDuration and DefaultIntensity if they are not provided (or falsy).
        """
        if not self.data[n].get('DefaultDuration'):
            self.data[n]['DefaultDuration'] = defaults['default_duration']
        if not self.data[n].get('DefaultIntensity'):
            self.data[n]['DefaultIntensity'] = defaults['default_intensity']
            
    def update_task_details(self, task_id, data):
        """
        Retrieve a task by its ID, update its fields with the provided data dictionary, 
        and apply business logic to revalidate the record. 
        Returns True if successful; otherwise, errors will be set.
        """
        self.getById(task_id)
        if not self.data:
            self.errors.append("Task not found.")
            return False
        
        # Update fields with values from 'data'
        for key, value in data.items():
            if key in self.data[0]:
                self.data[0][key] = value
        
        # Re-run business logic to validate the updated record.
        if not self.verify_new():
            return False
        
        self.update()
        return True

    def delete_task_by_id(self, task_id):
        """
        Delete the task identified by task_id.
        """
        self.deleteById(task_id)
        return True
