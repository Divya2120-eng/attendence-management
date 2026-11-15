/**
 * Standalone App Controller for GitHub Pages Deployment
 * Powers the full Dynamic QR Attendance System directly in the browser!
 */

// Initial Seed Data (Third Year CSE)
const defaultData = {
  teachers: [
    { id: 1, name: "Prof. Prasad (Class Teacher)", username: "classteacher", email: "prasadmhankraj21@gmail.com", role: "class_teacher" },
    { id: 2, name: "Prof. R. Verma", username: "prof_verma", role: "teacher" },
    { id: 3, name: "Prof. S. Gupta", username: "prof_gupta", role: "teacher" }
  ],

  students: [
    { id: 1, name: "Rohit Kumar", roll: "CSE-2023-01", username: "student_rohit", deviceId: null },
    { id: 2, name: "Priya Singh", roll: "CSE-2023-02", username: "student_priya", deviceId: null },
    { id: 3, name: "Amit Patel", roll: "CSE-2023-03", username: "student_amit", deviceId: null },
    { id: 4, name: "Neha Sharma", roll: "CSE-2023-04", username: "student_neha", deviceId: null },
    { id: 5, name: "Rahul Verma", roll: "CSE-2023-05", username: "student_rahul", deviceId: null }
  ],
  subjects: [
    { id: 1, code: "CS301", name: "Operating System", teacherId: 1 },
    { id: 2, code: "CS302", name: "Database Management Systems", teacherId: 2 },
    { id: 3, code: "CS303", name: "Computer Networks", teacherId: 3 }
  ],
  activeSession: null,
  history: []
};

// State Manager
const Store = {
  get: function() {
    const data = localStorage.getItem('attendance_sys_data');
    if (!data) {
      localStorage.setItem('attendance_sys_data', JSON.stringify(defaultData));
      return defaultData;
    }
    const parsed = JSON.parse(data);
    // Ensure exclusive single class teacher email is set
    if (parsed.teachers) {
      const ct = parsed.teachers.find(t => t.role === 'class_teacher');
      if (ct) {
        ct.email = "prasadmhankraj21@gmail.com";
        ct.name = "Prof. Prasad (Class Teacher)";
      }
    }
    // Ensure subjects are always populated and never empty
    if (!parsed.subjects || parsed.subjects.length === 0) {
      parsed.subjects = [
        { id: 1, code: "CS301", name: "Operating System", teacherId: 1 },
        { id: 2, code: "CS302", name: "Database Management Systems", teacherId: 2 },
        { id: 3, code: "CS303", name: "Computer Networks", teacherId: 3 }
      ];
      localStorage.setItem('attendance_sys_data', JSON.stringify(parsed));
    }
    return parsed;
  },
  save: function(data) {
    localStorage.setItem('attendance_sys_data', JSON.stringify(data));
  }
};



let currentUser = null;
let currentRole = 'student';
let qrInterval = null;
let countdownInterval = null;
let sessionSecondsRemaining = 60;
let qrcodeInstance = null;
let html5Scanner = null;

// Notification Alert
function showAlert(msg, type = 'info') {
  const container = document.getElementById('alert-container');
  const alertEl = document.createElement('div');
  const bg = type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' :
             type === 'danger' ? 'bg-rose-50 border-rose-200 text-rose-800' :
             type === 'warning' ? 'bg-amber-50 border-amber-200 text-amber-800' :
             'bg-indigo-50 border-indigo-200 text-indigo-800';
  alertEl.className = `p-4 mb-3 rounded-2xl border flex items-center justify-between shadow-sm animate-fade-in ${bg}`;
  alertEl.innerHTML = `
    <div class="flex items-center space-x-3 text-sm font-medium">
      <span>${msg}</span>
    </div>
    <button onclick="this.parentElement.remove()" class="text-slate-400 hover:text-slate-600">✕</button>
  `;
  container.appendChild(alertEl);
  setTimeout(() => alertEl.remove(), 4500);
}

// Navigation between views
function navigateTo(screenId) {
  document.querySelectorAll('.screen-view').forEach(s => s.classList.add('hidden'));
  const target = document.getElementById(`screen-${screenId}`);
  if (target) target.classList.remove('hidden');

  if (screenId === 'teacher') {
    renderTeacherView();
  } else if (screenId === 'class-teacher') {
    renderClassTeacherView();
  } else if (screenId === 'student') {
    renderStudentView();
  }

  updateNavbar();
  lucide.createIcons();
}


