/**
 * Empty Room — Enterprise Frontend Controller
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
  const fpsDisplay = document.getElementById("fpsDisplay");
  const faceCountDisplay = document.getElementById("faceCountDisplay");
  const bioBadge = document.getElementById("bioBadge");
  const bioSampleCount = document.getElementById("bioSampleCount");
  const bioEnrollDate = document.getElementById("bioEnrollDate");
  const matchModeDisplay = document.getElementById("matchModeDisplay");
  const logsTableBody = document.getElementById("logsTableBody");
  const toastContainer = document.getElementById("toastContainer");

  // Stream controls
  const liveFeedImg = document.getElementById("liveFeedImg");
  const toggleStreamBtn = document.getElementById("toggleStreamBtn");
  const streamPlaceholder = document.getElementById("streamPlaceholder");
  const resumeStreamBtn = document.getElementById("resumeStreamBtn");
  let isStreamActive = true;

  // Settings form elements
  const settingsForm = document.getElementById("settingsForm");
  const enabledToggle = document.getElementById("enabledToggle");
  const strictMatchToggle = document.getElementById("strictMatchToggle");
  const timeoutSlider = document.getElementById("timeoutSlider");
  const timeoutInput = document.getElementById("timeoutInput");
  const timeoutValText = document.getElementById("timeoutValText");
  const confSlider = document.getElementById("confSlider");
  const confInput = document.getElementById("confInput");
  const confValText = document.getElementById("confValText");

  // Enrollment elements
  const enrollFaceBtn = document.getElementById("enrollFaceBtn");
  const deleteFaceBtn = document.getElementById("deleteFaceBtn");
  const enrollModal = document.getElementById("enrollModal");
  const closeEnrollModalBtn = document.getElementById("closeEnrollModalBtn");
  const cancelEnrollBtn = document.getElementById("cancelEnrollBtn");
  const startCaptureBtn = document.getElementById("startCaptureBtn");
  const enrollSampleBadge = document.getElementById("enrollSampleBadge");
  const enrollProgressBar = document.getElementById("enrollProgressBar");
  const enrollProgressText = document.getElementById("enrollProgressText");

  // Lock test elements
  const testLockBtn = document.getElementById("testLockBtn");
  const lockConfirmModal = document.getElementById("lockConfirmModal");
  const abortLockBtn = document.getElementById("abortLockBtn");
  const instantLockBtn = document.getElementById("instantLockBtn");
  const abortSeconds = document.getElementById("abortSeconds");
  let lockAbortTimer = null;

  // Ring Circumference: 2 * PI * 46 ≈ 289
  const RING_CIRCUMFERENCE = 289;

  // Toast Helper
  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(40px)";
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // Synchronize Range Sliders & Number Inputs
  timeoutSlider.addEventListener("input", (e) => {
    timeoutInput.value = e.target.value;
    timeoutValText.textContent = `${e.target.value} seconds`;
  });
  timeoutInput.addEventListener("input", (e) => {
    timeoutSlider.value = e.target.value;
    timeoutValText.textContent = `${e.target.value} seconds`;
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
      camera_index: parseInt(document.getElementById("camSelect").value, 10)
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
        showToast("Configuration saved successfully.", "success");
      } else {
        showToast(data.error || "Failed to save settings.", "error");
      }
    } catch (err) {
      showToast("Network error while saving settings.", "error");
    }
  });

  // Stream Toggle
  function pauseStream() {
    isStreamActive = false;
    liveFeedImg.src = "";
    liveFeedImg.classList.add("hidden");
    streamPlaceholder.classList.remove("hidden");
  }

  function resumeStream() {
    isStreamActive = true;
    liveFeedImg.src = `/video_feed?t=${Date.now()}`;
    liveFeedImg.classList.remove("hidden");
    streamPlaceholder.classList.add("hidden");
  }

  if (toggleStreamBtn) {
    toggleStreamBtn.addEventListener("click", () => {
      if (isStreamActive) pauseStream();
      else resumeStream();
    });
  }
  if (resumeStreamBtn) {
    resumeStreamBtn.addEventListener("click", resumeStream);
  }

  // Real-Time Telemetry Polling Loop
  async function pollStatus() {
    try {
      const res = await fetch("/api/status");
      if (!res.ok) throw new Error("Status endpoint unavailable");
      const data = await res.json();
      if (!data.success) return;

      const t = data.telemetry;
      const face = data.face;
      const enroll = data.enrollment;

      // Telemetry pill
      if (t.enabled) {
        liveStatusText.textContent = t.state;
      } else {
        liveStatusText.textContent = "DISARMED";
      }

      // State Badge
      stateBadge.className = "status-badge";
      if (!t.enabled) {
        stateBadge.classList.add("status-disabled");
        stateBadge.textContent = "DISARMED";
      } else if (t.state === "PRESENT") {
        stateBadge.classList.add("status-present");
        stateBadge.textContent = "USER PRESENT";
      } else if (t.state === "AWAY" || t.state === "WARNING") {
        stateBadge.classList.add("status-away");
        stateBadge.textContent = "PRESENCE LOST";
      } else if (t.state === "LOCKED") {
        stateBadge.classList.add("status-locked");
        stateBadge.textContent = "SYSTEM LOCKED";
      } else {
        stateBadge.classList.add("status-disabled");
        stateBadge.textContent = t.state;
      }

      // Countdown & Progress Ring
      const secLeft = t.seconds_remaining;
      secondsLeftDisplay.textContent = Math.ceil(secLeft);
      statusTitle.textContent = t.status_message;

      const timeoutVal = Math.max(1, t.timeout);
      const ratio = Math.max(0, Math.min(1, secLeft / timeoutVal));
      const offset = RING_CIRCUMFERENCE * (1 - ratio);
      countdownCircle.style.strokeDashoffset = offset;

      if (ratio > 0.4) {
        countdownCircle.style.stroke = "var(--accent-success)";
      } else if (ratio > 0.15) {
        countdownCircle.style.stroke = "var(--accent-warning)";
      } else {
        countdownCircle.style.stroke = "var(--accent-danger)";
      }

      // FPS & Face count
      fpsDisplay.textContent = `${t.camera_fps || 0} FPS`;
      faceCountDisplay.textContent = t.faces_detected || 0;

      // Biometrics
      bioBadge.textContent = face.trained ? "REGISTERED" : "UNREGISTERED";
      bioBadge.style.color = face.trained ? "var(--accent-success)" : "var(--text-muted)";
      bioSampleCount.textContent = face.samples_count || 0;
      bioEnrollDate.textContent = face.enrolled_at ? face.enrolled_at.slice(0, 10) : "None";
      matchModeDisplay.textContent = t.strict_match ? "Strict (Face ID)" : "Presence (Any)";

      // Enrollment flow updater
      if (enroll && enroll.in_progress) {
        enrollSampleBadge.textContent = `Samples: ${enroll.collected} / ${enroll.target}`;
        const pct = Math.round((enroll.collected / enroll.target) * 100);
        enrollProgressBar.style.width = `${pct}%`;
        enrollProgressText.textContent = `Sampling frames (${pct}%)... Look at camera`;
      } else if (enroll && enroll.status === "completed") {
        enrollProgressBar.style.width = "100%";
        enrollProgressText.textContent = "Face enrolled & trained successfully!";
        setTimeout(() => {
          enrollModal.classList.add("hidden");
        }, 1500);
      }

    } catch (err) {
      liveStatusText.textContent = "OFFLINE";
    }
  }

  // Poll Activity Logs
  async function pollLogs() {
    try {
      const res = await fetch("/api/logs");
      const data = await res.json();
      if (!data.success || !data.logs) return;

      if (data.logs.length === 0) return;

      logsTableBody.innerHTML = data.logs.slice(0, 15).map(log => `
        <tr>
          <td>${log.time}</td>
          <td class="log-cat-${log.category}">${log.category}</td>
          <td>${log.message}</td>
        </tr>
      `).join("");
    } catch (err) {
      // Ignore background log fetch hiccups
    }
  }

  // Poll timers
  setInterval(pollStatus, 700);
  setInterval(pollLogs, 2500);
  pollStatus();
  pollLogs();

  // Face Enrollment Modal Interactions
  if (enrollFaceBtn) {
    enrollFaceBtn.addEventListener("click", () => {
      enrollProgressBar.style.width = "0%";
      enrollProgressText.textContent = "Click 'Start Sampling' to begin biometric capture.";
      enrollSampleBadge.textContent = "Samples: 0 / 50";
      enrollModal.classList.remove("hidden");
    });
  }

  const hideEnrollModal = () => enrollModal.classList.add("hidden");
  if (closeEnrollModalBtn) closeEnrollModalBtn.addEventListener("click", hideEnrollModal);
  if (cancelEnrollBtn) cancelEnrollBtn.addEventListener("click", hideEnrollModal);

  if (startCaptureBtn) {
    startCaptureBtn.addEventListener("click", async () => {
      startCaptureBtn.disabled = true;
      startCaptureBtn.textContent = "Sampling...";
      enrollProgressText.textContent = "Acquiring webcam frames...";

      try {
        const res = await fetch("/api/face/enroll/start", {
          method: "POST",
          headers: { "X-CSRF-Token": csrfToken }
        });
        const data = await res.json();
        if (!data.success) {
          showToast(data.error || "Failed to start enrollment.", "error");
          startCaptureBtn.disabled = false;
          startCaptureBtn.textContent = "Start Sampling";
        }
      } catch (err) {
        showToast("Error starting enrollment session.", "error");
        startCaptureBtn.disabled = false;
        startCaptureBtn.textContent = "Start Sampling";
      }
    });
  }

  // Delete Face Biometric
  if (deleteFaceBtn) {
    deleteFaceBtn.addEventListener("click", async () => {
      if (!confirm("Are you sure you want to delete your enrolled face model? System will switch to standard presence detection.")) {
        return;
      }
      try {
        const res = await fetch("/api/face/delete", {
          method: "POST",
          headers: { "X-CSRF-Token": csrfToken }
        });
        const data = await res.json();
        if (data.success) {
          showToast("Biometric profile removed.", "info");
          setTimeout(() => location.reload(), 800);
        } else {
          showToast("Failed to delete profile.", "error");
        }
      } catch (err) {
        showToast("Network error deleting face profile.", "error");
      }
    });
  }

  // Test Lock Safety Mechanism with 5-Second Cancel Countdown
  if (testLockBtn) {
    testLockBtn.addEventListener("click", () => {
      let countdown = 5;
      abortSeconds.textContent = countdown;
      lockConfirmModal.classList.remove("hidden");

      clearInterval(lockAbortTimer);
      lockAbortTimer = setInterval(async () => {
        countdown--;
        abortSeconds.textContent = countdown;
        if (countdown <= 0) {
          clearInterval(lockAbortTimer);
          lockConfirmModal.classList.add("hidden");
          executeTestLock();
        }
      }, 1000);
    });
  }

  if (abortLockBtn) {
    abortLockBtn.addEventListener("click", () => {
      clearInterval(lockAbortTimer);
      lockConfirmModal.classList.add("hidden");
      showToast("Lock test aborted.", "info");
    });
  }

  if (instantLockBtn) {
    instantLockBtn.addEventListener("click", () => {
      clearInterval(lockAbortTimer);
      lockConfirmModal.classList.add("hidden");
      executeTestLock();
    });
  }

  async function executeTestLock() {
    try {
      const res = await fetch("/api/test-lock", {
        method: "POST",
        headers: { "X-CSRF-Token": csrfToken }
      });
      const data = await res.json();
      if (data.success) {
        showToast("Workstation lock command sent.", "success");
      } else {
        showToast("Failed to lock screen: " + data.message, "error");
      }
    } catch (err) {
      showToast("Error triggering lock test.", "error");
    }
  }

  const refreshLogsBtn = document.getElementById("refreshLogsBtn");
  if (refreshLogsBtn) {
    refreshLogsBtn.addEventListener("click", pollLogs);
  }
});
