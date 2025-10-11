Smart Campus Management System (SCMS)

Overview
- PostgreSQL-centered academic project focusing on schema design, SQL operations, views, triggers, procedures, and integrity.
- Flask + SQLAlchemy backend for authentication and CRUD.
- Simple HTML/CSS templates for dashboards.

Requirements
- Python 3.10+
- PostgreSQL 13+

Setup
1) Create database and user (example):
   psql -U postgres -c "CREATE DATABASE smart_campus_db;"
   psql -U postgres -c "CREATE USER user WITH PASSWORD 'password';"
   psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE smart_campus_db TO user;"

2) Clone and install deps:
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt

3) Configure environment:
   Copy .env and set DATABASE_URL, SECRET_KEY

4) Apply schema (run once or on updates):
   python init_db.py

5) Run app:
   flask --app app.py run
   # or
   python app.py

Default Features
- Role-based login (Admin, Faculty, Student)
- Admin: create users, manage events, basic stats
- Faculty: view timetable, update grades
- Student: view timetable, enrollments, register for events
- Reports: students per course, event participation

Key SQL Objects
- 3NF tables with FKs (ON DELETE rules), unique constraints, check constraints
- Views: vw_students_per_course, vw_event_participation, vw_faculty_timetable, vw_student_timetable
- Triggers: enrollment validation, book issue inventory update, timetable validation stub
- Function: fn_students_per_course(semester)

Notes
- The schema lives in schema scms; ensure search_path includes scms or fully qualify names.
- Models mirror the schema and enums; types are pre-created in SQL.
- For demo, seed departments and rooms are inserted in the SQL file.
