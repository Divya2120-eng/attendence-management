import os
import sqlite3
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

class Database:
    def __init__(self):
        self.use_mysql = Config.USE_MYSQL
        self.connection = None
        self._init_db()

    def get_connection(self):
        if self.use_mysql:
            try:
                import pymysql
                import pymysql.cursors
                conn = pymysql.connect(
                    host=Config.MYSQL_HOST,
                    port=Config.MYSQL_PORT,
                    user=Config.MYSQL_USER,
                    password=Config.MYSQL_PASSWORD,
                    database=Config.MYSQL_DB,
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=True
                )
                return conn
            except Exception as e:
                print(f"[DB Warning] Could not connect to MySQL ({e}). Falling back to SQLite.")
                self.use_mysql = False
                return self._get_sqlite_connection()
        else:
            return self._get_sqlite_connection()

    def _get_sqlite_connection(self):
        conn = sqlite3.connect(Config.SQLITE_DB)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        """Initializes tables and seeds initial data if not present."""
        if self.use_mysql:
            try:
                import pymysql
                server_conn = pymysql.connect(
                    host=Config.MYSQL_HOST,
                    port=Config.MYSQL_PORT,
                    user=Config.MYSQL_USER,
                    password=Config.MYSQL_PASSWORD
                )
                with server_conn.cursor() as cur:
                    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` CHARACTER SET utf8mb4;")
                server_conn.close()
            except Exception as e:
                print(f"[DB Info] MySQL Server not reachable on port {Config.MYSQL_PORT}. Defaulting to SQLite. ({e})")
                self.use_mysql = False

        conn = self.get_connection()
        cursor = conn.cursor()

        if self.use_mysql:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                branch VARCHAR(50) NOT NULL,
                year VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(100),
                role ENUM('class_teacher', 'teacher', 'student') NOT NULL,
                class_id INT NULL,
                roll_no VARCHAR(50) NULL,
                bound_device_id VARCHAR(255) NULL,
                bound_at DATETIME NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE SET NULL
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                code VARCHAR(20) NOT NULL,
                name VARCHAR(100) NOT NULL,
                class_id INT NOT NULL,
                teacher_id INT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
                FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                subject_id INT NOT NULL,
                teacher_id INT NOT NULL,
                session_token VARCHAR(255) NOT NULL,
                duration_seconds INT NOT NULL DEFAULT 60,
                started_at DATETIME NOT NULL,
                expires_at DATETIME NOT NULL,
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id INT NOT NULL,
                student_id INT NOT NULL,
                device_id VARCHAR(255) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'PRESENT',
                scanned_at DATETIME NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_session_student (session_id, student_id),
                FOREIGN KEY (session_id) REFERENCES attendance_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """)
        else:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                branch TEXT NOT NULL,
                year TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT,
                role TEXT NOT NULL CHECK (role IN ('class_teacher', 'teacher', 'student')),
                class_id INTEGER NULL REFERENCES classes(id) ON DELETE SET NULL,
                roll_no TEXT NULL,
                bound_device_id TEXT NULL,
                bound_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                teacher_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
                teacher_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                session_token TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL DEFAULT 60,
                started_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES attendance_sessions(id) ON DELETE CASCADE,
                student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                device_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PRESENT',
                scanned_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(session_id, student_id)
            );
            """)
            conn.commit()

        self._seed_default_data(conn, cursor)
        # Ensure single Class Teacher has designated authorized email
        param = "%s" if self.use_mysql else "?"
        cursor.execute(f"UPDATE users SET email = {param} WHERE role = 'class_teacher'", (Config.CLASS_TEACHER_EMAIL,))
        if not self.use_mysql:
            conn.commit()
        conn.close()


    def _seed_default_data(self, conn, cursor):
        cursor.execute("SELECT COUNT(*) as count FROM users")
        row = cursor.fetchone()
        count = row['count'] if isinstance(row, dict) else row[0]
        if count == 0:
            print("[DB Seed] Seeding initial data...")
            default_pwd = generate_password_hash("password123")

            param = "%s" if self.use_mysql else "?"
            cursor.execute(f"INSERT INTO classes (name, branch, year) VALUES ({param}, {param}, {param})", 
                           ('Third Year CSE', 'Computer Science & Engineering', '3rd Year'))
            class_id = cursor.lastrowid

            cursor.execute(f"""
            INSERT INTO users (username, password_hash, full_name, email, role, class_id)
            VALUES ({param}, {param}, {param}, {param}, {param}, {param})
            """, ('classteacher', default_pwd, 'Prof. Prasad (Class Teacher)', Config.CLASS_TEACHER_EMAIL, 'class_teacher', class_id))
            ct_id = cursor.lastrowid


            teachers = [
                ('prof_verma', default_pwd, 'Prof. R. Verma', 'verma@college.edu', 'teacher', class_id),
                ('prof_gupta', default_pwd, 'Prof. S. Gupta', 'gupta@college.edu', 'teacher', class_id)
            ]
            t_ids = []
            for t in teachers:
                cursor.execute(f"""
                INSERT INTO users (username, password_hash, full_name, email, role, class_id)
                VALUES ({param}, {param}, {param}, {param}, {param}, {param})
                """, t)
                t_ids.append(cursor.lastrowid)

            subjects = [
                ('CS301', 'Operating System', class_id, ct_id),
                ('CS302', 'Database Management Systems', class_id, t_ids[0]),
                ('CS303', 'Computer Networks', class_id, t_ids[1])
            ]
            for s in subjects:
                cursor.execute(f"""
                INSERT INTO subjects (code, name, class_id, teacher_id)
                VALUES ({param}, {param}, {param}, {param})
                """, s)

            students = [
                ('student_rohit', default_pwd, 'Rohit Kumar', 'rohit@student.college.edu', 'student', class_id, 'CSE-2023-01'),
                ('student_priya', default_pwd, 'Priya Singh', 'priya@student.college.edu', 'student', class_id, 'CSE-2023-02'),
                ('student_amit', default_pwd, 'Amit Patel', 'amit@student.college.edu', 'student', class_id, 'CSE-2023-03'),
                ('student_neha', default_pwd, 'Neha Sharma', 'neha@student.college.edu', 'student', class_id, 'CSE-2023-04'),
                ('student_rahul', default_pwd, 'Rahul Verma', 'rahul@student.college.edu', 'student', class_id, 'CSE-2023-05')
            ]
            for stu in students:
                cursor.execute(f"""
                INSERT INTO users (username, password_hash, full_name, email, role, class_id, roll_no)
                VALUES ({param}, {param}, {param}, {param}, {param}, {param}, {param})
                """, stu)

            if not self.use_mysql:
                conn.commit()
            print("[DB Seed] Completed seeding initial data successfully.")

    def query(self, sql, params=(), one=False):
        conn = self.get_connection()
        cursor = conn.cursor()
        if not self.use_mysql:
            sql = sql.replace('%s', '?')
        else:
            sql = sql.replace('?', '%s')
        cursor.execute(sql, params)
        if one:
            result = cursor.fetchone()
            if result and not self.use_mysql:
                result = dict(result)
        else:
            rows = cursor.fetchall()
            if not self.use_mysql:
                result = [dict(r) for r in rows]
            else:
                result = rows
        conn.close()
        return result

    def execute(self, sql, params=()):
        conn = self.get_connection()
        cursor = conn.cursor()
        if not self.use_mysql:
            sql = sql.replace('%s', '?')
        else:
            sql = sql.replace('?', '%s')
        cursor.execute(sql, params)
        last_id = cursor.lastrowid
        row_count = cursor.rowcount
        if not self.use_mysql:
            conn.commit()
        conn.close()
        return last_id, row_count

    # ------------------ High Level Helper Methods ------------------

    # --- User Management ---
    def get_user_by_email_or_username(self, identifier):
        return self.query("""
            SELECT u.*, c.name as class_name, c.branch, c.year 
            FROM users u 
            LEFT JOIN classes c ON u.class_id = c.id 
            WHERE u.email = %s OR u.username = %s
        """, (identifier, identifier), one=True)

    def get_class_teacher(self):
        return self.query("""
            SELECT u.*, c.name as class_name, c.branch, c.year 
            FROM users u 
            LEFT JOIN classes c ON u.class_id = c.id 
            WHERE u.role = 'class_teacher'
        """, one=True)

    def get_user_by_username(self, username):

        return self.query("""
            SELECT u.*, c.name as class_name, c.branch, c.year 
            FROM users u 
            LEFT JOIN classes c ON u.class_id = c.id 
            WHERE u.username = %s
        """, (username,), one=True)

    def get_user_by_id(self, user_id):
        return self.query("""
            SELECT u.*, c.name as class_name, c.branch, c.year 
            FROM users u 
            LEFT JOIN classes c ON u.class_id = c.id 
            WHERE u.id = %s
        """, (user_id,), one=True)

    def get_teachers(self):
        sql = """
            SELECT u.id, u.username, u.full_name, u.email, u.role, u.created_at,
                   GROUP_CONCAT(s.name, ', ') as assigned_subjects
            FROM users u
            LEFT JOIN subjects s ON s.teacher_id = u.id
            WHERE u.role IN ('teacher', 'class_teacher')
            GROUP BY u.id
            ORDER BY u.role DESC, u.full_name ASC
        """ if not self.use_mysql else """
            SELECT u.id, u.username, u.full_name, u.email, u.role, u.created_at,
                   GROUP_CONCAT(s.name SEPARATOR ', ') as assigned_subjects
            FROM users u
            LEFT JOIN subjects s ON s.teacher_id = u.id
            WHERE u.role IN ('teacher', 'class_teacher')
            GROUP BY u.id
            ORDER BY u.role DESC, u.full_name ASC
        """
        return self.query(sql)

    def get_students(self, class_id=None):
        if class_id:
            return self.query("""
                SELECT u.id, u.username, u.full_name, u.email, u.roll_no, u.class_id, 
                       u.bound_device_id, u.bound_at, u.created_at, c.name as class_name
                FROM users u
                LEFT JOIN classes c ON u.class_id = c.id
                WHERE u.role = 'student' AND u.class_id = %s
                ORDER BY u.roll_no ASC
            """, (class_id,))
        else:
            return self.query("""
                SELECT u.id, u.username, u.full_name, u.email, u.roll_no, u.class_id, 
                       u.bound_device_id, u.bound_at, u.created_at, c.name as class_name
                FROM users u
                LEFT JOIN classes c ON u.class_id = c.id
                WHERE u.role = 'student'
                ORDER BY c.name ASC, u.roll_no ASC
            """)

    def add_teacher(self, username, password, full_name, email=None, class_id=1):
        existing = self.query("SELECT id FROM users WHERE username = %s", (username,), one=True)
        if existing:
            return None, "Username already exists."
        pwd_hash = generate_password_hash(password)
        last_id, _ = self.execute("""
            INSERT INTO users (username, password_hash, full_name, email, role, class_id)
            VALUES (%s, %s, %s, %s, 'teacher', %s)
        """, (username, pwd_hash, full_name, email, class_id))
        return last_id, None

    def remove_teacher(self, teacher_id):
        user = self.get_user_by_id(teacher_id)
        if not user:
            return False, "Teacher not found."
        if user['role'] == 'class_teacher':
            return False, "Cannot delete the designated Class Teacher account!"
        self.execute("DELETE FROM users WHERE id = %s AND role = 'teacher'", (teacher_id,))
        return True, None

    def add_student(self, username, password, full_name, roll_no, email=None, class_id=1):
        existing = self.query("SELECT id FROM users WHERE username = %s OR roll_no = %s", (username, roll_no), one=True)
        if existing:
            return None, "Username or Roll Number already exists."
        pwd_hash = generate_password_hash(password)
        last_id, _ = self.execute("""
            INSERT INTO users (username, password_hash, full_name, email, role, class_id, roll_no)
            VALUES (%s, %s, %s, %s, 'student', %s, %s)
        """, (username, pwd_hash, full_name, email, class_id, roll_no))
        return last_id, None

    def remove_student(self, student_id):
        self.execute("DELETE FROM users WHERE id = %s AND role = 'student'", (student_id,))
        return True, None

    # --- Device Binding Security ---
    def bind_device(self, user_id, device_id):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.execute("""
            UPDATE users SET bound_device_id = %s, bound_at = %s WHERE id = %s
        """, (device_id, now, user_id))

    def reset_device_binding(self, student_id):
        self.execute("""
            UPDATE users SET bound_device_id = NULL, bound_at = NULL WHERE id = %s AND role = 'student'
        """, (student_id,))
        return True

    def find_student_with_device(self, device_id, exclude_student_id=None):
        if exclude_student_id:
            return self.query("""
                SELECT id, username, full_name, roll_no FROM users 
                WHERE bound_device_id = %s AND id != %s AND role = 'student'
            """, (device_id, exclude_student_id), one=True)
        else:
            return self.query("""
                SELECT id, username, full_name, roll_no FROM users 
                WHERE bound_device_id = %s AND role = 'student'
            """, (device_id,), one=True)

    # --- Classes & Subjects ---
    def get_classes(self):
        return self.query("SELECT * FROM classes ORDER BY id ASC")

    def get_all_subjects(self):
        return self.query("""
            SELECT s.*, c.name as class_name, u.full_name as teacher_name
            FROM subjects s
            LEFT JOIN classes c ON s.class_id = c.id
            LEFT JOIN users u ON s.teacher_id = u.id
            ORDER BY c.name ASC, s.name ASC
        """)

    def get_subjects_for_teacher(self, teacher_id):
        return self.query("""
            SELECT s.*, c.name as class_name, c.branch, c.year
            FROM subjects s
            JOIN classes c ON s.class_id = c.id
            WHERE s.teacher_id = %s
            ORDER BY s.name ASC
        """, (teacher_id,))

    def get_subjects_for_student(self, class_id):
        return self.query("""
            SELECT s.*, u.full_name as teacher_name
            FROM subjects s
            LEFT JOIN users u ON s.teacher_id = u.id
            WHERE s.class_id = %s
            ORDER BY s.name ASC
        """, (class_id,))

    def add_subject(self, code, name, class_id, teacher_id=None):
        last_id, _ = self.execute("""
            INSERT INTO subjects (code, name, class_id, teacher_id)
            VALUES (%s, %s, %s, %s)
        """, (code, name, class_id, teacher_id))
        return last_id

    def delete_subject(self, subject_id):
        self.execute("DELETE FROM subjects WHERE id = %s", (subject_id,))
        return True

    # --- Attendance Sessions ---
    def create_session(self, subject_id, teacher_id, session_token, duration_seconds=60):
        # Close any previous active session for this subject
        self.execute("UPDATE attendance_sessions SET is_active = 0 WHERE subject_id = %s", (subject_id,))
        
        now = datetime.datetime.now()
        expires = now + datetime.timedelta(seconds=duration_seconds)
        started_at = now.strftime('%Y-%m-%d %H:%M:%S')
        expires_at = expires.strftime('%Y-%m-%d %H:%M:%S')

        last_id, _ = self.execute("""
            INSERT INTO attendance_sessions (subject_id, teacher_id, session_token, duration_seconds, started_at, expires_at, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, 1)
        """, (subject_id, teacher_id, session_token, duration_seconds, started_at, expires_at))
        return last_id

    def get_session(self, session_id):
        return self.query("""
            SELECT sess.*, s.name as subject_name, s.code as subject_code, s.class_id, 
                   c.name as class_name, u.full_name as teacher_name
            FROM attendance_sessions sess
            JOIN subjects s ON sess.subject_id = s.id
            JOIN classes c ON s.class_id = c.id
            JOIN users u ON sess.teacher_id = u.id
            WHERE sess.id = %s
        """, (session_id,), one=True)

    def get_active_session_for_subject(self, subject_id):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        session = self.query("""
            SELECT sess.*, s.name as subject_name, s.code as subject_code, s.class_id, c.name as class_name
            FROM attendance_sessions sess
            JOIN subjects s ON sess.subject_id = s.id
            JOIN classes c ON s.class_id = c.id
            WHERE sess.subject_id = %s AND sess.is_active = 1 AND sess.expires_at > %s
            ORDER BY sess.id DESC
        """, (subject_id, now), one=True)
        return session

    def get_active_session_for_class(self, class_id):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        session = self.query("""
            SELECT sess.*, s.name as subject_name, s.code as subject_code, s.class_id, 
                   c.name as class_name, u.full_name as teacher_name
            FROM attendance_sessions sess
            JOIN subjects s ON sess.subject_id = s.id
            JOIN classes c ON s.class_id = c.id
            JOIN users u ON sess.teacher_id = u.id
            WHERE s.class_id = %s AND sess.is_active = 1 AND sess.expires_at > %s
            ORDER BY sess.id DESC
        """, (class_id, now), one=True)
        return session

    def update_session_token(self, session_id, new_token):
        self.execute("""
            UPDATE attendance_sessions SET session_token = %s WHERE id = %s
        """, (new_token, session_id))

    def close_session(self, session_id):
        self.execute("""
            UPDATE attendance_sessions SET is_active = 0 WHERE id = %s
        """, (session_id,))

    def check_expired_sessions(self):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.execute("""
            UPDATE attendance_sessions SET is_active = 0 WHERE is_active = 1 AND expires_at <= %s
        """, (now,))

    # --- Attendance Records & Verification ---
    def record_attendance(self, session_id, student_id, device_id):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            self.execute("""
                INSERT INTO attendance_records (session_id, student_id, device_id, status, scanned_at)
                VALUES (%s, %s, %s, 'PRESENT', %s)
            """, (session_id, student_id, device_id, now))
            return True, "Attendance marked successfully!"
        except Exception as e:
            return False, f"Attendance already marked or error: {str(e)}"

    def get_session_present_students(self, session_id):
        return self.query("""
            SELECT r.*, u.full_name, u.roll_no, u.email
            FROM attendance_records r
            JOIN users u ON r.student_id = u.id
            WHERE r.session_id = %s
            ORDER BY r.scanned_at ASC
        """, (session_id,))

    def get_session_report(self, session_id):
        session = self.get_session(session_id)
        if not session:
            return None
        
        class_id = session['class_id']
        all_students = self.get_students(class_id)
        records = self.get_session_present_students(session_id)
        
        present_dict = {r['student_id']: r for r in records}
        
        students_report = []
        present_count = 0
        absent_count = 0

        for s in all_students:
            sid = s['id']
            if sid in present_dict:
                present_count += 1
                rec = present_dict[sid]
                students_report.append({
                    'id': sid,
                    'full_name': s['full_name'],
                    'roll_no': s['roll_no'],
                    'status': 'PRESENT',
                    'scanned_at': rec['scanned_at'],
                    'device_id': rec['device_id']
                })
            else:
                absent_count += 1
                students_report.append({
                    'id': sid,
                    'full_name': s['full_name'],
                    'roll_no': s['roll_no'],
                    'status': 'ABSENT',
                    'scanned_at': None,
                    'device_id': None
                })

        total = len(all_students)
        percentage = round((present_count / total * 100), 1) if total > 0 else 0

        return {
            'session': session,
            'total_students': total,
            'present_count': present_count,
            'absent_count': absent_count,
            'attendance_percentage': percentage,
            'students': students_report
        }

    def get_student_attendance_summary(self, student_id):
        student = self.get_user_by_id(student_id)
        if not student:
            return None
        class_id = student['class_id']
        total_sessions = self.query("""
            SELECT COUNT(*) as count 
            FROM attendance_sessions sess
            JOIN subjects s ON sess.subject_id = s.id
            WHERE s.class_id = %s
        """, (class_id,), one=True)['count']

        attended_sessions = self.query("""
            SELECT COUNT(*) as count 
            FROM attendance_records
            WHERE student_id = %s AND status = 'PRESENT'
        """, (student_id,), one=True)['count']

        records = self.query("""
            SELECT r.scanned_at, r.status, s.name as subject_name, s.code as subject_code
            FROM attendance_records r
            JOIN attendance_sessions sess ON r.session_id = sess.id
            JOIN subjects s ON sess.subject_id = s.id
            WHERE r.student_id = %s
            ORDER BY r.scanned_at DESC
            LIMIT 10
        """, (student_id,))

        percentage = round((attended_sessions / total_sessions * 100), 1) if total_sessions > 0 else 100

        return {
            'total_sessions': total_sessions,
            'attended_sessions': attended_sessions,
            'percentage': percentage,
            'records': records
        }

    def is_student_session_active(self, student_id):
        student = self.get_user_by_id(student_id)
        if not student or not student['class_id']:
            return False, None
        session = self.get_active_session_for_class(student['class_id'])
        if session:
            return True, session
        return False, None

db = Database()
