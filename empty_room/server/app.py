"""
Empty Room - Enterprise Configuration Web Application.
Provides secure localhost REST API, live camera stream, face enrollment,
and dashboard interface.
"""

import os
import secrets
import threading
import time
from pathlib import Path
from typing import Generator

import cv2
from flask import Flask, Response, jsonify, render_template, request

from empty_room.camera import CameraService
from empty_room.config import load_config, save_config, update_config
from empty_room.constants import SERVER_PID_FILE, get_cascade_path
from empty_room.detector import get_detector
from empty_room.face_engine import FaceEngine
from empty_room.locker import lock_workstation

# Base template and static paths
TEMPLATE_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"

app = Flask(
    __name__,
    template_folder=str(TEMPLATE_DIR),
    static_folder=str(STATIC_DIR)
)

# Cryptographically strong CSRF token for the session
CSRF_TOKEN = secrets.token_hex(32)

# Global enrollment session lock and state
_enrollment_lock = threading.Lock()
_enrollment_state = {
    "in_progress": False,
    "collected": 0,
    "target": 50,
    "status": "idle",
    "error": None
}


@app.after_request
def set_security_headers(response):
    """Enforce enterprise security headers."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(self)"
    # Localhost CSP
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob:;"
    )
    return response


def _verify_csrf(req) -> bool:
    """Verify CSRF token for state-altering requests."""
    token = req.headers.get("X-CSRF-Token") or req.form.get("csrf_token")
    return bool(token and secrets.compare_digest(token, CSRF_TOKEN))


@app.route("/")
def index():
    """Render the configuration and control dashboard."""
    config = load_config()
    detector = get_detector()
    telemetry = detector.get_telemetry()
    face_info = detector.face_engine.get_info()
    return render_template(
        "index.html",
        config=config,
        telemetry=telemetry,
        face_info=face_info,
        csrf_token=CSRF_TOKEN
    )


@app.route("/api/status", methods=["GET"])
def api_status():
    """Return real-time status and telemetry."""
    detector = get_detector()
    telemetry = detector.get_telemetry()
    face_info = detector.face_engine.get_info()
    return jsonify({
        "success": True,
        "telemetry": telemetry,
        "face": face_info,
        "enrollment": _enrollment_state
    })


@app.route("/api/config", methods=["GET"])
def api_get_config():
    """Return current configuration."""
    return jsonify({"success": True, "config": load_config()})


@app.route("/api/config", methods=["POST"])
def api_save_config():
    """Update system configuration with validation and CSRF verification."""
    if not _verify_csrf(request):
        return jsonify({"success": False, "error": "Invalid or missing CSRF token"}), 403

    payload = request.get_json(silent=True) or request.form.to_dict()
    if not payload:
        return jsonify({"success": False, "error": "Empty payload"}), 400

    updated = update_config(payload)
    detector = get_detector()
    detector.log_event("CONFIG", "Configuration updated via web interface.")
    return jsonify({"success": True, "config": updated})


@app.route("/api/test-lock", methods=["POST"])
def api_test_lock():
    """Trigger a workstation lock for verification."""
    if not _verify_csrf(request):
        return jsonify({"success": False, "error": "Invalid or missing CSRF token"}), 403

    detector = get_detector()
    detector.log_event("ACTION", "Manual lock screen test triggered from configuration UI.")
    success = lock_workstation()
    return jsonify({
        "success": success,
        "message": "Lock screen command dispatched." if success else "Lock command returned failure."
    })


@app.route("/api/face/delete", methods=["POST"])
def api_delete_face():
    """Remove enrolled face biometric model."""
    if not _verify_csrf(request):
        return jsonify({"success": False, "error": "Invalid or missing CSRF token"}), 403

    detector = get_detector()
    success = detector.face_engine.delete_model()
    # Reset strict match to false if no face exists
    update_config({"strict_match": False})
    detector.log_event("BIOMETRIC", "Enrolled face profile was deleted. Reverted to basic presence detection.")
    return jsonify({"success": success, "message": "Face profile removed."})


def _perform_enrollment_task():
    """Background task to collect face samples and train recognizer."""
    global _enrollment_state
    camera = CameraService.get_instance()
    detector = get_detector()
    
    if not camera.is_running:
        camera.start()

    engine = FaceEngine()
    cascade = cv2.CascadeClassifier(get_cascade_path())
    
    samples = []
    target = 50
    detector.log_event("BIOMETRIC", "Starting face enrollment session (target: 50 samples)...")

    start_time = time.time()
    while len(samples) < target and (time.time() - start_time) < 45.0:
        ret, frame = camera.read_frame()
        if not ret or frame is None:
            time.sleep(0.05)
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(60, 60))

        if len(faces) == 1:
            (x, y, w, h) = faces[0]
            face_crop = gray[y:y+h, x:x+w]
            samples.append(face_crop)
            _enrollment_state["collected"] = len(samples)

        time.sleep(0.08)

    if len(samples) >= 20:
        _enrollment_state["status"] = "training"
        detector.log_event("BIOMETRIC", f"Training model with {len(samples)} captured samples...")
        success = engine.train(samples)
        if success:
            _enrollment_state["status"] = "completed"
            detector.face_engine._load_recognizer()
            # Enable strict match now that a face is registered
            update_config({"strict_match": True})
            detector.log_event("BIOMETRIC", "Face training completed successfully! Strict match enabled.")
        else:
            _enrollment_state["status"] = "failed"
            _enrollment_state["error"] = "Training algorithm failed."
            detector.log_event("ERROR", "Model training failed.")
    else:
        _enrollment_state["status"] = "failed"
        _enrollment_state["error"] = f"Insufficient face samples collected ({len(samples)}/20 min)."
        detector.log_event("WARN", "Face enrollment timed out with insufficient samples.")

    time.sleep(2.0)
    with _enrollment_lock:
        _enrollment_state["in_progress"] = False


@app.route("/api/face/enroll/start", methods=["POST"])
def api_start_enrollment():
    """Initiate an automated face enrollment session."""
    if not _verify_csrf(request):
        return jsonify({"success": False, "error": "Invalid or missing CSRF token"}), 403

    global _enrollment_state
    with _enrollment_lock:
        if _enrollment_state["in_progress"]:
            return jsonify({"success": False, "error": "Enrollment already in progress"}), 409

        _enrollment_state = {
            "in_progress": True,
            "collected": 0,
            "target": 50,
            "status": "collecting",
            "error": None
        }

    thread = threading.Thread(target=_perform_enrollment_task, daemon=True)
    thread.start()
    return jsonify({"success": True, "message": "Enrollment started. Look directly at the camera."})


def generate_video_frames() -> Generator[bytes, None, None]:
    """Generate MJPEG video stream with detection overlays."""
    camera = CameraService.get_instance()
    detector = get_detector()
    
    if not camera.is_running:
        camera.start()

    while True:
        ret, frame = camera.read_frame()
        if not ret or frame is None:
            time.sleep(0.05)
            continue

        # Render overlays
        display_frame = frame.copy()
        telemetry = detector.get_telemetry()
        
        # Draw bounding boxes from latest detection
        for item in telemetry.get("latest_faces", []):
            box = item.get("box", [])
            if len(box) == 4:
                x, y, w, h = box
                auth = item.get("authorized", False)
                color = (46, 204, 113) if auth else (52, 152, 219) # Green if authorized, Blue if basic
                label = "AUTHORIZED" if auth else "FACE"
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(display_frame, label, (x, max(15, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Encode frame as JPEG
        encode_success, buffer = cv2.imencode(".jpg", display_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if not encode_success:
            time.sleep(0.02)
            continue

        frame_bytes = buffer.tobytes()
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
        time.sleep(0.04)


@app.route("/video_feed")
def video_feed():
    """Video streaming route for live webcam preview with bounding boxes."""
    return Response(
        generate_video_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/api/logs", methods=["GET"])
def api_logs():
    """Retrieve audit and telemetry logs."""
    detector = get_detector()
    return jsonify({"success": True, "logs": detector.get_events()})


def run_server(host: str = "127.0.0.1", port: int = 5050, open_browser: bool = False):
    """Start the Flask configuration server."""
    # Record PID
    SERVER_PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    SERVER_PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    
    url = f"http://{host}:{port}"
    print(f"\n=======================================================")
    print(f"  Empty Room Configuration Portal")
    print(f"  Local URL: {url}")
    print(f"  Security: Localhost binding only (127.0.0.1)")
    print(f"=======================================================\n")
    
    if open_browser:
        import webbrowser
        def _open():
            time.sleep(1.0)
            webbrowser.open(url)
        threading.Thread(target=_open, daemon=True).start()

    try:
        app.run(host=host, port=port, debug=False, use_reloader=False)
    finally:
        SERVER_PID_FILE.unlink(missing_ok=True)
