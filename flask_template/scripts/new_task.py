from task import task

# Define the tasks you want to add
sample_tasks = [
    {
        'TaskName': 'Deep Work Session',
        'TaskCategory': 'Flow',
        'TaskSubcategory': 'Deep Work'
    },
    {
        'TaskName': 'Morning Jog',
        'TaskCategory': 'Motion',
        'TaskSubcategory': 'Cardio & Endurance'
    }
]

# Insert them
for tdata in sample_tasks:
    t = task()
    t.set(tdata)
    if t.verify_new():
        t.insert()
        print(f"✅ Inserted task: {tdata['TaskName']}")
    else:
        print(f"❌ Errors for {tdata['TaskName']}: {t.errors}")

