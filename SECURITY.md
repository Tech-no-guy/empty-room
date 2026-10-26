# Security Policy

Empty Room is designed with secure, local-first privacy and zero-trust security principles.

## Security Architecture & Guarantees

1. **100% Local Inference**:
   - Zero telemetry, facial vectors, video frames, or metrics leave your local machine.
   - No external APIs, cloud models, or third-party analytical endpoints are ever contacted.

2. **Network Isolation**:
   - The web configuration portal binds strictly to loopback interface `127.0.0.1`.
   - Never binds to `0.0.0.0` or public network adapters.
   - HTTP requests are guarded by cryptographically secure per-session CSRF tokens (`secrets.token_hex(32)`).
   - Strict Content Security Policy (`CSP`), `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`.

3. **Biometric Data Protection**:
   - Enrolled facial models are serialized strictly to protected user directories (`~/.empty-room/face_model.yml`).
   - Facial models and metadata are explicitly excluded in `.gitignore` to prevent accidental public disclosure.

4. **Fail-Safe Integrity**:
   - Configuration reads and writes use atomic file operations (`tempfile` + `os.replace`) with strict type and range validation to prevent file corruption.

## Reporting a Vulnerability

If you discover a security vulnerability within Empty Room, please report it via private email or GitHub Security Advisory. Please do not file public issues for zero-day vulnerabilities.
