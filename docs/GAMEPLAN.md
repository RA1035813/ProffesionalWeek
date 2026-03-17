# SoilSMS Farm Game — Game Plan

> Forked from the SoilSMS demo. Strip the site, keep the world, make it a game.

---

## Phase 1: Fork & Clean

- [ ] Fork the repo into a new project (e.g. `soilsms-farm-game`)
- [ ] Delete all non-game files: `index.html`, `contact.html`, `support.html`, server code, IoT code
- [ ] Keep: `demo.html`, `style.css`, `scene.js`, `controls.js`, `app.js`, `sms.js`
- [ ] Rename `demo.html` → `index.html`
- [ ] Strip the sensor panel, AI panel, Nokia phone, SMS logic, and HUD overlays
- [ ] Remove helpdesk/contact links and footer
- [ ] Result: clean Three.js scene with terrain, animals, trees, buildings, sky

---

## Phase 2: First Person Controller

- [ ] Replace the orbit camera with a first-person camera (pointer lock)
- [ ] WASD movement, mouse look, spacebar jump
- [ ] Collision detection with ground (walk on terrain, follow height map)
- [ ] Basic collision with buildings/trees (don't walk through them)
- [ ] Sprint (shift key), crouch if needed later
- [ ] Player "body" — shadow on ground, maybe visible hands/tool

---

## Phase 3: Day/Night Cycle

- [ ] Sun moves across the sky over time (rotate directional light)
- [ ] Sky color transitions: dawn (orange) → day (blue) → dusk (red) → night (dark blue)
- [ ] Moonlight at night (dim blue directional light)
- [ ] Stars at night (particle system or skybox)
- [ ] Ambient light dims at night, fog changes color
- [ ] Game clock: 1 real minute = 1 game hour (24 min full cycle), tweak to feel right
- [ ] Animals sleep at night / different behavior

---

## Phase 4: Farming & Planting

- [ ] Inventory system (hotbar at bottom of screen)
- [ ] Seeds: maize, beans, cassava, sunflower, sorghum
- [ ] Planting: look at tilled soil + click to plant
- [ ] Growth stages: seed → sprout → half-grown → ready (time-based, tied to game clock)
- [ ] Watering: optional, speeds up growth (carry water bucket from well/river)
- [ ] Harvesting: click mature crop to collect into inventory
- [ ] Crop sell value varies (simple economy)
- [ ] Soil quality affects yield (tie into the existing sensor data concept)

---

## Phase 5: Hunting

- [ ] Some animals become huntable (not the cows/chickens — those are farm animals)
- [ ] Huntable: wild birds, maybe distant animals that spawn in the savanna
- [ ] Simple tool: slingshot or spear (click to throw/shoot)
- [ ] Projectile physics (arc trajectory)
- [ ] Drops: meat, hide, feathers
- [ ] Sell at market or use for crafting
- [ ] Animals flee when approached — need stealth/distance shots
- [ ] Don't hunt farm animals (penalty? they're yours!)

---

## Phase 6: Economy — Buying Stuff

- [ ] Currency: Tanzanian Shillings (TSh) or simplified "coins"
- [ ] Market/shop: interact with a building to open buy/sell menu
- [ ] Buyable items:
  - Seeds (different crop types)
  - Tools (hoe, watering can, slingshot, better versions)
  - Animal feed
  - Building materials
  - Fencing
- [ ] Sell: crops, animal products, hunted items
- [ ] Prices fluctuate slightly (simple random daily market)

---

## Phase 7: Land & Upgrades

- [ ] Start with a small plot near the hut
- [ ] Buy adjacent land plots to expand your farm
- [ ] Land types: fertile (cheap, good), savanna (cheap, needs work), riverside (expensive, great)
- [ ] Upgrades:
  - Bigger hut → house
  - Storage barn (increase inventory capacity)
  - Solar panel → power tools
  - Water pump (auto-irrigate nearby plots)
  - Sensor node (shows soil data for that plot — callback to original project!)
  - Chicken coop → eggs income
  - Cow pasture → milk income
  - Fenced areas to keep animals in/out
- [ ] Each upgrade is a visible 3D object placed in the world

---

## Phase 8: Electron Packaging

- [ ] `npm init` + install `electron`
- [ ] Create `main.js` (Electron entry point, loads `index.html`)
- [ ] Window config: fullscreen by default, resizable, title "SoilSMS Farm"
- [ ] Test on Windows + Linux
- [ ] Use `electron-builder` to create installers:
  - `.exe` for Windows
  - `.AppImage` / `.deb` for Linux
  - `.dmg` for macOS (if possible)
- [ ] Add app icon (pixel art farm icon)
- [ ] Optimize: disable devtools in production, set CSP headers

---

## Phase 9: itch.io Upload

- [ ] Create itch.io account + game page
- [ ] Upload two versions:
  - **HTML5** (browser playable) — zip the game files, upload as HTML
  - **Downloadable** — Electron builds per platform
- [ ] Set up game page:
  - Title: "SoilSMS Farm" (or new name)
  - Cover image / screenshots from the game
  - Description: low-poly Tanzanian farm sim
  - Tags: farming, low-poly, simulation, survival, indie
  - Price: free (or pay-what-you-want)
- [ ] Embed the HTML5 version for instant browser play
- [ ] Link downloadable builds for people who want the full experience

---

## Nice-to-Have (Later)

- [ ] Save/load system (localStorage for HTML5, file system for Electron)
- [ ] Sound effects: footsteps, ambient birds, wind, crop harvesting, animal sounds
- [ ] Music: chill lo-fi African-inspired ambient soundtrack
- [ ] Weather system: rain (boosts crops), drought (damages them), wind
- [ ] Seasons that affect what you can grow
- [ ] NPCs: other farmers, traders passing through
- [ ] Quests: "grow 10 maize", "build a chicken coop", "hunt 3 birds"
- [ ] Achievements / unlockables
- [ ] Multiplayer (way later, big scope)
- [ ] Mobile touch controls (if HTML5 version gets popular)
- [ ] Steam port (if itch.io does well — $100 fee, Steamworks SDK integration)

---

## Tech Stack

| Layer | Tool |
|-------|------|
| 3D Engine | Three.js (already in use) |
| UI | HTML/CSS overlays (already in use) |
| Desktop wrapper | Electron |
| Build tool | electron-builder |
| Distribution | itch.io (HTML5 + downloadable) |
| Version control | Git (forked repo) |

---

## Rough Priority Order

1. Clean fork (Phase 1)
2. First person (Phase 2) — this makes it feel like a game instantly
3. Day/night (Phase 3) — massive vibe boost
4. Planting (Phase 4) — core gameplay loop
5. Economy (Phase 6) — gives planting a purpose
6. Land & upgrades (Phase 7) — progression
7. Hunting (Phase 5) — secondary gameplay
8. Electron (Phase 8) — packaging
9. itch.io (Phase 9) — ship it!
