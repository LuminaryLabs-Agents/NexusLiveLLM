from __future__ import annotations

from pathlib import Path
import json
import os
import re

from .common import harness_root, repo_root, utc_id, write_json, write_text, ledger
from .orchestrator_loop import run as run_orchestrator
from .slot_loop import fill as fill_slot
from .run_tools import run_all
from .reviewer_loop import review
from .product_brief import make_brief, product_prompt, sanitize_public_text


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "build"


def determine_app_type(public_prompt: str, mode: str) -> str:
    low = public_prompt.lower()
    if "minecraft" in low or "voxel" in low or "block world" in low:
        return "minecraft-three"
    if "three" in low and ("open" in low or "world" in low):
        return "three-open-world"
    if "kit builder" in low or "domain service" in low or "dsk" in low or mode == "kit-builder":
        return "kit-builder"
    if mode == "harness-builder":
        return "kit-builder"
    return "kit-builder"


def update_manifest(repo: Path, run_id: str, title: str, public_summary: str) -> None:
    docs = repo / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    path = docs / "games.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    except json.JSONDecodeError:
        manifest = []
    manifest = [item for item in manifest if item.get("id") != run_id]
    manifest.insert(0, {
        "id": run_id,
        "title": sanitize_public_text(title),
        "prompt": sanitize_public_text(public_summary),
        "summary": sanitize_public_text(public_summary),
        "url": f"games/{run_id}/",
        "status": "active",
        "visibility": "public"
    })
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def shared_index(title: str) -> str:
    title = sanitize_public_text(title)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <link rel="stylesheet" href="./style.css" />
</head>
<body>
  <main id="app">
    <section id="hud" aria-live="polite">
      <h1>{title}</h1>
      <p id="status">Loading...</p>
      <p id="controls">WASD / arrows · click or number keys · inspect GameHost</p>
      <a href="../../index.html">Back to launcher</a>
    </section>
    <canvas id="game" role="application"></canvas>
    <section id="panel"></section>
  </main>
  <script src="./game.js"></script>
</body>
</html>
"""


def shared_css() -> str:
    return """html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#071017;color:#eef8ff;font-family:Inter,ui-sans-serif,system-ui,sans-serif}#app,#game{position:fixed;inset:0}#game{width:100vw;height:100vh;display:block}#hud{position:fixed;left:16px;top:16px;z-index:3;width:min(420px,calc(100vw - 32px));padding:16px;border:1px solid rgba(150,255,186,.24);border-radius:18px;background:rgba(4,10,18,.72);backdrop-filter:blur(10px)}#hud h1{margin:0 0 6px;font-size:clamp(24px,4vw,42px);letter-spacing:-.05em}#hud p{margin:6px 0;color:#cbd9e8}#hud a{display:inline-flex;margin-top:8px;color:#bfffd2;text-decoration:none;font-weight:900}#panel{position:fixed;right:16px;bottom:16px;z-index:2;display:grid;gap:8px;width:min(460px,calc(100vw - 32px))}.card,.action{border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.08);border-radius:14px;padding:10px}.action{display:inline-flex;margin:4px;cursor:pointer}.active{outline:2px solid #bfffd2}pre{white-space:pre-wrap;max-height:220px;overflow:auto}button{border:0;border-radius:999px;padding:8px 12px;background:#bfffd2;color:#06110b;font-weight:900}canvas{touch-action:none}"""


