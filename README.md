<!-- markdownlint-disable MD033 -->
<h1 align="center">
  Shibui<br>
  <small>A Balanced Planner for Work and Movement</small>
</h1>

<p align="center">
  <a href="https://shibui-planner.onrender.com/login" target="_blank">
    <img src="https://img.shields.io/badge/Launch_Live_App-4CAF50?style=for-the-badge" alt="Launch Live App">
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11-blue?logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
</p>

<p align="center"><b>Developed by Mutsa Mungoshi</b></p>

---

## Overview

**Shibui** is a Flask-based web application designed to help users maintain balance between productivity and wellness.  
It organizes daily activities into two equally important domains—**Flow** (work-related tasks) and **Motion** (physical activity)—emphasizing structure, reflection, and consistency throughout the day.

This project demonstrates full-stack design with a MySQL backend, Flask-Session authentication, SQL-based analytics, and a responsive Bootstrap interface.  
The live version currently hosts the **login interface** only, as the original university database has been retired.  

---

## Live Demo

<p align="center">
  <a href="https://shibui-planner.onrender.com/login" target="_blank">
    <img src="https://img.shields.io/badge/Launch_Sh­ibui_Planner-1976D2?style=for-the-badge" alt="Launch Shibui Planner">
  </a>
</p>

> **Note:** The demo displays the live login interface only.  
> Backend database integration was hosted on a university MySQL server and is currently offline.

---

## Table of Contents
- [Overview](#overview)
- [Live Demo](#live-demo)
- [Table of Contents](#table-of-contents)
- [Users and Permissions](#users-and-permissions)
- [Task Life Cycle](#task-life-cycle)
- [Features](#features)
- [Flow and Motion Categories](#flow-and-motion-categories)
- [Relational Schema](#relational-schema)
  - [Table Summary](#table-summary)
- [Analytics Examples](#analytics-examples)
- [Repository Link](#repository-link)

---

## Users and Permissions

| Role | Description |
|------|--------------|
| **Regular User** | Create, edit, and view personal tasks; cannot delete shared or system-defined tasks. |
| **Administrator** | Manage all users, assign shared tasks, and perform full CRUD operations across entities. |

---

## Task Life Cycle

A task progresses through the following states automatically or manually:

```
pending → in_progress → completed
```

Status updates occur dynamically based on scheduled start and end times.

---

## Features

- Two functional modes: **Flow** (work) and **Motion** (physical activity).  
- Intensity, duration, and mood tracking before and after each task.  
- Role-based permissions for users and administrators.  
- Persistent session management using `Flask-Session`.  
- MySQL 8 backend integrated through ORM-style modeling.  
- Clean, responsive Bootstrap 5 interface.  
- Analytical SQL queries for mood, duration, and productivity trends.  

---

## Flow and Motion Categories

| Flow Sub-Categories | Motion Sub-Categories |
|----------------------|------------------------|
| Deep Work            | Cardio and Endurance   |
| Meetings and Collaboration | Strength and Resistance |
| Creative Work        | Flexibility and Recovery |
| Planning and Organization | Sports and Recreation |
| Learning and Skills  | Outdoor and Lifestyle  |

---

## Relational Schema

<p align="center">
  <img src="relational schema.png" alt="Relational Schema" width="850">
</p>

### Table Summary

| Table | Purpose |
|--------|----------|
| **mmungoshi_user** | Stores user credentials, profiles, and access roles. |
| **mmungoshi_task** | Repository of all predefined and user-defined tasks. |
| **mmungoshi_user_task** | Links users to specific task instances with scheduling and mode data. |
| **mmungoshi_feedback** | Records user reflections, mood changes, and performance metrics. |

---

## Analytics Examples

Example SQL queries illustrating Shibui’s analytical capabilities:

```sql
-- 1. Completed tasks last week by mode
SELECT  t.TaskCategory AS Mode,
        COUNT(*) AS Completed
FROM    mmungoshi_user_task ut
JOIN    mmungoshi_task t ON t.TaskID = ut.TaskID
WHERE   ut.TaskStatus = 'completed'
  AND   ut.TaskEndTime >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
GROUP BY t.TaskCategory;

-- 2. Average mood delta by sub-category
SELECT  t.TaskSubcategory,
        ROUND(AVG(f.MoodAfter - f.MoodBefore), 2) AS AvgMoodDelta
FROM    mmungoshi_feedback f
JOIN    mmungoshi_user_task ut ON ut.UserTaskID = f.UserTaskID
JOIN    mmungoshi_task t ON t.TaskID = ut.TaskID
GROUP BY t.TaskSubcategory
ORDER BY AvgMoodDelta DESC;

-- 3. Top 5 users by Flow minutes this month
SELECT  u.UserName,
        SUM(TIMESTAMPDIFF(MINUTE, ut.TaskStartTime, ut.TaskEndTime)) AS Minutes
FROM    mmungoshi_user_task ut
JOIN    mmungoshi_task t  ON t.TaskID = ut.TaskID
JOIN    mmungoshi_user u  ON u.UserID = ut.UserID
WHERE   t.TaskCategory = 'flow'
  AND   MONTH(ut.TaskStartTime) = MONTH(CURDATE())
  AND   YEAR(ut.TaskStartTime) = YEAR(CURDATE())
GROUP BY u.UserID
ORDER BY Minutes DESC
LIMIT 5;
```

---

## Repository Link

📂 [GitHub Repository – Shibui Planner](https://github.com/Thooms-coder/Shibui_Planner)  
🌐 [Live App – Login Demo](https://shibui-planner.onrender.com/login)

---

<p align="center">
  <small>Developed by Mutsa Mungoshi — M.S. in Applied Data Science, Clarkson University</small>
</p>
