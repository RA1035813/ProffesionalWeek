// ============================================================
// Orbit controls (mouse + touch)
// ============================================================
let isDragging = false;
let prevMouse = { x: 0, y: 0 };
let orbitAngle = 0.8;
let orbitPitch = 0.45;
let orbitDist = 22;

container.addEventListener('mousedown', e => {
  if (e.target.closest('#ai-panel') || e.target.closest('#nokia-container')) return;
  isDragging = true; prevMouse = { x: e.clientX, y: e.clientY };
});
container.addEventListener('mousemove', e => {
  if (!isDragging) return;
  orbitAngle -= (e.clientX - prevMouse.x) * 0.005;
  orbitPitch = Math.max(0.1, Math.min(1.2, orbitPitch - (e.clientY - prevMouse.y) * 0.005));
  prevMouse = { x: e.clientX, y: e.clientY };
});
container.addEventListener('mouseup', () => isDragging = false);
container.addEventListener('mouseleave', () => isDragging = false);
container.addEventListener('wheel', e => {
  if (e.target.closest('#ai-panel') || e.target.closest('#nokia-container')) return;
  orbitDist = Math.max(8, Math.min(80, orbitDist + e.deltaY * 0.03));
});

// Touch
container.addEventListener('touchstart', e => {
  if (e.target.closest('#ai-panel') || e.target.closest('#nokia-container')) return;
  isDragging = true;
  prevMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
});
container.addEventListener('touchmove', e => {
  if (!isDragging) return;
  orbitAngle -= (e.touches[0].clientX - prevMouse.x) * 0.005;
  orbitPitch = Math.max(0.1, Math.min(1.2, orbitPitch - (e.touches[0].clientY - prevMouse.y) * 0.005));
  prevMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
});
container.addEventListener('touchend', () => isDragging = false);