function updateNavbar() {
  const navActions = document.getElementById('nav-actions');
  const userInfo = document.getElementById('nav-user-info');
  const userName = document.getElementById('nav-user-name');
  const userRole = document.getElementById('nav-user-role');

  const store = Store.get();
  const isSessionActive = !!store.activeSession;

  if (currentUser) {
    userInfo.classList.remove('hidden');
    userName.innerText = currentUser.name;
    userRole.innerText = currentUser.role.toUpperCase();

    let navHtml = '';
    if (currentUser.role === 'class_teacher') {
      navHtml += `<button onclick="navigateTo('class-teacher')" class="text-xs bg-indigo-800 hover:bg-indigo-700 text-indigo-100 px-3 py-1.5 rounded-md font-medium">Admin</button>`;
      navHtml += `<button onclick="navigateTo('teacher')" class="text-xs bg-indigo-700 hover:bg-indigo-600 text-white px-3 py-1.5 rounded-md font-medium">Attendance</button>`;
    } else if (currentUser.role === 'teacher') {
      navHtml += `<button onclick="navigateTo('teacher')" class="text-xs bg-indigo-700 hover:bg-indigo-600 text-white px-3 py-1.5 rounded-md font-medium">Sessions</button>`;
    } else if (currentUser.role === 'student') {
      navHtml += `<button onclick="navigateTo('student')" class="text-xs bg-indigo-700 hover:bg-indigo-600 text-white px-3 py-1.5 rounded-md font-medium">Dashboard</button>`;
    }

    // Logout Button with Security Lock Check
    if (currentUser.role === 'student' && isSessionActive) {
      navHtml += `
        <button onclick="alert('SECURITY LOCK ACTIVE: Logout is disabled on your device while QR attendance session is active!')" 
                class="text-xs bg-slate-400 text-white px-3 py-1.5 rounded-md font-semibold cursor-not-allowed opacity-60 flex items-center space-x-1" title="Locked during active session">
          <span>🔒 Logout Locked</span>
        </button>
      `;
    } else {
      navHtml += `
        <button onclick="logout()" class="text-xs bg-rose-600 hover:bg-rose-700 text-white px-3 py-1.5 rounded-md font-semibold flex items-center space-x-1">
          <span>Logout</span>
        </button>
      `;
    }

    navActions.innerHTML = navHtml;
  } else {
    userInfo.classList.add('hidden');
    navActions.innerHTML = `<button onclick="navigateTo('login')" class="text-xs bg-white text-indigo-900 font-bold px-4 py-2 rounded-lg shadow-sm">Sign In</button>`;
  }
}

// Auth Mode Switcher (Login vs Register)
function switchStandaloneAuthMode(mode) {
  const loginBox = document.getElementById('sa-login-container');
  const registerBox = document.getElementById('sa-register-container');
  const btnLogin = document.getElementById('btn-sa-login');
  const btnReg = document.getElementById('btn-sa-register');

  if (mode === 'register') {
    loginBox.classList.add('hidden');
    registerBox.classList.remove('hidden');
    btnReg.className = "flex-1 py-2 text-xs font-bold rounded-lg bg-white text-indigo-700 shadow-sm transition";
    btnLogin.className = "flex-1 py-2 text-xs font-bold rounded-lg text-slate-600 hover:text-indigo-600 transition";
  } else {
    registerBox.classList.add('hidden');
    loginBox.classList.remove('hidden');
    btnLogin.className = "flex-1 py-2 text-xs font-bold rounded-lg bg-white text-indigo-700 shadow-sm transition";
    btnReg.className = "flex-1 py-2 text-xs font-bold rounded-lg text-slate-600 hover:text-indigo-600 transition";
  }
  lucide.createIcons();
}

function toggleSaRegRole(role) {
  const rollBox = document.getElementById('sa-reg-roll-box');
  const rollInput = document.getElementById('sa-reg-roll');
  if (role === 'teacher') {
    rollBox.classList.add('hidden');
    rollInput.required = false;
  } else {
    rollBox.classList.remove('hidden');
    rollInput.required = true;
  }
}

function handleStandaloneRegister(event) {
  event.preventDefault();
  const store = Store.get();
  const devId = DeviceBinding.getDeviceId();

  const role = document.querySelector('input[name="sa_reg_role"]:checked').value;
  const name = document.getElementById('sa-reg-name').value.trim();
  const username = document.getElementById('sa-reg-username').value.trim();
  const password = document.getElementById('sa-reg-password').value.trim();

  if (role === 'student') {
    const roll = document.getElementById('sa-reg-roll').value.trim();

    // Check duplicate username or roll
    if (store.students.some(s => s.username === username || s.roll.toLowerCase() === roll.toLowerCase())) {
      showAlert("Username or Roll Number already registered! Please use another.", "danger");
      return;
    }

    // Check duplicate device
    const existingDev = store.students.find(s => s.deviceId === devId);
    if (existingDev) {
      showAlert(`SECURITY ALERT: This physical device is already bound to student '${existingDev.name}'. One device cannot be shared by multiple students.`, "danger");
      return;
    }

    const newStudent = {
      id: Date.now(),
      name,
      roll,
      username,
      deviceId: devId
    };
    store.students.push(newStudent);
    Store.save(store);

    showAlert(`Student account created for ${name} (${roll})! Device bound. Welcome!`, "success");
    currentUser = { ...newStudent, role: 'student' };
    renderStudentView();
    navigateTo('student');

  } else {
    if (store.teachers.some(t => t.username === username)) {
      showAlert("Username already taken by another teacher.", "danger");
      return;
    }

    const newTeacher = {
      id: Date.now(),
      name,
      username,
      role: 'teacher'
    };
    store.teachers.push(newTeacher);
    Store.save(store);

    showAlert(`Faculty account created for ${name}! Welcome!`, "success");
    currentUser = newTeacher;
    renderTeacherView();
    navigateTo('teacher');
  }
}

