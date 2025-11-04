from flask_template.baseObject import baseObject
import pymysql
import hashlib

class user(baseObject):
    def __init__(self):
        self.setup()
        self.user_type = [
            {'value':'Administrator','text':'Administrator'},
            {'value':'Regular','text':'Regular'}
            ]
        
    def hashPassword(self,pw):
        pw = pw+'xyz'
        return hashlib.md5(pw.encode('utf-8')).hexdigest()
    
    def type_list(self):
        tl = []
        for type in self.user_type:
            tl.append(type['value'])
        return tl
    
    def verify_new(self,n=0):
        self.errors = []
        if '@' not in self.data[n]['UserEmail']:
            self.errors.append('Email must contain @')
        if self.data[n]['UserType'] not in self.type_list():
            self.errors.append(f'User type must be one of {self.type_list()}')
        u = user()
        u.getByField('UserEmail',self.data[0]['UserEmail'])
        if len(u.data) > 0:
            self.errors.append(f"Email address is already in use. ({self.data[0]['UserEmail']})")
        if len(self.data[n]['UserPassword']) < 3:
            self.errors.append('Password should be greater than 3 chars.')
        if self.data[n]['UserPassword'] != self.data[n]['UserPassword2']:
            self.errors.append('Retyped password must match.')
        self.data[n]['UserPassword'] = self.hashPassword(self.data[n]['UserPassword'])
        
        if len(self.errors) == 0:
            return True
        else:
            return False
        
    def verify_update(self, n: int = 0) -> bool:
        """Validate a user record before update."""
        self.errors = []
        rec = self.data[n]           # shorthand

        # ─── email checks ─────────────────────────────────────────────
        if '@' not in rec['UserEmail']:
            self.errors.append('Email must contain @')

        if rec['UserType'] not in self.type_list():
            self.errors.append(f"User type must be one of {self.type_list()}")

        u = user()
        u.getByField('UserEmail', rec['UserEmail'])
        if u.data and u.data[0][u.pk] != rec[self.pk]:
            self.errors.append(f"Email address is already in use. ({rec['UserEmail']})")

        # ─── password checks ──────────────────────────────────────────
        pwd1 = rec.get('UserPassword', '')
        pwd2 = rec.get('UserPassword2', '')

        # no change → both boxes left blank
        if not pwd1 and not pwd2:
            rec.pop('UserPassword', None)   # keep existing hash
        else:
            # one empty or mismatch
            if pwd1 != pwd2:
                self.errors.append('Passwords do not match.')
            elif len(pwd1) < 3:
                self.errors.append('Password needs to be more than 3 chars.')
            else:
                rec['UserPassword'] = self.hashPassword(pwd1)

        # ─── final verdict ────────────────────────────────────────────
        return not self.errors

        
    def tryLogin(self,email,pw):
        pw = self.hashPassword(pw)
        sql = f'SELECT * FROM `{self.tn}` WHERE `UserEmail` = %s AND `UserPassword` = %s;'
        tokens = [email,pw]
        print(sql,tokens)
        self.cur.execute(sql,tokens)
        self.data = []
        for row in self.cur:
            self.data.append(row)
        if len(self.data) == 1: 
            return True
        else:
            return False