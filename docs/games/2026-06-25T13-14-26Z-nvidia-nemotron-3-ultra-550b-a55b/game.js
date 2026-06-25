const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

const W = canvas.width;
const H = canvas.height;

// Game state
let state = 'start'; // start, playing, gameover
let score = 0;
let highScore = 0;
let frame = 0;

// Player
const player = {
    x: W / 2,
    y: H / 2,
    radius: 14,
    speed: 4,
    color: '#00e5ff',
    trail: []
};

// Input
const keys = { ArrowUp: false, ArrowDown: false, ArrowLeft: false, ArrowRight: false, Enter: false, KeyR: false };
window.addEventListener('keydown', e => {
    if (e.code in keys) keys[e.code] = true;
    if (e.code === 'Space') e.preventDefault();
});
window.addEventListener('keyup', e => {
    if (e.code in keys) keys[e.code] = false;
});

// Entities
const tokens = []; // good words
const errors = []; // bad glitches
const particles = [];

function spawnToken() {
    const margin = 30;
    tokens.push({
        x: Math.random() * (W - 2 * margin) + margin,
        y: Math.random() * (H - 2 * margin) + margin,
        radius: 10,
        life: 600, // frames
        word: randomWord(),
        color: '#7fff7f',
        pulse: 0
    });
}
function spawnError() {
    const margin = 30;
    errors.push({
        x: Math.random() * (W - 2 * margin) + margin,
        y: Math.random() * (H - 2 * margin) + margin,
        radius: 12,
        life: 800,
        vx: (Math.random() - 0.5) * 1.5,
        vy: (Math.random() - 0.5) * 1.5,
        color: '#ff4d4d',
        angle: 0
    });
}

const wordPool = ['token', 'weight', 'bias', 'layer', 'epoch', 'batch', 'grad', 'loss', 'embed', 'attn', 'head', 'mask', 'softmax', 'relu', 'norm', 'drop', 'learn', 'model', 'data', 'seq'];
function randomWord() {
    return wordPool[Math.floor(Math.random() * wordPool.length)];
}

function addParticles(x, y, color, count = 12) {
    for (let i = 0; i < count; i++) {
        const angle = Math.random() * Math.PI * 2;
        const speed = 1 + Math.random() * 3;
        particles.push({
            x, y,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed,
            life: 30 + Math.random() * 20,
            maxLife: 50,
            radius: 2 + Math.random() * 3,
            color
        });
    }
}

function resetGame() {
    player.x = W / 2;
    player.y = H / 2;
    player.trail = [];
    tokens.length = 0;
    errors.length = 0;
    particles.length = 0;
    score = 0;
    frame = 0;
    state = 'playing';
    // initial spawns
    for (let i = 0; i < 5; i++) spawnToken();
    for (let i = 0; i < 3; i++) spawnError();
}

function update() {
    if (state !== 'playing') return;

    frame++;

    // Player movement
    let dx = 0, dy = 0;
    if (keys.ArrowLeft) dx -= 1;
    if (keys.ArrowRight) dx += 1;
    if (keys.ArrowUp) dy -= 1;
    if (keys.ArrowDown) dy += 1;
    const len = Math.hypot(dx, dy);
    if (len) { dx /= len; dy /= len; }
    player.x += dx * player.speed;
    player.y += dy * player.speed;

    // Clamp
    player.x = Math.max(player.radius, Math.min(W - player.radius, player.x));
    player.y = Math.max(player.radius, Math.min(H - player.radius, player.y));

    // Trail
    player.trail.unshift({ x: player.x, y: player.y, alpha: 1 });
    if (player.trail.length > 12) player.trail.pop();
    player.trail.forEach(p => p.alpha *= 0.85);

    // Spawn logic
    if (frame % 120 === 0) spawnToken();
    if (frame % 180 === 0) spawnError();

    // Update tokens
    for (let i = tokens.length - 1; i >= 0; i--) {
        const t = tokens[i];
        t.life--;
        t.pulse += 0.1;
        if (t.life <= 0) { tokens.splice(i, 1); continue; }
        // collision
        const dist = Math.hypot(t.x - player.x, t.y - player.y);
        if (dist < t.radius + player.radius) {
            score += 10;
            addParticles(t.x, t.y, t.color, 18);
            tokens.splice(i, 1);
        }
    }

    // Update errors
    for (let i = errors.length - 1; i >= 0; i--) {
        const e = errors[i];
        e.life--;
        e.x += e.vx;
        e.y += e.vy;
        e.angle += 0.05;
        // bounce walls
        if (e.x < e.radius || e.x > W - e.radius) e.vx *= -1;
        if (e.y < e.radius || e.y > H - e.radius) e.vy *= -1;
        if (e.life <= 0) { errors.splice(i, 1); continue; }
        // collision
        const dist = Math.hypot(e.x - player.x, e.y - player.y);
        if (dist < e.radius + player.radius) {
            state = 'gameover';
            if (score > highScore) highScore = score;
            addParticles(player.x, player.y, '#ff4d4d', 30);
        }
    }

    // Particles
    for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.life--;
        p.vx *= 0.98;
        p.vy *= 0.98;
        if (p.life <= 0) particles.splice(i, 1);
    }
}