// -------------------------------------------------------------------
// LOGIN LOGIC & DEVICE BINDING
// -------------------------------------------------------------------
function setLoginRole(role) {
  currentRole = role;
  ['class_teacher', 'teacher', 'student'].forEach(r => {
    const tab = document.getElementById(`tab-login-${r}`);
    if (r === role) {
      tab.className = "flex-1 py-2 text-xs font-bold rounded-lg bg-white text-indigo-700 shadow-sm transition";
    } else {
      tab.className = "flex-1 py-2 text-xs font-bold rounded-lg text-slate-600 hover:text-indigo-600 transition";
    }
  });

  const label = document.getElementById('login-username-label');
  const btn = document.getElementById('login-btn-text');
  const input = document.getElementById('login-username');

  if (role === 'class_teacher') {
    label.innerText = 'Authorized Class Teacher Email (Single Master Account)';
    input.placeholder = 'prasadmhankraj21@gmail.com';
    btn.innerText = 'Sign In as Class Teacher';
  } else if (role === 'teacher') {
    label.innerText = 'Faculty Username';
    input.placeholder = 'prof_verma';
    btn.innerText = 'Sign In as Faculty';
  } else {
    label.innerText = 'Student Username / Roll No';
    input.placeholder = 'student_rohit';
    btn.innerText = 'Sign In as Student';
  }
}

function autoLogin(username, role) {
  setLoginRole(role);
  document.getElementById('login-username').value = username;
  document.getElementById('login-password').value = 'password123';
  executeLogin(username, role);
}

function handleLoginSubmit(event) {
  event.preventDefault();
  const username = document.getElementById('login-username').value.trim();
  executeLogin(username, currentRole);
}

function executeLogin(username, role) {
  const store = Store.get();
  const devId = DeviceBinding.getDeviceId();

  if (role === 'student') {
    const student = store.students.find(s => s.username === username || s.roll.toLowerCase() === username.toLowerCase());
    if (!student) {
      showAlert("Student record not found. Try 'student_rohit'.", "danger");
      return;
    }

    // 1. Check if device is bound to another student
    const otherStudent = store.students.find(s => s.deviceId === devId && s.id !== student.id);
    if (otherStudent) {
      showAlert(`SECURITY VIOLATION: This device is already bound to '${otherStudent.name}'. Multiple student accounts on 1 device are prohibited.`, "danger");
      return;
    }

    // 2. Check if student is bound to a different device
    if (student.deviceId && student.deviceId !== devId) {
      showAlert(`ACCESS DENIED: Account bound to another device (${student.deviceId}). Contact Class Teacher to reset device binding.`, "danger");
      return;
    }

    // 3. Bind device if first time
    if (!student.deviceId) {
      student.deviceId = devId;
      Store.save(store);
      showAlert("Device successfully bound to your student account!", "success");
    }

    currentUser = { ...student, role: 'student' };
    renderStudentView();
    navigateTo('student');

  } else if (role === 'class_teacher') {
    const validEmails = ["prasadmhankraj21@gmail.com", "classteacher@college.edu", "classteacher"];
    if (!validEmails.includes(username.toLowerCase())) {
      showAlert("ACCESS DENIED: Class Teacher login is strictly restricted to single authorized email (prasadmhankraj21@gmail.com).", "danger");
      return;
    }
    const ct = store.teachers.find(t => t.role === 'class_teacher');
    if (!ct) {
      showAlert("Class Teacher master account not found.", "danger");
      return;
    }
    currentUser = ct;
    renderClassTeacherView();
    navigateTo('class-teacher');

  } else {

    const teacher = store.teachers.find(t => t.username === username);
    if (!teacher) {
      showAlert("Faculty user not found. Try 'prof_verma'.", "danger");
      return;
    }
    currentUser = teacher;
    renderTeacherView();
    navigateTo('teacher');
  }

  showAlert(`Welcome, ${currentUser.name}!`, "success");
}

function logout() {
  const store = Store.get();
  if (currentUser && currentUser.role === 'student' && store.activeSession) {
    showAlert("SECURITY RESTRICTION: You cannot log out while QR attendance is in progress!", "warning");
    return;
  }
  currentUser = null;
  navigateTo('login');
  showAlert("Signed out successfully.", "info");
}

