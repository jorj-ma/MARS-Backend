from flask import Blueprint, request, jsonify
from app.models import db, Student, Device, AttendanceLog
from flask_jwt_extended import jwt_required
from sqlalchemy import func

students_bp = Blueprint('students', __name__)

# GET /students - List all students (searchable)
@students_bp.route('', methods=['GET'])
@jwt_required()
def get_students():
    search = request.args.get('search')
    query = Student.query
    if search:
        query = query.filter(
            (Student.first_name.ilike(f'%{search}%')) | 
            (Student.last_name.ilike(f'%{search}%')) |
            (Student.student_code.ilike(f'%{search}%'))
        )
    students = query.all()
    return jsonify([s.to_dict() for s in students]), 200

# POST /students - Atomic creation of Student & MAC record
@students_bp.route('', methods=['POST'])
@jwt_required()
def create_student():
    data = request.get_json() or {}

    required_fields = ['student_code', 'first_name', 'last_name', 'email', 'dept_id', 'mac_address']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Field '{field}' is required"}), 400
        
    student_code_clean = str(data['student_code']).strip().upper()
    email_clean = str(data['email']).strip().lower()
    mac_clean = str(data['mac_address']).strip().lower()

    if Student.query.filter_by(student_code=student_code_clean).first():
        return jsonify({"error": f"Student code '{student_code_clean}' is already registered"}), 400
        
    if Student.query.filter_by(email=email_clean).first():
        return jsonify({"error": f"Email '{email_clean}' is already registered"}), 400
        
    if Device.query.filter(func.lower(Device.mac_address) == mac_clean).first():
        return jsonify({"error": f"MAC address '{data['mac_address']}' is already assigned to a device"}), 400
    
    try:
        new_student = Student(
            student_code=data['student_code'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            dept_id=data['dept_id']
        )
        db.session.add(new_student)
        db.session.flush() 

        new_device = Device(
            mac_address=data['mac_address'],
            device_name=data.get('device_name', f"{data['first_name']}'s Device"),
            student_id=new_student.student_id
        )
        db.session.add(new_device)
        db.session.commit()
        
        return jsonify({"message": "Student and Device registered successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# GET /students/<id> - View profile and hardware details
@students_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_student_details(id):
    student = Student.query.get_or_404(id)
    student_data = {
        "student_id": student.student_id,
        "student_code": student.student_code,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "email": student.email,
        "dept_id": student.dept_id,
        "devices": [
            {
                "device_id": d.device_id,
                "mac_address": d.mac_address,
                "device_name": d.device_name
            } for d in student.devices
        ]
    }
    return jsonify(student_data), 200

# DELETE /students/<id> - Remove student and associated devices
@students_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_student(id):
    student = Student.query.get_or_404(id)
    try:
        db.session.delete(student)  
        db.session.commit()
        return jsonify({"message": f"Student {id} and all related hardware profiles dropped successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete student record", "details": str(e)}), 500

# GET /students/<id>/activity - Fetch activity logs for the student
@students_bp.route('/<int:id>/activity', methods=['GET'])
@jwt_required()
def get_student_activity(id):
    student = Student.query.get_or_404(id)
    
    activity_query = db.session.query(
        func.date(AttendanceLog.timestamp).label('date'),
        func.count(AttendanceLog.log_id).label('count')
    ).filter(
        AttendanceLog.student_id == id,
        AttendanceLog.status == 'Active'
    ).group_by(
        func.date(AttendanceLog.timestamp)
    ).all()

    heatmap_data = []
    for row in activity_query:
        if row.date:
            date_str = row.date.strftime('%Y-%m-%d') if hasattr(row.date, 'strftime') else str(row.date)
            heatmap_data.append({
                "date": date_str,
                "count": row.count or 0
            })

    return jsonify({
        "student_id": id,
        "full_name": f"{student.first_name} {student.last_name}",
        "activity": heatmap_data
    }), 200