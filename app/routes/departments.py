from flask import Blueprint, request, jsonify
from app import db
from app.models import Department
from flask_jwt_extended import jwt_required
from sqlalchemy import func

dept_bp = Blueprint('departments', __name__)

@dept_bp.route('/', methods=['GET'])
@jwt_required() # Require login to view departments
def get_all_departments():
    departments = Department.query.all() or []
    # Uses SerializerMixin's to_dict() for easy conversion
    return jsonify([d.to_dict(rules=('-students', '-teachers', '-reports')) for d in departments]), 200

@dept_bp.route('/', methods=['POST'])
@jwt_required()
def create_department():
    data = request.get_json() or {}
    
    # Validate required fields from models.py
    if not data.get('dept_name') or not data.get('dept_code'):
        return jsonify({"message": "Department name and code are required"}), 400
    
    name_clean = str(data.get('dept_name')).strip()
    code_clean = str(data.get('dept_code')).strip().upper()
    description_clean = str(data.get('description')).strip() if data.get('description') else None

    # 3. Prevent duplicate unique key violations before hitting the database
    existing_code = Department.query.filter(func.upper(Department.dept_code) == code_clean).first()
    if existing_code:
        return jsonify({"error": f"A department with code '{code_clean}' already exists"}), 400

    existing_name = Department.query.filter(func.lower(Department.dept_name) == name_clean.lower()).first()
    if existing_name:
        return jsonify({"error": f"A department named '{name_clean}' already exists"}), 400

    try:
        # 4. Create and commit the instance
        new_dept = Department(
            dept_name=name_clean,
            dept_code=code_clean,
            description=description_clean
        )
    
        db.session.add(new_dept)
        db.session.commit()
        
        return jsonify({
            "message": "Department added successfully",
            "department": new_dept.to_dict(rules=('-students', '-teachers', '-reports'))
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to save department record", "details": str(e)}), 500

@dept_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_department(id):
    dept = Department.query.get_or_404(id)
    return jsonify(dept.to_dict(rules=('-students', '-teachers', '-reports'))), 200

@dept_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_department(id):
    dept = Department.query.get_or_404(id)
    try:
        db.session.delete(dept)
        db.session.commit()
        return jsonify({"message": f"Department '{dept.dept_name}' deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        # Catches cases where foreign keys from students or teachers block a deletion cascade
        return jsonify({
            "error": "Cannot delete department. Ensure no students or teachers are still linked to it.",
            "details": str(e)
        }), 422