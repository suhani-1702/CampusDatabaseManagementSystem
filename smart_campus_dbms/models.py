from __future__ import annotations

from datetime import date, datetime
from typing import Optional, List

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum, UniqueConstraint, CheckConstraint, func
from sqlalchemy.dialects.postgresql import ENUM


db = SQLAlchemy()


# Enums
GenderEnum = ENUM('Male', 'Female', 'Other', name='gender_enum', create_type=False)
EventStatusEnum = ENUM('Scheduled', 'Ongoing', 'Completed', 'Cancelled', name='event_status_enum', create_type=False)


class Admin(db.Model):
    __tablename__ = 'admin'
    __table_args__ = {'schema': 'scms'}

    admin_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(50), nullable=False, default='Admin')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())


class Department(db.Model):
    __tablename__ = 'department'
    __table_args__ = {'schema': 'scms'}

    department_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    sections = db.relationship('Section', back_populates='department', cascade='all, delete-orphan')
    students = db.relationship('Student', back_populates='department')
    faculty_members = db.relationship('Faculty', back_populates='department')
    courses = db.relationship('Course', back_populates='department')


class Section(db.Model):
    __tablename__ = 'section'
    __table_args__ = (
        UniqueConstraint('department_id', 'name', name='uq_section_dept_name'),
        {'schema': 'scms'}
    )

    section_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('scms.department.department_id', ondelete='CASCADE'), nullable=False)

    department = db.relationship('Department', back_populates='sections')
    students = db.relationship('Student', back_populates='section')
    timetables = db.relationship('Timetable', back_populates='section', cascade='all, delete-orphan')


