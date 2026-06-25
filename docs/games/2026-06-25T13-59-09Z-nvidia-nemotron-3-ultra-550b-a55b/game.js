const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const W = canvas.width;
const H = canvas.height;

const scoreEl = document.getElementById('score');
const livesEl = document.getElementById('lives');

// Game constants
const PLAYER_W = 60, PLAYER_H = 20;
const PLAYER_SPEED = 6;
const WORD_MIN_SPEED = 2, WORD_MAX_SPEED = 5;
const WORD_SPAWN_INTERVAL = 1200; // ms
const WORD_FONT = '18px monospace';
const MAX_WORDS = 10;

// Word pool
const WORD_POOL = [
    'function','variable','loop','array','object','promise','async',
    'await','callback','closure','scope','hoisting','prototype',
    'module','import','export','default','const','let','var'
];

// Game state
let playerX, playerY;
let words = [];
let lastSpawn = 0;
let score = 0;
let lives = 3;
let gameOver = false;
let keys = { left: false, right: false };

function resetGame() {
    playerX = (W - PLAYER_W) / 2;
    playerY = H - PLAYER_H - 10;
    words = [];
    lastSpawn = performance.now();
    score = 0;
    lives = 3;
    gameOver = false;
    updateUI();
}

function updateUI() {
    scoreEl.textContent = score;
    livesEl.textContent = lives;
}

function spawnWord() {
    if (words.length >= MAX_WORDS) return;
    const text = WORD_POOL[Math.floor(Math.random() * WORD_POOL.length)];
    const width = ctx.measureText(text).width + 10;
    const x = Math.random() * (W - width);
    const speed = WORD_MIN_SPEED + Math.random() * (WORD_MAX_SPEED - WORD_MIN_SPEED);
    words.push({ text, x, y: -30, width, speed, caught: false });
}

function handleInput() {
    if (keys.left) playerX -= PLAYER_SPEED;
    if (keys.right) playerX += PLAYER_SPEED;
    playerX = Math.max(0, Math.min(W - PLAYER_W, playerX));
}

function updateWords(delta) {
    for (let i = words.length - 1; i >= 0; i--) {
        const w = words[i];
        w.y += w.speed * (delta / 16); // normalize to 60fps
        // Check catch
        if (!w.caught &&
            w.y + 20 >= playerY &&
            w.y <= playerY + PLAYER_H &&
            w.x + w.width >= playerX &&
            w.x <= playerX + PLAYER_W) {
            w.caught = true;
            score += 10;
            updateUI();
            // remove after brief flash
            setTimeout(() => {
                const idx = words.indexOf(w);
                if (idx > -1) words.splice(idx, 1);
            }, 80);
        }
        // Missed
        if (w.y > H + 30 && !w.caught) {
            lives--;
            updateUI();
            words.splice(i, 1);
            if (lives <= 0) gameOver = true;
        }
    }
}

function draw() {
    // Clear
    ctx.fillStyle = '#0d0d1a';
    ctx.fillRect(0, 0, W, H);

    // Draw player (language model core)
    ctx.fillStyle = '#00ff99';
    ctx.fillRect(playerX, playerY, PLAYER_W, PLAYER_H);
    ctx.fillStyle = '#003322';
    ctx.font = '14px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('LM', playerX + PLAYER_W/2, playerY + 14);

    // Draw words
    ctx.font = WORD_FONT;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    for (const w of words) {
        if (w.caught) {
            // flash effect
            ctx.fillStyle = 'rgba(0,255,153,0.6)';
            ctx.fillRect(w.x, w.y, w.width, 24);
            ctx.fillStyle = '#fff';
        } else {
            ctx.fillStyle = '#ffdd57';
            ctx.fillRect(w.x, w.y, w.width, 24);
            ctx.fillStyle = '#1e1e2f';
        }
        ctx.fillText(w.text, w.x + 5, w.y + 3);
    }

    // Game over overlay
    if (gameOver) {
        ctx.fillStyle = 'rgba(0,0,0,0.75)';
        ctx.fillRect(0, 0, W, H);
        ctx.fillStyle = '#ff4444';
        ctx.font = '48px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('GAME OVER', W/2, H/2 - 20);
        ctx.fillStyle = '#fff';
        ctx.font = '20px sans-serif';
        ctx.fillText(`Final Score: ${score}`, W/2, H/2 + 30);
        ctx.fillText('Press R to restart', W/2, H/2 + 60);
    }
}

function loop(timestamp) {
    const delta = timestamp - (loop.last || timestamp);
    loop.last = timestamp;

    if (!gameOver) {
        handleInput();
        updateWords(delta);
        if (timestamp - lastSpawn > WORD_SPAWN_INTERVAL) {
            spawnWord();
            lastSpawn = timestamp;
        }
    } else {
        // allow restart via R key handled in keydown
    }

    draw();
    requestAnimationFrame(loop);
}

// Keyboard events
window.addEventListener('keydown', e => {
    if (e.code === 'ArrowLeft') keys.left = true;
    if (e.code === 'ArrowRight') keys.right = true;
    if (e.code === 'KeyR' && gameOver) resetGame();
});
window.addEventListener('keyup', e => {
    if (e.code === 'ArrowLeft') keys.left = false;
    if (e.code === 'ArrowRight') keys.right = false;
});

// Touch support for mobile (optional)
canvas.addEventListener('touchstart', e => {
    const rect = canvas.getBoundingClientRect();
    const x = e.touches[0].clientX - rect.left;
    if (x < W/2) keys.left = true; else keys.right = true;
});
canvas.addEventListener('touchend', () => { keys.left = false; keys.right = false; });

// Start
resetGame();
requestAnimationFrame(loop);
