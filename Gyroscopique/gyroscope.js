(() => {
  const photo = document.getElementById('spatial-photo');
  const statusEl = document.getElementById('status');
  const permissionBtn = document.getElementById('permission-button');

  const spatialPhotoSrc =
    new URLSearchParams(window.location.search).get('photo') || './spatial.heic';

  const settings = {
    maxTiltDeg: 10,
    translatePx: 28,
    smoothing: 0.12,
  };

  const target = { x: 0, y: 0 };
  const current = { x: 0, y: 0 };
  let rafId = null;

  photo.src = spatialPhotoSrc;

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function updateStatus(message) {
    statusEl.textContent = message;
  }

  function animationStep() {
    current.x += (target.x - current.x) * settings.smoothing;
    current.y += (target.y - current.y) * settings.smoothing;

    const rotateX = current.y * settings.maxTiltDeg;
    const rotateY = -current.x * settings.maxTiltDeg;
    const translateX = current.x * settings.translatePx;
    const translateY = current.y * settings.translatePx;

    photo.style.transform = `translate3d(${translateX}px, ${translateY}px, 0) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.06)`;

    rafId = requestAnimationFrame(animationStep);
  }

  function ensureAnimation() {
    if (!rafId) {
      rafId = requestAnimationFrame(animationStep);
    }
  }

  function handleOrientation(event) {
    const normalizedX = clamp(event.gamma / 45, -1, 1);
    const normalizedY = clamp(event.beta / 90, -1, 1);

    target.x = normalizedX;
    target.y = normalizedY;
  }

  async function requestAccess() {
    if (!window.DeviceOrientationEvent) {
      updateStatus('Gyroscope not supported in this browser.');
      return;
    }

    if (!window.isSecureContext) {
      updateStatus('Motion permission requires HTTPS or localhost.');
      return;
    }

    try {
      let granted = true;

      if (typeof DeviceOrientationEvent.requestPermission === 'function') {
        const response = await DeviceOrientationEvent.requestPermission();
        granted = response === 'granted';
      }

      // Some iOS versions gate DeviceMotion instead.
      if (!granted && typeof DeviceMotionEvent?.requestPermission === 'function') {
        const response = await DeviceMotionEvent.requestPermission();
        granted = response === 'granted';
      }

      if (!granted) {
        updateStatus('Motion access was denied. Check Safari Settings > Motion & Orientation.');
        return;
      }
    } catch (error) {
      console.error('Motion permission error', error);
      updateStatus('Unable to request motion access. Check Safari Settings.');
      return;
    }

    window.addEventListener('deviceorientation', handleOrientation, true);
    ensureAnimation();
    permissionBtn.disabled = true;
    updateStatus('Tilt and rotate your iPhone to explore the photo.');
  }

  permissionBtn.addEventListener('click', requestAccess);
})();