class Student(db.Model):
    __tablename__ = 'student'
    __table_args__ = {'schema': 'scms'}

    student_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(GenderEnum, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('scms.department.department_id', ondelete='RESTRICT'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('scms.section.section_id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())

    department = db.relationship('Department', back_populates='students')
    section = db.relationship('Section', back_populates='students')
    enrollments = db.relationship('Enrollment', back_populates='student', cascade='all, delete-orphan')
    event_registrations = db.relationship('EventRegistration', back_populates='student', cascade='all, delete-orphan')
    book_issues = db.relationship('BookIssue', back_populates='student', cascade='all, delete-orphan')


class Faculty(db.Model):
    __tablename__ = 'faculty'
    __table_args__ = {'schema': 'scms'}

    faculty_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('scms.department.department_id', ondelete='RESTRICT'), nullable=False)
    subject = db.Column(db.String(150), nullable=False)
    experience_years = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())

    department = db.relationship('Department', back_populates='faculty_members')
    courses = db.relationship('Course', back_populates='faculty')
    timetables = db.relationship('Timetable', back_populates='faculty', cascade='all, delete-orphan')


class Course(db.Model):
    __tablename__ = 'course'
    __table_args__ = {'schema': 'scms'}

    course_id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    course_name = db.Column(db.String(150), nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('scms.department.department_id', ondelete='RESTRICT'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('scms.faculty.faculty_id', ondelete='SET NULL'))

    department = db.relationship('Department', back_populates='courses')
    faculty = db.relationship('Faculty', back_populates='courses')
    enrollments = db.relationship('Enrollment', back_populates='course', cascade='all, delete-orphan')
    timetables = db.relationship('Timetable', back_populates='course', cascade='all, delete-orphan')


class Enrollment(db.Model):
    __tablename__ = 'enrollment'
    __table_args__ = (
        UniqueConstraint('student_id', 'course_id', 'semester', name='uq_enrollment_unique'),
        {'schema': 'scms'}
    )

    enroll_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('scms.student.student_id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('scms.course.course_id', ondelete='CASCADE'), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    grade = db.Column(db.String(2))
    enrolled_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())

    student = db.relationship('Student', back_populates='enrollments')
    course = db.relationship('Course', back_populates='enrollments')


class LibraryBook(db.Model):
    __tablename__ = 'library_book'
    __table_args__ = (
        CheckConstraint('available_copies >= 0', name='ck_available_nonnegative'),
        CheckConstraint('total_copies >= 0', name='ck_total_nonnegative'),
        {'schema': 'scms'}
    )

    book_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    total_copies = db.Column(db.Integer, nullable=False)
    available_copies = db.Column(db.Integer, nullable=False)

    issues = db.relationship('BookIssue', back_populates='book', cascade='all, delete-orphan')


class BookIssue(db.Model):
    __tablename__ = 'book_issue'
    __table_args__ = {'schema': 'scms'}

    issue_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('scms.student.student_id', ondelete='CASCADE'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('scms.library_book.book_id', ondelete='CASCADE'), nullable=False)
    issue_date = db.Column(db.Date, nullable=False, default=date.today)
    return_date = db.Column(db.Date)
    returned = db.Column(db.Boolean, nullable=False, default=False)

    student = db.relationship('Student', back_populates='book_issues')
    book = db.relationship('LibraryBook', back_populates='issues')


class Event(db.Model):
    __tablename__ = 'event'
    __table_args__ = {'schema': 'scms'}

    event_id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(150), nullable=False)
    date = db.Column(db.Date, nullable=False)
    venue = db.Column(db.String(120), nullable=False)
    status = db.Column(EventStatusEnum, nullable=False, server_default='Scheduled')
    created_by_admin = db.Column(db.Integer, db.ForeignKey('scms.admin.admin_id', ondelete='SET NULL'))

    registrations = db.relationship('EventRegistration', back_populates='event', cascade='all, delete-orphan')


class EventRegistration(db.Model):
    __tablename__ = 'event_registration'
    __table_args__ = (
        UniqueConstraint('event_id', 'student_id', name='uq_event_student'),
        {'schema': 'scms'}
    )

    reg_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('scms.event.event_id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('scms.student.student_id', ondelete='CASCADE'), nullable=False)
    registered_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())

    event = db.relationship('Event', back_populates='registrations')
    student = db.relationship('Student', back_populates='event_registrations')


class Room(db.Model):
    __tablename__ = 'room'
    __table_args__ = {'schema': 'scms'}

    room_id = db.Column(db.Integer, primary_key=True)
    room_no = db.Column(db.String(20), unique=True, nullable=False)
    is_lab = db.Column(db.Boolean, nullable=False, default=False)
    capacity = db.Column(db.Integer, nullable=False)

    timetables = db.relationship('Timetable', back_populates='room')


class Timetable(db.Model):
    __tablename__ = 'timetable'
    __table_args__ = (
        UniqueConstraint('section_id', 'day_of_week', 'time_slot', name='uq_tt_section_slot'),
        UniqueConstraint('faculty_id', 'day_of_week', 'time_slot', name='uq_tt_faculty_slot'),
        UniqueConstraint('room_id', 'day_of_week', 'time_slot', name='uq_tt_room_slot'),
        {'schema': 'scms'}
    )

    timetable_id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('scms.section.section_id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('scms.course.course_id', ondelete='CASCADE'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('scms.faculty.faculty_id', ondelete='CASCADE'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('scms.room.room_id', ondelete='RESTRICT'), nullable=False)
    day_of_week = db.Column(db.SmallInteger, nullable=False)
    time_slot = db.Column(db.String(20), nullable=False)

    section = db.relationship('Section', back_populates='timetables')
    course = db.relationship('Course', back_populates='timetables')
    faculty = db.relationship('Faculty', back_populates='timetables')
    room = db.relationship('Room', back_populates='timetables')


# Utility factory helpers

def create_admin(name: str, email: str, password_hash: str) -> Admin:
    admin = Admin(name=name, email=email, password_hash=password_hash)
    db.session.add(admin)
    return admin


def create_student(**kwargs) -> Student:
    student = Student(**kwargs)
    db.session.add(student)
    return student


def create_faculty(**kwargs) -> Faculty:
    faculty = Faculty(**kwargs)
    db.session.add(faculty)
    return faculty
