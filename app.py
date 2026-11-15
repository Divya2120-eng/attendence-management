import os
import io
import time
import base64
import uuid
import csv
import datetime
from flask import (
    Flask, render_template, request, redirect, url_for, 
    session, flash, jsonify, Response
)
from config import Config
from db import db
import qrcode

app = Flask(__name__)
app.config.from_object(Config)

# Provide configuration to templates
@app.context_processor
def inject_config():
    return dict(config=Config)

# ----------------------------------------------------
# Authentication & Access Control
# ----------------------------------------------------

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    role = session.get('role')
    if role == 'class_teacher':
        return redirect(url_for('class_teacher_dashboard'))
    elif role == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    elif role == 'student':
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        device_id = request.form.get('device_id', '').strip()
        selected_role = request.form.get('selected_role', 'student')

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template('login.html')

        user = db.get_user_by_username(username)
        if not user:
            flash("Invalid credentials. User not found.", "danger")
            return render_template('login.html')

        # Check password hash
        from werkzeug.security import check_password_hash
        if not check_password_hash(user['password_hash'], password):
            flash("Incorrect password. Please try again.", "danger")
            return render_template('login.html')

        # --- DEVICE BINDING SECURITY FOR STUDENTS ---
        if user['role'] == 'student':
            if not device_id:
                flash("Device ID could not be detected. Please enable JavaScript.", "warning")
                return render_template('login.html')

            # 1. Check if device is already bound to ANOTHER student
            other_student = db.find_student_with_device(device_id, exclude_student_id=user['id'])
            if other_student:
                flash(f"SECURITY VIOLATION: This physical hardware device is already bound to student '{other_student['full_name']}' ({other_student['roll_no']}). Multiple student accounts on 1 device are prohibited.", "danger")
                return render_template('login.html')

            # 2. Check if this student account is already bound to a DIFFERENT device
            if user['bound_device_id']:
                if user['bound_device_id'] != device_id:
                    flash(f"ACCESS DENIED: Your student account is bound to another device ({user['bound_device_id']}). You cannot log in from this device. Please use your registered phone or contact Class Teacher to reset device binding.", "danger")
                    return render_template('login.html')
            else:
                # First time login on this device: Bind device!
                db.bind_device(user['id'], device_id)
                user['bound_device_id'] = device_id
                flash("Device successfully bound to your student account!", "success")

        # Set session
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['full_name'] = user['full_name']
        session['role'] = user['role']
        session['class_id'] = user.get('class_id')
        session['roll_no'] = user.get('roll_no')
        session['device_id'] = device_id

        flash(f"Welcome back, {user['full_name']}!", "success")

        if user['role'] == 'class_teacher':
            return redirect(url_for('class_teacher_dashboard'))
        elif user['role'] == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    # Prompt requirement: Student CANNOT logout while QR code session is active!
    if session.get('role') == 'student' and 'user_id' in session:
        is_active, active_session = db.is_student_session_active(session['user_id'])
        if is_active:
            flash("SECURITY RESTRICTION: You cannot log out right now! An active QR attendance session is currently running for your class. This restriction prevents proxy attendance.", "warning")
            return redirect(url_for('student_dashboard'))

    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for('login'))

# ----------------------------------------------------
# Class Teacher (Admin) Routes
# ----------------------------------------------------

@app.route('/class-teacher')
def class_teacher_dashboard():
    if session.get('role') != 'class_teacher':
        flash("Unauthorized. Only the designated Class Teacher has administrative access.", "danger")
        return redirect(url_for('index'))

    teachers = db.get_teachers()
    students = db.get_students()
    subjects = db.get_all_subjects()
    classes = db.get_classes()

    return render_template('class_teacher.html', 
                           teachers=teachers, 
                           students=students, 
                           subjects=subjects, 
                           classes=classes)

