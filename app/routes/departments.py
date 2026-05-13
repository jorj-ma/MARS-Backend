from flask import Blueprint, request, jsonify
from app import db
from app.models import Department
from flask_jwt_extended import jwt_required

dept_bp = Blueprint('departments', __name__)

@dept_bp.route('/', methods=['GET'])
@jwt_required() # Require login to view departments
def get_all_departments():
    departments = Department.query.all()
    # Uses SerializerMixin's to_dict() for easy conversion
    return jsonify([d.to_dict(rules=('-students', '-teachers', '-reports')) for d in departments]), 200

@dept_bp.route('/', methods=['POST'])
@jwt_required()
def create_department():
    data = request.get_json()
    
    # Validate required fields from models.py
    if not data.get('dept_name') or not data.get('dept_code'):
        return jsonify({"message": "Department name and code are required"}), 400
    
    new_dept = Department(
        dept_name=data.get('dept_name'),
        dept_code=data.get('dept_code'),
        description=data.get('description')
    )
    
    db.session.add(new_dept)
    db.session.commit()
    
    return jsonify({
        "message": "Department added",
        "department": new_dept.to_dict()
    }), 201

@dept_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_department(id):
    dept = Department.query.get_or_404(id)
    return jsonify(dept.to_dict()), 200

@dept_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_department(id):
    dept = Department.query.get_or_404(id)
    db.session.delete(dept)
    db.session.commit()
    return jsonify({"message": "Department deleted"}), 200