#!/usr/bin/env node

/**
 * Empty Room — Global Node.js CLI Wrapper
 * Enables global terminal execution via `npm install -g empty-room`
 */

const { spawn, spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

// Candidate python paths in priority order
function resolvePython() {
  const isWindows = process.platform === 'win32';
  const realScript = fs.existsSync(__filename) ? fs.realpathSync(__filename) : __filename;
  const rootDir = path.resolve(path.dirname(realScript), '..');
  const userHome = os.homedir();

  const candidates = [
    // 1. Project local virtual environment
    isWindows ? path.join(rootDir, '.venv', 'Scripts', 'python.exe') : path.join(rootDir, '.venv', 'bin', 'python'),
    // 2. Global user home virtual environment
    isWindows ? path.join(userHome, '.empty-room', 'venv', 'Scripts', 'python.exe') : path.join(userHome, '.empty-room', 'venv', 'bin', 'python'),
    // 3. Virtualenv in VIRTUAL_ENV env var
    process.env.VIRTUAL_ENV ? (isWindows ? path.join(process.env.VIRTUAL_ENV, 'Scripts', 'python.exe') : path.join(process.env.VIRTUAL_ENV, 'bin', 'python')) : null,
    // 4. System python
    'python3',
    'python'
  ].filter(Boolean);

  let fallback = 'python';

  for (const candidate of candidates) {
    try {
      if (candidate.includes(path.sep) && !fs.existsSync(candidate)) {
        continue;
      }
      // Check if this python has opencv and flask installed
      const test = spawnSync(candidate, ['-c', 'import cv2, flask, numpy; print("READY")'], {
        encoding: 'utf-8',
        stdio: ['ignore', 'pipe', 'ignore']
      });
      if (test.status === 0 && test.stdout.trim() === 'READY') {
        return candidate;
      }
      // If basic python3 works, keep as fallback
      const verTest = spawnSync(candidate, ['-c', 'import sys; print(sys.version_info[0])'], {
        encoding: 'utf-8',
        stdio: ['ignore', 'pipe', 'ignore']
      });
      if (verTest.status === 0 && verTest.stdout.trim() === '3' && fallback === 'python') {
        fallback = candidate;
      }
    } catch (e) {
      // Continue searching
    }
  }

  // If no Python environment has dependencies installed, attempt auto-bootstrap into ~/.empty-room/venv
  const defaultVenvDir = path.join(userHome, '.empty-room', 'venv');
  const defaultVenvPython = isWindows
    ? path.join(defaultVenvDir, 'Scripts', 'python.exe')
    : path.join(defaultVenvDir, 'bin', 'python');
  const defaultVenvPip = isWindows
    ? path.join(defaultVenvDir, 'Scripts', 'pip.exe')
    : path.join(defaultVenvDir, 'bin', 'pip');

  if (fallback) {
    try {
      console.log('\x1b[36m[Empty Room] Python vision dependencies not found. Setting up environment...\x1b[0m');
      if (!fs.existsSync(defaultVenvPython)) {
        console.log(`[Empty Room] Creating virtual environment in ${defaultVenvDir}...`);
        fs.mkdirSync(path.join(userHome, '.empty-room'), { recursive: true });
        spawnSync(fallback, ['-m', 'venv', defaultVenvDir], { stdio: 'inherit' });
      }
      if (fs.existsSync(defaultVenvPython)) {
        console.log('[Empty Room] Installing opencv-contrib-python, flask, and numpy (~30s)...');
        const reqPath = path.join(rootDir, 'requirements.txt');
        const pipArgs = fs.existsSync(reqPath)
          ? ['install', '-r', reqPath]
          : ['install', 'opencv-contrib-python>=4.8.0', 'numpy>=1.24.0', 'Flask>=3.0.0'];
        spawnSync(defaultVenvPip, pipArgs, { stdio: 'inherit' });

        const recheck = spawnSync(defaultVenvPython, ['-c', 'import cv2, flask, numpy; print("READY")'], {
          encoding: 'utf-8',
          stdio: ['ignore', 'pipe', 'ignore']
        });
        if (recheck.status === 0 && recheck.stdout.trim() === 'READY') {
          console.log('\x1b[32m[Empty Room] Environment initialized successfully!\x1b[0m\n');
          return defaultVenvPython;
        }
      }
    } catch (e) {
      console.warn('\x1b[33m[Empty Room] Auto-setup notice:\x1b[0m', e.message);
    }
  }

  return fallback;
}

function main() {
  const realScript = fs.existsSync(__filename) ? fs.realpathSync(__filename) : __filename;
  const rootDir = path.resolve(path.dirname(realScript), '..');
  const pythonPath = resolvePython();
  const args = process.argv.slice(2);

  const env = Object.assign({}, process.env, {
    PYTHONPATH: [rootDir, process.env.PYTHONPATH || ''].filter(Boolean).join(path.delimiter)
  });

  const isTest = args[0] === 'test';
  const pyArgs = isTest
    ? ['-m', 'unittest', 'discover', '-s', path.join(rootDir, 'tests'), ...args.slice(1)]
    : ['-m', 'core.cli', ...args];

  const child = spawn(pythonPath, pyArgs, {
    stdio: 'inherit',
    env: env,
    cwd: process.cwd()
  });

  child.on('error', (err) => {
    if (err.code === 'ENOENT') {
      console.error('\x1b[31m[ERROR] Python 3 was not found on your system path.\x1b[0m');
      console.error('Please install Python 3.9+ from https://www.python.org/ or run the installer script.');
    } else {
      console.error('\x1b[31m[ERROR] Failed to launch empty-room:\x1b[0m', err.message);
    }
    process.exit(1);
  });

  child.on('close', (code) => {
    process.exit(code || 0);
  });

  // Forward termination signals
  ['SIGINT', 'SIGTERM'].forEach((signal) => {
    process.on(signal, () => {
      if (child && !child.killed) {
        child.kill(signal);
      }
    });
  });
}

main();
