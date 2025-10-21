<!-- markdownlint-disable MD033 -->
<h1 align="center">
  Shibui<br>
  <small>A Balanced Planner for Work and Movement</small>
</h1>

<p align="center">
  <a href="https://github.com/Thooms-coder/Shibui_Planner/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/Thooms-coder/Shibui_Planner/ci.yml?branch=main&logo=github" alt="build">
  </a>
  <img src="https://img.shields.io/badge/python-3.11-blue?logo=python" alt="python">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="license">
</p>

<p align="center"><b>Developed by Mutsa Mungoshi</b></p>

---

## Table of Contents
- [Table of Contents](#table-of-contents)
- [Overview](#overview)
  - [Users and Permissions](#users-and-permissions)
  - [Task Life Cycle](#task-life-cycle)
- [Test Users](#test-users)
- [Features](#features)
- [Relational Schema](#relational-schema)
  - [Table Summary](#table-summary)
- [Analytics Examples](#analytics-examples)

---

## Overview
**Shibui** is a Flask-based web application designed to help users achieve balance between productivity and wellness.  
It treats **work (Flow)** and **physical activity (Motion)** as equally important components of the day—encouraging structured planning, consistent reflection, and data-driven self-awareness.

| Flow Sub-Categories | Motion Sub-Categories |
|----------------------|------------------------|
| Deep Work            | Cardio and Endurance   |
| Meetings and Collab  | Strength and Resistance|
| Creative Work        | Flexibility and Recovery|
| Planning and Org.    | Sports and Recreation |
| Learning and Skills  | Outdoor and Lifestyle  |

---

### Users and Permissions
| Role | Abilities |
|------|------------|
| **Regular User** | Create, edit, and view personal tasks; cannot delete shared or system tasks. |
| **Administrator** | Assign tasks to any user and perform full CRUD operations. |

### Task Life Cycle
`pending → in_progress → completed`  
Tasks automatically progress when their start or end times elapse.

---

## Test Users
<p align="center">
  <img src="list of test users.png" alt="Test Users" width="800">
</p>

---

## Features
- Intensity, duration, and mood tracking before and after each task.  
- Automatic status updates via background scheduler.  
- Administrative dashboard for managing users and tasks.  
- Predefined **Flow** and **Motion** categories with extensible structure.  
- MySQL 8 backend integrated via SQLAlchemy ORM.  
- Bootstrap 5 responsive interface for cross-device accessibility.  

---

## Relational Schema
<p align="center">
  <img src="relational schema.png" alt="Relational Schema" width="900">
</p>

### Table Summary

| Table | Purpose |
|--------|----------|
| **mmungoshi_user** | Stores user profiles and role-based access data. |
| **mmungoshi_task** | Master list of predefined tasks and categories. |
| **mmungoshi_user_task** | Links users to scheduled task instances. |
| **mmungoshi_feedback** | Stores post-task reflections and mood metrics. |

---

## Analytics Examples
> All table names include the `mmungoshi_` prefix.

<details>
<summary>Example SQL Queries</summary>

```sql
-- 1 · Completed tasks last week by mode
SELECT  t.TaskCategory AS Mode,
        COUNT(*) AS Completed
FROM    mmungoshi_user_task ut
JOIN    mmungoshi_task t ON t.TaskID = ut.TaskID
WHERE   ut.TaskStatus = 'completed'
  AND   ut.TaskEndTime >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
GROUP BY t.TaskCategory;

-- 2 · Average mood delta by sub-category
SELECT  t.TaskSubcategory,
        ROUND(AVG(f.MoodAfter - f.MoodBefore), 2) AS AvgMoodDelta
FROM    mmungoshi_feedback f
JOIN    mmungoshi_user_task ut ON ut.UserTaskID = f.UserTaskID
JOIN    mmungoshi_task t ON t.TaskID = ut.TaskID
GROUP BY t.TaskSubcategory
ORDER BY AvgMoodDelta DESC;

-- 3 · Top-5 users by Flow minutes this month
SELECT  u.UserName,
        SUM(TIMESTAMPDIFF(MINUTE, ut.TaskStartTime, ut.TaskEndTime)) AS Minutes
FROM    mmungoshi_user_task ut
JOIN    mmungoshi_task t  ON t.TaskID = ut.TaskID
JOIN    mmungoshi_user u  ON u.UserID = ut.UserID
WHERE   t.TaskCategory = 'flow'
  AND   MONTH(ut.TaskStartTime) = MONTH(CURDATE())
  AND   YEAR (ut.TaskStartTime) = YEAR (CURDATE())
GROUP BY u.UserID
ORDER BY Minutes DESC
LIMIT 5;