// -------------------------------------------------------------------
// CLASS TEACHER VIEW & ACTIONS
// -------------------------------------------------------------------
function renderClassTeacherView() {
  const store = Store.get();

  document.getElementById('ct-full-name').innerText = currentUser.name;
  document.getElementById('ct-stat-students').innerText = store.students.length;
  document.getElementById('ct-stat-teachers').innerText = store.teachers.length;
  document.getElementById('ct-stat-subjects').innerText = store.subjects.length;
  document.getElementById('ct-stat-bound').innerText = store.students.filter(s => s.deviceId).length;

  // Render Teachers Table
  const tTbody = document.getElementById('ct-teachers-table-body');
  tTbody.innerHTML = store.teachers.map(t => `
    <tr class="hover:bg-slate-50 transition">
      <td class="p-3 font-semibold text-slate-900">${t.name}</td>
      <td class="p-3 font-mono text-xs">${t.username}</td>
      <td class="p-3">
        <span class="${t.role === 'class_teacher' ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-700'} text-xs px-2.5 py-0.5 rounded-full font-bold">
          ${t.role === 'class_teacher' ? 'Class Teacher' : 'Faculty'}
        </span>
      </td>
      <td class="p-3 text-right">
        ${t.role !== 'class_teacher' 
          ? `<button onclick="removeTeacher(${t.id})" class="text-rose-600 hover:text-rose-800 text-xs font-bold px-2 py-1 rounded hover:bg-rose-50">Remove</button>` 
          : `<span class="text-xs text-slate-400 italic">Protected</span>`
        }
      </td>
    </tr>
  `).join('');

  // Render Students Table
  const sTbody = document.getElementById('ct-students-table-body');
  sTbody.innerHTML = store.students.map(s => `
    <tr class="hover:bg-slate-50 transition">
      <td class="p-3 font-mono font-bold text-xs text-slate-900">${s.roll}</td>
      <td class="p-3 font-semibold text-slate-900">${s.name}</td>
      <td class="p-3 font-mono text-xs">${s.username}</td>
      <td class="p-3">
        ${s.deviceId 
          ? `<span class="font-mono text-xs text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded">${s.deviceId}</span>`
          : `<span class="text-xs text-slate-400 italic">Pending First Login</span>`
        }
      </td>
      <td class="p-3 text-right space-x-2">
        ${s.deviceId ? `<button onclick="resetStudentDevice(${s.id})" class="text-amber-700 hover:text-amber-900 text-xs font-bold px-2 py-1 rounded bg-amber-50">Reset Device</button>` : ''}
        <button onclick="removeStudent(${s.id})" class="text-rose-600 hover:text-rose-800 text-xs font-bold px-2 py-1 rounded hover:bg-rose-50">Remove</button>
      </td>
    </tr>
  `).join('');

  // Render Subjects Table & Teacher Select dropdown
  const subSelect = document.getElementById('add-sub-teacher');
  subSelect.innerHTML = store.teachers.map(t => `<option value="${t.id}">${t.name}</option>`).join('');

  const subTbody = document.getElementById('ct-subjects-table-body');
  subTbody.innerHTML = store.subjects.map(sub => {
    const t = store.teachers.find(tch => tch.id === sub.teacherId);
    return `
      <tr class="hover:bg-slate-50 transition">
        <td class="p-3 font-mono font-bold text-indigo-700 text-xs">${sub.code}</td>
        <td class="p-3 font-semibold text-slate-900">${sub.name}</td>
        <td class="p-3 text-xs font-medium">${t ? t.name : 'Unassigned'}</td>
        <td class="p-3 text-right">
          <button onclick="removeSubject(${sub.id})" class="text-rose-600 hover:text-rose-800 text-xs font-bold px-2 py-1 rounded hover:bg-rose-50">Delete</button>
        </td>
      </tr>
    `;
  }).join('');
}

function switchAdminTab(tabId) {
  document.querySelectorAll('.admin-tab-pane').forEach(el => el.classList.add('hidden'));
  document.getElementById(tabId).classList.remove('hidden');

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.className = "tab-btn pb-4 font-bold text-sm border-b-2 border-transparent text-slate-500 hover:text-slate-800 flex items-center space-x-2";
  });
  const activeBtnId = tabId.replace('tab-admin-', 'btn-admin-');
  document.getElementById(activeBtnId).className = "tab-btn pb-4 font-bold text-sm border-b-2 border-indigo-600 text-indigo-600 flex items-center space-x-2";
}

function handleAddTeacher(event) {
  event.preventDefault();
  const store = Store.get();
  const name = document.getElementById('add-teacher-name').value.trim();
  const username = document.getElementById('add-teacher-user').value.trim();

  store.teachers.push({ id: Date.now(), name, username, role: 'teacher' });
  Store.save(store);
  showAlert(`Teacher '${name}' added!`, "success");
  event.target.reset();
  renderClassTeacherView();
}

