const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const scoreEl = document.getElementById('score');
const stateEl = document.getElementById('state');

const WIDTH = 600;
const HEIGHT = 400;
canvas.width = WIDTH;
canvas.height = HEIGHT;

const PLAYER_R = 12;
const TOKEN_R = 6;
const GLITCH_R = 10;
const PLAYER_SPEED = 4;
const GLITCH_SPEED = 2;
const TOKEN_COUNT = 8;
const GLITCH_COUNT = 5;

let player, tokens, glitches, score, running, lastTime;

function init() {
  player = { x: WIDTH/2, y: HEIGHT/2 };
  tokens = [];
  glitches = [];
  score = 0;
  running = true;
  stateEl.textContent = '';
  spawnTokens();
  spawnGlitches();
  updateScore();
  requestAnimationFrame(loop);
}

function spawnTokens() {
  tokens = [];
  for (let i = 0; i < TOKEN_COUNT; i++) {
    tokens.push({
      x: Math.random() * (WIDTH - 40) + 20,
      y: Math.random() * (HEIGHT - 40) + 20
    });
  }
}

function spawnGlitches() {
  glitches = [];
  for (let i = 0; i < GLITCH_COUNT; i++) {
    glitches.push({
      x: Math.random() * (WIDTH - 40) + 20,
      y: Math.random() * (HEIGHT - 40) + 20,
      vx: (Math.random() - 0.5) * GLITCH_SPEED * 2,
      vy: (Math.random() - 0.5) * GLITCH_SPEED * 2
    });
  }
}

function updateScore() {
  scoreEl.textContent = `Score: ${score}`;
}

function loop(timestamp) {
  if (!running) return;
  const dt = (timestamp - (lastTime || timestamp)) / 16.666; // normalize to 60fps
  lastTime = timestamp;
  update(dt);
  draw();
  requestAnimationFrame(loop);
}

function update(dt) {
  // player movement
  if (keys.ArrowUp || keys.KeyW) player.y -= PLAYER_SPEED * dt;
  if (keys.ArrowDown || keys.KeyS) player.y += PLAYER_SPEED * dt;
  if (keys.ArrowLeft || keys.KeyA) player.x -= PLAYER_SPEED * dt;
  if (keys.ArrowRight || keys.KeyD) player.x += PLAYER_SPEED * dt;

  // clamp
  player.x = Math.max(PLAYER_R, Math.min(WIDTH - PLAYER_R, player.x));
  player.y = Math.max(PLAYER_R, Math.min(HEIGHT - PLAYER_R, player.y));

  // token collection
  for (let i = tokens.length - 1; i >= 0; i--) {
    const t = tokens[i];
    const dx = player.x - t.x;
    const dy = player.y - t.y;
    if (dx*dx + dy*dy < (PLAYER_R + TOKEN_R)*(PLAYER_R + TOKEN_R)) {
      tokens.splice(i,1);
      score += 10;
      updateScore();
    }
  }
  if (tokens.length === 0) spawnTokens();

  // glitch movement & collision
  for (const g of glitches) {
    g.x += g.vx * dt;
    g.y += g.vy * dt;
    // bounce
    if (g.x < GLITCH_R || g.x > WIDTH - GLITCH_R) g.vx *= -1;
    if (g.y < GLITCH_R || g.y > HEIGHT - GLITCH_R) g.vy *= -1;
    // clamp
    g.x = Math.max(GLITCH_R, Math.min(WIDTH - GLITCH_R, g.x));
    g.y = Math.max(GLITCH_R, Math.min(HEIGHT - GLITCH_R, g.y));

    const dx = player.x - g.x;
    const dy = player.y - g.y;
    if (dx*dx + dy*dy < (PLAYER_R + GLITCH_R)*(PLAYER_R + GLITCH_R)) {
      gameOver();
    }
  }
}

function gameOver() {
  running = false;
  stateEl.textContent = 'GAME OVER - Press R to restart';
}

function draw() {
  ctx.clearRect(0,0,WIDTH,HEIGHT);
  // grid background
  ctx.strokeStyle = '#222';
  ctx.lineWidth = 1;
  for (let x=0;x<WIDTH;x+=40){ ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,HEIGHT); ctx.stroke(); }
  for (let y=0;y<HEIGHT;y+=40){ ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(WIDTH,y); ctx.stroke(); }

  // tokens
  ctx.fillStyle = '#00ff99';
  for (const t of tokens) {
    ctx.beginPath();
    ctx.arc(t.x, t.y, TOKEN_R, 0, Math.PI*2);
    ctx.fill();
  }

  // glitches
  ctx.fillStyle = '#ff4444';
  for (const g of glitches) {
    ctx.beginPath();
    ctx.arc(g.x, g.y, GLITCH_R, 0, Math.PI*2);
    ctx.fill();
    // cross
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(g.x - 6, g.y - 6);
    ctx.lineTo(g.x + 6, g.y + 6);
    ctx.moveTo(g.x + 6, g.y - 6);
    ctx.lineTo(g.x - 6, g.y + 6);
    ctx.stroke();
  }

  // player (LLM core)
  const grad = ctx.createRadialGradient(player.x, player.y, 0, player.x, player.y, PLAYER_R);
  grad.addColorStop(0, '#00ffff');
  grad.addColorStop(1, '#0066ff');
  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.arc(player.x, player.y, PLAYER_R, 0, Math.PI*2);
  ctx.fill();
  // pulse ring
  ctx.strokeStyle = 'rgba(0,255,255,0.5)';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(player.x, player.y, PLAYER_R + 4 + Math.sin(Date.now()/200)*3, 0, Math.PI*2);
  ctx.stroke();
}

const keys = {};
window.addEventListener('keydown', e => {
  keys[e.code] = true;
  if (e.code === 'KeyR' && !running) init();
});
window.addEventListener('keyup', e => keys[e.code] = false);

init();