function draw() {
    // Clear
    ctx.fillStyle = '#16213e';
    ctx.fillRect(0, 0, W, H);

    // Grid background
    ctx.strokeStyle = 'rgba(0,229,255,0.04)';
    ctx.lineWidth = 1;
    for (let x = 0; x <= W; x += 40) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    }
    for (let y = 0; y <= H; y += 40) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }

    // Particles
    particles.forEach(p => {
        const alpha = p.life / p.maxLife;
        ctx.globalAlpha = alpha;
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius * alpha, 0, Math.PI * 2);
        ctx.fill();
    });
    ctx.globalAlpha = 1;

    // Tokens
    tokens.forEach(t => {
        const pulse = Math.sin(t.pulse) * 2;
        ctx.fillStyle = t.color;
        ctx.beginPath();
        ctx.arc(t.x, t.y, t.radius + pulse, 0, Math.PI * 2);
        ctx.fill();
        // word label
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 11px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(t.word, t.x, t.y - t.radius - 6);
    });

    // Errors
    errors.forEach(e => {
        ctx.save();
        ctx.translate(e.x, e.y);
        ctx.rotate(e.angle);
        ctx.fillStyle = e.color;
        // glitch square
        ctx.fillRect(-e.radius, -e.radius, e.radius * 2, e.radius * 2);
        // cross
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(-e.radius, -e.radius); ctx.lineTo(e.radius, e.radius);
        ctx.moveTo(e.radius, -e.radius); ctx.lineTo(-e.radius, e.radius);
        ctx.stroke();
        ctx.restore();
    });

    // Player trail
    player.trail.forEach((pt, idx) => {
        ctx.globalAlpha = pt.alpha * 0.4;
        ctx.fillStyle = player.color;
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, player.radius * (1 - idx / player.trail.length), 0, Math.PI * 2);
        ctx.fill();
    });
    ctx.globalAlpha = 1;

    // Player
    ctx.fillStyle = player.color;
    ctx.shadowColor = player.color;
    ctx.shadowBlur = 15;
    ctx.beginPath();
    ctx.arc(player.x, player.y, player.radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;

    // UI
    ctx.fillStyle = '#e0e0e0';
    ctx.font = '16px monospace';
    ctx.textAlign = 'left';
    ctx.fillText(`SCORE: ${score}`, 16, 28);
    ctx.fillText(`BEST: ${highScore}`, 16, 50);

    // State overlays
    if (state === 'start') {
        drawOverlay('LIVING LANGUAGE MODEL', 'ARROWS to move, collect green tokens, avoid red glitches', 'PRESS ENTER TO START');
    } else if (state === 'gameover') {
        drawOverlay('SYSTEM CRASH', `FINAL SCORE: ${score}`, 'PRESS R TO REBOOT');
    }
}

function drawOverlay(title, subtitle, hint) {
    // dim background
    ctx.fillStyle = 'rgba(22,33,62,0.92)';
    ctx.fillRect(0, 0, W, H);
    ctx.textAlign = 'center';
    ctx.fillStyle = '#00e5ff';
    ctx.font = 'bold 36px monospace';
    ctx.fillText(title, W / 2, H / 2 - 60);
    ctx.fillStyle = '#fff';
    ctx.font = '20px monospace';
    ctx.fillText(subtitle, W / 2, H / 2 - 10);
    ctx.fillStyle = '#7fff7f';
    ctx.font = '16px monospace';
    ctx.fillText(hint, W / 2, H / 2 + 40);
}

function loop() {
    update();
    draw();
    requestAnimationFrame(loop);
}

// Start handling
window.addEventListener('keydown', e => {
    if (state === 'start' && e.code === 'Enter') {
        resetGame();
    }
    if (state === 'gameover' && e.code === 'KeyR') {
        resetGame();
    }
});

resetGame(); // sets state to playing but we want start screen first
state = 'start';
loop();
