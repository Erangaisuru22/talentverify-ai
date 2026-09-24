import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const isWindows = process.platform === 'win32';
const python = path.join(root, 'backend', 'venv', isWindows ? 'Scripts/python.exe' : 'bin/python');

if (!existsSync(python)) {
  console.error(`Backend Python was not found at ${python}`);
  console.error('Create the virtual environment and install backend/requirements.txt first.');
  process.exit(1);
}

async function hasRunningBackend() {
  for (let attempt = 0; attempt < 5; attempt += 1) {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/health', { signal: AbortSignal.timeout(1500) });
      if (response.ok) {
        const health = await response.json();
        if (health.status === 'ok' && health.database === 'connected') return true;
      }
    } catch { /* The backend may still be restarting. */ }
    if (attempt < 4) await new Promise((resolve) => setTimeout(resolve, 400));
  }
  return false;
}

async function hasRunningFrontend() {
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const response = await fetch('http://127.0.0.1:5173', { signal: AbortSignal.timeout(1500) });
      const html = response.ok ? await response.text() : '';
      if (html.includes('<title>TalentVerifyAI</title>') && html.includes('id="root"')) return true;
    } catch { /* Vite may still be starting. */ }
    if (attempt < 2) await new Promise((resolve) => setTimeout(resolve, 300));
  }
  return false;
}

const services = [];

if (await hasRunningBackend()) {
  console.log('TalentVerify backend is already running at http://127.0.0.1:8000; reusing it.');
} else {
  services.push(spawn(python, ['-m', 'uvicorn', 'main:app', '--reload', '--host', '127.0.0.1', '--port', '8000'], {
    cwd: path.join(root, 'backend'),
    stdio: 'inherit',
  }));
}

if (await hasRunningFrontend()) {
  console.log('TalentVerify frontend is already running at http://127.0.0.1:5173; reusing it.');
} else {
  services.push(spawn(isWindows ? (process.env.ComSpec || 'cmd.exe') : 'npm', isWindows ? ['/d', '/s', '/c', 'npm.cmd run dev'] : ['run', 'dev'], {
    cwd: path.join(root, 'frontend'),
    stdio: 'inherit',
  }));
}

if (services.length === 0) {
  console.log('TalentVerifyAI is ready: http://127.0.0.1:5173');
  process.exitCode = 0;
}

let stopping = false;
function stop(exitCode = 0) {
  if (stopping) return;
  stopping = true;
  for (const service of services) {
    if (!service.killed) service.kill(isWindows ? undefined : 'SIGTERM');
  }
  setTimeout(() => process.exit(exitCode), 500);
}

for (const service of services) {
  service.on('error', (error) => {
    console.error(error.message);
    stop(1);
  });
  service.on('exit', (code, signal) => {
    if (!stopping && code !== null) {
      console.error(`A development service stopped with exit code ${code}.`);
      stop(code || 1);
    } else if (!stopping && signal) {
      stop(0);
    }
  });
}

process.on('SIGINT', () => stop(0));
process.on('SIGTERM', () => stop(0));
