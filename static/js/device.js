/**
 * Device Binding & Fingerprinting System
 * Ensures 1 Student Account = 1 Single Device Binding
 */

const DeviceBinding = {
  getDeviceId: function() {
    let devId = localStorage.getItem('college_device_id');
    if (!devId) {
      // Generate a persistent, pseudo-unique hardware fingerprint
      const screenInfo = `${window.screen.width}x${window.screen.height}x${window.screen.colorDepth}`;
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
      const navInfo = `${navigator.hardwareConcurrency || 2}-${navigator.platform || 'web'}`;
      
      // Random entropy
      const randomPart = Math.random().toString(36).substring(2, 10).toUpperCase();
      const timePart = Date.now().toString(36).toUpperCase();

      // Simple hash
      let rawString = `${screenInfo}|${tz}|${navInfo}`;
      let hash = 0;
      for (let i = 0; i < rawString.length; i++) {
        hash = ((hash << 5) - hash) + rawString.charCodeAt(i);
        hash |= 0;
      }
      const hashStr = Math.abs(hash).toString(16).toUpperCase();

      devId = `DEV-${hashStr.substring(0, 4)}-${randomPart}-${timePart}`;
      localStorage.setItem('college_device_id', devId);
    }
    return devId;
  },

  getDeviceInfo: function() {
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    return {
      deviceId: this.getDeviceId(),
      platform: isMobile ? 'Mobile Phone' : 'Desktop/Laptop',
      browser: navigator.userAgent.split(' ')[0]
    };
  },

  attachToForms: function() {
    const devId = this.getDeviceId();
    const hiddenInputs = document.querySelectorAll('input[name="device_id"]');
    hiddenInputs.forEach(input => {
      input.value = devId;
    });
  }
};

// Auto attach on load
document.addEventListener('DOMContentLoaded', () => {
  DeviceBinding.attachToForms();
});
