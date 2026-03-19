// ============================================================
// Signal rings
// ============================================================
const signalRings = [];
function createSignalRing() {
  const mat = new THREE.MeshBasicMaterial({ color: 0xf1c40f, transparent: true, opacity: 0.8, side: THREE.DoubleSide });
  const ring = new THREE.Mesh(new THREE.RingGeometry(0.2, 0.24, 16), mat);
  ring.position.set(rpiGroup.position.x + 0.15, 2.85, rpiGroup.position.z);
  ring.lookAt(towerGroup.position.x, 15, towerGroup.position.z);
  scene.add(ring);
  signalRings.push({ mesh: ring, scale: 1, opacity: 0.8 });
}

// ============================================================
// Animation
// ============================================================
let time = 0, particleTimer = 0, signalTimer = 0;

function animate() {
  requestAnimationFrame(animate);
  time += 0.016;
  particleTimer += 0.016;
  signalTimer += 0.016;

  if (!isDragging) orbitAngle += 0.0004;

  camera.position.x = Math.sin(orbitAngle) * Math.cos(orbitPitch) * orbitDist;
  camera.position.y = Math.sin(orbitPitch) * orbitDist;
  camera.position.z = Math.cos(orbitAngle) * Math.cos(orbitPitch) * orbitDist;
  camera.lookAt(0, 1.5, 0);

  clouds.forEach((c, i) => {
    c.position.x += 0.008 * (i % 2 === 0 ? 1 : -1);
    if (c.position.x > 60) c.position.x = -60;
    if (c.position.x < -60) c.position.x = 60;
  });

  led.material.emissiveIntensity = Math.sin(time * 4) > 0 ? 1 : 0.1;
  led.material.color.setHex(Math.sin(time * 4) > 0 ? 0x00ff00 : 0x004400);
  towerLight.material.emissiveIntensity = Math.sin(time * 2) > 0 ? 0.8 : 0.1;

  if (signalTimer > 2.0) { signalTimer = 0; createSignalRing(); }
  for (let i = signalRings.length - 1; i >= 0; i--) {
    const r = signalRings[i];
    r.scale += 0.08;
    r.opacity -= 0.008;
    r.mesh.scale.set(r.scale, r.scale, r.scale);
    r.mesh.material.opacity = Math.max(0, r.opacity);
    if (r.opacity <= 0) { scene.remove(r.mesh); signalRings.splice(i, 1); }
  }

  if (particleTimer > 1.5) {
    particleTimer = 0;
    const p = particles.find(p => !p.active);
    if (p) { p.active = true; p.t = 0; p.mesh.visible = true; }
  }
  particles.forEach(p => {
    if (!p.active) return;
    p.t += p.speed;
    if (p.t >= 1) { p.active = false; p.mesh.visible = false; p.t = 0; return; }
    p.mesh.position.copy(getPointOnPath(p.path, p.t));
    const s = 1 + Math.sin(p.t * 20) * 0.3;
    p.mesh.scale.set(s, s, s);
  });

  if (Math.floor(time * 60) % 60 === 0) updateSensors();

  // Gentle sway on the stake
  rpiGroup.rotation.z = Math.sin(time * 0.8) * 0.01;

  // --- Animate Animals ---

  // Chickens: wander in circles, peck occasionally
  chickens.forEach(c => {
    c.wanderAngle += c.wanderSpeed;
    c.peckTimer -= 0.016;
    const wx = c.baseX + Math.cos(c.wanderAngle) * 1.5;
    const wz = c.baseZ + Math.sin(c.wanderAngle) * 1.5;
    c.mesh.position.x = wx;
    c.mesh.position.z = wz;
    c.mesh.rotation.y = c.wanderAngle + Math.PI / 2;
    // Pecking: head dips down
    if (c.peckTimer < 0.5 && c.peckTimer > 0) {
      c.mesh.rotation.x = Math.sin(c.peckTimer * 12) * 0.3;
    } else {
      c.mesh.rotation.x = 0;
    }
    if (c.peckTimer < 0) c.peckTimer = 2 + Math.random() * 4;
    // Tiny hop
    c.mesh.position.y = Math.abs(Math.sin(time * 6 + c.wanderAngle * 3)) * 0.03;
  });

  // Goats: wander around, occasionally stop
  goats.forEach(g => {
    g.wanderAngle += g.wanderSpeed;
    const wx = g.baseX + Math.cos(g.wanderAngle) * g.wanderRadius;
    const wz = g.baseZ + Math.sin(g.wanderAngle) * g.wanderRadius;
    g.mesh.position.x = wx;
    g.mesh.position.z = wz;
    g.mesh.rotation.y = g.wanderAngle + Math.PI / 2;
    // Slight bobbing
    g.mesh.position.y = Math.sin(time * 3 + g.wanderAngle) * 0.02;
  });

  // Cows: very slow drift, head bob for grazing
  cows.forEach(c => {
    c.wanderAngle += c.wanderSpeed;
    c.mesh.rotation.y += c.wanderSpeed * 0.5;
    c.headBob += 0.02;
    // Gentle grazing head motion
    c.mesh.children[1].rotation.x = Math.sin(c.headBob) * 0.15;
  });

  // Giraffes: gentle sway
  [giraffe1, giraffe2].forEach(g => {
    g.rotation.y += 0.0003;
    // Neck sway
    g.children[1].rotation.x = Math.sin(time * 0.5) * 0.05;
  });

  // Hippo: lazy ear wiggle and breathing
  hippo.scale.y = 1 + Math.sin(time * 0.8) * 0.02;
  hippo.children[5].rotation.z = Math.sin(time * 2) * 0.1; // ear wiggle
  hippo.children[6].rotation.z = Math.sin(time * 2 + 1) * 0.1;

  // Elephant: slow turn and ear flap
  elephant.rotation.y += 0.0002;
  elephant.children[6].rotation.y = Math.sin(time * 1.5) * 0.2 - 0.3;  // left ear
  elephant.children[7].rotation.y = Math.sin(time * 1.5 + 0.5) * 0.2 + 0.3;  // right ear

  // Birds circling lazily
  birds.forEach(b => {
    b.angle += b.speed;
    b.mesh.position.x = Math.cos(b.angle) * b.radius;
    b.mesh.position.z = Math.sin(b.angle) * b.radius;
    b.mesh.position.y = b.height + Math.sin(time * 0.5 + b.angle) * 1.5;
    b.mesh.rotation.y = b.angle + Math.PI / 2;
  });

  renderer.render(scene, camera);
}

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

document.getElementById('info-overlay').addEventListener('click', () => {
  document.getElementById('info-overlay').classList.add('hidden');
});

updateSensors();
animate();
