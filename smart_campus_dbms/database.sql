-- Smart Campus Management System - PostgreSQL Schema
-- Emphasis: 3NF, referential integrity, constraints, views, triggers, procedures

-- Safety: drop existing objects in dev
DO $$ BEGIN
  PERFORM 1 FROM pg_database WHERE datname = 'smart_campus_db';
  -- DB creation handled externally; this file assumes you connect to the DB
EXCEPTION WHEN OTHERS THEN NULL; END $$;

-- Enable extensions commonly useful (optional)
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- for gen_random_uuid

-- SCHEMA
CREATE SCHEMA IF NOT EXISTS scms;
SET search_path TO scms, public;

-- ENUMS
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'gender_enum') THEN
    CREATE TYPE gender_enum AS ENUM ('Male', 'Female', 'Other');
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'event_status_enum') THEN
    CREATE TYPE event_status_enum AS ENUM ('Scheduled', 'Ongoing', 'Completed', 'Cancelled');
  END IF;
END $$;

-- TABLES
CREATE TABLE IF NOT EXISTS admin (
  admin_id        SERIAL PRIMARY KEY,
  name            VARCHAR(100) NOT NULL,
  email           VARCHAR(150) UNIQUE NOT NULL,
  password_hash   TEXT NOT NULL,
  role            VARCHAR(50) NOT NULL DEFAULT 'Admin',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS department (
  department_id   SERIAL PRIMARY KEY,
  name            VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS section (
  section_id      SERIAL PRIMARY KEY,
  name            VARCHAR(10) NOT NULL,
  department_id   INT NOT NULL REFERENCES department(department_id) ON DELETE CASCADE,
  UNIQUE (department_id, name)
);

CREATE TABLE IF NOT EXISTS student (
  student_id      SERIAL PRIMARY KEY,
  name            VARCHAR(120) NOT NULL,
  dob             DATE NOT NULL,
  gender          gender_enum NOT NULL,
  email           VARCHAR(150) UNIQUE NOT NULL,
  phone           VARCHAR(20) UNIQUE,
  password_hash   TEXT NOT NULL,
  department_id   INT NOT NULL REFERENCES department(department_id) ON DELETE RESTRICT,
  section_id      INT REFERENCES section(section_id) ON DELETE SET NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS faculty (
  faculty_id      SERIAL PRIMARY KEY,
  name            VARCHAR(120) NOT NULL,
  email           VARCHAR(150) UNIQUE NOT NULL,
  phone           VARCHAR(20) UNIQUE,
  password_hash   TEXT NOT NULL,
  department_id   INT NOT NULL REFERENCES department(department_id) ON DELETE RESTRICT,
  subject         VARCHAR(150) NOT NULL,
  experience_years INT NOT NULL CHECK (experience_years >= 0),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS course (
  course_id       SERIAL PRIMARY KEY,
  course_code     VARCHAR(20) UNIQUE NOT NULL,
  course_name     VARCHAR(150) NOT NULL,
  credits         INT NOT NULL CHECK (credits BETWEEN 1 AND 10),
  department_id   INT NOT NULL REFERENCES department(department_id) ON DELETE RESTRICT,
  faculty_id      INT REFERENCES faculty(faculty_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS enrollment (
  enroll_id       SERIAL PRIMARY KEY,
  student_id      INT NOT NULL REFERENCES student(student_id) ON DELETE CASCADE,
  course_id       INT NOT NULL REFERENCES course(course_id) ON DELETE CASCADE,
  semester        VARCHAR(20) NOT NULL,
  grade           VARCHAR(2),
  enrolled_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (student_id, course_id, semester)
);

CREATE TABLE IF NOT EXISTS library_book (
  book_id         SERIAL PRIMARY KEY,
  title           VARCHAR(200) NOT NULL,
  author          VARCHAR(150) NOT NULL,
  total_copies    INT NOT NULL CHECK (total_copies >= 0),
  available_copies INT NOT NULL CHECK (available_copies >= 0),
  CHECK (available_copies <= total_copies)
);

CREATE TABLE IF NOT EXISTS book_issue (
  issue_id        SERIAL PRIMARY KEY,
  student_id      INT NOT NULL REFERENCES student(student_id) ON DELETE CASCADE,
  book_id         INT NOT NULL REFERENCES library_book(book_id) ON DELETE CASCADE,
  issue_date      DATE NOT NULL DEFAULT CURRENT_DATE,
  return_date     DATE,
  returned        BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS event (
  event_id        SERIAL PRIMARY KEY,
  event_name      VARCHAR(150) NOT NULL,
  date            DATE NOT NULL,
  venue           VARCHAR(120) NOT NULL,
  status          event_status_enum NOT NULL DEFAULT 'Scheduled',
  created_by_admin INT REFERENCES admin(admin_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS event_registration (
  reg_id          SERIAL PRIMARY KEY,
  event_id        INT NOT NULL REFERENCES event(event_id) ON DELETE CASCADE,
  student_id      INT NOT NULL REFERENCES student(student_id) ON DELETE CASCADE,
  registered_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (event_id, student_id)
);

CREATE TABLE IF NOT EXISTS room (
  room_id         SERIAL PRIMARY KEY,
  room_no         VARCHAR(20) UNIQUE NOT NULL,
  is_lab          BOOLEAN NOT NULL DEFAULT FALSE,
  capacity        INT NOT NULL CHECK (capacity > 0)
);

CREATE TABLE IF NOT EXISTS timetable (
  timetable_id    SERIAL PRIMARY KEY,
  section_id      INT NOT NULL REFERENCES section(section_id) ON DELETE CASCADE,
  course_id       INT NOT NULL REFERENCES course(course_id) ON DELETE CASCADE,
  faculty_id      INT NOT NULL REFERENCES faculty(faculty_id) ON DELETE CASCADE,
  room_id         INT NOT NULL REFERENCES room(room_id) ON DELETE RESTRICT,
  day_of_week     SMALLINT NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
  time_slot       VARCHAR(20) NOT NULL,
  UNIQUE (section_id, day_of_week, time_slot),
  UNIQUE (faculty_id, day_of_week, time_slot),
  UNIQUE (room_id, day_of_week, time_slot)
);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_student_section ON student(section_id);
CREATE INDEX IF NOT EXISTS idx_enrollment_course ON enrollment(course_id);
CREATE INDEX IF NOT EXISTS idx_event_date ON event(date);
CREATE INDEX IF NOT EXISTS idx_book_issue_student ON book_issue(student_id);

-- VIEWS
CREATE OR REPLACE VIEW vw_students_per_course AS
SELECT c.course_id, c.course_code, c.course_name,
       COUNT(e.student_id) AS num_students
FROM course c
LEFT JOIN enrollment e ON e.course_id = c.course_id
GROUP BY c.course_id, c.course_code, c.course_name;

CREATE OR REPLACE VIEW vw_event_participation AS
SELECT ev.event_id, ev.event_name, ev.date, ev.status,
       COUNT(er.student_id) AS participants
FROM event ev
LEFT JOIN event_registration er ON er.event_id = ev.event_id
GROUP BY ev.event_id, ev.event_name, ev.date, ev.status;

CREATE OR REPLACE VIEW vw_library_availability AS
SELECT author, title, total_copies, available_copies
FROM library_book
ORDER BY author, title;

CREATE OR REPLACE VIEW vw_faculty_timetable AS
SELECT f.faculty_id, f.name AS faculty_name,
       t.day_of_week, t.time_slot, r.room_no,
       c.course_code, c.course_name, s.name AS section_name
FROM timetable t
JOIN faculty f ON f.faculty_id = t.faculty_id
JOIN course c ON c.course_id = t.course_id
JOIN section s ON s.section_id = t.section_id
JOIN room r ON r.room_id = t.room_id;

CREATE OR REPLACE VIEW vw_student_timetable AS
SELECT st.student_id, st.name AS student_name,
       t.day_of_week, t.time_slot, r.room_no,
       c.course_code, c.course_name, f.name AS faculty_name,
       s.name AS section_name
FROM student st
JOIN section s ON s.section_id = st.section_id
JOIN timetable t ON t.section_id = s.section_id
JOIN room r ON r.room_id = t.room_id
JOIN course c ON c.course_id = t.course_id
JOIN faculty f ON f.faculty_id = t.faculty_id;

-- FUNCTIONS / PROCEDURES
-- Enrollment validation: ensure student department matches course department
CREATE OR REPLACE FUNCTION fn_validate_enrollment() RETURNS TRIGGER AS $$
DECLARE
  student_dept INT;
  course_dept INT;
BEGIN
  SELECT department_id INTO student_dept FROM student WHERE student_id = NEW.student_id;
  SELECT department_id INTO course_dept FROM course WHERE course_id = NEW.course_id;
  IF student_dept IS NULL OR course_dept IS NULL OR student_dept <> course_dept THEN
    RAISE EXCEPTION 'Student and Course must be in the same department';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_enrollment
BEFORE INSERT OR UPDATE ON enrollment
FOR EACH ROW EXECUTE FUNCTION fn_validate_enrollment();

-- Book issue tracking: decrement/increment available_copies
CREATE OR REPLACE FUNCTION fn_handle_book_issue() RETURNS TRIGGER AS $$
DECLARE
  available INT;
BEGIN
  IF TG_OP = 'INSERT' THEN
    SELECT available_copies INTO available FROM library_book WHERE book_id = NEW.book_id FOR UPDATE;
    IF available IS NULL OR available <= 0 THEN
      RAISE EXCEPTION 'No available copies for book_id %', NEW.book_id;
    END IF;
    UPDATE library_book SET available_copies = available_copies - 1 WHERE book_id = NEW.book_id;
    RETURN NEW;
  ELSIF TG_OP = 'UPDATE' THEN
    IF NEW.returned = TRUE AND (OLD.returned IS DISTINCT FROM TRUE) THEN
      UPDATE library_book SET available_copies = available_copies + 1 WHERE book_id = NEW.book_id;
    END IF;
    RETURN NEW;
  ELSIF TG_OP = 'DELETE' THEN
    IF OLD.returned = FALSE THEN
      UPDATE library_book SET available_copies = available_copies + 1 WHERE book_id = OLD.book_id;
    END IF;
    RETURN OLD;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_book_issue_ins
BEFORE INSERT ON book_issue
FOR EACH ROW EXECUTE FUNCTION fn_handle_book_issue();

CREATE TRIGGER trg_book_issue_upd
AFTER UPDATE ON book_issue
FOR EACH ROW EXECUTE FUNCTION fn_handle_book_issue();

CREATE TRIGGER trg_book_issue_del
AFTER DELETE ON book_issue
FOR EACH ROW EXECUTE FUNCTION fn_handle_book_issue();

-- Automatic timetable update example: prevent conflicts (faculty/room/section)
CREATE OR REPLACE FUNCTION fn_validate_timetable() RETURNS TRIGGER AS $$
BEGIN
  -- Uniqueness is already enforced via UNIQUE constraints; function can enforce labs vs rooms or capacity checks later
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_timetable
BEFORE INSERT OR UPDATE ON timetable
FOR EACH ROW EXECUTE FUNCTION fn_validate_timetable();

-- Reporting helper: students per course in a semester
CREATE OR REPLACE FUNCTION fn_students_per_course(p_semester VARCHAR)
RETURNS TABLE (course_id INT, course_code VARCHAR, course_name VARCHAR, num_students BIGINT) AS $$
BEGIN
  RETURN QUERY
  SELECT c.course_id, c.course_code, c.course_name, COUNT(e.student_id)
  FROM course c
  LEFT JOIN enrollment e ON e.course_id = c.course_id AND e.semester = p_semester
  GROUP BY c.course_id, c.course_code, c.course_name
  ORDER BY c.course_code;
END; $$ LANGUAGE plpgsql STABLE;

-- Seed minimal data for departments and rooms (optional)
INSERT INTO department (name) VALUES ('Computer Science') ON CONFLICT (name) DO NOTHING;
INSERT INTO department (name) VALUES ('Electrical Engineering') ON CONFLICT (name) DO NOTHING;
INSERT INTO department (name) VALUES ('Mechanical Engineering') ON CONFLICT (name) DO NOTHING;

INSERT INTO room (room_no, is_lab, capacity) VALUES ('A101', FALSE, 60)
  ON CONFLICT (room_no) DO NOTHING;
INSERT INTO room (room_no, is_lab, capacity) VALUES ('Lab-CS-1', TRUE, 40)
  ON CONFLICT (room_no) DO NOTHING;

-- Suggested useful queries
-- 1) Section-wise timetable for students
-- SELECT * FROM vw_student_timetable WHERE student_id = 1 ORDER BY day_of_week, time_slot;
-- 2) Faculty timetable with room numbers
-- SELECT * FROM vw_faculty_timetable WHERE faculty_id = 1 ORDER BY day_of_week, time_slot;
-- 3) Students enrolled in each course (by semester)
-- SELECT * FROM fn_students_per_course('Fall-2025');
-- 4) Event participation count per event
-- SELECT * FROM vw_event_participation ORDER BY date DESC;
-- 5) Library books available per author/title
-- SELECT * FROM vw_library_availability;
