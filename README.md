# Campus Database Management System

A full-stack campus management system built with Flask and PostgreSQL, covering students, faculty, courses, and enrollments.

---

## About

A structured database-driven web application that manages core campus operations through a clean admin interface and a well-designed relational database backend.

---

## Features

**Database Design**
- Normalized PostgreSQL database for students, faculty, courses, and enrollments
- Triggers and stored procedures to automate data validation and enforce business rules

**SQL & Querying**
- Queries with joins, subqueries, and aggregations for reports
- SQL injection prevention through parameterized queries

**Admin Panel**
- Flask-based admin panel with full CRUD operations
- Role-based access control for admin, faculty, and students
- Separate dashboards for each role

---

## Tech Stack

| Layer       | Technology              |
|-------------|-------------------------|
| Language    | Python, PLpgSQL         |
| Backend     | Flask                   |
| Database    | PostgreSQL              |
| Frontend    | HTML, CSS, JavaScript   |

---


**Installation**

```bash
git clone https://github.com/suhani-1702/CampusDatabaseManagementSystem.git
cd CampusDatabaseManagementSystem/smart_campus_dbms
pip install -r requirements.txt
```

---

## Project Structure

```
smart_campus_dbms/
├── templates/
│   ├── login.html
│   ├── admin_dashboard.html
│   ├── faculty_dashboard.html
│   ├── student_dashboard.html
│   ├── events.html
│   └── timetable.html
├── static/
│   ├── script.js
│   └── style.css
├── app.py           # Flask application
├── models.py        # Database models
├── init_db.py       # Database initialisation
├── database.sql     # SQL schema and procedures
├── requirements.txt
└── .env
```

---

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Database Normalization — Wikipedia](https://en.wikipedia.org/wiki/Database_normalization)
- [SQL Joins — Wikipedia](https://en.wikipedia.org/wiki/Join_(SQL))
- [PLpgSQL — PostgreSQL Triggers & Procedures](https://www.postgresql.org/docs/current/plpgsql.html)
- [Flask CRUD Tutorial — YouTube](https://www.youtube.com/results?search_query=flask+crud+postgresql+tutorial)

---

## Authors

Suhani Rayal — [@suhani-1702](https://github.com/suhani-1702)
