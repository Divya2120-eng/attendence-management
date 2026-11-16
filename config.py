import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dynamic-qr-attendance-secret-key-2026')
    
    # Database Configuration
    # To use MySQL: Set USE_MYSQL = True and configure MySQL credentials below
    # If MySQL is not running, the application automatically falls back to SQLite
    USE_MYSQL = os.environ.get('USE_MYSQL', 'False').lower() in ('true', '1', 't')
    
    # MySQL Settings (XAMPP / WAMP / Standalone MySQL)
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'attendance_system')
    
    # SQLite fallback file
    SQLITE_DB = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'attendance.db')

    # Exclusive Single Class Teacher / Admin Credentials
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin1955')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '1955')
    CLASS_TEACHER_EMAIL = os.environ.get('CLASS_TEACHER_EMAIL', 'prasadmhankraj21@gmail.com')
    CLASS_TEACHER_BACKUP_EMAIL = 'classteacher@college.edu'
