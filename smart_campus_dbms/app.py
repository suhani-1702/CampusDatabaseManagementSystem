import os
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

from models import db, Admin, Student, Faculty, Department, Section, Course, Enrollment, Event, EventRegistration, Timetable, Room, LibraryBook, BookIssue


def create_app():
    load_dotenv()
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

    database_url = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/smart_campus_db')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Auth helpers
    def login_required(role=None):
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                if 'user_id' not in session or 'role' not in session:
                    return redirect(url_for('login'))
                if role and session.get('role') != role:
                    flash('Unauthorized access', 'danger')
                    return redirect(url_for('login'))
                return f(*args, **kwargs)
            return wrapper
        return decorator

    @app.route('/')
    def index():
        if 'role' in session:
            if session['role'] == 'Admin':
                return redirect(url_for('admin_dashboard'))
            if session['role'] == 'Faculty':
                return redirect(url_for('faculty_dashboard'))
            if session['role'] == 'Student':
                return redirect(url_for('student_dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            role = request.form.get('role')

            if role == 'Admin':
                user = Admin.query.filter_by(email=email).first()
            elif role == 'Faculty':
                user = Faculty.query.filter_by(email=email).first()
            else:
                user = Student.query.filter_by(email=email).first()

            if user and check_password_hash(user.password_hash, password):
                session['user_id'] = getattr(user, f"{role.lower()}_id", None) or getattr(user, 'admin_id', None)
                session['role'] = role
                flash('Logged in successfully', 'success')
                if role == 'Admin':
                    return redirect(url_for('admin_dashboard'))
                if role == 'Faculty':
                    return redirect(url_for('faculty_dashboard'))
                return redirect(url_for('student_dashboard'))
            flash('Invalid credentials', 'danger')
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    # Admin routes
    @app.route('/admin')
    @login_required(role='Admin')
    def admin_dashboard():
        stats = {
            'students': Student.query.count(),
            'faculty': Faculty.query.count(),
            'courses': Course.query.count(),
            'events': Event.query.count(),
        }
        recent_events = Event.query.order_by(Event.date.desc()).limit(10).all()
        return render_template('admin_dashboard.html', stats=stats, events=recent_events)

    @app.route('/admin/create_user', methods=['POST'])
    @login_required(role='Admin')
    def admin_create_user():
        user_type = request.form.get('user_type')
        name = request.form.get('name', '')
        email = request.form.get('email', '').lower()
        password = request.form.get('password', '')
        department_id = request.form.get('department_id')
        section_id = request.form.get('section_id')
        subject = request.form.get('subject')
        experience_years = request.form.get('experience_years')

        pwd_hash = generate_password_hash(password)

        if user_type == 'Faculty':
            faculty = Faculty(
                name=name,
                email=email,
                password_hash=pwd_hash,
                department_id=int(department_id),
                subject=subject or 'General',
                experience_years=int(experience_years or 0)
            )
            db.session.add(faculty)
        elif user_type == 'Student':
            student = Student(
                name=name,
                email=email,
                password_hash=pwd_hash,
                department_id=int(department_id),
                section_id=int(section_id) if section_id else None,
                dob=datetime(2000, 1, 1).date(),
                gender='Other'
            )
            db.session.add(student)
        else:
            admin = Admin(name=name, email=email, password_hash=pwd_hash)
            db.session.add(admin)
        db.session.commit()
        flash(f'{user_type} created', 'success')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/events', methods=['GET', 'POST'])
    @login_required(role='Admin')
    def admin_events():
        if request.method == 'POST':
            name = request.form.get('event_name')
            date_str = request.form.get('date')
            venue = request.form.get('venue')
            status = request.form.get('status', 'Scheduled')
            ev = Event(event_name=name, date=datetime.strptime(date_str, '%Y-%m-%d').date(), venue=venue, status=status, created_by_admin=session['user_id'])
            db.session.add(ev)
            db.session.commit()
            flash('Event created', 'success')
        events = Event.query.order_by(Event.date.desc()).all()
        return render_template('events.html', events=events)

    # Faculty routes
    @app.route('/faculty')
    @login_required(role='Faculty')
    def faculty_dashboard():
        faculty_id = session['user_id']
        timetable = (Timetable.query
                     .filter(Timetable.faculty_id == faculty_id)
                     .join(Room)
                     .join(Course)
                     .join(Section)
                     .all())
        return render_template('faculty_dashboard.html', timetable=timetable)

    @app.route('/faculty/grades', methods=['POST'])
    @login_required(role='Faculty')
    def faculty_update_grade():
        student_id = int(request.form.get('student_id'))
        course_id = int(request.form.get('course_id'))
        semester = request.form.get('semester')
        grade = request.form.get('grade')
        enrollment = Enrollment.query.filter_by(student_id=student_id, course_id=course_id, semester=semester).first()
        if enrollment:
            enrollment.grade = grade
            db.session.commit()
            flash('Grade updated', 'success')
        else:
            flash('Enrollment not found', 'danger')
        return redirect(url_for('faculty_dashboard'))

    # Student routes
    @app.route('/student')
    @login_required(role='Student')
    def student_dashboard():
        student_id = session['user_id']
        student = Student.query.get(student_id)
        timetable = []
        if student.section_id:
            timetable = Timetable.query.filter_by(section_id=student.section_id).join(Room).join(Course).join(Faculty).all()
        enrollments = Enrollment.query.filter_by(student_id=student_id).join(Course).all()
        events = (EventRegistration.query
                  .filter_by(student_id=student_id)
                  .join(Event)
                  .all())
        return render_template('student_dashboard.html', student=student, timetable=timetable, enrollments=enrollments, events=events)

    @app.route('/student/register_event', methods=['POST'])
    @login_required(role='Student')
    def student_register_event():
        event_id = int(request.form.get('event_id'))
        reg = EventRegistration(event_id=event_id, student_id=session['user_id'])
        db.session.add(reg)
        try:
            db.session.commit()
            flash('Registered for event', 'success')
        except Exception:
            db.session.rollback()
            flash('Already registered or error occurred', 'warning')
        return redirect(url_for('student_dashboard'))

    # Simple reports
    @app.route('/reports/students_per_course')
    @login_required(role='Admin')
    def report_students_per_course():
        rows = db.session.execute("SELECT * FROM scms.vw_students_per_course ORDER BY course_code").fetchall()
        return {'data': [dict(r._mapping) for r in rows]}

    @app.route('/reports/event_participation')
    @login_required(role='Admin')
    def report_event_participation():
        rows = db.session.execute("SELECT * FROM scms.vw_event_participation ORDER BY date DESC").fetchall()
        return {'data': [dict(r._mapping) for r in rows]}

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # Only ensures tables exist if using SQLAlchemy metadata; schema created via SQL file
        pass
    app.run(host='0.0.0.0', port=5000, debug=True)
