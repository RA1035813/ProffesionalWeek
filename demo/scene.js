// ============================================================
// SoilSMS Farm World — 3D Scene Setup
// ============================================================

const container = document.getElementById('canvas-container');
const scene = new THREE.Scene();
// Warm Tanzanian sky — hazy golden-blue
scene.background = new THREE.Color(0x9ec8e0);
scene.fog = new THREE.FogExp2(0xc8b890, 0.006);

const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 500);
camera.position.set(12, 8, 14);
camera.lookAt(0, 1, 0);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
container.appendChild(renderer.domElement);

// --- Lights (hot equatorial sun) ---
scene.add(new THREE.AmbientLight(0xffe8c0, 0.55));

const sunLight = new THREE.DirectionalLight(0xfff0c0, 1.4);
sunLight.position.set(30, 50, 20);
sunLight.castShadow = true;
sunLight.shadow.mapSize.set(2048, 2048);
sunLight.shadow.camera.left = -50;
sunLight.shadow.camera.right = 50;
sunLight.shadow.camera.top = 50;
sunLight.shadow.camera.bottom = -50;
scene.add(sunLight);
// Warm hemisphere: hot sky above, red earth below
scene.add(new THREE.HemisphereLight(0xdec88a, 0x8b4513, 0.45));

// --- Ground (Tanzanian red laterite earth with dry savanna) ---
const groundGeo = new THREE.PlaneGeometry(200, 200, 50, 50);
const posAttr = groundGeo.attributes.position;
for (let i = 0; i < posAttr.count; i++) {
  const x = posAttr.getX(i), y = posAttr.getY(i);
  posAttr.setZ(i, Math.sin(x * 0.05) * 0.8 + Math.cos(y * 0.04) * 0.6 + Math.random() * 0.15);
}
groundGeo.computeVertexNormals();
// Vertex colors: mix red earth and dry yellow grass
const groundColors = new Float32Array(posAttr.count * 3);
for (let i = 0; i < posAttr.count; i++) {
  const x = posAttr.getX(i), y = posAttr.getY(i);
  const dist = Math.sqrt(x * x + y * y);
  const noise = Math.sin(x * 0.3) * Math.cos(y * 0.2) * 0.5 + 0.5;
  // Near farm = darker tilled soil, far = dry savanna mix
  if (dist < 12) {
    // Red-brown tilled earth
    groundColors[i*3]   = 0.36 + noise * 0.06;
    groundColors[i*3+1] = 0.22 + noise * 0.04;
    groundColors[i*3+2] = 0.1 + noise * 0.02;
  } else {
    // Savanna: mix of dry yellow grass and red earth
    const grassMix = noise;
    groundColors[i*3]   = 0.55 * grassMix + 0.5 * (1-grassMix);
    groundColors[i*3+1] = 0.45 * grassMix + 0.28 * (1-grassMix);
    groundColors[i*3+2] = 0.15 * grassMix + 0.12 * (1-grassMix);
  }
}
groundGeo.setAttribute('color', new THREE.BufferAttribute(groundColors, 3));
const ground = new THREE.Mesh(groundGeo, new THREE.MeshLambertMaterial({ vertexColors: true }));
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
scene.add(ground);

// --- Farm soil patch (dark tilled Tanzanian earth) ---
const soilPatch = new THREE.Mesh(
  new THREE.PlaneGeometry(18, 12, 8, 8),
  new THREE.MeshLambertMaterial({ color: 0x6b3420 })
);
soilPatch.rotation.x = -Math.PI / 2;
soilPatch.position.set(0, 0.06, 0);
soilPatch.receiveShadow = true;
scene.add(soilPatch);

// --- Dry grass tufts scattered across savanna ---
function createGrassTuft(x, z) {
  const blades = 4 + Math.floor(Math.random() * 5);
  for (let i = 0; i < blades; i++) {
    const h = 0.3 + Math.random() * 0.5;
    const blade = new THREE.Mesh(
      new THREE.PlaneGeometry(0.05, h),
      new THREE.MeshLambertMaterial({
        color: Math.random() > 0.3 ? 0xb8a050 : 0x8a7a30,
        side: THREE.DoubleSide
      })
    );
    blade.position.set(x + (Math.random()-0.5)*0.4, h/2, z + (Math.random()-0.5)*0.4);
    blade.rotation.y = Math.random() * Math.PI;
    blade.rotation.z = (Math.random()-0.5) * 0.3;
    scene.add(blade);
  }
}
for (let i = 0; i < 120; i++) {
  const angle = Math.random() * Math.PI * 2;
  const dist = 12 + Math.random() * 50;
  createGrassTuft(Math.cos(angle)*dist, Math.sin(angle)*dist);
}

