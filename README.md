# Smart Dynamic QR Attendance & Management System
> **Academic Mini-Project** | CSE Department • Third Year CSE

A complete College Attendance Management System built with **Python Flask**, **MySQL / Oracle SQL / SQLite**, dynamic rotating QR code security, hardware device-binding (anti-proxy), and real-time attendance reporting.

---

## 🌟 Key Features & Problem Solutions

1. **Role-Based Access Control**:
   - **Class Teacher (Head Admin - Single Person Designated)**:
     - Only **ONE** designated master administrator account (`classteacher`).
     - Can **Add & Remove Teachers / Faculty**.
     - Can **Add & Remove Students** (with Roll Number, Branch, Class).
     - Can **Reset Student Hardware Device Bindings** (if a student changes phones).
     - Can choose their assigned subject (e.g., *Operating System*) and **take attendance directly**.
   - **Faculty / Teachers**:
     - Login with faculty credentials.
     - Select assigned subject (e.g., *Database Management Systems*, *Computer Networks*).
     - Configure attendance validity duration (e.g., 30s, 60s, 2 min, 5 min).
     - Live Dynamic QR Code generation with countdown timer.
     - Live real-time scan feed.
     - Instant completion report (**Present vs Absent list**) with CSV export and printing.
   - **Students (Third Year CSE)**:
     - Login with Student username or Roll Number.
     - Dashboard displays student's class (*Third Year CSE*) and all enrolled courses (*Operating System, DBMS, Computer Networks*).
     - **Device Binding**: Student account is bound strictly to **1 physical device**. Logins from duplicate phones or sharing phones with friends are prohibited.
     - **Dynamic QR Scanner**: Uses mobile / laptop camera (`html5-qrcode`) to scan the teacher's dynamic QR code.
     - **Active Session Logout Lock**: Students **cannot log out** while a QR attendance session is active for their class.

2. **Anti-Proxy Security**:
   - **Rotating Dynamic QR Code**: Changes cryptographic tokens every 15 seconds. Taking photos or forwarding screenshots over WhatsApp expires before other students can scan.
   - **1-Student = 1-Device Binding**: Enforced via hardware fingerprints. Multiple student accounts cannot share a single phone, and a student account cannot be used from an unauthorized device.
   - **Session Logout Restriction**: Logout is blocked while attendance is in progress.

3. **Dual Database Architecture (MySQL + Oracle + Zero-Setup SQLite)**:
   - **MySQL**: Full DDL schema provided in `schema_mysql.sql`.
   - **Oracle**: Complete Oracle 12c/19c/21c DDL script provided in `schema_oracle.sql`.
   - **Auto-Fallback / Zero-Setup Mode**: If MySQL is not running locally, the project automatically launches on embedded SQLite with identical tables and seed data, allowing immediate testing and demonstrations without requiring MySQL to be configured first.

---

## 🚀 How to Run the Project

### 1. Requirements
- Python 3.10+
- Flask, PyMySQL, qrcode, pillow (all included in `requirements.txt`)

### 2. Quick Start
```bash
# Clone or navigate to the project directory
cd "d:\attendence miniproj"

# Install dependencies (already installed)
pip install -r requirements.txt

# Launch the Application
python app.py
```
Open your browser and navigate to:
👉 **`http://localhost:5000`**

---

## 🗄️ Database Setup (MySQL & Oracle)

### Using MySQL (XAMPP / WAMP / MySQL Workbench)
1. Start MySQL Server (e.g., on Port 3306).
2. Create and import the database:
   ```bash
   mysql -u root -p < schema_mysql.sql
   ```
3. Enable MySQL in `config.py` or `.env`:
   ```python
   USE_MYSQL = True
   MYSQL_HOST = 'localhost'
   MYSQL_USER = 'root'
   MYSQL_PASSWORD = ''
   MYSQL_DB = 'attendance_system'
   ```
4. Restart `python app.py`. The system connects directly to MySQL via `pymysql`.

### Using Oracle Database
Import `schema_oracle.sql` using Oracle SQL Developer or SQL*Plus:
```sql
@schema_oracle.sql;
```

---

## 🔑 Demo Login Credentials

For quick testing and live evaluation, 1-click auto-fill buttons are provided on the login page:

| Role | Username | Password | Notes |
|---|---|---|---|
| **Class Teacher** | `classteacher` | `password123` | Exclusive Single-Person Admin (Prof. Sharma) |
| **Faculty (Teacher)** | `prof_verma` | `password123` | Teacher for DBMS |
| **Faculty (Teacher)** | `prof_gupta` | `password123` | Teacher for Computer Networks |
| **Student 1** | `student_rohit` | `password123` | Rohit Kumar (CSE-2023-01) |
| **Student 2** | `student_priya` | `password123` | Priya Singh (CSE-2023-02) |
| **Student 3** | `student_amit` | `password123` | Amit Patel (CSE-2023-03) |
| **Student 4** | `student_neha` | `password123` | Neha Sharma (CSE-2023-04) |
| **Student 5** | `student_rahul` | `password123` | Rahul Verma (CSE-2023-05) |

---

## 📋 Project Directory Structure

```
d:\attendence miniproj\
├── app.py                     # Main Flask Application & Web Controller
├── config.py                  # Environment & Database Configuration
├── db.py                      # Database Abstraction Layer (MySQL & SQLite)
├── schema_mysql.sql           # MySQL DDL & Seed Data
├── schema_oracle.sql          # Oracle DDL & Constraints
├── requirements.txt           # Python Dependencies
├── README.md                  # Complete Documentation
├── static/
│   ├── css/
│   │   └── style.css          # Modern Styling, QR & Timer Animation
│   ├── js/
│   │   ├── device.js          # Hardware Fingerprinting & Device Binding
│   │   └── scanner.js         # Camera QR Scanner & Audio Feedback
│   └── vendor/
│       └── html5-qrcode.min.js# Offline QR Scanner Engine
└── templates/
    ├── base.html              # Layout, Navigation, Logout Interceptor
    ├── login.html             # Multi-role Login & Hardware ID Detector
    ├── class_teacher.html     # Class Teacher Management Panel
    ├── teacher.html           # Dynamic QR Session & Attendance Report
    └── student.html           # Student Dashboard & In-App QR Scanner
```
