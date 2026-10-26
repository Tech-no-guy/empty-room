<p align="center">
  <img src="assets/logo.png" width="120" height="120" alt="Empty Room Logo" style="border-radius: 50%;">
</p>

<h1 align="center">Empty Room</h1>

<p align="center">
  <strong>Smart screen lock that automatically secures your computer when you walk away.</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License"></a>
  <a href="https://nodejs.org/"><img src="https://img.shields.io/badge/npm-ready-green?style=flat-square&logo=npm" alt="npm"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python" alt="Python"></a>
</p>

---

## What is Empty Room?

**Empty Room** is a fast, privacy-first smart screen lock. Using local computer vision, it detects when you step away from your desk and locks your screen before anyone can access your computer.

- **100% On-Device & Private**: Zero data leaves your computer. All vision inference runs entirely on local hardware with no cloud dependencies.
- **Efficient & Lightweight**: Designed for minimal CPU and battery usage.
- **Strict Face Match**: Optionally train the lock to recognize only your face, locking instantly if someone else sits at your desk.
- **Background Shadow Mode**: Run it silently in the background, surviving terminal closures.
- **Cross-Platform**: Native screen locking on Windows, macOS, and Linux.

---

## Installation

Install Empty Room on your system using your preferred method:

### 1. Install via npm (Global CLI)
```bash
npm install -g empty-room
```
*(Or from source: `npm link`)*

### 2. Install via PowerShell (Windows one-liner)
```powershell
irm https://raw.githubusercontent.com/empty-room/empty-room/main/install.ps1 | iex
```
*(Or locally: `iex (Get-Content ./install.ps1 -Raw)`)*

### 3. Install via Shell (Linux & macOS)
```bash
curl -fsSL https://raw.githubusercontent.com/empty-room/empty-room/main/install.sh | bash
```

### 4. Install via Python
```bash
pip install -r requirements.txt
pip install -e .
```

---

## How to Use

After installation, use the `empty-room` command in your terminal:

```bash
# Start screen lock in terminal
empty-room run

# Open web settings and register your face
empty-room configure run

# Run silently in background (survives terminal close)
empty-room shadow on

# Stop background mode
empty-room shadow off

# Stop all running instances
empty-room stop

# Check current status and settings
empty-room status

# View command guide
empty-room help
```

---

## Configuration & Face Registration

Run `empty-room configure run` to open the local dashboard (`http://127.0.0.1:5050`):

- **Face Registration**: Click "Register Face" to quickly enroll your face with live webcam sampling.
- **Strict Match**: Toggle between generic presence detection (any person) or your face only.
- **Lock Delay**: Set how many seconds of absence should trigger the lock.
- **Camera Preview**: Click "Open Camera Preview" whenever you want to test your webcam angle.
- **Test Lock**: Safely verify your screen lock mechanism with a 5-second countdown abort button.

---

## License

Released under the [MIT License](LICENSE).