// --- Crop rows (maize — taller, with drooping leaves) ---
function createCropRow(x, z, count) {
  for (let i = 0; i < count; i++) {
    const h = 1.0 + Math.random() * 1.4;
    const stalk = new THREE.Mesh(
      new THREE.CylinderGeometry(0.04, 0.07, h, 5),
      new THREE.MeshLambertMaterial({ color: 0x4a8a28 })
    );
    stalk.position.set(x + i * 1.2 - count * 0.6, h / 2, z);
    stalk.castShadow = true;
    scene.add(stalk);

    // Maize leaves (2-3 per stalk, drooping)
    const leafCount = 2 + Math.floor(Math.random() * 2);
    for (let l = 0; l < leafCount; l++) {
      const leaf = new THREE.Mesh(
        new THREE.PlaneGeometry(0.8, 0.12),
        new THREE.MeshLambertMaterial({ color: 0x5aaa38, side: THREE.DoubleSide })
      );
      leaf.position.set(x + i * 1.2 - count * 0.6, h * (0.4 + l * 0.2), z);
      leaf.rotation.y = Math.random() * Math.PI;
      leaf.rotation.z = 0.2 + Math.random() * 0.4;
      scene.add(leaf);
    }
  }
}
for (let row = -4; row <= 4; row += 2) createCropRow(0, row, 12);

// --- Kilimanjaro in the distance ---
const kiliGroup = new THREE.Group();
kiliGroup.position.set(-70, 0, -80);
// Main mountain body
const kiliGeo = new THREE.ConeGeometry(30, 22, 8);
const kiliMat = new THREE.MeshLambertMaterial({ color: 0x6a7a8a });
const kiliMountain = new THREE.Mesh(kiliGeo, kiliMat);
kiliMountain.position.y = 11;
kiliGroup.add(kiliMountain);
// Snow cap
const snowGeo = new THREE.ConeGeometry(12, 6, 8);
const snowMat = new THREE.MeshLambertMaterial({ color: 0xf0f0ff });
const snowCap = new THREE.Mesh(snowGeo, snowMat);
snowCap.position.y = 20;
kiliGroup.add(snowCap);
// Secondary peak (Mawenzi)
const mawenzi = new THREE.Mesh(
  new THREE.ConeGeometry(14, 14, 6),
  new THREE.MeshLambertMaterial({ color: 0x5a6a7a })
);
mawenzi.position.set(22, 7, 5);
kiliGroup.add(mawenzi);
scene.add(kiliGroup);

// --- Distant hills (typical Tanzanian rolling landscape) ---
function createHill(x, z, radius, height, color) {
  const hill = new THREE.Mesh(
    new THREE.SphereGeometry(radius, 12, 8, 0, Math.PI * 2, 0, Math.PI / 2),
    new THREE.MeshLambertMaterial({ color })
  );
  hill.position.set(x, 0, z);
  hill.scale.y = height / radius;
  scene.add(hill);
}
createHill(50, -50, 20, 6, 0x7a8a5a);
createHill(-50, -60, 25, 8, 0x8a9060);
createHill(70, 40, 18, 5, 0x6a7a4a);
createHill(-60, 50, 22, 7, 0x7a8050);

// --- Red rocks / boulders (laterite outcrops) ---
function createRock(x, z, s) {
  const rock = new THREE.Mesh(
    new THREE.DodecahedronGeometry(s, 0),
    new THREE.MeshLambertMaterial({ color: 0x8b4525 + Math.floor(Math.random() * 0x151515) })
  );
  rock.position.set(x, s * 0.4, z);
  rock.rotation.set(Math.random(), Math.random(), Math.random());
  rock.castShadow = true;
  scene.add(rock);
}
[[12, -8, 0.5], [-10, -10, 0.7], [14, 7, 0.4], [-8, 10, 0.6],
 [22, -5, 0.3], [-14, -6, 0.5], [8, 14, 0.35]
].forEach(([x,z,s]) => createRock(x,z,s));

