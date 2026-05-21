from app import db, bcrypt
from sqlalchemy_serializer import SerializerMixin

class Teacher(db.Model, SerializerMixin):
    __tablename__ = 'teachers'
    # Resolves metadata conflicts if an old plural 'Teachers' model definition is still loaded in cache
    __table_args__ = {'extend_existing': True}
    
    teacher_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    profile_image_url = db.Column(db.String)
    role = db.Column(db.String, default="TEACHER")
    join_date = db.Column(db.DateTime, server_default=db.func.now())
    last_login = db.Column(db.DateTime)

    # Safe serialization rules
    serialize_only = ('teacher_id', 'first_name', 'last_name', 'email', 'role', 'dept_id')
    serialize_rules = ('-password', '-reports')

    # Relationships
    reports = db.relationship('Report', backref='teacher', lazy=True)
    dept_id = db.Column(db.Integer, db.ForeignKey('departments.dept_id'))

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

class Department(db.Model, SerializerMixin):
    __tablename__ = 'departments'
    __table_args__ = {'extend_existing': True}
    
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
    __table_args__ = {'extend_existing': True}
    
    student_id = db.Column(db.Integer, primary_key=True)
    student_code = db.Column(db.String, unique=True, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    status = db.Column(db.String, default="Active")
    dept_id = db.Column(db.Integer, db.ForeignKey('departments.dept_id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Safe serialization - corrected to point to matching 'department' relation backref string name
    serialize_only = ('student_id', 'student_code', 'first_name', 'last_name', 'email', 'dept_id')
    serialize_rules = ('-devices.owner', '-department.students')

    # Relationships
    devices = db.relationship('Device', backref='owner', lazy=True, cascade="all, delete-orphan")
    attendance_logs = db.relationship(
        'AttendanceLog', 
        backref='student', 
        cascade='all, delete-orphan'
    )

class Device(db.Model, SerializerMixin):
    __tablename__ = 'devices'
    __table_args__ = {'extend_existing': True}
    
    device_id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String, unique=True, nullable=False)
    device_name = db.Column(db.String) 
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    registration_date = db.Column(db.DateTime, server_default=db.func.now())

    serialize_rules = ('-owner.devices',)

class AttendanceLog(db.Model, SerializerMixin):
    __tablename__ = 'attendance_logs'
    __table_args__ = {'extend_existing': True}
    
    log_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.device_id'), nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    status = db.Column(db.String) 

    # Relationships 
    device = db.relationship('Device', backref='attendance_logs')

class Report(db.Model, SerializerMixin):
    __tablename__ = 'reports'
    __table_args__ = {'extend_existing': True}
    
    report_id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.teacher_id'), nullable=False)
    dept_id = db.Column(db.Integer, db.ForeignKey('departments.dept_id'), nullable=False)
    generated_at = db.Column(db.DateTime, server_default=db.func.now())
    report_type = db.Column(db.String)
    average_attendance = db.Column(db.Float)

    serialize_rules = ('-department.reports', '-teacher.reports', '-department.students', '-department.teachers')