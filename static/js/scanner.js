/**
 * Dynamic QR Code Scanner for Students
 * Uses html5-qrcode library + audio feedback
 */

let html5QrCode = null;
let isScanning = false;

// Web Audio API Beep on successful scan
function playBeepSuccess() {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(880, audioCtx.currentTime); // A5 note
    gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.15);
  } catch (e) {
    console.log("Audio not supported or blocked:", e);
  }
}

function startScanner(onSuccessCallback) {
  const qrReaderElement = document.getElementById('qr-reader');
  if (!qrReaderElement) return;

  if (isScanning) return;

  html5QrCode = new Html5Qrcode("qr-reader");
  const config = { 
    fps: 15, 
    qrbox: { width: 250, height: 250 },
    aspectRatio: 1.0
  };

  html5QrCode.start(
    { facingMode: "environment" }, // Prefer back camera on mobile
    config,
    (decodedText, decodedResult) => {
      // Scanned successfully!
      console.log("QR Code Scanned:", decodedText);
      playBeepSuccess();
      stopScanner();
      if (onSuccessCallback) {
        onSuccessCallback(decodedText);
      }
    },
    (errorMessage) => {
      // Parse error, ignore frame
    }
  ).then(() => {
    isScanning = true;
    document.getElementById('scanner-loading')?.classList.add('hidden');
    document.getElementById('scanner-active-msg')?.classList.remove('hidden');
  }).catch((err) => {
    console.error("Failed to start camera:", err);
    alert("Camera permission denied or camera not found. Please allow camera permissions or use manual code entry.");
  });
}

function stopScanner() {
  if (html5QrCode && isScanning) {
    html5QrCode.stop().then(() => {
      isScanning = false;
      document.getElementById('qr-reader').innerHTML = '';
    }).catch(err => console.error("Error stopping scanner:", err));
  }
}

// Mark Attendance API Call
async function submitAttendance(token, subjectId) {
  const deviceId = DeviceBinding.getDeviceId();
  const feedbackEl = document.getElementById('scan-feedback');
  
  if (feedbackEl) {
    feedbackEl.innerHTML = `
      <div class="p-4 bg-indigo-50 border border-indigo-200 text-indigo-700 rounded-lg flex items-center space-x-3">
        <svg class="animate-spin h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
        </svg>
        <span>Verifying QR token and device binding...</span>
      </div>
    `;
  }

  try {
    const res = await fetch('/api/student/mark-attendance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token: token,
        device_id: deviceId,
        subject_id: subjectId
      })
    });

    const data = await res.json();
    if (res.ok && data.success) {
      if (feedbackEl) {
        feedbackEl.innerHTML = `
          <div class="p-4 bg-green-50 border border-green-300 text-green-800 rounded-lg flex items-start space-x-3 animate-bounce">
            <svg class="h-6 w-6 text-green-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            <div>
              <h4 class="font-bold text-lg">Attendance Marked: PRESENT!</h4>
              <p class="text-sm mt-1">${data.message}</p>
              <p class="text-xs text-green-600 mt-1">Timestamp: ${data.timestamp} | Subject: ${data.subject_name}</p>
            </div>
          </div>
        `;
      }
      setTimeout(() => {
        window.location.reload();
      }, 2500);
    } else {
      if (feedbackEl) {
        feedbackEl.innerHTML = `
          <div class="p-4 bg-red-50 border border-red-300 text-red-800 rounded-lg flex items-start space-x-3">
            <svg class="h-6 w-6 text-red-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
            <div>
              <h4 class="font-bold text-lg">Verification Failed</h4>
              <p class="text-sm mt-1">${data.error || "Unable to mark attendance."}</p>
              <button onclick="location.reload()" class="mt-2 text-xs font-semibold text-red-700 underline">Retry</button>
            </div>
          </div>
        `;
      }
    }
  } catch (err) {
    if (feedbackEl) {
      feedbackEl.innerHTML = `
        <div class="p-4 bg-red-50 border border-red-300 text-red-800 rounded-lg">
          <p class="font-bold">Network Connection Error</p>
          <p class="text-sm">${err.message}</p>
        </div>
      `;
    }
  }
}