// ============================================================
// RPi Sensor Device — tall wooden stake with small computer box
// ============================================================
const rpiGroup = new THREE.Group();
rpiGroup.position.set(-3, 0, -2);

// Wooden stake (main structure)
const stake = new THREE.Mesh(
  new THREE.CylinderGeometry(0.04, 0.06, 2.4, 6),
  new THREE.MeshLambertMaterial({ color: 0x8B6914 })
);
stake.position.y = 1.2;
stake.castShadow = true;
rpiGroup.add(stake);

// Small RPi enclosure box on the stake
const rpiBox = new THREE.Mesh(
  new THREE.BoxGeometry(0.4, 0.25, 0.3),
  new THREE.MeshPhongMaterial({ color: 0x2c8c3c, specular: 0x222222 })
);
rpiBox.position.y = 2.0;
rpiBox.castShadow = true;
rpiGroup.add(rpiBox);

// Tiny solar panel on top of box
const solar = new THREE.Mesh(
  new THREE.BoxGeometry(0.5, 0.02, 0.35),
  new THREE.MeshPhongMaterial({ color: 0x1a1a4a, specular: 0x4444aa, shininess: 80 })
);
solar.position.y = 2.2;
solar.rotation.z = 0.15;
rpiGroup.add(solar);

// Thin antenna wire
const antenna = new THREE.Mesh(
  new THREE.CylinderGeometry(0.01, 0.01, 0.6, 4),
  new THREE.MeshLambertMaterial({ color: 0xcccccc })
);
antenna.position.set(0.15, 2.5, 0);
rpiGroup.add(antenna);

// Antenna tip (red bead)
const tip = new THREE.Mesh(
  new THREE.SphereGeometry(0.03, 8, 8),
  new THREE.MeshPhongMaterial({ color: 0xff3333, emissive: 0xff0000, emissiveIntensity: 0.5 })
);
tip.position.set(0.15, 2.85, 0);
rpiGroup.add(tip);

// Two soil probes going into ground
for (let i = -1; i <= 1; i += 2) {
  const probe = new THREE.Mesh(
    new THREE.CylinderGeometry(0.015, 0.015, 0.5, 6),
    new THREE.MeshLambertMaterial({ color: 0x666666 })
  );
  probe.position.set(i * 0.12, -0.05, 0.1);
  rpiGroup.add(probe);
}

// Tiny LED on box face
const ledGeo = new THREE.SphereGeometry(0.025, 8, 8);
const ledMat = new THREE.MeshPhongMaterial({ color: 0x00ff00, emissive: 0x00ff00, emissiveIntensity: 1 });
const led = new THREE.Mesh(ledGeo, ledMat);
led.position.set(-0.12, 2.02, 0.16);
rpiGroup.add(led);

// Thin wire from box down to probes
const wire = new THREE.Mesh(
  new THREE.CylinderGeometry(0.008, 0.008, 1.6, 4),
  new THREE.MeshLambertMaterial({ color: 0x444444 })
);
wire.position.set(0, 1.1, 0.1);
rpiGroup.add(wire);

scene.add(rpiGroup);

// --- Cell Tower ---
const towerGroup = new THREE.Group();
towerGroup.position.set(20, 0, -15);

const legMat = new THREE.MeshLambertMaterial({ color: 0xaaaaaa });
for (let i = 0; i < 3; i++) {
  const angle = (i / 3) * Math.PI * 2;
  const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.15, 14, 6), legMat);
  leg.position.set(Math.cos(angle) * 0.8, 7, Math.sin(angle) * 0.8);
  leg.castShadow = true;
  towerGroup.add(leg);
}
for (let h = 2; h < 14; h += 2) {
  const bar = new THREE.Mesh(new THREE.BoxGeometry(2.0, 0.06, 0.06), legMat);
  bar.position.y = h;
  bar.rotation.y = h * 0.5;
  towerGroup.add(bar);
}
for (let i = 0; i < 3; i++) {
  const angle = (i / 3) * Math.PI * 2;
  const panel = new THREE.Mesh(
    new THREE.BoxGeometry(0.6, 1.2, 0.1),
    new THREE.MeshPhongMaterial({ color: 0xdddddd })
  );
  panel.position.set(Math.cos(angle) * 1.0, 14, Math.sin(angle) * 1.0);
  panel.rotation.y = angle;
  panel.castShadow = true;
  towerGroup.add(panel);
}
const towerLightMat = new THREE.MeshPhongMaterial({ color: 0xff0000, emissive: 0xff0000, emissiveIntensity: 0.8 });
const towerLight = new THREE.Mesh(new THREE.SphereGeometry(0.15, 8, 8), towerLightMat);
towerLight.position.y = 15;
towerGroup.add(towerLight);
scene.add(towerGroup);