function removeTeacher(id) {
  if (!confirm("Remove this teacher?")) return;
  const store = Store.get();
  store.teachers = store.teachers.filter(t => t.id !== id);
  Store.save(store);
  renderClassTeacherView();
}

function handleAddStudent(event) {
  event.preventDefault();
  const store = Store.get();
  const name = document.getElementById('add-student-name').value.trim();
  const roll = document.getElementById('add-student-roll').value.trim();
  const username = document.getElementById('add-student-user').value.trim();

  store.students.push({ id: Date.now(), name, roll, username, deviceId: null });
  Store.save(store);
  showAlert(`Student '${name}' (${roll}) enrolled!`, "success");
  event.target.reset();
  renderClassTeacherView();
}

function removeStudent(id) {
  if (!confirm("Remove this student?")) return;
  const store = Store.get();
  store.students = store.students.filter(s => s.id !== id);
  Store.save(store);
  renderClassTeacherView();
}

function resetStudentDevice(id) {
  const store = Store.get();
  const student = store.students.find(s => s.id === id);
  if (student) {
    student.deviceId = null;
    Store.save(store);
    showAlert(`Device reset for ${student.name}. They can bind a new phone on next login.`, "success");
    renderClassTeacherView();
  }
}

function handleAddSubject(event) {
  event.preventDefault();
  const store = Store.get();
  const code = document.getElementById('add-sub-code').value.trim();
  const name = document.getElementById('add-sub-name').value.trim();
  const teacherId = parseInt(document.getElementById('add-sub-teacher').value, 10);

  store.subjects.push({ id: Date.now(), code, name, teacherId });
  Store.save(store);
  showAlert(`Subject '${name}' added!`, "success");
  event.target.reset();
  renderClassTeacherView();
}

function removeSubject(id) {
  const store = Store.get();
  store.subjects = store.subjects.filter(s => s.id !== id);
  Store.save(store);
  renderClassTeacherView();
}

// -------------------------------------------------------------------
// TEACHER VIEW & DYNAMIC QR SESSION
// -------------------------------------------------------------------
function renderTeacherView() {
  const store = Store.get();
  if (currentUser) {
    const nameEl = document.getElementById('teacher-full-name');
    if (nameEl) nameEl.innerText = currentUser.name;
  }

  const select = document.getElementById('session-subject-select');
  if (select) {
    const subjects = (store.subjects && store.subjects.length > 0) ? store.subjects : [
      { id: 1, code: "CS301", name: "Operating System", teacherId: 1 },
      { id: 2, code: "CS302", name: "Database Management Systems", teacherId: 2 },
      { id: 3, code: "CS303", name: "Computer Networks", teacherId: 3 }
    ];
    select.innerHTML = subjects.map(s => `
      <option value="${s.id}">${s.code} - ${s.name} (Third Year CSE)</option>
    `).join('');
  }

  if (store.activeSession) {
    showActiveQrStage();
  } else {
    document.getElementById('teacher-start-box').classList.remove('hidden');
    document.getElementById('teacher-active-stage').classList.add('hidden');
    document.getElementById('teacher-report-box').classList.add('hidden');
  }
}


function setTimerSecs(secs) {
  document.getElementById('custom-session-secs').value = secs;
  document.querySelectorAll('.dur-btn').forEach(btn => {
    btn.className = "dur-btn py-2 px-3 text-xs font-bold border border-slate-200 rounded-xl hover:border-indigo-500 hover:text-indigo-600 transition";
  });
  event.target.className = "dur-btn py-2 px-3 text-xs font-bold border border-indigo-600 bg-indigo-50 text-indigo-700 rounded-xl transition";
}

function handleStartSessionSubmit(event) {
  event.preventDefault();
  const store = Store.get();
  const selectEl = document.getElementById('session-subject-select');
  const subjectId = selectEl ? parseInt(selectEl.value, 10) : 1;
  const duration = parseInt(document.getElementById('custom-session-secs').value, 10) || 60;
  
  const subject = (store.subjects && store.subjects.find(s => s.id === subjectId)) 
               || (store.subjects && store.subjects[0]) 
               || { id: 1, name: "Operating System", code: "CS301" };

  const sessionId = Date.now();
  sessionSecondsRemaining = duration;

  store.activeSession = {
    id: sessionId,
    subjectId: subject.id,
    subjectName: subject.name,
    subjectCode: subject.code,
    teacherName: currentUser ? currentUser.name : "Faculty Member",
    duration: duration,
    startedAt: new Date().toLocaleTimeString(),
    salt: Math.random().toString(36).substring(2, 8).toUpperCase(),
    records: []
  };
  Store.save(store);

  showActiveQrStage();
  showAlert("Dynamic QR Attendance Session Started!", "success");
}


