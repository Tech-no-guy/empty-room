/**
 * Empty Room — Frontend Client Controller (Light Theme & Efficient)
 */

document.addEventListener("DOMContentLoaded", () => {
  const csrfToken = document.body.dataset.csrf || "";

  // Elements
  const livePill = document.getElementById("livePill");
  const liveStatusText = document.getElementById("liveStatusText");
  const stateBadge = document.getElementById("stateBadge");
  const secondsLeftDisplay = document.getElementById("secondsLeftDisplay");
  const countdownCircle = document.getElementById("countdownCircle");
  const statusTitle = document.getElementById("statusTitle");
  const statusSubtitle = document.getElementById("statusSubtitle");
  const faceCountDisplay = document.getElementById("faceCountDisplay");
  const timeAwayDisplay = document.getElementById("timeAwayDisplay");

  // Biometrics
  const bioBadge = document.getElementById("bioBadge");
  const bioSampleCount = document.getElementById("bioSampleCount");
  const bioEnrollDate = document.getElementById("bioEnrollDate");
  const matchModeDisplay = document.getElementById("matchModeDisplay");
  const enrollFaceBtn = document.getElementById("enrollFaceBtn");
  const deleteFaceBtn = document.getElementById("deleteFaceBtn");

  // Camera preview controls (Off by default for efficiency)
  const toggleCameraBtn = document.getElementById("toggleCameraBtn");
  const cameraBtnText = document.getElementById("cameraBtnText");
  const cameraPreviewBox = document.getElementById("cameraPreviewBox");
  const liveVideoImg = document.getElementById("liveVideoImg");
  const videoFpsTag = document.getElementById("videoFpsTag");
  let isCameraOpen = false;

  // Settings
  const settingsForm = document.getElementById("settingsForm");
  const enabledToggle = document.getElementById("enabledToggle");
  const strictMatchToggle = document.getElementById("strictMatchToggle");
  const timeoutSlider = document.getElementById("timeoutSlider");
  const timeoutInput = document.getElementById("timeoutInput");
  const timeoutValText = document.getElementById("timeoutValText");
  const confSlider = document.getElementById("confSlider");
  const confInput = document.getElementById("confInput");
  const confValText = document.getElementById("confValText");
  const camSelect = document.getElementById("camSelect");

  // Logs
  const logsTableBody = document.getElementById("logsTableBody");
  const refreshLogsBtn = document.getElementById("refreshLogsBtn");
  const toastContainer = document.getElementById("toastContainer");

  // Enrollment modal
  const enrollModal = document.getElementById("enrollModal");
  const closeEnrollModalBtn = document.getElementById("closeEnrollModalBtn");
  const cancelEnrollBtn = document.getElementById("cancelEnrollBtn");
  const startCaptureBtn = document.getElementById("startCaptureBtn");
  const enrollSampleBadge = document.getElementById("enrollSampleBadge");
  const enrollProgressBar = document.getElementById("enrollProgressBar");
  const enrollProgressText = document.getElementById("enrollProgressText");
  const enrollVideoImg = document.getElementById("enrollVideoImg");

  // Lock test modal
  const testLockBtn = document.getElementById("testLockBtn");
  const lockConfirmModal = document.getElementById("lockConfirmModal");
  const abortLockBtn = document.getElementById("abortLockBtn");
  const instantLockBtn = document.getElementById("instantLockBtn");
  const abortSeconds = document.getElementById("abortSeconds");
  let lockAbortTimer = null;

  // Circumference: 2 * PI * 36 ≈ 226
  const RING_CIRCUMFERENCE = 226;

  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      setTimeout(() => toast.remove(), 250);
    }, 3000);
  }

  // Camera preview toggle (On-demand)
  if (toggleCameraBtn) {
    toggleCameraBtn.addEventListener("click", () => {
      isCameraOpen = !isCameraOpen;
      if (isCameraOpen) {
        cameraPreviewBox.classList.remove("hidden");
        liveVideoImg.src = `/video_feed?t=${Date.now()}`;
        cameraBtnText.textContent = "Close Preview";
      } else {
        cameraPreviewBox.classList.add("hidden");
        liveVideoImg.src = "";
        cameraBtnText.textContent = "Open Camera Preview";
      }
    });
  }

  // Sliders sync
  timeoutSlider.addEventListener("input", (e) => {
    timeoutInput.value = e.target.value;
    timeoutValText.textContent = `${e.target.value}s`;
  });
  timeoutInput.addEventListener("input", (e) => {
    timeoutSlider.value = e.target.value;
    timeoutValText.textContent = `${e.target.value}s`;
  });

  confSlider.addEventListener("input", (e) => {
    confInput.value = e.target.value;
    confValText.textContent = e.target.value;
  });
  confInput.addEventListener("input", (e) => {
    confSlider.value = e.target.value;
    confValText.textContent = e.target.value;
  });

  // Settings Save
  settingsForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      enabled: enabledToggle.checked,
      strict_match: strictMatchToggle.checked,
      timeout: parseInt(timeoutInput.value, 10),
      confidence_threshold: parseInt(confInput.value, 10),
      camera_index: parseInt(camSelect.value, 10)
    };

    try {
      const res = await fetch("/api/config", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken
        },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        showToast("Settings saved.", "success");
      } else {
        showToast(data.error || "Failed to save settings.", "error");
      }
    } catch (err) {
      showToast("Network error.", "error");
    }
  });

  // Real telemetry loop
  async function pollStatus() {
    try {
      const res = await fetch("/api/status");
      if (!res.ok) throw new Error("Offline");
      const data = await res.json();
      if (!data.success) return;

      const t = data.telemetry;
      const face = data.face;
      const enroll = data.enrollment;

      liveStatusText.textContent = t.enabled ? t.state : "DISARMED";

      // Badge
      stateBadge.className = "status-badge";
      if (!t.enabled) {
        stateBadge.classList.add("status-disabled");
        stateBadge.textContent = "DISARMED";
      } else if (t.state === "PRESENT") {
        stateBadge.classList.add("status-present");
        stateBadge.textContent = "USER PRESENT";
      } else if (t.state === "AWAY" || t.state === "WARNING") {
        stateBadge.classList.add("status-away");
        stateBadge.textContent = "AWAY";
      } else if (t.state === "LOCKED") {
        stateBadge.classList.add("status-locked");
        stateBadge.textContent = "LOCKED";
      } else {
        stateBadge.classList.add("status-disabled");
        stateBadge.textContent = t.state;
      }

      // Countdown
      const secLeft = t.seconds_remaining;
      secondsLeftDisplay.textContent = Math.ceil(secLeft);
      statusTitle.textContent = t.status_message;
      faceCountDisplay.textContent = t.faces_detected || 0;
      timeAwayDisplay.textContent = `${t.time_away || 0}s`;

      if (isCameraOpen && videoFpsTag) {
        videoFpsTag.textContent = `${t.camera_fps || 0} FPS`;
      }

      const timeoutVal = Math.max(1, t.timeout);
      const ratio = Math.max(0, Math.min(1, secLeft / timeoutVal));
      const offset = RING_CIRCUMFERENCE * (1 - ratio);
      countdownCircle.style.strokeDashoffset = offset;

      if (ratio > 0.4) {
        countdownCircle.style.stroke = "var(--color-success)";
      } else if (ratio > 0.15) {
        countdownCircle.style.stroke = "var(--color-warning)";
      } else {
        countdownCircle.style.stroke = "var(--color-danger)";
      }

      // Real User Biometric Data (No demo or fake data)
      if (face && face.trained) {
        bioBadge.textContent = "Registered";
        bioBadge.style.color = "var(--color-success)";
        bioSampleCount.textContent = face.samples_count || 0;
        bioEnrollDate.textContent = face.enrolled_at ? face.enrolled_at.slice(0, 10) : "Registered";
        matchModeDisplay.textContent = t.strict_match ? "Registered Face" : "Any Person";
        if (deleteFaceBtn) deleteFaceBtn.classList.remove("hidden");
      } else {
        bioBadge.textContent = "No Face Registered";
        bioBadge.style.color = "var(--text-muted)";
        bioSampleCount.textContent = "0";
        bioEnrollDate.textContent = "None";
        matchModeDisplay.textContent = "Any Person";
        if (deleteFaceBtn) deleteFaceBtn.classList.add("hidden");
      }

      // Enrollment Wizard progress
      if (enroll && enroll.in_progress) {
        enrollSampleBadge.textContent = `${enroll.collected} / ${enroll.target} samples`;
        const pct = Math.round((enroll.collected / enroll.target) * 100);
        enrollProgressBar.style.width = `${pct}%`;
        enrollProgressText.textContent = `Sampling (${pct}%)... Look at camera`;
      } else if (enroll && enroll.status === "completed") {
        enrollProgressBar.style.width = "100%";
        enrollProgressText.textContent = "Face registered successfully!";
        setTimeout(() => {
          hideEnroll();
          startCaptureBtn.disabled = false;
          startCaptureBtn.textContent = "Start Registration";
        }, 1200);
      } else if (enroll && enroll.status === "failed") {
        enrollProgressText.textContent = enroll.error || "Enrollment failed. Try again.";
        startCaptureBtn.disabled = false;
        startCaptureBtn.textContent = "Retry Registration";
      }
    } catch (e) {
      liveStatusText.textContent = "OFFLINE";
    }
  }

  // Poll Activity Logs (Real events only)
  async function pollLogs() {
    try {
      const res = await fetch("/api/logs");
      const data = await res.json();
      if (!data.success || !data.logs || data.logs.length === 0) return;

      logsTableBody.innerHTML = data.logs.slice(0, 10).map(log => `
        <tr>
          <td>${log.time}</td>
          <td class="log-cat-${log.category}">${log.category}</td>
          <td>${log.message}</td>
        </tr>
      `).join("");
    } catch (e) {}
  }

  // Poll every 1s
  setInterval(pollStatus, 1000);
  setInterval(pollLogs, 3000);
  pollStatus();
  pollLogs();

  // Face Enrollment
  if (enrollFaceBtn) {
    enrollFaceBtn.addEventListener("click", () => {
      enrollProgressBar.style.width = "0%";
      enrollProgressText.textContent = "Click 'Start Registration' when ready.";
      enrollSampleBadge.textContent = "0 / 50 samples";
      if (enrollVideoImg) {
        enrollVideoImg.src = `/video_feed?t=${Date.now()}`;
      }
      enrollModal.classList.remove("hidden");
    });
  }

  const hideEnroll = () => {
    enrollModal.classList.add("hidden");
    if (enrollVideoImg) {
      enrollVideoImg.src = "";
    }
  };
  if (closeEnrollModalBtn) closeEnrollModalBtn.addEventListener("click", hideEnroll);
  if (cancelEnrollBtn) cancelEnrollBtn.addEventListener("click", hideEnroll);

  if (startCaptureBtn) {
    startCaptureBtn.addEventListener("click", async () => {
      startCaptureBtn.disabled = true;
      startCaptureBtn.textContent = "Capturing...";
      enrollProgressText.textContent = "Connecting camera...";

      try {
        const res = await fetch("/api/face/enroll/start", {
          method: "POST",
          headers: { "X-CSRF-Token": csrfToken }
        });
        const data = await res.json();
        if (!data.success) {
          showToast(data.error || "Failed to start capture.", "error");
          startCaptureBtn.disabled = false;
          startCaptureBtn.textContent = "Start Registration";
        }
      } catch (e) {
        showToast("Error starting capture.", "error");
        startCaptureBtn.disabled = false;
        startCaptureBtn.textContent = "Start Registration";
      }
    });
  }

  // Delete Face
  if (deleteFaceBtn) {
    deleteFaceBtn.addEventListener("click", async () => {
      if (!confirm("Delete your registered face profile? The lock will use standard presence detection.")) {
        return;
      }
      try {
        const res = await fetch("/api/face/delete", {
          method: "POST",
          headers: { "X-CSRF-Token": csrfToken }
        });
        const data = await res.json();
        if (data.success) {
          showToast("Face profile removed.", "info");
          setTimeout(() => location.reload(), 600);
        }
      } catch (e) {
        showToast("Error deleting profile.", "error");
      }
    });
  }

  // Test Lock
  if (testLockBtn) {
    testLockBtn.addEventListener("click", () => {
      let count = 5;
      abortSeconds.textContent = count;
      lockConfirmModal.classList.remove("hidden");

      clearInterval(lockAbortTimer);
      lockAbortTimer = setInterval(() => {
        count--;
        abortSeconds.textContent = count;
        if (count <= 0) {
          clearInterval(lockAbortTimer);
          lockConfirmModal.classList.add("hidden");
          executeLock();
        }
      }, 1000);
    });
  }

  if (abortLockBtn) {
    abortLockBtn.addEventListener("click", () => {
      clearInterval(lockAbortTimer);
      lockConfirmModal.classList.add("hidden");
      showToast("Test cancelled.", "info");
    });
  }

  if (instantLockBtn) {
    instantLockBtn.addEventListener("click", () => {
      clearInterval(lockAbortTimer);
      lockConfirmModal.classList.add("hidden");
      executeLock();
    });
  }

  async function executeLock() {
    try {
      const res = await fetch("/api/test-lock", {
        method: "POST",
        headers: { "X-CSRF-Token": csrfToken }
      });
      const data = await res.json();
      if (data.success) {
        showToast("Screen locked.", "success");
      } else {
        showToast("Lock command failed: " + data.message, "error");
      }
    } catch (e) {
      showToast("Error triggering lock.", "error");
    }
  }

  if (refreshLogsBtn) refreshLogsBtn.addEventListener("click", pollLogs);
});