// --- Server building ---
const serverGroup = new THREE.Group();
serverGroup.position.set(20, 0, 18);

const building = new THREE.Mesh(
  new THREE.BoxGeometry(4, 3, 3),
  new THREE.MeshPhongMaterial({ color: 0x4a4a6a })
);
building.position.y = 1.5;
building.castShadow = true;
serverGroup.add(building);

const roof = new THREE.Mesh(
  new THREE.BoxGeometry(4.4, 0.2, 3.4),
  new THREE.MeshLambertMaterial({ color: 0x3a3a5a })
);
roof.position.y = 3.1;
serverGroup.add(roof);

for (let i = 0; i < 4; i++) {
  const sLed = new THREE.Mesh(
    new THREE.BoxGeometry(0.3, 0.08, 0.01),
    new THREE.MeshPhongMaterial({
      color: i % 2 === 0 ? 0x00ff88 : 0x3388ff,
      emissive: i % 2 === 0 ? 0x00ff88 : 0x3388ff,
      emissiveIntensity: 0.8
    })
  );
  sLed.position.set(-0.8 + i * 0.5, 1.5, 1.51);
  serverGroup.add(sLed);
}

// AI SERVER label
const aiCanvas = document.createElement('canvas');
aiCanvas.width = 150; aiCanvas.height = 60;
const aiCtx = aiCanvas.getContext('2d');
aiCtx.fillStyle = '#3498db';
aiCtx.fillRect(0, 0, 150, 60);
aiCtx.fillStyle = '#fff';
aiCtx.font = 'bold 30px monospace';
aiCtx.textAlign = 'center';
aiCtx.fillText('AI SERVER', 75, 40);
const aiLabel = new THREE.Mesh(
  new THREE.PlaneGeometry(1.5, 0.6),
  new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(aiCanvas) })
);
aiLabel.position.set(0, 2.5, 1.52);
serverGroup.add(aiLabel);

const dish = new THREE.Mesh(
  new THREE.SphereGeometry(0.6, 12, 8, 0, Math.PI * 2, 0, Math.PI / 2),
  new THREE.MeshPhongMaterial({ color: 0xdddddd, side: THREE.DoubleSide })
);
dish.position.set(1.2, 3.3, 0);
dish.rotation.x = Math.PI * 0.7;
serverGroup.add(dish);
scene.add(serverGroup);

// --- Farmer hut (Tanzanian boma style) ---
const hutGroup = new THREE.Group();
hutGroup.position.set(-18, 0, 12);

// Mud-brick circular wall
const wall = new THREE.Mesh(
  new THREE.CylinderGeometry(2.5, 2.8, 2.5, 12),
  new THREE.MeshLambertMaterial({ color: 0xa0704a })
);
wall.position.y = 1.25;
wall.castShadow = true;
hutGroup.add(wall);

// Thatched makuti roof
const thatch = new THREE.Mesh(
  new THREE.ConeGeometry(3.4, 2.2, 12),
  new THREE.MeshLambertMaterial({ color: 0x9a7a20 })
);
thatch.position.y = 3.6;
thatch.castShadow = true;
hutGroup.add(thatch);

// Door opening
const door = new THREE.Mesh(
  new THREE.PlaneGeometry(0.8, 1.6),
  new THREE.MeshLambertMaterial({ color: 0x3a2510 })
);
door.position.set(0, 0.8, 2.81);
hutGroup.add(door);

// Boma fence (thorn-branch fence around hut)
const fenceMat = new THREE.MeshLambertMaterial({ color: 0x6b5030 });
for (let a = 0; a < Math.PI * 2; a += 0.3) {
  if (a > 1.3 && a < 1.85) continue; // gap for entrance
  const fencePost = new THREE.Mesh(
    new THREE.CylinderGeometry(0.04, 0.05, 1.2, 4),
    fenceMat
  );
  fencePost.position.set(Math.cos(a) * 4.5, 0.6, Math.sin(a) * 4.5);
  fencePost.rotation.z = (Math.random() - 0.5) * 0.15;
  hutGroup.add(fencePost);
}
scene.add(hutGroup);

