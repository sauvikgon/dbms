from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from models import db, User, Student, Course, Grade, Attendance
from forms import LoginForm
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///student_dbms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
bcrypt = Bcrypt(app)

db.init_app(app)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/students/manage', methods=['GET', 'POST'])
def manage_students():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Process the form data when it's posted
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            # Adding a new student
            name = request.form['name']
            major = request.form['major']
            year = request.form['year']

            # Create a new student instance and add to DB
            student = Student(name=name, major=major, year=year)
            db.session.add(student)
            db.session.commit()
            flash(f'Student {name} added successfully!', 'success')

        elif action == 'delete':
            # Deleting a student
            student_id = request.form['student_id']
            student = Student.query.get(student_id)

            if student:
                db.session.delete(student)
                db.session.commit()
                flash(f'Student {student.name} deleted successfully!', 'success')
            else:
                flash('Student not found!', 'danger')

    # Fetch all students to display
    students = Student.query.all()
    return render_template('manage_students.html', students=students)


@app.route('/courses/manage', methods=['GET', 'POST'])
def manage_courses():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            course_code = request.form['course_code']
            name = request.form['name']
            instructor = request.form['instructor']
            course = Course(course_code=course_code, name=name, instructor=instructor)
            db.session.add(course)
            db.session.commit()
        elif action == 'delete':
            course_id = request.form['course_id']
            course = Course.query.get(course_id)
            db.session.delete(course)
            db.session.commit()
        elif action == 'edit':
            course_id = request.form['course_id']
            course = Course.query.get(course_id)
            if course:
                course.course_code = request.form['course_code']
                course.name = request.form['name']
                course.instructor = request.form['instructor']
                db.session.commit()

    courses = Course.query.all()
    # Pass a list of unique instructors for dropdown options
    instructors = [course.instructor for course in courses]
    instructors = list(set(instructors))  # Remove duplicates
    return render_template('manage_courses.html', courses=courses, instructors=instructors)



@app.route('/grades/add', methods=['GET', 'POST'])
def add_grades():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fetch all students and courses to populate the dropdowns
    students = Student.query.all()
    courses = Course.query.all()

    # Initialize grades to be displayed in the template
    grades = Grade.query.all()  # Get all grades from the database

    if request.method == 'POST':
        if 'action' in request.form and request.form['action'] == 'delete':
            # Handle delete functionality
            grade_id = request.form['grade_id']
            grade_to_delete = Grade.query.get(grade_id)
            if grade_to_delete:
                db.session.delete(grade_to_delete)
                db.session.commit()
                flash('Grade deleted successfully!', 'success')
            else:
                flash('Grade not found.', 'danger')

        else:
            # Handle add grade functionality
            student_id = request.form['student_id']
            course_code = request.form['course_code']
            grade_value = request.form['grade']

            # Check if a grade for this student and course already exists
            existing_grade = Grade.query.filter_by(student_id=student_id, course_code=course_code).first()

            if existing_grade:
                flash('Grade already assigned for this student in this course.', 'warning')
            else:
                # Add the new grade to the database
                new_grade = Grade(
                    student_id=student_id,
                    course_code=course_code,
                    grade=grade_value
                )
                db.session.add(new_grade)
                db.session.commit()
                flash('Grade assigned successfully!', 'success')

        # Re-fetch grades to display the updated list
        grades = Grade.query.all()

    return render_template('add_grades.html', students=students, courses=courses, grades=grades)

@app.route('/attendance/track', methods=['GET', 'POST'])
def track_attendance():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # If the request is POST, save the attendance data
    if request.method == 'POST':
        student_id = request.form['student_id']
        course_code = request.form['course_code']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        status = request.form['status']

        # Check if the student has already been marked present/absent for this course on the same day
        existing_attendance = Attendance.query.filter_by(
            student_id=student_id,
            course_code=course_code,
            date=date
        ).first()

        if existing_attendance:
            flash("Attendance has already been recorded for this student on this day.", "warning")
            return redirect(url_for('track_attendance'))

        attendance = Attendance(student_id=student_id, course_code=course_code, date=date, attendance_status=status)
        db.session.add(attendance)
        db.session.commit()
        flash("Attendance marked successfully!", "success")

    # Query to get all attendance records
    attendances = Attendance.query.all()

    # Get all students and courses
    students = Student.query.all()
    courses = Course.query.all()

    return render_template('track_attendance.html', students=students, courses=courses, attendances=attendances)


@app.route('/reports', methods=['GET'])
def generate_reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # GPA Report with Student Name
    gpa_report = db.session.query(
        Student.student_id,
        Student.name.label('student_name'),  # Fetch the student name
        db.func.avg(Grade.grade).label('gpa')
    ).join(Student, Student.student_id == Grade.student_id).group_by(Student.student_id, Student.name).all()

    # Enrollment by Major
    enrollment_report = db.session.query(
        Student.major,
        db.func.count(Student.student_id).label('enrollment_count')
    ).group_by(Student.major).all()

    return render_template('generate_reports.html', gpa_report=gpa_report, enrollment_report=enrollment_report)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Optionally, create a test user
        if not User.query.filter_by(username='admin').first():
            user = User(username='admin')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
    app.run(debug=True)