function showActiveQrStage() {
  const store = Store.get();
  const sess = store.activeSession;
  if (!sess) return;

  document.getElementById('teacher-start-box').classList.add('hidden');
  document.getElementById('teacher-report-box').classList.add('hidden');
  document.getElementById('teacher-active-stage').classList.remove('hidden');

  document.getElementById('live-subject-heading').innerText = `${sess.subjectCode} - ${sess.subjectName}`;
  document.getElementById('live-total-enrolled').innerText = store.students.length;

  document.getElementById('teacher-status-dot').className = "w-3 h-3 bg-emerald-500 rounded-full animate-ping";
  document.getElementById('teacher-status-text').innerText = "Session Active";
  document.getElementById('teacher-status-text').className = "text-xs font-bold uppercase tracking-wider text-emerald-400";

  updateDynamicQr();
  clearInterval(qrInterval);
  qrInterval = setInterval(updateDynamicQr, 15000); // Rotate QR token every 15s

  startTimer();
  updateLiveFeed();
}

function updateDynamicQr() {
  const store = Store.get();
  if (!store.activeSession) return;

  const timeWindow = Math.floor(Date.now() / 15000);
  const token = `QR-${store.activeSession.id}-${timeWindow}-${store.activeSession.salt}`;
  store.activeSession.currentToken = token;
  Store.save(store);

  // Render in-browser QR
  const qrContainer = document.getElementById('qrcode-canvas-wrapper');
  qrContainer.innerHTML = '';
  new QRCode(qrContainer, {
    text: token,
    width: 256,
    height: 256,
    colorDark: "#1e1b4b",
    colorLight: "#ffffff",
    correctLevel: QRCode.CorrectLevel.M
  });

  document.getElementById('backup-code-display').innerText = token.slice(-6);
}

function startTimer() {
  clearInterval(countdownInterval);
  updateTimerDisplay();

  countdownInterval = setInterval(() => {
    sessionSecondsRemaining--;
    updateTimerDisplay();
    updateLiveFeed();

    if (sessionSecondsRemaining <= 0) {
      clearInterval(countdownInterval);
      concludeSession();
    }
  }, 1000);
}

function updateTimerDisplay() {
  const mins = Math.floor(sessionSecondsRemaining / 60).toString().padStart(2, '0');
  const secs = (sessionSecondsRemaining % 60).toString().padStart(2, '0');
  const box = document.getElementById('timer-box');
  const text = document.getElementById('timer-text');
  text.innerText = `${mins}:${secs}`;

  if (sessionSecondsRemaining <= 10) {
    box.className = "timer-badge danger";
  } else if (sessionSecondsRemaining <= 30) {
    box.className = "timer-badge warning";
  } else {
    box.className = "timer-badge";
  }
}

function updateLiveFeed() {
  const store = Store.get();
  if (!store.activeSession) return;

  const records = store.activeSession.records || [];
  document.getElementById('live-scan-count').innerText = records.length;

  const list = document.getElementById('live-scan-list');
  if (records.length > 0) {
    list.innerHTML = records.map(r => `
      <div class="p-3 bg-emerald-50/70 border border-emerald-200 rounded-xl flex items-center justify-between text-xs animate-fade-in">
        <div class="flex items-center space-x-2.5">
          <span class="w-2 h-2 bg-emerald-500 rounded-full"></span>
          <div>
            <p class="font-bold text-slate-900">${r.name}</p>
            <p class="text-[10px] text-slate-500 font-mono">${r.roll}</p>
          </div>
        </div>
        <div class="text-right">
          <span class="font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded text-[10px]">PRESENT</span>
          <p class="text-[10px] text-slate-400 mt-0.5">${r.time}</p>
        </div>
      </div>
    `).join('');
  } else {
    list.innerHTML = `<div class="text-center py-12 text-slate-400 text-xs italic">Waiting for students to scan QR code...</div>`;
  }
}

function endSessionEarly() {
  if (confirm("End attendance session now?")) {
    concludeSession();
  }
}