def kit_builder_js(public_payload: dict) -> str:
    data = {
        "kits": [
            {"id": "interaction-domain-service-kit", "status": "candidate", "owns": ["verbs", "affordances", "validation"]},
            {"id": "movement-control-kit", "status": "candidate", "owns": ["input intent", "movement mode", "camera descriptors"]},
            {"id": "save-snapshot-kit", "status": "candidate", "owns": ["archive index", "replay trace", "state capsules"]},
            {"id": "gallery-curation-kit", "status": "active", "owns": ["score", "fate", "max 10 builds"]}
        ],
        "actions": ["CONTINUE", "SHOW_ADVANCED", "ASK_ORCHESTRATOR", "ASK_SLOT", "RECONCILE", "STOP"],
        "product": public_payload,
    }
    return "const KIT_DATA = " + json.dumps(data) + r''';
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const panel = document.getElementById('panel');
const statusLine = document.getElementById('status');
let selected = 0;
let frame = 0;
function resize(){canvas.width=innerWidth*devicePixelRatio;canvas.height=innerHeight*devicePixelRatio;ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0)}
addEventListener('resize',resize);resize();
function renderPanel(){const kit=KIT_DATA.kits[selected];panel.innerHTML=`<article class="card"><h2>${kit.id}</h2><p>Status: ${kit.status}</p><p>Owns: ${kit.owns.join(', ')}</p><pre>${JSON.stringify({kit,actions:KIT_DATA.actions,product:KIT_DATA.product},null,2)}</pre></article><article class="card"><h3>Bounded actions</h3>${KIT_DATA.actions.map(a=>`<button class="action" data-action="${a}">${a}</button>`).join('')}</article>`;panel.querySelectorAll('button').forEach(btn=>btn.onclick=()=>{statusLine.textContent=`${btn.dataset.action} selected for ${kit.id}`})}
function draw(){frame++;ctx.clearRect(0,0,innerWidth,innerHeight);const t=performance.now()*0.001;ctx.fillStyle='#071017';ctx.fillRect(0,0,innerWidth,innerHeight);KIT_DATA.kits.forEach((kit,i)=>{const x=innerWidth/2+Math.cos(t+i*1.7)*220;const y=innerHeight/2+Math.sin(t*.8+i*1.3)*150;ctx.beginPath();ctx.arc(x,y,54+i*4,0,Math.PI*2);ctx.fillStyle=i===selected?'rgba(191,255,210,.38)':'rgba(92,153,255,.22)';ctx.fill();ctx.strokeStyle=i===selected?'#bfffd2':'rgba(255,255,255,.34)';ctx.lineWidth=2;ctx.stroke();ctx.fillStyle='#eef8ff';ctx.textAlign='center';ctx.font='700 13px system-ui';ctx.fillText(kit.id.replaceAll('-', ' '),x,y)});requestAnimationFrame(draw)}
canvas.addEventListener('click',()=>{selected=(selected+1)%KIT_DATA.kits.length;renderPanel()});
window.GameHost={getState:()=>({frame,selected:KIT_DATA.kits[selected],all:KIT_DATA}),select:(i)=>{selected=i%KIT_DATA.kits.length;renderPanel()}};
statusLine.textContent='Kit Builder dashboard ready. Click the canvas to cycle domain kits.';renderPanel();draw();
'''.strip() + "\n"


