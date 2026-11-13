"""3D view of one park search dump (zeno_skills.park_search, env ZB_PARK_DUMP; the arms as their collision spheres) as a standalone HTML page.

usage: python3 tools/park_search_view3d.py <dump.json> <annotation.json> <door name> <door q> <out.html> [title]
"""
import json
import math
import sys

dump_p, ann_p, door_name, door_q, out_p = sys.argv[1:6]
title = sys.argv[6] if len(sys.argv) > 6 else "Park search 3D"
door_q = float(door_q)
D = json.load(open(dump_p))
A = json.load(open(ann_p))

gx = [g[0] for g in D["goals"]]
gy = [g[1] for g in D["goals"]]
cx, cy = sum(gx) / len(gx), sum(gy) / len(gy)
R = 2.2

boxes = []                    # [cx, cy, cz, sx, sy, sz, yaw, kind, name]
for o in A.get("obstacles", []):
    b = o.get("aabb")
    if not b or len(b) != 6:
        continue
    if b[3] < cx - R or b[0] > cx + R or b[4] < cy - R or b[1] > cy + R:
        continue
    boxes.append([(b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2, b[3] - b[0], b[4] - b[1], b[5] - b[2],
                  0.0, "obstacle", o.get("name", "")])
for sp in A["supports"]:
    x0, y0, x1, y1 = sp["aabb_xy"]
    if x1 < cx - R or x0 > cx + R or y1 < cy - R or y0 > cy + R:
        continue
    kind = "shelf" if sp.get("category") == "cabinet_inside" else "support"
    boxes.append([(x0 + x1) / 2, (y0 + y1) / 2, sp["z"] - 0.005, x1 - x0, y1 - y0, 0.01, 0.0, kind, sp["name"]])
door = next(a for a in A["articulated"] if a["name"] == door_name)
F = door["part_frame"]
px, py = door["pivot"][0], door["pivot"][1]
t = door_q - door["closed_q"]
c, s = math.cos(t), math.sin(t)
yaw0 = math.atan2(F[1][0], F[0][0])
for lo, hi in door.get("part_boxes") or [door["part_box"]]:
    u, v, w = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2
    wx = F[0][0] * u + F[0][1] * v + F[0][3]
    wy = F[1][0] * u + F[1][1] * v + F[1][3]
    wz = F[2][2] * w + F[2][3]
    dx, dy = wx - px, wy - py
    boxes.append([px + c * dx - s * dy, py + s * dx + c * dy, wz, hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2],
                  yaw0 + t, "door", f"{door_name} door (q {door_q:.3f})"])

builds = []
for i, (b, arm) in enumerate(zip(D.get("built", []), D.get("arms", []))):
    builds.append({"i": i + 1, "x": b[0], "y": b[1], "yaw": b[2], "k": b[3], "why": b[4],
                   "eep": arm.get("eep"), "rank": arm.get("rank", []), "relay": arm.get("relay")})
data = {"centre": [cx, cy], "boxes": boxes, "builds": builds, "goals": D["goals"], "prefer": D.get("prefer", []),
        "found": D.get("found"), "label": D.get("label", "")}

html = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Park search 3D</title>
<style>
:root { --bg:#ffffff; --fg:#1d1d1f; --muted:#666; --card:#f4f4f2; --sel:#dfe9ff; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#18181a; --fg:#ececec; --muted:#aaa; --card:#232326; --sel:#2c3a5c; } }
:root[data-theme="dark"] { --bg:#18181a; --fg:#ececec; --muted:#aaa; --card:#232326; --sel:#2c3a5c; }
body { background:var(--bg); color:var(--fg); font:13px/1.4 system-ui,sans-serif; margin:0; display:flex; height:100vh; }
#side { width:360px; overflow:auto; padding:12px 16px; box-sizing:border-box; border-right:1px solid #8884; }
#view { flex:1; position:relative; } canvas { display:block; }
h1 { font-size:16px; margin:0 0 6px; } .muted { color:var(--muted); }
.b { padding:5px 6px; border-radius:6px; cursor:pointer; margin:2px 0; background:var(--card); }
.b.sel { background:var(--sel); } .b small { color:var(--muted); display:block; }
label { display:block; margin:3px 0; } .key span { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:5px; }
@media (max-width: 700px) { body { flex-direction:column; } #side { width:100%; height:40vh; } }
</style></head><body>
<div id="side"><h1>TITLE</h1><div class="muted" id="sum"></div>
<p class="key"><span style="background:#4a7fd6"></span>ranking IK solution (what the park was ranked by)<br>
<span style="background:#2fa866"></span>IK the build solved (then the motion failed)<br>
<span style="background:#e0443a"></span>spheres penetrating something (depth on hover)<br>
<span style="background:#8a5a2b"></span>door leaf · <span style="background:#e9b44c"></span>inside shelf · RGB triad = set-down TCP (EEP)</p>
<label><input type="checkbox" id="cRank" checked> ranking solution</label>
<label><input type="checkbox" id="cRelay" checked> solved IK</label>
<label><input type="checkbox" id="cAll" checked> every build's base (faint)</label>
<label><input type="checkbox" id="cObs" checked> furniture boxes</label>
<div id="list"></div><div id="hover" class="muted" style="margin-top:8px"></div></div>
<div id="view"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
const D = DATA;
const view = document.getElementById('view');
let renderer;
try { renderer = new THREE.WebGLRenderer({antialias:true, alpha:true}); }
catch (e) {
  view.innerHTML = '<p style="padding:16px">This browser has no WebGL: the 3D view cannot be drawn here.</p>';
  renderer = null;
}
if (!renderer) {
  const list = document.getElementById('list');
  D.builds.forEach(b => { const e = document.createElement('div'); e.className = 'b';
    e.innerHTML = `#${b.i} base (${b.x.toFixed(2)}, ${b.y.toFixed(2)}, ${b.yaw.toFixed(0)}°) goal ${b.k}${b.relay ? ' · IK solved' : ''}<small>${b.why}</small>`;
    list.appendChild(e); });
  throw new Error('no WebGL');
}
renderer.setPixelRatio(window.devicePixelRatio);
view.appendChild(renderer.domElement);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, 1, 0.01, 50);
camera.up.set(0, 0, 1);
const [cx, cy] = D.centre;
camera.position.set(cx + 2.2, cy - 2.6, 2.4);
const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.target.set(cx, cy, 0.5);
scene.add(new THREE.AmbientLight(0xffffff, 0.65));
const sun = new THREE.DirectionalLight(0xffffff, 0.6); sun.position.set(cx + 3, cy - 2, 5); scene.add(sun);
const grid = new THREE.GridHelper(4.4, 22, 0x999999, 0xcccccc); grid.rotation.x = Math.PI / 2; grid.position.set(cx, cy, 0);
scene.add(grid);
function resize() { const w = view.clientWidth, h = view.clientHeight; renderer.setSize(w, h); camera.aspect = w / h; camera.updateProjectionMatrix(); }
window.addEventListener('resize', resize); resize();

const obs = new THREE.Group(); scene.add(obs);
const pickable = [];
for (const [x, y, z, sx, sy, sz, yaw, kind, name] of D.boxes) {
  const g = new THREE.BoxGeometry(sx, sy, sz);
  let m;
  if (kind === 'door') m = new THREE.Mesh(g, new THREE.MeshLambertMaterial({color:0x8a5a2b, transparent:true, opacity:0.85}));
  else if (kind === 'shelf') m = new THREE.Mesh(g, new THREE.MeshLambertMaterial({color:0xe9b44c, transparent:true, opacity:0.75}));
  else if (kind === 'support') m = new THREE.Mesh(g, new THREE.MeshLambertMaterial({color:0xc9c3b3, transparent:true, opacity:0.35}));
  else m = new THREE.LineSegments(new THREE.EdgesGeometry(g), new THREE.LineBasicMaterial({color:0x9b8f75}));
  m.position.set(x, y, z); m.rotation.z = yaw; m.userData = {name};
  (kind === 'obstacle' ? obs : scene).add(m); if (kind !== 'obstacle') pickable.push(m);
}
function triad(p, Rm, len, group) {
  const cols = [0xe53935, 0x43a047, 0x1e88e5];
  for (let a = 0; a < 3; a++) {
    const d = new THREE.Vector3(Rm[0][a], Rm[1][a], Rm[2][a]).multiplyScalar(len);
    const geo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...p), new THREE.Vector3(...p).add(d)]);
    group.add(new THREE.Line(geo, new THREE.LineBasicMaterial({color:cols[a]})));
  }
}
function baseMarker(x, y, yaw, opacity, group) {
  const disc = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.02, 24),
                              new THREE.MeshLambertMaterial({color:0x555555, transparent:true, opacity}));
  disc.rotation.x = Math.PI / 2; disc.position.set(x, y, 0.01); group.add(disc);
  const a = yaw * Math.PI / 180;
  const geo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(x, y, 0.03), new THREE.Vector3(x + 0.3 * Math.cos(a), y + 0.3 * Math.sin(a), 0.03)]);
  group.add(new THREE.Line(geo, new THREE.LineBasicMaterial({color:0x222222, transparent:true, opacity:Math.min(1, opacity * 2)})));
}
const all = new THREE.Group(); scene.add(all);
for (const b of D.builds) baseMarker(b.x, b.y, b.yaw, 0.12, all);
for (const g of D.goals) { const m = new THREE.Mesh(new THREE.SphereGeometry(0.008), new THREE.MeshBasicMaterial({color:0x1f4fbf})); m.position.set(...g); all.add(m); }
for (const p of D.prefer) { const m = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.12, 0.02), new THREE.MeshBasicMaterial({color:0x7a1fbf})); m.position.set(p[0], p[1], 0.01); m.userData = {name:'seed in front of the free edge'}; scene.add(m); pickable.push(m); }