function concludeSession() {
  clearInterval(countdownInterval);
  clearInterval(qrInterval);

  const store = Store.get();
  const sess = store.activeSession;
  if (!sess) return;

  const total = store.students.length;
  const presentRecords = sess.records || [];
  const presentStudentIds = presentRecords.map(r => r.studentId);

  const reportStudents = store.students.map(s => {
    const isPresent = presentStudentIds.includes(s.id);
    const rec = presentRecords.find(r => r.studentId === s.id);
    return {
      roll: s.roll,
      name: s.name,
      status: isPresent ? 'PRESENT' : 'ABSENT',
      scannedAt: isPresent ? rec.time : '—',
      deviceId: isPresent ? rec.deviceId : '—'
    };
  });

  const presentCount = presentRecords.length;
  const absentCount = total - presentCount;
  const pct = total > 0 ? Math.round((presentCount / total) * 100) : 0;

  // Save to history
  store.history.push({
    session: sess,
    total,
    presentCount,
    absentCount,
    pct,
    students: reportStudents
  });
  store.activeSession = null;
  Store.save(store);

  // Render Report
  document.getElementById('teacher-active-stage').classList.add('hidden');
  document.getElementById('teacher-report-box').classList.remove('hidden');

  document.getElementById('teacher-status-dot').className = "w-3 h-3 bg-slate-400 rounded-full";
  document.getElementById('teacher-status-text').innerText = "Session Ended";
  document.getElementById('teacher-status-text').className = "text-xs font-bold uppercase tracking-wider text-slate-400";

  document.getElementById('report-title').innerText = `${sess.subjectName} • Attendance Report`;
  document.getElementById('report-meta').innerText = `Conducted on ${new Date().toLocaleDateString()} by ${sess.teacherName}`;
  document.getElementById('rep-total').innerText = total;
  document.getElementById('rep-present').innerText = presentCount;
  document.getElementById('rep-absent').innerText = absentCount;
  document.getElementById('rep-pct').innerText = `${pct}%`;

  const tbody = document.getElementById('report-table-body');
  tbody.innerHTML = reportStudents.map(s => `
    <tr class="hover:bg-slate-50 transition">
      <td class="p-3 font-mono font-bold text-xs text-slate-900">${s.roll}</td>
      <td class="p-3 font-semibold text-slate-900">${s.name}</td>
      <td class="p-3">
        <span class="${s.status === 'PRESENT' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'} text-xs px-2.5 py-0.5 rounded-full font-bold">
          ${s.status}
        </span>
      </td>
      <td class="p-3 text-xs font-mono text-slate-500">${s.scannedAt}</td>
      <td class="p-3 text-xs font-mono text-indigo-700">${s.deviceId}</td>
    </tr>
  `).join('');

  updateNavbar();
  showAlert("Attendance session concluded! Full report generated.", "success");
}

function resetTeacherSession() {
  document.getElementById('teacher-report-box').classList.add('hidden');
  document.getElementById('teacher-start-box').classList.remove('hidden');
}

function downloadCSVReport() {
  const store = Store.get();
  const lastReport = store.history[store.history.length - 1];
  if (!lastReport) return;

  let csvContent = "data:text/csv;charset=utf-8,";
  csvContent += "Dynamic QR Attendance Report\n";
  csvContent += `Subject,${lastReport.session.subjectName},Class,Third Year CSE\n`;
  csvContent += `Total Enrolled,${lastReport.total},Present,${lastReport.presentCount},Absent,${lastReport.absentCount},Rate,${lastReport.pct}%\n\n`;
  csvContent += "Roll Number,Student Name,Status,Scan Timestamp,Verified Device ID\n";

  lastReport.students.forEach(s => {
    csvContent += `${s.roll},${s.name},${s.status},${s.scannedAt},${s.deviceId}\n`;
  });

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `attendance_report_${Date.now()}.csv`);
  document.body.appendChild(link);
  link.click();
  link.remove();
}

// -------------------------------------------------------------------
// STUDENT VIEW & QR SCANNER
// -------------------------------------------------------------------
function renderStudentView() {
  const store = Store.get();
  document.getElementById('student-full-name').innerText = currentUser.name;
  document.getElementById('student-roll-no').innerText = currentUser.roll;
  document.getElementById('student-bound-dev').innerText = currentUser.deviceId || 'DEV-BINDING...';

  // Render enrolled subjects (Third Year CSE)
  const subContainer = document.getElementById('student-subjects-list');
  subContainer.innerHTML = store.subjects.map(s => {
    const t = store.teachers.find(tch => tch.id === s.teacherId);
    return `
      <div class="p-4 rounded-2xl border border-slate-200 hover:border-indigo-300 transition bg-slate-50/50 flex items-center justify-between">
        <div class="flex items-center space-x-3.5">
          <div class="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold font-mono text-xs">
            ${s.code}
          </div>
          <div>
            <h4 class="font-bold text-slate-900 text-sm">${s.name}</h4>
            <p class="text-xs text-slate-500 mt-0.5">Faculty: <strong>${t ? t.name : 'Faculty Assigned'}</strong></p>
          </div>
        </div>
        <span class="text-[11px] bg-slate-200 text-slate-700 font-semibold px-2.5 py-1 rounded-lg">Regular Course</span>
      </div>
    `;
  }).join('');

  // Check Active Attendance
  const banner = document.getElementById('student-active-banner');
  if (store.activeSession) {
    banner.classList.remove('hidden');
    document.getElementById('student-active-sub').innerText = `${store.activeSession.subjectCode} - ${store.activeSession.subjectName}`;
  } else {
    banner.classList.add('hidden');
  }

  // Summary stats
  const scansContainer = document.getElementById('student-recent-scans');
  const myScans = [];
  store.history.forEach(h => {
    const found = h.students.find(st => st.roll === currentUser.roll && st.status === 'PRESENT');
    if (found) myScans.push({ subject: h.session.subjectName, time: found.scannedAt });
  });

  if (myScans.length > 0) {
    scansContainer.innerHTML = myScans.map(s => `
      <div class="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-center justify-between text-xs">
        <div>
          <p class="font-bold text-slate-800">${s.subject}</p>
          <p class="text-[10px] text-slate-400 font-mono">${s.time}</p>
        </div>
        <span class="bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded text-[10px]">PRESENT</span>
      </div>
    `).join('');
  } else {
    scansContainer.innerHTML = `<p class="text-xs text-slate-400 italic text-center py-4">No attendance scans recorded yet.</p>`;
  }

  updateNavbar();
}

