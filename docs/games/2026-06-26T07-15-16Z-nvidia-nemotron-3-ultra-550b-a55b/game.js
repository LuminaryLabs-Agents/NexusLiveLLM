const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const scoreEl = document.getElementById('score');
const instructionsEl = document.getElementById('instructions');

let width, height;
function resize() {
  width = canvas.width = window.innerWidth;
  height = canvas.height = window.innerHeight;
}
window.addEventListener('resize', resize);
resize();

// Game state
let player, words, bugs, score, gameOver, keys;

function init() {
  player = { x: width/2, y: height/2, r: 16, speed: 5, color: '#4af' };
  words = [];
  bugs = [];
  score = 0;
  gameOver = false;
  keys = {};
  spawnEntities();
  updateScore();
}

function spawnEntities() {
  for (let i = 0; i < 12; i++) spawnWord();
  for (let i = 0; i < 6; i++) spawnBug();
}

function spawnWord() {
  const margin = 40;
  words.push({
    x: Math.random() * (width - 2*margin) + margin,
    y: Math.random() * (height - 2*margin) + margin,
    r: 10,
    color: '#4f4',
    collected: false
  });
}

function spawnBug() {
  const margin = 60;
  bugs.push({
    x: Math.random() * (width - 2*margin) + margin,
    y: Math.random() * (height - 2*margin) + margin,
    r: 14,
    color: '#f44',
    vx: (Math.random()-0.5)*2,
    vy: (Math.random()-0.5)*2,
    speed: 1.5
  });
}

function updateScore() {
  scoreEl.textContent = 'Score: ' + score;
}

window.addEventListener('keydown', e => {
  keys[e.code] = true;
  if (e.code === 'KeyR' && gameOver) init();
});
window.addEventListener('keyup', e => keys[e.code] = false);

function updatePlayer() {
  let dx = 0, dy = 0;
  if (keys['ArrowUp'] || keys['KeyW']) dy -= 1;
  if (keys['ArrowDown'] || keys['KeyS']) dy += 1;
  if (keys['ArrowLeft'] || keys['KeyA']) dx -= 1;
  if (keys['ArrowRight'] || keys['KeyD']) dx += 1;
  if (dx || dy) {
    const len = Math.hypot(dx, dy);
    dx = dx/len * player.speed;
    dy = dy/len * player.speed;
  }
  player.x = Math.max(player.r, Math.min(width - player.r, player.x + dx));
  player.y = Math.max(player.r, Math.min(height - player.r, player.y + dy));
}

function updateBugs() {
  bugs.forEach(b => {
    // simple wander
    if (Math.random() < 0.02) {
      b.vx = (Math.random()-0.5)*2;
      b.vy = (Math.random()-0.5)*2;
    }
    b.x += b.vx * b.speed;
    b.y += b.vy * b.speed;
    // bounce edges
    if (b.x < b.r || b.x > width - b.r) b.vx *= -1;
    if (b.y < b.r || b.y > height - b.r) b.vy *= -1;
    b.x = Math.max(b.r, Math.min(width - b.r, b.x));
    b.y = Math.max(b.r, Math.min(height - b.r, b.y));
  });
}

function checkCollisions() {
  // words
  words.forEach(w => {
    if (!w.collected) {
      const dx = player.x - w.x;
      const dy = player.y - w.y;
      if (dx*dx + dy*dy < (player.r + w.r)*(player.r + w.r)) {
        w.collected = true;
        score += 10;
        updateScore();
        // respawn a new word after short delay
        setTimeout(() => {
          if (!gameOver) spawnWord();
        }, 800);
      }
    }
  });
  // remove collected
  words = words.filter(w => !w.collected);

  // bugs
  bugs.forEach(b => {
    const dx = player.x - b.x;
    const dy = player.y - b.y;
    if (dx*dx + dy*dy < (player.r + b.r)*(player.r + b.r)) {
      gameOver = true;
      instructionsEl.textContent = 'Game Over! Press R to restart.';
    }
  });
}

function draw() {
  ctx.clearRect(0, 0, width, height);
  // draw words
  words.forEach(w => {
    ctx.beginPath();
    ctx.arc(w.x, w.y, w.r, 0, Math.PI*2);
    ctx.fillStyle = w.color;
    ctx.fill();
    // tiny label
    ctx.fillStyle = '#fff';
    ctx.font = '10px monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('💬', w.x, w.y+3);
  });
  // draw bugs
  bugs.forEach(b => {
    ctx.beginPath();
    ctx.arc(b.x, b.y, b.r, 0, Math.PI*2);
    ctx.fillStyle = b.color;
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.font = '12px monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('🐛', b.x, b.y+4);
  });
  // draw player
  ctx.beginPath();
  ctx.arc(player.x, player.y, player.r, 0, Math.PI*2);
  ctx.fillStyle = player.color;
  ctx.fill();
  ctx.fillStyle = '#fff';
  ctx.font = '14px monospace';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('🤖', player.x, player.y+5);
}

function loop() {
  if (!gameOver) {
    updatePlayer();
    updateBugs();
    checkCollisions();
  }
  draw();
  requestAnimationFrame(loop);
}

init();
loop();