// --- Acacia trees (flat-topped, iconic Tanzania) ---
function createAcacia(x, z, s) {
  const trunkH = 3 * s;
  // Trunk — slender, slightly curved
  const trunk = new THREE.Mesh(
    new THREE.CylinderGeometry(0.08 * s, 0.18 * s, trunkH, 6),
    new THREE.MeshLambertMaterial({ color: 0x5a3a1a })
  );
  trunk.position.set(x, trunkH / 2, z);
  trunk.castShadow = true;
  scene.add(trunk);

  // Flat canopy (wide, thin disc — the classic acacia silhouette)
  const canopy = new THREE.Mesh(
    new THREE.CylinderGeometry(2.5 * s, 2.8 * s, 0.5 * s, 10),
    new THREE.MeshLambertMaterial({ color: 0x4a7a28 + Math.floor(Math.random() * 0x101000) })
  );
  canopy.position.set(x, trunkH + 0.2 * s, z);
  canopy.castShadow = true;
  scene.add(canopy);

  // Some branches reaching up into canopy
  for (let b = 0; b < 3; b++) {
    const bAngle = (b / 3) * Math.PI * 2 + Math.random() * 0.5;
    const branch = new THREE.Mesh(
      new THREE.CylinderGeometry(0.02 * s, 0.04 * s, 1.5 * s, 4),
      new THREE.MeshLambertMaterial({ color: 0x5a3a1a })
    );
    branch.position.set(
      x + Math.cos(bAngle) * 0.5 * s,
      trunkH * 0.7,
      z + Math.sin(bAngle) * 0.5 * s
    );
    branch.rotation.z = Math.cos(bAngle) * 0.5;
    branch.rotation.x = Math.sin(bAngle) * 0.5;
    scene.add(branch);
  }
}

// --- Baobab trees (fat trunk, sparse crown) ---
function createBaobab(x, z, s) {
  // Massive trunk
  const trunk = new THREE.Mesh(
    new THREE.CylinderGeometry(0.8 * s, 1.2 * s, 3.5 * s, 8),
    new THREE.MeshLambertMaterial({ color: 0x8a7a6a })
  );
  trunk.position.set(x, 1.75 * s, z);
  trunk.castShadow = true;
  scene.add(trunk);

  // Sparse gnarly branches at top
  for (let b = 0; b < 6; b++) {
    const bAngle = (b / 6) * Math.PI * 2;
    const bLen = (1.0 + Math.random() * 1.0) * s;
    const branch = new THREE.Mesh(
      new THREE.CylinderGeometry(0.06 * s, 0.15 * s, bLen, 5),
      new THREE.MeshLambertMaterial({ color: 0x7a6a5a })
    );
    branch.position.set(
      x + Math.cos(bAngle) * 0.6 * s,
      3.5 * s + bLen * 0.2,
      z + Math.sin(bAngle) * 0.6 * s
    );
    branch.rotation.z = Math.cos(bAngle) * 0.7;
    branch.rotation.x = Math.sin(bAngle) * 0.7;
    scene.add(branch);

    // Small leaf clusters at branch tips
    if (Math.random() > 0.3) {
      const leafCluster = new THREE.Mesh(
        new THREE.SphereGeometry(0.4 * s, 6, 4),
        new THREE.MeshLambertMaterial({ color: 0x5a8a30 })
      );
      leafCluster.position.set(
        x + Math.cos(bAngle) * (0.6 + bLen * 0.35) * s,
        3.5 * s + bLen * 0.6,
        z + Math.sin(bAngle) * (0.6 + bLen * 0.35) * s
      );
      scene.add(leafCluster);
    }
  }
}

// Place acacias (scattered across savanna)
[[-25,-8,1.2],[-22,-5,1],[-28,2,1.3],[28,-10,1.3],[30,5,1],[25,12,1.1],
 [-12,-18,1.1],[15,-20,1.2],[-8,20,1],[10,22,1.1],[-30,-15,1.3],
 [32,-18,1.0],[-15,22,0.9],[35,20,1.2],[18,25,1.0],[-35,-10,1.1],
 [40,-15,0.9],[-25,18,1.0]
].forEach(([x,z,s]) => createAcacia(x,z,s));

