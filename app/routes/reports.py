import csv
import io
from flask import Blueprint, request, jsonify, Response
from app import db
from app.models import Report, Department, AttendanceLog, Student, Teacher
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from datetime import datetime

# Blueprint definition
reports_bp = Blueprint('reports', __name__)

# --- REPORT LISTING & DETAILS ---

@reports_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_reports():
    """Fetch all reports with related teacher and department names."""
    reports = Report.query.all()
    # Serialize while excluding sensitive fields from the nested teacher object
    return jsonify([r.to_dict(rules=('-teacher.password', '-teacher.reports')) for r in reports]), 200


@reports_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_report_details(id):
    """View a specific report's metadata."""
    report = Report.query.get_or_404(id)
    return jsonify(report.to_dict()), 200


# --- REPORT GENERATION ---

@reports_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_report():
    """
    Calculates department-wide average attendance and saves a 
    new report record to the database.
    """
    data = request.get_json() or {}
    current_teacher_id = get_jwt_identity()
    
    dept_id = data.get('dept_id')
    report_type = data.get('report_type', 'Departmental Summary') # e.g., Weekly, Monthly

    if not dept_id:
        return jsonify({"error": "Field 'dept_id' is required"}), 400
    
    # Inside a route or report generator
    if dept_id == 999:
        # Global scope: count ALL students in the school
        total_students_count = Student.query.count()
        
        students_present_count = db.session.query(func.count(func.distinct(AttendanceLog.student_id)))\
            .join(Student)\
            .scalar() or 0
    else:
        # Departmental scope: count within specific group
        total_students_count = Student.query.filter_by(dept_id=dept_id).count()
        
        students_present_count = db.session.query(func.count(func.distinct(AttendanceLog.student_id)))\
            .join(Student)\
            .filter(Student.dept_id == dept_id)\
            .scalar() or 0
    
    # 2. Prevent division by zero safely
    if total_students_count == 0:
        avg_attendance = 0.0
    else:
        avg_attendance = (students_present_count / total_students_count) * 100
    # 2. Create the Report instance
    new_report = Report(
        teacher_id=current_teacher_id,
        dept_id=dept_id,
        report_type=report_type,
        average_attendance=round(float(avg_attendance), 2),
        generated_at=datetime.now()
    )

    try:
        db.session.add(new_report)
        db.session.commit()
        return jsonify({
            "message": "Report generated and saved",
            "report": new_report.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# --- DATA EXPORT ---

@reports_bp.route('/<int:id>/export', methods=['GET'])
@jwt_required()
def export_report_csv(id):
    """Generates a downloadable CSV summary of students and their attendance counts."""
    report = Report.query.get_or_404(id)
    
    # Setup string-based file in memory
    output = io.StringIO()
    writer = csv.writer(output)
    if report.dept_id == 999:
        dept_name = "All Departments (Global)"
    else:
        dept = Department.query.get(report.dept_id)
        dept_name = dept.dept_name if dept else "N/A"
    
    # Write Metadata Headers
    writer.writerow(['Report Title', report.report_type])
    writer.writerow(['Department', dept.dept_name if dept else "N/A"])
    writer.writerow(['Generated At', report.generated_at.strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow(['Average Attendance (%)', f"{report.average_attendance}%"])
    writer.writerow([]) # Spacer
    writer.writerow(['Student Name', 'Student Code', 'Status', 'Total Attendance Hits'])

    # Fetch granular student stats for the department
    student_stats = db.session.query(
        Student.first_name, 
        Student.last_name, 
        Student.student_code,
        Student.status,
        func.count(func.distinct(func.date(AttendanceLog.timestamp)))
    ).outerjoin(AttendanceLog).filter(
        Student.dept_id == report.dept_id
    ).group_by(Student.student_id).all()

    for first, last, code, status, count in student_stats:
        writer.writerow([f"{first} {last}", code, status, count])

    # Return as a downloadable file response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=MARS_Report_{id}.csv"}
    )


# --- DELETION ---

@reports_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_report(id):
    """Deletes a specific report. Only the creator can delete it."""
    report = Report.query.get_or_404(id)
    
    current_user_id = get_jwt_identity()
    if str(report.teacher_id) != str(current_user_id):
        return jsonify({"message": "Permission denied: Only the creator can delete this report"}), 403

    db.session.delete(report)
    db.session.commit()
    return jsonify({"message": "Report deleted successfully"}), 200