def three_world_js() -> str:
    return r'''
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const statusLine = document.getElementById('status');
let player = { x: 0, y: 0, vx: 0, vy: 0 };
let frame = 0;
let score = 0;
const keys = new Set();
const seedPoints = Array.from({ length: 90 }, (_, i) => ({ x: Math.sin(i * 91.7) * 820, y: Math.cos(i * 41.1) * 820, type: i % 7 === 0 ? 'core' : i % 3 === 0 ? 'rock' : 'tree', got: false }));
function resize(){canvas.width=innerWidth*devicePixelRatio;canvas.height=innerHeight*devicePixelRatio;ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0)}
addEventListener('resize',resize);resize();
addEventListener('keydown',e=>keys.add(e.key.toLowerCase()));addEventListener('keyup',e=>keys.delete(e.key.toLowerCase()));addEventListener('blur',()=>keys.clear());
function heightAt(x,y){return Math.sin(x*.01)*20+Math.cos(y*.012)*18+Math.sin((x+y)*.006)*12}
function update(){frame++;const ax=(keys.has('d')||keys.has('arrowright'))-(keys.has('a')||keys.has('arrowleft'));const ay=(keys.has('s')||keys.has('arrowdown'))-(keys.has('w')||keys.has('arrowup'));player.vx=player.vx*.88+ax*.9;player.vy=player.vy*.88+ay*.9;player.x+=player.vx;player.y+=player.vy;seedPoints.forEach(p=>{if(p.type==='core'&&!p.got&&Math.hypot(p.x-player.x,p.y-player.y)<28){p.got=true;score++}});statusLine.textContent=`Cores ${score}/${seedPoints.filter(p=>p.type==='core').length} · Height ${heightAt(player.x,player.y).toFixed(1)} · GameHost ready`}
function draw(){update();ctx.fillStyle='#071017';ctx.fillRect(0,0,innerWidth,innerHeight);const cx=innerWidth/2,cy=innerHeight/2;for(let gx=-10;gx<=10;gx++){for(let gy=-8;gy<=8;gy++){const wx=player.x+gx*70,wy=player.y+gy*70;const h=heightAt(wx,wy);ctx.fillStyle=`hsl(${120+h},38%,${26+h*.25}%)`;ctx.fillRect(cx+gx*70-player.x%70,cy+gy*70-player.y%70,72,72)}}seedPoints.forEach(p=>{const sx=cx+p.x-player.x,sy=cy+p.y-player.y;if(sx<-80||sy<-80||sx>innerWidth+80||sy>innerHeight+80)return;ctx.beginPath();ctx.arc(sx,sy,p.type==='core'?9:14,0,Math.PI*2);ctx.fillStyle=p.got?'rgba(255,255,255,.12)':p.type==='core'?'#ffd24a':p.type==='rock'?'#8a93a4':'#2f8f4d';ctx.fill()});ctx.beginPath();ctx.arc(cx,cy,16,0,Math.PI*2);ctx.fillStyle='#82a7ff';ctx.fill();requestAnimationFrame(draw)}
window.GameHost={getState:()=>({frame,player,score,points:seedPoints}),heightAt,restart:()=>{player={x:0,y:0,vx:0,vy:0};score=0;seedPoints.forEach(p=>p.got=false)}};draw();
'''.strip() + "\n"