@app.route('/api/class-teacher/add-teacher', methods=['POST'])
def add_teacher():
    if session.get('role') != 'class_teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    username = request.form.get('username')
    password = request.form.get('password')
    full_name = request.form.get('full_name')
    email = request.form.get('email', '')

    last_id, err = db.add_teacher(username, password, full_name, email)
    if err:
        flash(f"Error adding teacher: {err}", "danger")
    else:
        flash(f"Teacher {full_name} added successfully!", "success")
    return redirect(url_for('class_teacher_dashboard'))

@app.route('/api/class-teacher/delete-teacher/<int:teacher_id>', methods=['POST'])
def delete_teacher(teacher_id):
    if session.get('role') != 'class_teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    ok, err = db.remove_teacher(teacher_id)
    if not ok:
        flash(f"Cannot delete teacher: {err}", "danger")
    else:
        flash("Teacher removed successfully.", "success")
    return redirect(url_for('class_teacher_dashboard'))

@app.route('/api/class-teacher/add-student', methods=['POST'])
def add_student():
    if session.get('role') != 'class_teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    username = request.form.get('username')
    password = request.form.get('password')
    full_name = request.form.get('full_name')
    roll_no = request.form.get('roll_no')
    email = request.form.get('email', '')

    last_id, err = db.add_student(username, password, full_name, roll_no, email)
    if err:
        flash(f"Error enrolling student: {err}", "danger")
    else:
        flash(f"Student {full_name} ({roll_no}) enrolled successfully!", "success")
    return redirect(url_for('class_teacher_dashboard'))

