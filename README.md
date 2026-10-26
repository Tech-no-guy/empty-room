<p align="center">
  <img src="assets/logo.png" width="140" height="140" alt="Empty Room Logo" style="border-radius: 50%;">
</p>

<h1 align="center">Empty Room</h1>

<p align="center">
  <strong>Enterprise-Grade Workstation Presence Sentinel & Autonomous Screen Locker</strong><br>
  <em>Continuous computer-vision attendance verification with zero cloud reliance.</em>
</p>

<p align="center">
  <a href="https://github.com/empty-room/empty-room/actions"><img src="https://img.shields.io/badge/CI-Passing-10b981?style=flat-square&logo=githubactions" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-3b82f6?style=flat-square" alt="License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python" alt="Python"></a>
  <a href="https://nodejs.org/"><img src="https://img.shields.io/badge/Node.js-%3E%3D16-green?style=flat-square&logo=nodedotjs" alt="Node"></a>
  <a href="SECURITY.md"><img src="https://img.shields.io/badge/Security-Localhost%20Only-emerald?style=flat-square" alt="Security"></a>
</p>

---

## Overview

**Empty Room** is a biometric workstation sentinel designed for defense against physical desk snooping and unattended workstation vulnerabilities. When an authorized user leaves their desk ("empty room"), the sentinel initiates an intelligent countdown and triggers native operating system workstation locks.

```
+--------------------------------------------------------------------------------+
|  Webcam Feed  -->  Haar Face Detection  -->  LBPH Biometric  -->  Auto-Lock   |
|   (Local CV)       (Low CPU Grayscale)        (Strict Match)     (OS Native)   |
+--------------------------------------------------------------------------------+
```

### Key Pillars
- **Zero Cloud Exposure**: 100% of video streaming, facial vector processing, and inference runs strictly on-device. No telemetry or biometric data ever leaves your hardware.
- **Enterprise Web Portal**: Modern dark-mode configuration dashboard at `http://127.0.0.1:5050` with live camera streaming, interactive face enrollment, sensitivity adjustments, and an audit activity trail.
- **Background Shadow Daemon**: Operates silently in the background (`empty-room shadow on`), surviving terminal closures and shell disconnections.
- **Multi-Platform Support**: Native workstation locking on Windows (`user32.LockWorkStation`), macOS (`pmset / CGSession`), and Linux (`loginctl`, `xdg-screensaver`, `gnome`, `sway`, `i3`).

---

## Installation

Empty Room can be installed on any platform using **npm**, **PowerShell (iex)**, or **curl**:

### Option 1: Install via npm (Global CLI)
```bash
npm install -g empty-room
```
*(Or from source clone: `npm link`)*

### Option 2: Install via PowerShell (Windows one-liner)
```powershell
irm https://raw.githubusercontent.com/empty-room/empty-room/main/install.ps1 | iex
```
*(Or locally from repository: `iex (Get-Content ./install.ps1 -Raw)`)*

### Option 3: Install via Shell (Linux & macOS)
```bash
curl -fsSL https://raw.githubusercontent.com/empty-room/empty-room/main/install.sh | bash
```

### Option 4: Install via Python pip
```bash
pip install -r requirements.txt
pip install -e .
```

---

## Command-Line Usage

Once installed, the `empty-room` command is globally accessible in your terminal:

| Command | Description |
| :--- | :--- |
| `empty-room run` | Starts the default presence detection sentinel in the foreground. |
| `empty-room configure run` | Launches the web configuration portal on `http://127.0.0.1:5050` and opens the browser to register/modify faces or adjust settings. |
| `empty-room stop` | Terminates all running Empty Room processes (foreground, shadow, or server). |
| `empty-room shadow on` | Spawns Empty Room in detached background mode (runs forever, surviving terminal close). |
| `empty-room shadow off` | Gracefully halts the background shadow daemon. |
| `empty-room status` | Displays process telemetry, active configuration, face biometrics status, and locker diagnostics. |
| `empty-room help` | Displays the comprehensive CLI reference manual. |

---

## Web Configuration Portal

Run `empty-room configure run` to open the local security console:

- **Live Optical Stream**: High-performance MJPEG stream with real-time detection bounding boxes and FPS telemetry.
- **Biometric Enrollment Wizard**: Interactive 50-sample progressive face enrollment right from the browser. Supports face retraining and profile deletion.
- **Strict Match Mode**: Choose between generic human presence detection or strict biometric authentication (locks workstation if anyone other than the registered user sits down).
- **Lock Delay Slider**: Configure the timeout countdown (from 3 to 180 seconds).
- **Test Lock with Safety Abort**: Test native lock screen execution with a 5-second countdown abort window.
- **Audit Activity Trail**: Real-time log of presence changes, timeout events, and lock executions.

---

## Security & Architecture Standards

- **Localhost Isolation**: The configuration web server binds strictly to `127.0.0.1`.
- **CSRF Defense**: All state-modifying requests (`POST /api/config`, `POST /api/face/enroll/start`, `POST /api/test-lock`) require cryptographically generated per-session CSRF tokens (`secrets.token_hex(32)`).
- **Strict Headers**: Enforces `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`.
- **Atomic Persistence**: Configurations are persisted through atomic temporary file swaps (`tempfile` + `os.replace`), preventing corrupt configurations from system power drops.
- **Biometric Privacy**: Face biometric models (`face_model.yml`) are ignored by Git via `.gitignore` to prevent committing biometrics to public repositories.

---

## Verification & Automated Testing

Empty Room includes a comprehensive test suite covering configuration validation, biometric pipelines, locker diagnostics, and CLI routing:

```bash
# Run tests with Python unittest
python -m unittest discover -s tests -v

# Or run with npm
npm test
```

---

## License

Released under the [MIT License](LICENSE). Copyright © 2026 Empty Room Contributors.
