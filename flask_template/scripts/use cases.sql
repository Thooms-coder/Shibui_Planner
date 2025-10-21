--SQL Queries

--Registering a new user

INSERT INTO mmungoshi_user (UserName, UserEmail, UserPassword, UserType)
VALUES ('Randy', 'randy@example.com', 'hashedpassword', 'Regular');

--Login verification

SELECT * FROM mmungoshi_user
WHERE UserEmail = 'jane@example.com'
AND UserPassword = 'hashedpassword';

--Get Tasks Assigned to Current User

SELECT ut.*, t.TaskName, t.TaskCategory
FROM mmungoshi_user_task ut, mmungoshi_task t
WHERE ut.TaskID = t.TaskID
AND ut.UserID = 3;

--Create a new task template

INSERT INTO mmungoshi_task (...) VALUES (...);

--Start a Task (Change Status + Set Start Time)

UPDATE mmungoshi_user_task
SET TaskStatus = 'In Progress', TaskStartTime = NOW()
WHERE UserTaskID = 12
AND UserID = ...;

--Submit Feedback

INSERT INTO mmungoshi_feedback
(Timestamp, MoodBefore, MoodAfter, ActualDuration, Intensity, UserID, UserTaskID)
VALUES (NOW(), 6, 9, 50, 7, 2, 12);