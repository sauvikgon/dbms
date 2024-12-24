from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# User Model (For authentication)
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Student Model
class Student(db.Model):
    __tablename__ = 'students'
    student_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    major = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)

    # Relationship to Attendance
    attendances = db.relationship('Attendance', back_populates='student')


# Course Model
class Course(db.Model):
    __tablename__ = 'courses'
    course_code = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    instructor = db.Column(db.String(100), nullable=False)

    # Relationship to Attendance
    attendances = db.relationship('Attendance', back_populates='course')


# Grade Model
class Grade(db.Model):
    __tablename__ = 'grades'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    course_code = db.Column(db.String(10), db.ForeignKey('courses.course_code'), nullable=False)
    grade = db.Column(db.Float, nullable=False)

    # Relationship to Student (one-to-many)
    student = db.relationship('Student', backref='grades')
    course = db.relationship('Course', backref='grades')


# Attendance Model
class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'))  # Corrected foreign key
    course_code = db.Column(db.String(10), db.ForeignKey('courses.course_code'))  # Corrected foreign key
    date = db.Column(db.Date, nullable=False)
    attendance_status = db.Column(db.String(20), nullable=False)

    # Relationships to Student and Course
    student = db.relationship('Student', back_populates='attendances')
    course = db.relationship('Course', back_populates='attendances')
