from flask import Blueprint, request, jsonify
from app.models import db, Student, Device, AttendanceLog
from sqlalchemy import func
from flask_jwt_extended import jwt_required

attendance_bp = Blueprint('attendance', __name__)

# POST /attendance/scan - Hardware entry point for MAC detection
@attendance_bp.route('/scan', methods=['POST'])
def scan_mac():
    data = request.get_json() or {}
    mac_list = data.get("mac_addresses") or []
    if isinstance(mac_list, str):
        mac_list = [mac_list]

    results = {"students": [], "unknown": []}

    try:
        for mac in mac_list:
            mac = mac.lower()
            device = Device.query.filter_by(mac_address=mac).first()
            if not device:
                results["unknown"].append(mac)
                continue

            # Prevent duplicate logs for same student/device today
            existing_log = AttendanceLog.query.filter_by(
                student_id=device.student_id,
                device_id=device.device_id
            ).filter(func.date(AttendanceLog.timestamp) == func.current_date()).first()

            if not existing_log:
                db.session.add(AttendanceLog(
                    student_id=device.student_id,
                    device_id=device.device_id,
                    status="Active"
                ))

            # Safe relationship access
            student_name = getattr(device.owner, "first_name", "Unknown")

            results["students"].append({
                "student": student_name,
                "mac_address": mac
            })

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify(results), 201 if results["students"] else (jsonify(results), 404)

# GET /attendance/stats - Present vs Registered totals
@attendance_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    total_students = Student.query.count() or 0
    present_today = db.session.query(AttendanceLog.student_id).distinct().filter(
        func.date(AttendanceLog.timestamp) == func.current_date()
    ).count() or 0
    absent_today = max(0, total_students - present_today)

    return jsonify({
        "total_registered": total_students,
        "present_today": present_today,
        "absent_today": absent_today
    }), 200


# GET /attendance/live - Stream of recent network connections
@attendance_bp.route('/live', methods=['GET'])
@jwt_required()
def get_live_stream():
    recent_logs = AttendanceLog.query.order_by(AttendanceLog.timestamp.desc()).limit(10).all()
    logs_data = []
    for log in recent_logs:
        logs_data.append({
            "student": f"{log.student.first_name} {log.student.last_name}" if log.student else "Unknown",
            "mac": log.device.mac_address if log.device else "Unknown",
            "time": log.timestamp.strftime("%H:%M:%S"),
            "status": log.status
        })
    return jsonify(logs_data), 200