@app.route('/api/class-teacher/delete-student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    if session.get('role') != 'class_teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    db.remove_student(student_id)
    flash("Student removed successfully.", "success")
    return redirect(url_for('class_teacher_dashboard'))

@app.route('/api/class-teacher/reset-device/<int:student_id>', methods=['POST'])
def reset_student_device(student_id):
    if session.get('role') != 'class_teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    db.reset_device_binding(student_id)
    flash("Student hardware device binding reset. Student can now bind a new device on next login.", "success")
    return redirect(url_for('class_teacher_dashboard'))

@app.route('/api/class-teacher/add-subject', methods=['POST'])
def add_subject():
    if session.get('role') != 'class_teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    code = request.form.get('code')
    name = request.form.get('name')
    teacher_id = request.form.get('teacher_id')
    db.add_subject(code, name, class_id=1, teacher_id=teacher_id)
    flash(f"Subject {name} created successfully!", "success")
    return redirect(url_for('class_teacher_dashboard'))

@app.route('/api/class-teacher/delete-subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    if session.get('role') != 'class_teacher':
        return jsonify({'error': 'Unauthorized'}), 403

    db.delete_subject(subject_id)
    flash("Subject removed successfully.", "success")
    return redirect(url_for('class_teacher_dashboard'))

# ----------------------------------------------------
# Teacher & Attendance Session Routes
# ----------------------------------------------------

@app.route('/teacher')
def teacher_dashboard():
    role = session.get('role')
    if role not in ('teacher', 'class_teacher'):
        flash("Unauthorized. Teacher or Class Teacher role required.", "danger")
        return redirect(url_for('index'))

    teacher_id = session.get('user_id')
    if role == 'class_teacher':
        # Class teacher can teach any subject or take attendance for their own subjects
        subjects = db.get_all_subjects()
    else:
        subjects = db.get_subjects_for_teacher(teacher_id)

    return render_template('teacher.html', subjects=subjects)

@app.route('/api/session/start', methods=['POST'])
def start_session():
    role = session.get('role')
    if role not in ('teacher', 'class_teacher'):
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json() or {}
    subject_id = data.get('subject_id')
    duration_seconds = int(data.get('duration_seconds', 60))

    if not subject_id:
        return jsonify({'error': 'Subject is required'}), 400

    teacher_id = session.get('user_id')
    initial_token = f"ATT-{uuid.uuid4().hex[:8].upper()}"
    session_id = db.create_session(subject_id, teacher_id, initial_token, duration_seconds)

    sess = db.get_session(session_id)
    return jsonify({
        'success': True,
        'session_id': session_id,
        'subject_name': sess['subject_name'],
        'duration_seconds': duration_seconds,
        'token': initial_token
    })

@app.route('/api/session/<int:session_id>/qr')
def get_session_qr(session_id):
    role = session.get('role')
    if role not in ('teacher', 'class_teacher'):
        return jsonify({'error': 'Unauthorized'}), 403

    sess = db.get_session(session_id)
    if not sess:
        return jsonify({'error': 'Session not found'}), 404

    # Check if expired
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if str(sess['expires_at']) <= now or not sess['is_active']:
        db.close_session(session_id)
        return jsonify({'is_active': False, 'message': 'Session expired'})

    # Generate a dynamic rotating token (changes every 15 seconds)
    # Token structure: ATT-[SESSION_ID]-[TIMESTAMP_WINDOW]-[SALT]
    time_window = int(time.time() // 15)
    dynamic_token = f"QR-{sess['id']}-{time_window}-{sess['session_token'][:6]}"

    # Generate QR Code image in memory
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=3,
    )
    qr.add_data(dynamic_token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1e1b4b", back_color="white")

    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return jsonify({
        'is_active': True,
        'token': dynamic_token,
        'qr_image': f"data:image/png;base64,{img_b64}"
    })

@app.route('/api/session/<int:session_id>/live-status')
def session_live_status(session_id):
    sess = db.get_session(session_id)
    if not sess:
        return jsonify({'error': 'Session not found'}), 404

    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    is_active = (str(sess['expires_at']) > now) and bool(sess['is_active'])
    if not is_active and sess['is_active']:
        db.close_session(session_id)

    students = db.get_students(sess['class_id'])
    present_records = db.get_session_present_students(session_id)

    return jsonify({
        'is_active': is_active,
        'total_enrolled': len(students),
        'present_count': len(present_records),
        'records': present_records
    })

@app.route('/api/session/<int:session_id>/close', methods=['POST'])
def close_session(session_id):
    role = session.get('role')
    if role not in ('teacher', 'class_teacher'):
        return jsonify({'error': 'Unauthorized'}), 403

    db.close_session(session_id)
    return jsonify({'success': True, 'message': 'Session closed.'})

@app.route('/api/session/<int:session_id>/report')
def session_report(session_id):
    role = session.get('role')
    if role not in ('teacher', 'class_teacher'):
        return jsonify({'error': 'Unauthorized'}), 403

    report = db.get_session_report(session_id)
    if not report:
        return jsonify({'error': 'Session not found'}), 404
    return jsonify(report)

@app.route('/session/<int:session_id>/export-csv')
def export_session_csv(session_id):
    role = session.get('role')
    if role not in ('teacher', 'class_teacher'):
        return "Unauthorized", 403

    report = db.get_session_report(session_id)
    if not report:
        return "Session not found", 404

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Dynamic QR Attendance Report'])
    cw.writerow(['Subject', report['session']['subject_name'], 'Code', report['session']['subject_code']])
    cw.writerow(['Class', report['session']['class_name'], 'Faculty', report['session']['teacher_name']])
    cw.writerow(['Conducted On', report['session']['started_at'], 'Duration', f"{report['session']['duration_seconds']}s"])
    cw.writerow(['Total Students', report['total_students'], 'Present', report['present_count'], 'Absent', report['absent_count'], 'Attendance Rate', f"{report['attendance_percentage']}%"])
    cw.writerow([])
    cw.writerow(['Roll Number', 'Student Name', 'Status', 'Scan Timestamp', 'Verified Device ID'])

    for s in report['students']:
        cw.writerow([
            s['roll_no'],
            s['full_name'],
            s['status'],
            s['scanned_at'] or 'N/A',
            s['device_id'] or 'N/A'
        ])

    output = si.getvalue()
    filename = f"attendance_report_{report['session']['subject_code']}_{report['session']['id']}.csv"
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )

# ----------------------------------------------------
# Student Portal & QR Scan Verification Routes
# ----------------------------------------------------

@app.route('/student')
def student_dashboard():
    if session.get('role') != 'student':
        flash("Unauthorized. Student access only.", "danger")
        return redirect(url_for('index'))

    student_id = session.get('user_id')
    student = db.get_user_by_id(student_id)
    subjects = db.get_subjects_for_student(student['class_id'])
    summary = db.get_student_attendance_summary(student_id)

    return render_template('student.html', 
                           student=student, 
                           subjects=subjects, 
                           summary=summary)

@app.route('/api/student/check-active-session')
def check_student_active_session():
    if session.get('role') != 'student':
        return jsonify({'is_active': False})

    student_id = session.get('user_id')
    is_active, sess = db.is_student_session_active(student_id)
    if is_active and sess:
        return jsonify({
            'is_active': True,
            'session': {
                'id': sess['id'],
                'name': sess['subject_name'],
                'code': sess['subject_code'],
                'teacher_name': sess['teacher_name'],
                'expires_at': str(sess['expires_at']),
                'subject_id': sess['subject_id']
            }
        })
    return jsonify({'is_active': False})

@app.route('/api/student/mark-attendance', methods=['POST'])
def mark_attendance():
    if session.get('role') != 'student':
        return jsonify({'success': False, 'error': 'Unauthorized. Student session required.'}), 403

    student_id = session.get('user_id')
    student = db.get_user_by_id(student_id)
    if not student:
        return jsonify({'success': False, 'error': 'Student not found.'}), 404

    data = request.get_json() or {}
    token = data.get('token', '').strip()
    device_id = data.get('device_id', '').strip()

    # 1. Device Binding Verification
    if not student['bound_device_id']:
        db.bind_device(student_id, device_id)
        student['bound_device_id'] = device_id

    if student['bound_device_id'] != device_id:
        return jsonify({
            'success': False, 
            'error': f'Device mismatch! Attendance must be scanned from your registered device ({student["bound_device_id"]}).'
        }), 403

    # 2. Check Active Session for this student's class
    is_active, sess = db.is_student_session_active(student_id)
    if not is_active or not sess:
        return jsonify({
            'success': False, 
            'error': 'No active attendance session found for your class or the session has expired.'
        }), 400

    # 3. Dynamic Token Verification
    # Expected token formats:
    # Full QR: QR-[SESSION_ID]-[TIME_WINDOW]-[SALT]
    # Suffix or manual 6-digit code: sess['session_token'][-6:] or token string
    time_window = int(time.time() // 15)
    valid_window_tokens = [
        f"QR-{sess['id']}-{time_window}-{sess['session_token'][:6]}",
        f"QR-{sess['id']}-{time_window - 1}-{sess['session_token'][:6]}", # Accept previous 15s window to avoid edge cases
        f"QR-{sess['id']}-{time_window + 1}-{sess['session_token'][:6]}",
        sess['session_token'],
        sess['session_token'][-6:].upper()
    ]

    is_token_valid = (token in valid_window_tokens) or (token == sess['session_token'][-6:].upper())
    if not is_token_valid:
        return jsonify({
            'success': False, 
            'error': 'QR Code has expired or is invalid! Dynamic QR rotates every 15 seconds. Please scan the current QR code on the screen.'
        }), 400

    # 4. Mark attendance in database
    ok, msg = db.record_attendance(sess['id'], student_id, device_id)
    if not ok:
        return jsonify({'success': False, 'error': msg}), 400

    now_str = datetime.datetime.now().strftime('%I:%M:%S %p')
    return jsonify({
        'success': True,
        'message': 'Your attendance has been recorded successfully.',
        'subject_name': sess['subject_name'],
        'timestamp': now_str
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    print("=" * 65)
    print(" Smart Dynamic QR Attendance & Management System")
    print(" Class Teacher, Teachers & Student Portals with Device Binding")
    print("=" * 65)
    print(f" * Running on: http://0.0.0.0:{port}")
    print(" * Class Teacher Demo:  classteacher / password123")
    print(" * Faculty Demo:        prof_verma   / password123")
    print(" * Student Demo:        student_rohit / password123")
    print("=" * 65)
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

