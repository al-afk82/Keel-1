const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const crypto = require('crypto');

const PORT = 3000;
const PASSWORD = '960605115086';
const sessions = new Set();
let claudeSessionActive = false;

// Where the live drift chain lives. The website fires run_chain.py here after an
// answer is produced, so every turn on the site goes through the same agents.
const CHAIN_CWD = '/root/hackathon-drift-agent/coordinator';
const CHAIN_TIMEOUT_MS = 150000;

const app = express();
const server = http.createServer(app);

app.use(express.urlencoded({ extended: false }));
app.use(express.json());

function parseCookies(h) {
  const c = {};
  if (!h) return c;
  h.split(';').forEach(p => { const x = p.trim().split('='); c[x[0]] = x[1]; });
  return c;
}

function authed(req) {
  return sessions.has(parseCookies(req.headers.cookie).session);
}

app.get('/login', (req, res) => {
  const err = req.query.e ? '<p class="err">Incorrect password.</p>' : '';
  res.send(`<!DOCTYPE html><html><head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <link rel="manifest" href="/manifest.json">
  <title>Malec Systems</title>
  <style>
    *{margin:0;padding:0;box-sizing:border-box}
    html,body{height:100%;background:#ffffff;font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',sans-serif}
    body{display:flex;align-items:center;justify-content:center}
    .wrap{width:100%;max-width:320px;padding:0 32px}
    .wordmark{font-size:10px;letter-spacing:6px;color:#000000;text-transform:uppercase;font-weight:600;display:block;margin-bottom:56px}
    .hint{font-size:11px;letter-spacing:2px;color:#aaaaaa;text-transform:uppercase;margin-bottom:20px;display:block}
    input{width:100%;border:none;border-bottom:1.5px solid #000000;padding:12px 0;font-size:16px;font-family:inherit;outline:none;background:transparent;color:#000000;border-radius:0}
    input::placeholder{color:#cccccc}
    .btn{display:block;width:100%;margin-top:24px;background:#000000;color:#ffffff;border:none;padding:15px;font-size:11px;letter-spacing:3px;text-transform:uppercase;font-family:inherit;font-weight:500;cursor:pointer;border-radius:0}
    .btn:active{background:#333333}
    .err{font-size:11px;color:#cc0000;margin-top:16px;letter-spacing:0.5px;display:block}
  </style></head><body>
  <div class="wrap">
    <span class="wordmark">Malec Systems</span>
    <span class="hint">your best friend</span>
    <form method="POST" action="/login">
      <input type="password" name="password" placeholder="Password" autofocus>
      <button class="btn" type="submit">Enter</button>
    </form>
    ${err}
  </div></body></html>`);
});

app.post('/login', (req, res) => {
  if (req.body.password === PASSWORD) {
    const token = crypto.randomBytes(32).toString('hex');
    sessions.add(token);
    res.setHeader('Set-Cookie', 'session=' + token + '; Path=/; HttpOnly');
    res.redirect('/');
  } else {
    res.redirect('/login?e=1');
  }
});

app.use((req, res, next) => {
  if (!authed(req)) return res.redirect('/login');
  next();
});

app.use((req, res, next) => {
  res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
  next();
});

app.use(express.static(path.join(__dirname, 'public')));

app.post('/chat', (req, res) => {
  const { message, reset } = req.body;
  if (!message || !message.trim()) return res.status(400).json({ error: 'empty message' });

  if (reset) claudeSessionActive = false;

  const args = claudeSessionActive ? ['--continue', '-p', message] : ['-p', message];
  claudeSessionActive = true;

  const child = spawn('/usr/bin/claude', args, {
    cwd: '/root/alecs-echosystem',
    env: process.env
  });

  let output = '';
  let errOutput = '';

  child.stdout.on('data', d => { output += d.toString(); });
  child.stderr.on('data', d => { errOutput += d.toString(); });

  child.on('close', code => {
    if (code !== 0) {
      claudeSessionActive = false;
      return res.status(500).json({ error: errOutput || 'claude exited with code ' + code });
    }
    res.json({ response: output.trim() });
  });

  child.on('error', err => {
    claudeSessionActive = false;
    res.status(500).json({ error: err.message });
  });
});

// Drift check. The page calls this once an answer is on screen, passing the same
// message and the answer it received. It runs the live agent chain on that pair
// and returns one rolled up verdict plus every agent's finding for the drill down.
app.post('/drift', (req, res) => {
  const { message, response } = req.body;
  if (!message || !response) return res.status(400).json({ error: 'message and response required' });

  const chain = spawn('python3', ['run_chain.py', '--json', message, response], {
    cwd: CHAIN_CWD,
    env: process.env
  });

  let out = '';
  const killer = setTimeout(() => chain.kill('SIGKILL'), CHAIN_TIMEOUT_MS);

  chain.stdout.on('data', d => { out += d.toString(); });

  chain.on('close', () => {
    clearTimeout(killer);
    const last = out.trim().split('\n').filter(Boolean).pop() || '';
    try {
      res.json({ drift: JSON.parse(last) });
    } catch (e) {
      res.json({ drift: null, error: 'chain produced no verdict' });
    }
  });

  chain.on('error', err => {
    clearTimeout(killer);
    res.json({ drift: null, error: err.message });
  });
});

// Live drift stream. Same chain, but the page reads it as it runs — one ndjson
// line per agent the moment it resolves, then a done line. This is what draws
// the pipeline live under the answer on the input page itself.
app.post('/drift/stream', (req, res) => {
  const { message, response } = req.body;
  if (!message || !response) return res.status(400).json({ error: 'message and response required' });

  res.setHeader('Content-Type', 'application/x-ndjson');
  res.setHeader('Cache-Control', 'no-cache, no-transform');
  res.setHeader('X-Accel-Buffering', 'no');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  const chain = spawn('python3', ['-u', 'run_chain.py', '--stream', message, response], {
    cwd: CHAIN_CWD,
    env: process.env
  });

  let finished = false;
  const killer = setTimeout(() => chain.kill('SIGKILL'), CHAIN_TIMEOUT_MS);

  chain.stdout.on('data', d => res.write(d));

  chain.on('close', () => { finished = true; clearTimeout(killer); res.end(); });
  chain.on('error', err => {
    finished = true;
    clearTimeout(killer);
    try { res.write(JSON.stringify({ event: 'error', data: { message: err.message } }) + '\n'); } catch (e) {}
    res.end();
  });

  // Only kill the chain on a genuine client disconnect, and only while it is
  // still running. req 'close' fires once the request body is consumed, which is
  // not a disconnect — using that would kill every run before the first agent.
  res.on('close', () => { if (!finished) { clearTimeout(killer); chain.kill('SIGKILL'); } });
});

app.post('/reset', (req, res) => {
  claudeSessionActive = false;
  res.json({ ok: true });
});

server.listen(PORT, () => console.log('running on port ' + PORT));
