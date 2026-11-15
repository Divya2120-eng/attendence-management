-- Dynamic QR Code Attendance & Management System
-- MySQL Database Schema
-- Database: attendance_system

CREATE DATABASE IF NOT EXISTS attendance_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE attendance_system;

-- 1. Classes Table
CREATE TABLE IF NOT EXISTS classes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    branch VARCHAR(50) NOT NULL,
    year VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Users Table (Class Teacher, Teachers, Students)
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
    bound_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_class FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 3. Subjects Table
CREATE TABLE IF NOT EXISTS subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    class_id INT NOT NULL,
    teacher_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_subjects_class FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
    CONSTRAINT fk_subjects_teacher FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 4. Attendance Sessions Table
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
    CONSTRAINT fk_sessions_subject FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    CONSTRAINT fk_sessions_teacher FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5. Attendance Records Table
CREATE TABLE IF NOT EXISTS attendance_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    student_id INT NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    status ENUM('PRESENT', 'ABSENT') NOT NULL DEFAULT 'PRESENT',
    scanned_at DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_session_student (session_id, student_id),
    CONSTRAINT fk_records_session FOREIGN KEY (session_id) REFERENCES attendance_sessions(id) ON DELETE CASCADE,
    CONSTRAINT fk_records_student FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ========================================================
-- Seed Initial Data
-- ========================================================

-- Insert Sample Class: Third Year CSE
INSERT INTO classes (id, name, branch, year) VALUES 
(1, 'Third Year CSE', 'Computer Science & Engineering', '3rd Year')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- Insert Default Single Class Teacher (Admin)
-- Default Password: password123 (hashed)
INSERT INTO users (id, username, password_hash, full_name, email, role, class_id, roll_no, bound_device_id) VALUES 
(1, 'classteacher', 'pbkdf2:sha256:600000$defaultHash$8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'Prof. Sharma (Class Teacher)', 'classteacher@college.edu', 'class_teacher', 1, NULL, NULL),
(2, 'prof_verma', 'pbkdf2:sha256:600000$defaultHash$8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'Prof. Verma', 'verma@college.edu', 'teacher', 1, NULL, NULL),
(3, 'prof_gupta', 'pbkdf2:sha256:600000$defaultHash$8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'Prof. Gupta', 'gupta@college.edu', 'teacher', 1, NULL, NULL)
ON DUPLICATE KEY UPDATE full_name=VALUES(full_name);

-- Insert Subjects for Third Year CSE
INSERT INTO subjects (id, code, name, class_id, teacher_id) VALUES 
(1, 'CS301', 'Operating System', 1, 1),
(2, 'CS302', 'Database Management Systems', 1, 2),
(3, 'CS303', 'Computer Networks', 1, 3)
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- Insert Sample Students for Third Year CSE
INSERT INTO users (username, password_hash, full_name, email, role, class_id, roll_no) VALUES 
('student_rohit', 'pbkdf2:sha256:600000$defaultHash$8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'Rohit Kumar', 'rohit@student.college.edu', 'student', 1, 'CSE-2023-01'),
('student_priya', 'pbkdf2:sha256:600000$defaultHash$8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'Priya Singh', 'priya@student.college.edu', 'student', 1, 'CSE-2023-02'),
('student_amit', 'pbkdf2:sha256:600000$defaultHash$8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'Amit Patel', 'amit@student.college.edu', 'student', 1, 'CSE-2023-03'),
('student_neha', 'pbkdf2:sha256:600000$defaultHash$8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'Neha Sharma', 'neha@student.college.edu', 'student', 1, 'CSE-2023-04'),
('student_rahul', 'pbkdf2:sha256:600000$defaultHash$8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'Rahul Verma', 'rahul@student.college.edu', 'student', 1, 'CSE-2023-05')
ON DUPLICATE KEY UPDATE full_name=VALUES(full_name);