def minecraft_three_js(public_payload: dict) -> str:
    data = {
        "product": public_payload,
        "domains": ["build-break-domain-service-kit", "inventory-domain-service-kit", "movement-control-kit", "save-snapshot-kit"],
        "blocks": ["grass", "dirt", "stone", "wood", "glass"]
    }
    return "const VOXEL_BRIEF = " + json.dumps(data) + r''';
const statusLine = document.getElementById('status');
const panel = document.getElementById('panel');
const keys = new Set();
let frame = 0;
let selectedBlock = 1;
let player = { x: 10, y: 14, z: 24, yaw: 0 };
const world = new Map();
const blockTypes = [null,{id:'grass',color:0x5aa052},{id:'dirt',color:0x8a5a35},{id:'stone',color:0x898f99},{id:'wood',color:0x8b5a2b},{id:'glass',color:0x8fe6ff}];
function key(x,y,z){return `${x},${y},${z}`}
function blockAt(x,y,z){return world.get(key(x,y,z))||0}
function setBlock(x,y,z,t){const k=key(x,y,z); if(t) world.set(k,t); else world.delete(k)}
for(let x=-18;x<=18;x++){for(let z=-18;z<=18;z++){const h=2+Math.floor(Math.sin(x*.45)*1.7+Math.cos(z*.36)*1.6);for(let y=0;y<=h;y++)setBlock(x,y,z,y===h?1:y>h-2?2:3);if((x*31+z*17)%29===0){for(let y=h+1;y<h+5;y++)setBlock(x,y,z,4);setBlock(x,h+5,z,1)}}}
function renderPanel(){panel.innerHTML=`<article class="card"><h2>Voxel Domains</h2><p>${VOXEL_BRIEF.domains.join(' · ')}</p><p>Selected block: ${blockTypes[selectedBlock].id}</p><pre>${JSON.stringify({selectedBlock:blockTypes[selectedBlock],player,blocks:world.size},null,2)}</pre></article>`}
function boot(THREE){
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x9fd0ff); scene.fog = new THREE.Fog(0x9fd0ff, 45, 120);
  const camera = new THREE.PerspectiveCamera(70, innerWidth/innerHeight, .1, 500);
  const renderer = new THREE.WebGLRenderer({canvas:document.getElementById('game'),antialias:true}); renderer.setPixelRatio(Math.min(devicePixelRatio,2)); renderer.setSize(innerWidth,innerHeight);
  scene.add(new THREE.HemisphereLight(0xffffff,0x446633,1.2)); const sun=new THREE.DirectionalLight(0xffffff,2); sun.position.set(30,60,25); scene.add(sun);
  const geo = new THREE.BoxGeometry(1,1,1); const mats = blockTypes.map(b=>b?new THREE.MeshStandardMaterial({color:b.color,roughness:.82,transparent:b.id==='glass',opacity:b.id==='glass'?.45:1}):null);
  const group = new THREE.Group(); scene.add(group);
  function rebuild(){group.clear(); const meshes={}; for(const [k,t] of world){const [x,y,z]=k.split(',').map(Number); const exposed=[[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]].some(([a,b,c])=>!blockAt(x+a,y+b,z+c)); if(!exposed)continue; const m=meshes[t]||(meshes[t]=[]); m.push([x,y,z]);} Object.entries(meshes).forEach(([t,pts])=>{const mesh=new THREE.InstancedMesh(geo,mats[Number(t)],pts.length); const o=new THREE.Object3D(); pts.forEach((p,i)=>{o.position.set(p[0],p[1],p[2]);o.updateMatrix();mesh.setMatrixAt(i,o.matrix)}); group.add(mesh);}); }
  rebuild();
  addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)});
  addEventListener('keydown',e=>{keys.add(e.key.toLowerCase()); const n=Number(e.key); if(n>0&&n<blockTypes.length){selectedBlock=n;renderPanel()}}); addEventListener('keyup',e=>keys.delete(e.key.toLowerCase())); addEventListener('blur',()=>keys.clear());
  document.addEventListener('mousedown',e=>{const dx=Math.round(Math.sin(player.yaw)); const dz=Math.round(-Math.cos(player.yaw)); const tx=Math.round(player.x+dx*4), ty=Math.max(1,Math.round(player.y-3)), tz=Math.round(player.z+dz*4); if(e.button===2){setBlock(tx,ty,tz,selectedBlock)}else{setBlock(tx,ty,tz,0)} rebuild(); renderPanel();}); document.addEventListener('contextmenu',e=>e.preventDefault());
  function step(){frame++; if(keys.has('arrowleft'))player.yaw+=.04;if(keys.has('arrowright'))player.yaw-=.04; const f=(keys.has('w')||keys.has('arrowup'))-(keys.has('s')||keys.has('arrowdown')); const r=keys.has('d')-keys.has('a'); player.x+=Math.sin(player.yaw)*f*.18+Math.cos(player.yaw)*r*.18; player.z+=-Math.cos(player.yaw)*f*.18+Math.sin(player.yaw)*r*.18; const groundY=18; for(let y=20;y>=0;y--){if(blockAt(Math.round(player.x),y,Math.round(player.z))){player.y=Math.max(player.y, y+3.2);break}} camera.position.set(player.x,player.y,player.z); camera.rotation.order='YXZ'; camera.rotation.y=player.yaw; camera.rotation.x=-0.12; statusLine.textContent=`WASD move · arrows turn · click removes · right click places · block ${blockTypes[selectedBlock].id}`; renderer.render(scene,camera); requestAnimationFrame(step)}
  window.GameHost={getState:()=>({frame,player,selectedBlock:blockTypes[selectedBlock],blockCount:world.size,domains:VOXEL_BRIEF.domains}),rebuild,setBlock}; renderPanel(); step();
}
import('https://unpkg.com/three@0.160.0/build/three.module.js').then(boot).catch(err=>{statusLine.textContent='3D renderer could not load. '+err.message});
'''.strip() + "\n"