// Student Scanner
function openStudentScanner() {
  document.getElementById('scanner-modal').classList.remove('hidden');
  document.getElementById('modal-device-id').innerText = DeviceBinding.getDeviceId();
  document.getElementById('student-scan-feedback').innerHTML = '';

  try {
    html5Scanner = new Html5Qrcode("html5-qr-reader");
    html5Scanner.start(
      { facingMode: "environment" },
      { fps: 15, qrbox: { width: 220, height: 220 } },
      (decodedText) => {
        playBeep();
        closeStudentScanner();
        verifyAndRecordAttendance(decodedText);
      },
      () => {}
    ).then(() => {
      document.getElementById('scanner-status-msg').classList.add('hidden');
    }).catch(err => {
      console.log("Camera access error:", err);
      document.getElementById('scanner-status-msg').innerHTML = `
        <p class="text-amber-300">Camera permission denied or camera not found.</p>
        <p class="text-[10px] mt-1 text-slate-300">Please enter the 6-digit backup code below.</p>
      `;
    });
  } catch (e) {
    console.log("Scanner exception:", e);
  }
}

function closeStudentScanner() {
  if (html5Scanner) {
    html5Scanner.stop().then(() => {
      document.getElementById('html5-qr-reader').innerHTML = '';
      html5Scanner = null;
    }).catch(() => {});
  }
  document.getElementById('scanner-modal').classList.add('hidden');
}

function submitManualCode() {
  const code = document.getElementById('manual-code-val').value.trim();
  if (!code) {
    alert("Please enter backup code.");
    return;
  }
  closeStudentScanner();
  verifyAndRecordAttendance(code);
}

function verifyAndRecordAttendance(scannedToken) {
  const store = Store.get();
  const sess = store.activeSession;
  const devId = DeviceBinding.getDeviceId();

  if (!sess) {
    showAlert("No active attendance session currently in progress.", "danger");
    return;
  }

  // Check device match
  if (currentUser.deviceId !== devId) {
    showAlert(`DEVICE MISMATCH: Attendance must be scanned on your bound device!`, "danger");
    return;
  }

  // Check token match
  const timeWindow = Math.floor(Date.now() / 15000);
  const validTokens = [
    sess.currentToken,
    `QR-${sess.id}-${timeWindow}-${sess.salt}`,
    `QR-${sess.id}-${timeWindow - 1}-${sess.salt}`,
    sess.salt,
    sess.salt.slice(-6)
  ];

  const isValid = validTokens.includes(scannedToken) || scannedToken.endsWith(sess.salt.slice(-6));
  if (!isValid) {
    showAlert("QR Code expired or invalid! Dynamic QR code updates every 15 seconds. Please scan current QR on screen.", "danger");
    return;
  }

  // Check if already scanned
  const already = sess.records.find(r => r.studentId === currentUser.id);
  if (already) {
    showAlert("You have already recorded attendance for this session!", "warning");
    return;
  }

  // Record attendance
  sess.records.push({
    studentId: currentUser.id,
    name: currentUser.name,
    roll: currentUser.roll,
    deviceId: devId,
    time: new Date().toLocaleTimeString()
  });
  Store.save(store);

  showAlert(`SUCCESS! Attendance recorded: PRESENT for ${sess.subjectName}!`, "success");
  renderStudentView();
}

function playBeep() {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.frequency.setValueAtTime(880, audioCtx.currentTime);
    gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.15);
  } catch (e) {}
}

// Global Poll for Active Attendance
setInterval(() => {
  const store = Store.get();
  if (currentUser && currentUser.role === 'student') {
    const banner = document.getElementById('student-active-banner');
    if (store.activeSession) {
      banner.classList.remove('hidden');
      document.getElementById('student-active-sub').innerText = `${store.activeSession.subjectCode} - ${store.activeSession.subjectName}`;
    } else {
      banner.classList.add('hidden');
    }
    updateNavbar();
  }
}, 3000);

// Init on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  const devId = DeviceBinding.getDeviceId();
  const disp = document.getElementById('display-dev-id');
  if (disp) disp.innerText = devId;

  // Initialize Store if needed
  Store.get();
  renderTeacherView();
  navigateTo('login');

});