// Place baobabs (fewer, they're rare and iconic)
[[-20,8,1.4],[38,8,1.2],[-40,-20,1.5],[45,25,1.1]
].forEach(([x,z,s]) => createBaobab(x,z,s));

// --- African sun (big, hot, golden) ---
const sun = new THREE.Mesh(
  new THREE.SphereGeometry(4, 16, 16),
  new THREE.MeshBasicMaterial({ color: 0xffdd33 })
);
sun.position.set(60, 45, -40);
scene.add(sun);
// Heat haze glow
const glow = new THREE.Mesh(
  new THREE.SphereGeometry(8, 16, 16),
  new THREE.MeshBasicMaterial({ color: 0xffcc22, transparent: true, opacity: 0.12 })
);
glow.position.copy(sun.position);
scene.add(glow);
// Second glow ring (heat shimmer)
const glow2 = new THREE.Mesh(
  new THREE.SphereGeometry(14, 16, 16),
  new THREE.MeshBasicMaterial({ color: 0xffaa00, transparent: true, opacity: 0.04 })
);
glow2.position.copy(sun.position);
scene.add(glow2);

// --- Clouds (sparse, bright tropical cumulus) ---
function createCloud(x,y,z) {
  const g = new THREE.Group();
  const mat = new THREE.MeshLambertMaterial({color: 0xfff8f0, transparent:true, opacity:0.8});
  const count = 3 + Math.floor(Math.random()*3);
  for (let i=0;i<count;i++) {
    const m = new THREE.Mesh(new THREE.SphereGeometry(1.2+Math.random()*2,8,6), mat);
    m.position.set(i*2-count, Math.random()*0.8, Math.random()*1.5-0.75);
    g.add(m);
  }
  g.position.set(x,y,z);
  scene.add(g);
  return g;
}
const clouds = [createCloud(-20,28,-30), createCloud(25,32,-25), createCloud(50,26,15), createCloud(-40,30,20)];

// --- Birds circling (simple dark triangles high up) ---
const birds = [];
for (let i = 0; i < 5; i++) {
  const birdGeo = new THREE.BufferGeometry();
  const verts = new Float32Array([0,0,0, -0.3,0,-0.15, 0.3,0,-0.15]);
  birdGeo.setAttribute('position', new THREE.BufferAttribute(verts, 3));
  const bird = new THREE.Mesh(birdGeo, new THREE.MeshBasicMaterial({color:0x222222, side:THREE.DoubleSide}));
  const angle = (i/5) * Math.PI * 2;
  const radius = 15 + Math.random() * 10;
  bird.position.set(Math.cos(angle)*radius, 18+Math.random()*8, Math.sin(angle)*radius);
  scene.add(bird);
  birds.push({ mesh: bird, angle, radius, speed: 0.003 + Math.random()*0.002, height: bird.position.y });
}

// ============================================================
// SMS data flow particles
// ============================================================
const particles = [];
const particleGeo = new THREE.SphereGeometry(0.15, 6, 6);
const particleSendMat = new THREE.MeshBasicMaterial({ color: 0xf1c40f });
const particleRecvMat = new THREE.MeshBasicMaterial({ color: 0x7cfc00 });

const sendPath = [
  new THREE.Vector3(-3, 2.85, -2),
  new THREE.Vector3(8, 10, -8),
  new THREE.Vector3(20, 15, -15),
];
const recvPath = [
  new THREE.Vector3(20, 3, 18),
  new THREE.Vector3(20, 15, -15),
  new THREE.Vector3(0, 10, 0),
  new THREE.Vector3(-18, 3, 12),
];

function createParticle(path, mat, speed) {
  const mesh = new THREE.Mesh(particleGeo, mat);
  mesh.visible = false;
  scene.add(mesh);
  return { mesh, path, t: 0, speed, active: false };
}
for (let i = 0; i < 5; i++) {
  particles.push(createParticle(sendPath, particleSendMat, 0.008 + Math.random() * 0.004));
  particles.push(createParticle(recvPath, particleRecvMat, 0.007 + Math.random() * 0.003));
}

function getPointOnPath(path, t) {
  const segs = path.length - 1;
  const seg = Math.min(Math.floor(t * segs), segs - 1);
  return new THREE.Vector3().lerpVectors(path[seg], path[seg + 1], (t * segs) - seg);
}
