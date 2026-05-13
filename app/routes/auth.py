from flask import Blueprint, request, jsonify
from app import db
from app.models import Teacher
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Check if user already exists
    if Teacher.query.filter_by(email=data.get('email')).first():
        return jsonify({"message": "Email already registered"}), 400
    
    # Create new teacher instance based on models.py
    new_teacher = Teacher(
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        email=data.get('email'),
        role=data.get('role', 'TEACHER'),
        dept_id=data.get('dept_id') # Optional: link to a department during signup
    )
    
    # Use the method defined in your models.py
    new_teacher.set_password(data.get('password'))
    
    db.session.add(new_teacher)
    db.session.commit()
    
    return jsonify({
        "message": "Account created successfully",
        "user": new_teacher.to_dict(only=('teacher_id', 'email', 'role'))
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    teacher = Teacher.query.filter_by(email=data.get('email')).first()
    
    # Verify credentials using your check_password model method
    if teacher and teacher.check_password(data.get('password')):
        # Create identity for JWT
        access_token = create_access_token(identity=str(teacher.teacher_id))
        
        return jsonify({
            "access_token": access_token,
            "user": teacher.to_dict(rules=('-password', '-reports'))
        }), 200
    
    return jsonify({"message": "Invalid email or password"}), 401

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    teacher = Teacher.query.get(current_user_id)
    return jsonify(teacher.to_dict(rules=('-password',))), 200