from flask_template.user import user
u = user()
d = {'UserName': 'Gordi', 'UserEmail': 'gordi@yahoo.com', 'UserPassword': 'abc', 'UserPassword2': 'abc', 'UserType': 'Regular'}
u.set(d)
if u.verify_new():
    u.insert()
    print("Inserted:", u.data[0])
else:
    print(u.errors)
