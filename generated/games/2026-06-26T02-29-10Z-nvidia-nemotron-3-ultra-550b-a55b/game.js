const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const W = canvas.width;
const H = canvas.height;

// Game state
let state = 'playing'; // 'playing' | 'gameover'
let score = 0;
let lives = 3;
let frame = 0;

// Player (the living language model)
const player = {
  x: W / 2,
  y: H / 2,
  r: 14,
  speed: 3.5,
  color: '#0ff',
  trail: []
};

// Tokens (knowledge bits)
const tokens = [];
const TOKEN_COUNT = 12;
function spawnTokens() {
  tokens.length = 0;
  for (let i = 0; i < TOKEN_COUNT; i++) {
    tokens.push({
      x: Math.random() * (W - 40) + 20,
      y: Math.random() * (H - 40) + 20,
      r: 6,
      color: '#ff0',
      pulse: Math.random() * Math.PI * 2
    });
  }
}

// Obstacles (hallucinations)
const obstacles = [];
const OBSTACLE_COUNT = 6;
function spawnObstacles() {
  obstacles.length = 0;
  for (let i = 0; i < OBSTACLE_COUNT; i++) {
    obstacles.push({
      x: Math.random() * (W - 40) + 20,
      y: Math.random() * (H - 40) + 20,
      w: 20,
      h: 20,
      vx: (Math.random() - 0.5) * 2,
      vy: (Math.random() - 0.5) * 2,
      color: '#f44'
    });
  }
}

// Input
const keys = {};
window.addEventListener('keydown', e => { keys[e.code] = true; if (e.code === 'KeyR' && state === 'gameover') reset(); });
window.addEventListener('keyup', e => { keys[e.code] = false; });

function reset() {
  state = 'playing';
  score = 0;
  lives = 3;
  player.x = W / 2;
  player.y = H / 2;
  player.trail = [];
  spawnTokens();
  spawnObstacles();
  frame = 0;
  requestAnimationFrame(loop);
}

function update() {
  if (state !== 'playing') return;

  // Player movement
  let dx = 0, dy = 0;
  if (keys['ArrowUp'] || keys['KeyW']) dy = -1;
  if (keys['ArrowDown'] || keys['KeyS']) dy = 1;
  if (keys['ArrowLeft'] || keys['KeyA']) dx = -1;
  if (keys['ArrowRight'] || keys['KeyD']) dx = 1;
  if (dx !== 0 && dy !== 0) { dx *= 0.7071; dy *= 0.7071; }
  player.x += dx * player.speed;
  player.y += dy * player.speed;

  // Clamp to canvas
  player.x = Math.max(player.r, Math.min(W - player.r, player.x));
  player.y = Math.max(player.r, Math.min(H - player.r, player.y));

  // Trail for visual polish
  player.trail.unshift({ x: player.x, y: player.y, life: 12 });
  if (player.trail.length > 20) player.trail.pop();
  player.trail.forEach(p => p.life--);
  player.trail = player.trail.filter(p => p.life > 0);

  // Token collection
  for (let i = tokens.length - 1; i >= 0; i--) {
    const t = tokens[i];
    const dx = player.x - t.x;
    const dy = player.y - t.y;
    if (dx * dx + dy * dy < (player.r + t.r) ** 2) {
      tokens.splice(i, 1);
      score += 10;
      // spawn a new token elsewhere
      tokens.push({
        x: Math.random() * (W - 40) + 20,
        y: Math.random() * (H - 40) + 20,
        r: 6,
        color: '#ff0',
        pulse: Math.random() * Math.PI * 2
      });
    }
    t.pulse += 0.08;
  }

  // Obstacle movement & collision
  for (const o of obstacles) {
    o.x += o.vx;
    o.y += o.vy;
    if (o.x < o.w / 2 || o.x > W - o.w / 2) o.vx *= -1;
    if (o.y < o.h / 2 || o.y > H - o.h / 2) o.vy *= -1;

    // AABB vs circle collision
    const cx = Math.max(o.x - o.w / 2, Math.min(player.x, o.x + o.w / 2));
    const cy = Math.max(o.y - o.h / 2, Math.min(player.y, o.y + o.h / 2));
    const dx = player.x - cx;
    const dy = player.y - cy;
    if (dx * dx + dy * dy < player.r * player.r) {
      lives--;
      // knockback
      player.x += dx > 0 ? 20 : -20;
      player.y += dy > 0 ? 20 : -20;
      player.x = Math.max(player.r, Math.min(W - player.r, player.x));
      player.y = Math.max(player.r, Math.min(H - player.r, player.y));
      if (lives <= 0) state = 'gameover';
    }
  }

  frame++;
}

function draw() {
  // Clear
  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, W, H);

  // Draw trail
  for (const p of player.trail) {
    const alpha = p.life / 12 * 0.4;
    ctx.beginPath();
    ctx.arc(p.x, p.y, player.r * (p.life / 12), 0, Math.PI * 2);
    ctx.fillStyle = `rgba(0,255,255,${alpha})`;
    ctx.fill();
  }

  // Draw tokens
  for (const t of tokens) {
    const pulse = Math.sin(t.pulse) * 2;
    ctx.beginPath();
    ctx.arc(t.x, t.y, t.r + pulse, 0, Math.PI * 2);
    ctx.fillStyle = t.color;
    ctx.shadowColor = '#ff0';
    ctx.shadowBlur = 8;
    ctx.fill();
    ctx.shadowBlur = 0;
  }

  // Draw obstacles
  for (const o of obstacles) {
    ctx.fillStyle = o.color;
    ctx.fillRect(o.x - o.w / 2, o.y - o.h / 2, o.w, o.h);
    // simple eyes
    ctx.fillStyle = '#000';
    ctx.fillRect(o.x - 5, o.y - 4, 4, 4);
    ctx.fillRect(o.x + 1, o.y - 4, 4, 4);
  }

  // Draw player
  ctx.beginPath();
  ctx.arc(player.x, player.y, player.r, 0, Math.PI * 2);
  const grad = ctx.createRadialGradient(player.x - 3, player.y - 3, 0, player.x, player.y, player.r);
  grad.addColorStop(0, '#0ff');
  grad.addColorStop(1, '#088');
  ctx.fillStyle = grad;
  ctx.shadowColor = '#0ff';
  ctx.shadowBlur = 12;
  ctx.fill();
  ctx.shadowBlur = 0;

  // UI
  ctx.fillStyle = '#eee';
  ctx.font = '16px monospace';
  ctx.textAlign = 'left';
  ctx.fillText(`Score: ${score}`, 10, 22);
  ctx.fillText(`Lives: ${'♥'.repeat(lives)}`, 10, 42);
  ctx.textAlign = 'center';
  ctx.font = '12px monospace';
  ctx.fillStyle = '#888';
  ctx.fillText('Arrows/WASD move • Collect yellow tokens • Avoid red squares', W / 2, H - 10);

  if (state === 'gameover') {
    ctx.fillStyle = 'rgba(0,0,0,0.7)';
    ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = '#f44';
    ctx.font = '48px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('GAME OVER', W / 2, H / 2 - 20);
    ctx.fillStyle = '#eee';
    ctx.font = '20px monospace';
    ctx.fillText(`Final Score: ${score}`, W / 2, H / 2 + 20);
    ctx.font = '16px monospace';
    ctx.fillText('Press R to restart', W / 2, H / 2 + 55);
  }
}

function loop() {
  update();
  draw();
  if (state !== 'gameover') requestAnimationFrame(loop);
}

// Init
spawnTokens();
spawnObstacles();
requestAnimationFrame(loop);
