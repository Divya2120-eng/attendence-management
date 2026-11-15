from app import app
from db import db
import json

def run_tests():
    client = app.test_client()

    # 1. Login as Class Teacher
    res = client.post('/login', data={'username': 'classteacher', 'password': 'password123', 'device_id': 'DEV-ADMIN', 'selected_role': 'class_teacher'}, follow_redirects=True)
    assert res.status_code == 200
    print('[TEST 1 PASSED] Class Teacher login successful.')

    # 2. Add teacher via Class Teacher
    res = client.post('/api/class-teacher/add-teacher', data={'full_name': 'Prof. Test Faculty', 'username': 'prof_test', 'password': 'password123'}, follow_redirects=True)
    assert res.status_code == 200
    print('[TEST 2 PASSED] Teacher added by Class Teacher.')

    # 3. Start Attendance Session
    res = client.post('/api/session/start', data=json.dumps({'subject_id': 1, 'duration_seconds': 60}), content_type='application/json')
    sess_data = res.get_json()
    assert sess_data['success'] == True
    sess_id = sess_data['session_id']
    print(f'[TEST 3 PASSED] Dynamic attendance session started. ID: {sess_id}')

    # 4. Get dynamic QR token
    res = client.get(f'/api/session/{sess_id}/qr')
    qr_data = res.get_json()
    assert qr_data['is_active'] == True
    token = qr_data['token']
    print(f'[TEST 4 PASSED] Dynamic QR generated with token: {token[:15]}...')

    # 5. Login as Student Rohit with Device 1
    client_stu = app.test_client()
    res = client_stu.post('/login', data={'username': 'student_rohit', 'password': 'password123', 'device_id': 'DEV-ROHIT-PHONE', 'selected_role': 'student'}, follow_redirects=True)
    assert res.status_code == 200
    print('[TEST 5 PASSED] Student Rohit logged in and bound to DEV-ROHIT-PHONE.')

    # 6. Test Logout Lock during active session
    res = client_stu.get('/logout', follow_redirects=True)
    assert b'SECURITY RESTRICTION: You cannot log out' in res.data
    print('[TEST 6 PASSED] Logout successfully blocked while QR attendance is active.')

    # 7. Student Marks Attendance via QR scan
    res = client_stu.post('/api/student/mark-attendance', data=json.dumps({'token': token, 'device_id': 'DEV-ROHIT-PHONE'}), content_type='application/json')
    mark_data = res.get_json()
    assert mark_data['success'] == True
    print('[TEST 7 PASSED] Student attendance marked PRESENT via dynamic QR token.')

    # 8. Check Report on Teacher Screen
    res = client.get(f'/api/session/{sess_id}/report')
    report_data = res.get_json()
    p_cnt = report_data['present_count']
    a_cnt = report_data['absent_count']
    assert p_cnt == 1
    print(f'[TEST 8 PASSED] Final Report: Present = {p_cnt}, Absent = {a_cnt}.')

    # 9. Close Session and Test Student Logout Allowed
    client.post(f'/api/session/{sess_id}/close')
    res = client_stu.get('/logout', follow_redirects=True)
    assert b'You have been signed out' in res.data
    print('[TEST 9 PASSED] After session closed, Student logout is allowed.')

    print('\n========================================')
    print('ALL 9 END-TO-END VERIFICATION TESTS PASSED!')
    print('========================================')

if __name__ == '__main__':
    run_tests()
