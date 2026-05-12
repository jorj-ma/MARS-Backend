from app import db,bcrypt
from sqlalchemy_serializer import SerializerMixin

class Teacher(db.Model, SerializerMixin):
    __tablename__ = 'teachers'
    
    teacher_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    profile_image_url = db.Column(db.String)
    role = db.Column(db.String, default="TEACHER")
    join_date = db.Column(db.DateTime, server_default=db.func.now())
    last_login = db.Column(db.DateTime)

    # Relationships
    reports = db.relationship('Report', backref='teacher', lazy=True)
    dept_id = db.Column(db.Integer, db.ForeignKey('departments.dept_id'))

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

class Department(db.Model, SerializerMixin):
    __tablename__ = 'departments'
    
    dept_id = db.Column(db.Integer, primary_key=True)
    dept_name = db.Column(db.String, nullable=False)
    dept_code = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.Text)

    # Relationships
    students = db.relationship('Student', backref='department', lazy=True)
    teachers = db.relationship('Teacher', backref='department', lazy=True)
    reports = db.relationship('Report', backref='department', lazy=True)

class Student(db.Model, SerializerMixin):
    __tablename__ = 'students'
    
    student_id = db.Column(db.Integer, primary_key=True)
    student_code = db.Column(db.String, unique=True, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    status = db.Column(db.String, default="Active")
    dept_id = db.Column(db.Integer, db.ForeignKey('departments.dept_id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships
    devices = db.relationship('Device', backref='owner', lazy=True, cascade="all, delete-orphan")
    attendance_logs = db.relationship('AttendanceLog', backref='student', lazy=True)

class Device(db.Model, SerializerMixin):
    __tablename__ = 'devices'
    
    device_id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String, unique=True, nullable=False)
    device_name = db.Column(db.String) # e.g. Aria's MacBook Pro
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    registration_date = db.Column(db.DateTime, server_default=db.func.now())

class AttendanceLog(db.Model, SerializerMixin):
    __tablename__ = 'attendance_logs'
    
    log_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.device_id'), nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    status = db.Column(db.String) # Active, Roaming, Absent

class Report(db.Model, SerializerMixin):
    __tablename__ = 'reports'
    
    report_id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.teacher_id'), nullable=False)
    dept_id = db.Column(db.Integer, db.ForeignKey('departments.dept_id'), nullable=False)
    generated_at = db.Column(db.DateTime, server_default=db.func.now())
    report_type = db.Column(db.String)
    average_attendance = db.Column(db.Float)

    # Mac_address_registration_system_database