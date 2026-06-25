const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const W = canvas.width, H = canvas.height;

const WORDS = [
  'hello','world','model','token','layer','attention','vector','embed','decode','prompt',
  'inference','training','loss','gradient','batch','epoch','learning','rate','bias','weight'
];

let score = 0;
let gameOver = false;
let fallingWords = [];
let currentInput = '';
let targetWord = null;
let spawnTimer = 0;
const SPAWN_INTERVAL = 1800; // ms
const FALL_SPEED = 0.6; // px per frame

function spawnWord() {
  const word = WORDS[Math.floor(Math.random()*WORDS.length)];
  const x = Math.random()*(W-120)+60;
  fallingWords.push({word, x, y:-30, speed:FALL_SPEED, active:true});
}

function resetGame() {
  score = 0;
  gameOver = false;
  fallingWords = [];
  currentInput = '';
  targetWord = null;
  spawnTimer = 0;
}

function drawText(text, x, y, size=20, color='#0f0', align='center') {
  ctx.font = `${size}px monospace`;
  ctx.fillStyle = color;
  ctx.textAlign = align;
  ctx.fillText(text, x, y);
}

function drawUI() {
  drawText(`Score: ${score}`, 20, 30, 24, '#0f0', 'left');
  drawText('Type the falling words', W/2, 30, 18, '#888');
  if (gameOver) {
    drawText('GAME OVER', W/2, H/2-20, 48, '#f44');
    drawText(`Final Score: ${score}`, W/2, H/2+30, 28, '#ff0');
    drawText('Press SPACE to restart', W/2, H/2+70, 20, '#888');
  }
}

function drawModel() {
  // simple pulsing orb in center bottom
  const cx = W/2, cy = H-60;
  const time = Date.now()/300;
  const r = 30 + Math.sin(time)*5;
  const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
  grad.addColorStop(0, '#0f0');
  grad.addColorStop(0.5, '#0a0');
  grad.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI*2);
  ctx.fillStyle = grad;
  ctx.fill();
}

function drawFallingWords() {
  fallingWords.forEach(w => {
    if (!w.active) return;
    drawText(w.word, w.x, w.y, 22, '#ff0');
    // highlight typed portion if this is target
    if (w === targetWord && currentInput.length>0) {
      ctx.font = '22px monospace';
      const metrics = ctx.measureText(w.word.substring(0, currentInput.length));
      ctx.fillStyle = '#0f0';
      ctx.fillText(w.word.substring(0, currentInput.length), w.x - metrics.width/2, w.y);
    }
  });
}

function update(delta) {
  if (gameOver) return;
  spawnTimer += delta;
  if (spawnTimer > SPAWN_INTERVAL) {
    spawnWord();
    spawnTimer = 0;
  }
  fallingWords.forEach(w => {
    if (!w.active) return;
    w.y += w.speed * (delta/16); // normalize to 60fps
    if (w.y > H-80) {
      // reached model -> game over
      gameOver = true;
    }
  });
  // clean inactive
  fallingWords = fallingWords.filter(w => w.active);
}

function checkInput() {
  if (!targetWord) {
    // find first word that matches start of currentInput
    for (let w of fallingWords) {
      if (w.active && w.word.startsWith(currentInput)) {
        targetWord = w;
        break;
      }
    }
  } else {
    if (!targetWord.word.startsWith(currentInput)) {
      // mismatch, reset input
      currentInput = '';
      targetWord = null;
    } else if (currentInput === targetWord.word) {
      // completed word
      score += targetWord.word.length * 10;
      targetWord.active = false;
      currentInput = '';
      targetWord = null;
    }
  }
}

function gameLoop(timestamp) {
  const delta = timestamp - (gameLoop.last||timestamp);
  gameLoop.last = timestamp;
  update(delta);
  // clear
  ctx.clearRect(0,0,W,H);
  drawModel();
  drawFallingWords();
  drawUI();
  requestAnimationFrame(gameLoop);
}

window.addEventListener('keydown', e => {
  if (gameOver) {
    if (e.code === 'Space') resetGame();
    return;
  }
  if (e.key === 'Backspace') {
    currentInput = currentInput.slice(0,-1);
  } else if (e.key.length === 1 && /[a-zA-Z]/.test(e.key)) {
    currentInput += e.key.toLowerCase();
  }
  checkInput();
});

resetGame();
requestAnimationFrame(gameLoop);
