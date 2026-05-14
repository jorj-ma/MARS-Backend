from flask import Blueprint, request, jsonify
from app.models import db, Student, Device, AttendanceLog
from sqlalchemy import func
from flask_jwt_extended import jwt_required


attendance_bp = Blueprint('attendance', __name__)

# POST /attendance/scan - Hardware entry point for MAC detection
@attendance_bp.route('/scan', methods=['POST'])
def scan_mac():
    data = request.get_json()
    mac = data.get('mac_address')
    
    # Check if MAC is registered
    device = Device.query.filter_by(mac_address=mac).first()
    if not device:
        return jsonify({"status": "unknown", "message": "Device not registered"}), 404

    # Log attendance
    new_log = AttendanceLog(
        student_id=device.student_id,
        device_id=device.device_id,
        status="Active"
    )
    db.session.add(new_log)
    db.session.commit()

    return jsonify({"status": "success", "student": device.owner.first_name}), 201

# GET /attendance/stats - Present vs Registered totals
@attendance_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    total_students = Student.query.count()
    # Count unique students who appeared in logs today
    present_today = db.session.query(AttendanceLog.student_id).distinct().filter(
        func.date(AttendanceLog.timestamp) == func.current_date()
    ).count()

    return jsonify({
        "total_registered": total_students,
        "present_today": present_today,
        "absent_today": total_students - present_today
    }), 200

# GET /attendance/live - Stream of recent network connections
@attendance_bp.route('/live', methods=['GET'])
@jwt_required()
def get_live_stream():
    # Get last 10 logs
    recent_logs = AttendanceLog.query.order_by(AttendanceLog.timestamp.desc()).limit(10).all()
    logs_data = []
    for log in recent_logs:
        logs_data.append({
            "student": f"{log.student.first_name} {log.student.last_name}",
            "mac": log.device.mac_address,
            "time": log.timestamp.strftime("%H:%M:%S"),
            "status": log.status
        })
    return jsonify(logs_data), 200