let sel = new THREE.Group(); scene.add(sel);
const sphereGeo = new THREE.SphereGeometry(1, 14, 10);
function arm(spheres, color, group) {
  for (const [x, y, z, r, d, link] of spheres) {
    const hit = d > 0.001;
    const m = new THREE.Mesh(sphereGeo, new THREE.MeshLambertMaterial({color: hit ? 0xe0443a : color, transparent:true,
                                         opacity: hit ? 0.75 : 0.22, depthWrite:false}));
    m.scale.setScalar(r); m.position.set(x, y, z);
    m.userData = {name: link + (hit ? ` · into the world ${(d * 1000).toFixed(0)} mm` : '')};
    group.add(m);
  }
}
function show(i) {
  scene.remove(sel); sel = new THREE.Group(); scene.add(sel);
  const b = D.builds[i];
  document.querySelectorAll('.b').forEach((e, j) => e.classList.toggle('sel', j === i));
  baseMarker(b.x, b.y, b.yaw, 0.6, sel);
  if (b.eep) triad(b.eep[0], b.eep[1], 0.1, sel);
  const rg = new THREE.Group(), lg = new THREE.Group(); rg.name = 'rank'; lg.name = 'relay';
  arm(b.rank || [], 0x4a7fd6, rg); if (b.relay) arm(b.relay, 0x2fa866, lg);
  rg.visible = document.getElementById('cRank').checked; lg.visible = document.getElementById('cRelay').checked;
  sel.add(rg); sel.add(lg);
}
const list = document.getElementById('list');
D.builds.forEach((b, i) => {
  const e = document.createElement('div'); e.className = 'b';
  const short = b.why === 'ok' ? 'OK — this park was chosen' : b.why;
  e.innerHTML = `#${b.i} base (${b.x.toFixed(2)}, ${b.y.toFixed(2)}, ${b.yaw.toFixed(0)}°) goal ${b.k}${b.relay ? ' · IK solved' : ''}<small>${short}</small>`;
  e.onclick = () => show(i); list.appendChild(e);
});
document.getElementById('sum').textContent = `${D.label} · ${D.builds.length} builds · found: ${D.found ? D.found.slice(0, 3).map(v => v.toFixed(2)).join(', ') : 'none'}`;
document.getElementById('cRank').onchange = e => { const g = sel.getObjectByName('rank'); if (g) g.visible = e.target.checked; };
document.getElementById('cRelay').onchange = e => { const g = sel.getObjectByName('relay'); if (g) g.visible = e.target.checked; };
document.getElementById('cAll').onchange = e => { all.visible = e.target.checked; };
document.getElementById('cObs').onchange = e => { obs.visible = e.target.checked; };
const ray = new THREE.Raycaster(), mouse = new THREE.Vector2();
renderer.domElement.addEventListener('mousemove', ev => {
  const r = renderer.domElement.getBoundingClientRect();
  mouse.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(mouse, camera);
  const hit = ray.intersectObjects(sel.children.flatMap(g => g.children || []).concat(pickable.filter(o => o.parent === scene)), false)
                 .find(h => h.object.visible && h.object.parent.visible);
  document.getElementById('hover').textContent = hit ? hit.object.userData.name || '' : '';
});
if (D.builds.length) show(0);
(function loop() { requestAnimationFrame(loop); controls.update(); renderer.render(scene, camera); })();
</script></body></html>"""
open(out_p, "w").write(html.replace("TITLE", title).replace("DATA", json.dumps(data)))
print(out_p, len(builds), "builds")
