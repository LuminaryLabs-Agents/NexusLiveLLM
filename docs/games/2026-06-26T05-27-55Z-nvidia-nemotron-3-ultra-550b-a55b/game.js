const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const scoreEl = document.getElementById('score');
const gameOverEl = document.getElementById('gameOver');
const instructionsEl = document.getElementById('instructions');

let width, height;
let player = { x:0, y:0, w:80, h:20, speed:7, color:'#00ffcc' };
let tokens = [];
let score = 0;
let gameOver = false;
let spawnTimer = 0;
let spawnInterval = 1000; // ms
let lastTime = 0;
let tokenSpeed = 3;
let tokenSpeedIncrease = 0.001;
let maxTokenSpeed = 10;
let keys = { left:false, right:false };

function resize() {
  width = window.innerWidth;
  height = window.innerHeight;
  canvas.width = width;
  canvas.height = height;
  player.x = (width - player.w) / 2;
  player.y = height - player.h - 20;
}
window.addEventListener('resize', resize);
resize();

window.addEventListener('keydown', e => {
  if (e.key === 'ArrowLeft') keys.left = true;
  if (e.key === 'ArrowRight') keys.right = true;
  if (e.key === 'r' || e.key === 'R') restart();
});
window.addEventListener('keyup', e => {
  if (e.key === 'ArrowLeft') keys.left = false;
  if (e.key === 'ArrowRight') keys.right = false;
});

function spawnToken() {
  const size = 20 + Math.random() * 15;
  tokens.push({
    x: Math.random() * (width - size),
    y: -size,
    size,
    color: `hsl(${Math.random()*360}, 70%, 60%)`,
    vy: tokenSpeed
  });
}

function update(dt) {
  if (gameOver) return;
  // player movement
  if (keys.left) player.x -= player.speed * dt / 16;
  if (keys.right) player.x += player.speed * dt / 16;
  player.x = Math.max(0, Math.min(width - player.w, player.x));

  // spawn tokens
  spawnTimer += dt;
  if (spawnTimer >= spawnInterval) {
    spawnToken();
    spawnTimer = 0;
    // gradually decrease interval down to 400ms
    spawnInterval = Math.max(400, spawnInterval - 5);
  }

  // update tokens
  for (let i = tokens.length - 1; i >= 0; i--) {
    const t = tokens[i];
    t.y += t.vy * dt / 16;
    t.vy += tokenSpeedIncrease * dt / 16;
    if (t.vy > maxTokenSpeed) t.vy = maxTokenSpeed;

    // collision with player
    if (t.y + t.size >= player.y &&
        t.x + t.size >= player.x &&
        t.x <= player.x + player.w) {
      score++;
      scoreEl.textContent = `Score: ${score}`;
      tokens.splice(i, 1);
      continue;
    }
    // missed
    if (t.y > height) {
      gameOver = true;
      gameOverEl.classList.remove('hidden');
      instructionsEl.classList.add('hidden');
    }
  }
}

function draw() {
  ctx.clearRect(0,0,width,height);
  // draw player
  ctx.fillStyle = player.color;
  ctx.fillRect(player.x, player.y, player.w, player.h);
  // draw tokens
  tokens.forEach(t => {
    ctx.fillStyle = t.color;
    ctx.beginPath();
    ctx.arc(t.x + t.size/2, t.y + t.size/2, t.size/2, 0, Math.PI*2);
    ctx.fill();
  });
}

function loop(time) {
  const dt = time - lastTime;
  lastTime = time;
  update(dt);
  draw();
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);

function restart() {
  tokens = [];
  score = 0;
  scoreEl.textContent = `Score: ${score}`;
  gameOver = false;
  gameOverEl.classList.add('hidden');
  instructionsEl.classList.remove('hidden');
  spawnTimer = 0;
  spawnInterval = 1000;
  tokenSpeed = 3;
  player.x = (width - player.w) / 2;
}
