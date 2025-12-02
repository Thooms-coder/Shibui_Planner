from flask_template.baseObject import baseObject
import hashlib


class user(baseObject):
    def __init__(self):
        self.setup()
        self.user_type = [
            {'value': 'Administrator', 'text': 'Administrator'},
            {'value': 'Regular', 'text': 'Regular'}
        ]

    # ----------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------
    def hashPassword(self, pw):
        pw = pw + 'xyz'
        return hashlib.md5(pw.encode('utf-8')).hexdigest()

    def type_list(self):
        return [t['value'] for t in self.user_type]

    # ----------------------------------------------------------------------
    # Validation for new user insert
    # ----------------------------------------------------------------------
    def verify_new(self, n=0):
        self.errors = []
        rec = self.data[n]

        # Email check
        if '@' not in rec.get('UserEmail', ''):
            self.errors.append('Email must contain @')

        if rec.get('UserType') not in self.type_list():
            self.errors.append(f"User type must be one of {self.type_list()}")

        # Check email duplication
        u = user()
        u.getByField('UserEmail', rec.get('UserEmail', ''))
        if len(u.data) > 0:
            self.errors.append(f"Email address is already in use. ({rec.get('UserEmail')})")

        # Password checks
        pwd1 = rec.get('UserPassword', '')
        pwd2 = rec.get('UserPassword2', '')

        if len(pwd1) < 3:
            self.errors.append('Password should be greater than 3 chars.')

        if pwd1 != pwd2:
            self.errors.append('Retyped password must match.')

        # Only hash if valid
        if not self.errors:
            rec['UserPassword'] = self.hashPassword(pwd1)
            rec.pop('UserPassword2', None)
            return True

        return False

    # ----------------------------------------------------------------------
    # Validation for updates
    # ----------------------------------------------------------------------
    def verify_update(self, n=0):
        """Validate a user record before update."""
        self.errors = []
        rec = self.data[n]

        # Email checks
        if '@' not in rec.get('UserEmail', ''):
            self.errors.append('Email must contain @')

        if rec.get('UserType') not in self.type_list():
            self.errors.append(f"User type must be one of {self.type_list()}")

        # duplicate email check (exclude self)
        u = user()
        u.getByField('UserEmail', rec.get('UserEmail'))
        if u.data and u.data[0][u.pk] != rec[self.pk]:
            self.errors.append(f"Email address is already in use. ({rec.get('UserEmail')})")

        # Password checks
        pwd1 = rec.get('UserPassword', '')
        pwd2 = rec.get('UserPassword2', '')

        if not pwd1 and not pwd2:
            # No password change requested
            rec.pop('UserPassword', None)
        else:
            if pwd1 != pwd2:
                self.errors.append('Passwords do not match.')
            elif len(pwd1) < 3:
                self.errors.append('Password needs to be more than 3 chars.')
            else:
                rec['UserPassword'] = self.hashPassword(pwd1)

        # Remove extra field
        rec.pop('UserPassword2', None)

        return not self.errors

    # ----------------------------------------------------------------------
    # Authentication
    # ----------------------------------------------------------------------
    def tryLogin(self,email,pw):
        print("TRYLOGIN INPUT:", email, pw)

        pw = self.hashPassword(pw)
        print("HASHED PW:", pw)

        sql = f"SELECT * FROM `{self.tn}` WHERE `UserEmail` = %s AND `UserPassword` = %s;"
        print("SQL:", sql)
        print("PARAMS:", [email, pw])

        self.cur.execute(sql, [email, pw])
        self.data = list(self.cur.fetchall())
        print("QUERY RESULT:", self.data)

        return len(self.data) == 1