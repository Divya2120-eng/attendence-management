-- Dynamic QR Code Attendance & Management System
-- Oracle Database Schema (DDL & Sample Data)
-- Compatible with Oracle 12c, 19c, 21c, XE

-- 1. Classes Table
CREATE TABLE classes (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR2(100) NOT NULL,
    branch VARCHAR2(50) NOT NULL,
    year VARCHAR2(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Users Table
CREATE TABLE users (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR2(50) NOT NULL UNIQUE,
    password_hash VARCHAR2(255) NOT NULL,
    full_name VARCHAR2(100) NOT NULL,
    email VARCHAR2(100),
    role VARCHAR2(20) NOT NULL CHECK (role IN ('class_teacher', 'teacher', 'student')),
    class_id NUMBER NULL REFERENCES classes(id) ON DELETE SET NULL,
    roll_no VARCHAR2(50) NULL,
    bound_device_id VARCHAR2(255) NULL,
    bound_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Subjects Table
CREATE TABLE subjects (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR2(20) NOT NULL,
    name VARCHAR2(100) NOT NULL,
    class_id NUMBER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    teacher_id NUMBER NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Attendance Sessions Table
CREATE TABLE attendance_sessions (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    subject_id NUMBER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    teacher_id NUMBER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR2(255) NOT NULL,
    duration_seconds NUMBER DEFAULT 60 NOT NULL,
    started_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_active NUMBER(1) DEFAULT 1 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Attendance Records Table
CREATE TABLE attendance_records (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_id NUMBER NOT NULL REFERENCES attendance_sessions(id) ON DELETE CASCADE,
    student_id NUMBER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id VARCHAR2(255) NOT NULL,
    status VARCHAR2(10) DEFAULT 'PRESENT' NOT NULL CHECK (status IN ('PRESENT', 'ABSENT')),
    scanned_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_session_student UNIQUE (session_id, student_id)
);

COMMIT;
