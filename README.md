<!-- markdownlint-disable MD033 -->
<h1 align="center">
  Shibui <br>
  <small>A balanced planner for work & movement</small>
</h1>

<p align="center">
  <a href="https://github.com/your-org/shibui/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/your-org/shibui/ci.yml?branch=main&logo=github" alt="build">
  </a>
  <img src="https://img.shields.io/badge/python-3.11-blue?logo=python" alt="python">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="license">
</p>

> **by Mutsa Mungoshi**

---

## Table&nbsp;of&nbsp;Contents
- [Table of Contents](#tableofcontents)
- [Overview](#overview)
  - [Users \& permissions](#users--permissions)
  - [Task life-cycle](#task-life-cycle)
- [Test Users](#test-users)
- [Features](#features)
- [Relational Schema](#relational-schema)
  - [Table summary](#table-summary)
- [Analytics examples](#analytics-examples)

---

## Overview
Shibui treats **work (_Flow_)** and **physical activity (_Motion_)** as parallel parts  
of your day—helping you schedule, execute, and reflect on both.

| Flow sub-categories | Motion sub-categories |
|---------------------|-----------------------|
| Deep Work           | Cardio & Endurance    |
| Meetings & Collab   | Strength & Resistance |
| Creative Work       | Flexibility & Recovery|
| Planning & Org.     | Sports & Recreation   |
| Learning & Skills   | Outdoor & Lifestyle   |

### Users & permissions
| Role | Abilities |
|------|-----------|
| 🧑‍💻 **Regular** | choose mode · create / edit **own** tasks · no delete |
| 👑 **Admin**     | assign tasks to any user · full CRUD |

### Task life-cycle
`pending → in_progress → completed`  
*auto-progresses when start / end times elapse*

---

## Test Users
<p align="center">
  <img src="list of test users.png" alt="Test Users" width="800">
</p>

---

## Features
* Intensity, duration & mood tracking (before / after).
* Auto-advancing status + cron job to catch missed transitions.
* Admin dashboard to reassign or delete tasks.
* Pre-defined **Flow / Motion** categories; easy to extend.
* MySQL 8 + Flask / SQLAlchemy backend; Bootstrap 5 frontend.

---

## Relational Schema
<p align="center">
  <img src="relational schema.png" alt="Relational Schema" width="900">
</p>

### Table summary

| Table | Purpose |
|-------|---------|
| **mmungoshi_user** | users & roles |
| **mmungoshi_task** | master tasks (defaults) |
| **mmungoshi_user_task** | scheduled assignments |
| **mmungoshi_feedback** | mood & actuals collected per run |

---

## Analytics examples
> All table names include the `mmungoshi_` prefix.

<details>
<summary>show queries</summary>

```sql
-- 1 · Completed tasks last week by mode
SELECT  t.TaskCategory AS Mode,
        COUNT(*)       AS Completed
FROM    mmungoshi_user_task ut
JOIN    mmungoshi_task      t ON t.TaskID = ut.TaskID
WHERE   ut.TaskStatus  = 'completed'
  AND   ut.TaskEndTime >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
GROUP BY t.TaskCategory;

-- 2 · Average mood delta by sub-category
SELECT  t.TaskSubcategory,
        ROUND(AVG(f.MoodAfter - f.MoodBefore),2) AS AvgMoodDelta
FROM    mmungoshi_feedback      f
JOIN    mmungoshi_user_task     ut ON ut.UserTaskID = f.UserTaskID
JOIN    mmungoshi_task          t  ON t.TaskID      = ut.TaskID
GROUP BY t.TaskSubcategory
ORDER BY AvgMoodDelta DESC;

-- 3 · Top-5 users by Flow minutes this month
SELECT  u.UserName,
        SUM(TIMESTAMPDIFF(MINUTE, ut.TaskStartTime, ut.TaskEndTime)) AS Minutes
FROM    mmungoshi_user_task ut
JOIN    mmungoshi_task      t  ON t.TaskID = ut.TaskID
JOIN    mmungoshi_user      u  ON u.UserID = ut.UserID
WHERE   t.TaskCategory = 'flow'
  AND   MONTH(ut.TaskStartTime) = MONTH(CURDATE())
  AND   YEAR (ut.TaskStartTime) = YEAR (CURDATE())
GROUP BY u.UserID
ORDER BY Minutes DESC
LIMIT 5;
