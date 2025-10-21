CREATE TABLE mmungoshi_user
(
  UserID INT AUTO_INCREMENT,
  UserName VARCHAR(100) NOT NULL,
  UserEmail VARCHAR(255) NOT NULL UNIQUE,
  UserPassword VARCHAR(255) NOT NULL,
  UserType ENUM('Administrator', 'Regular') NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (UserID)
);

CREATE TABLE mmungoshi_task
(
  TaskID INT AUTO_INCREMENT,
  TaskName VARCHAR(255) NOT NULL,
  TaskCategory VARCHAR(100) NOT NULL,
  TaskSubcategory VARCHAR(100),
  DefaultDuration INT,  -- Duration might be in minutes
  DefaultIntensity INT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (TaskID)
);

CREATE TABLE mmungoshi_user_task
(
  UserTaskID INT AUTO_INCREMENT,
  TaskStartTime DATETIME NOT NULL,
  TaskEndTime DATETIME,
  TaskStatus ENUM('pending', 'in_progress', 'completed') NOT NULL,
  UserID INT NOT NULL,
  TaskID INT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (UserTaskID),
  FOREIGN KEY (UserID) REFERENCES mmungoshi_user(UserID),
  FOREIGN KEY (TaskID) REFERENCES mmungoshi_task(TaskID)
);

CREATE TABLE mmungoshi_feedback
(
  FeedbackID INT AUTO_INCREMENT,
  Timestamp DATETIME NOT NULL,
  MoodBefore INT,
  MoodAfter INT,
  ActualDuration INT,
  Intensity INT,
  UserID INT NOT NULL,
  UserTaskID INT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (FeedbackID),
  FOREIGN KEY (UserID) REFERENCES mmungoshi_user(UserID),
  FOREIGN KEY (UserTaskID) REFERENCES mmungoshi_user_task(UserTaskID)
);