def write_game(repo: Path, run_id: str, title: str, public_summary: str, public_payload: dict, app_type: str) -> Path:
    game_dir = repo / "docs" / "games" / run_id
    write_text(game_dir / "index.html", shared_index(title))
    write_text(game_dir / "style.css", shared_css())
    if app_type == "kit-builder":
        js = kit_builder_js(public_payload)
    elif app_type == "minecraft-three":
        js = minecraft_three_js(public_payload)
    else:
        js = three_world_js()
    write_text(game_dir / "game.js", js)
    write_text(game_dir / "README.md", f"# {sanitize_public_text(title)}\n\n{sanitize_public_text(public_summary)}\n\nType: `{app_type}`\n")
    update_manifest(repo, run_id, title, public_summary)
    return game_dir


def main() -> None:
    harness = harness_root()
    repo = repo_root()
    raw_prompt = os.environ.get("GAME_PROMPT", "Build a Kit Builder app.")
    default_mode = os.environ.get("LIVEHARNESS_MODE", "kit-builder")
    brief = make_brief(raw_prompt, default_mode)
    public_prompt = product_prompt(raw_prompt, default_mode)
    mode = brief.mode or default_mode
    run_stamp = os.environ.get("LIVEHARNESS_RUN_ID") or utc_id()
    run_dir_env = os.environ.get("LIVEHARNESS_RUN_DIR")
    run_dir = Path(run_dir_env) if run_dir_env else harness / "runs" / run_stamp
    if not run_dir.is_absolute():
        run_dir = harness / run_dir
    app_type = determine_app_type(public_prompt, mode)
    run_id = slugify(run_stamp) + "-" + app_type
    if app_type == "minecraft-three":
        title = brief.public_title if "minecraft" in brief.public_title.lower() or "voxel" in brief.public_title.lower() else "Voxel Domain Builder"
    elif app_type == "kit-builder":
        title = brief.public_title or "NexusRealtime Kit Builder"
    else:
        title = brief.public_title or "Open World Experiment"

    public_payload = brief.to_dict()
    write_json(run_dir / "input" / "product-brief.json", public_payload)
    write_json(run_dir / "run-summary.json", {"run_id": run_id, "public_summary": brief.public_summary, "harness": "LiveHarnessV.01", "mode": mode, "app_type": app_type})
    run_orchestrator(run_dir, "root-orchestrator", f"{app_type} app", ["runtime", "world", "player", "gameplay", "visuals", "tests"])
    for name in ["runtime", "world", "player", "gameplay", "visuals", "tests"]:
        run_orchestrator(run_dir, name + "-orchestrator", name + " domain", [])
    fill_slot(run_dir, "product-brief", "public_contract", public_payload)
    fill_slot(run_dir, "debug-host", "state_contract", {"global": "window.GameHost", "method": "getState"})
    fill_slot(run_dir, "launcher-card", "copy", {"title": title, "url": f"games/{run_id}/"})

    game_dir = write_game(repo, run_id, title, brief.public_summary, public_payload, app_type)
    applied = {"files": [str(game_dir / name) for name in ["index.html", "style.css", "game.js", "README.md"]], "manifest": "docs/games.json"}
    write_json(run_dir / "reconcile" / "applied-files.json", applied)
    ledger("action-ledger.jsonl", {"time": utc_id(), "move": "WRITE_FINAL_FILES", "run_id": run_id, "app_type": app_type})
    tools = run_all()
    write_json(run_dir / "tools" / "final-tool-results.json", tools)
    review(run_dir, tools)
    write_json(harness / "state" / "latest.json", {"run_id": run_id, "url": f"docs/games/{run_id}/", "tools_ok": tools.get("ok"), "app_type": app_type})


if __name__ == "__main__":
    main()
