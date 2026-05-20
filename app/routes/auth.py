from flask import Blueprint, request, jsonify
from app import db
from app.models import Teacher
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}

    required_fields= ['first_name','last_name','email','password'] # check for missing required fields
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Field '{field}' is required"}), 400
            
    # Email formatting check
    if "@" not in data.get('email', ''):
        return jsonify({"error": "Invalid email address format"}), 400
    
    if Teacher.query.filter_by(email=data.get('email')).first():
        return jsonify({"message": "Email already registered"}), 400
    
    new_teacher = Teacher(
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        email=data.get('email'),
        role=data.get('role', 'TEACHER'),
        dept_id=data.get('dept_id', 999)
    )
    new_teacher.set_password(data.get('password'))
    
    db.session.add(new_teacher)
    db.session.commit()
    
    return jsonify({
        "message": "Account created successfully",
        "user": new_teacher.to_dict(only=('teacher_id', 'email', 'role'))
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}

    if not data.get('email') or not data.get('password'):
        return jsonify({"error": "Both email and password are required"}), 400
    
    teacher = Teacher.query.filter_by(email=data.get('email')).first()
    
    if teacher and teacher.check_password(data.get('password')):
        access_token = create_access_token(identity=str(teacher.teacher_id))
        return jsonify({
            "access_token": access_token,
            "user": teacher.to_dict()
        }), 200
    
    return jsonify({"message": "Invalid email or password"}), 401

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    teacher = Teacher.query.get(current_user_id)
    if not teacher:
        return jsonify({"error": "Teacher profile not found"}), 404
    return jsonify(teacher.to_dict(rules=('-password',))), 200

# NEW PATCH ROUTE added from image_2a5d9c.jpg
@auth_bp.route('/me', methods=['PATCH'])
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    teacher = Teacher.query.get(current_user_id)
    if not teacher:
        return jsonify({"error": "Teacher profile not found"}), 404
    
    data = request.get_json() or {}

    # Update basic profile info if provided in payload
    if 'first_name' in data and data['first_name']:
        teacher.first_name = data['first_name']

    if 'last_name' in data and data['last_name']:
        teacher.last_name = data['last_name']
        
    if 'email' in data and data['email']:
        if "@" not in data['email']:
            return jsonify({"error": "Invalid email address format"}), 400
        # Check if new email is already taken by someone else
        existing_user = Teacher.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.teacher_id != teacher.teacher_id:
            return jsonify({"message": "Email already in use"}), 400
        teacher.email = data['email']

    # Handle password update using model method
    if 'password' in data and data['password']:
        teacher.set_password(data['password'])

    if 'dept_id' in data:
        teacher.dept_id = data['dept_id']

    db.session.commit()

    return jsonify({
        "message": "Profile updated successfully",
        "user": teacher.to_dict(rules=('-password',))
    }), 200