const video = document.querySelector("#camera-video");
const overlay = document.querySelector("#camera-overlay");
const startButton = document.querySelector("#camera-start");
const stopButton = document.querySelector("#camera-stop");
const status = document.querySelector("#camera-status");

if (video && overlay && startButton && stopButton && status) {
	const context = overlay.getContext("2d");
	const capture = document.createElement("canvas");
	let stream = null;
	let timer = null;
	let requestInFlight = false;

	function setStatus(message, state = "") {
		status.textContent = message;
		status.className = `camera-status ${state}`;
	}

	function stopCamera() {
		if (timer) window.clearInterval(timer);
		timer = null;
		if (stream) stream.getTracks().forEach((track) => track.stop());
		stream = null;
		video.srcObject = null;
		context.clearRect(0, 0, overlay.width, overlay.height);
		startButton.disabled = false;
		stopButton.disabled = true;
		setStatus("Arrêtée");
	}

	function drawDetections(detections) {
		overlay.width = video.videoWidth;
		overlay.height = video.videoHeight;
		context.clearRect(0, 0, overlay.width, overlay.height);
		context.font = "600 16px Georgia";
		detections.forEach((detection) => {
			const [x1, y1, x2, y2] = detection.bbox;
			const known = Boolean(detection.student_id);
			const label = detection.full_name || `Inconnu (${detection.score.toFixed(2)})`;
			context.strokeStyle = known ? "#16805c" : "#c23b32";
			context.lineWidth = 3;
			context.strokeRect(x1, y1, x2 - x1, y2 - y1);
			context.fillStyle = context.strokeStyle;
			context.fillText(label, x1, Math.max(20, y1 - 8));
		});
		setStatus(
			detections.length ? `${detections.length} visage(s) détecté(s)` : "Aucun visage",
			detections.length ? "active" : "",
		);
	}

	async function detectFrame() {
		if (requestInFlight || video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) return;
		requestInFlight = true;
		capture.width = video.videoWidth;
		capture.height = video.videoHeight;
		const captureContext = capture.getContext("2d");
		captureContext.drawImage(video, 0, 0, capture.width, capture.height);
		const sample = captureContext.getImageData(
			Math.floor(capture.width / 2), Math.floor(capture.height / 2), 1, 1,
		).data;
		if (sample[1] > 90 && sample[1] > sample[0] * 1.8 && sample[1] > sample[2] * 1.8) {
			setStatus("Flux caméra anormal: essayez une autre caméra ou une photo", "error");
			requestInFlight = false;
			return;
		}
		try {
			const response = await fetch("/attendance/detect", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ image: capture.toDataURL("image/jpeg", 0.82) }),
			});
			const result = await response.json();
			if (!response.ok) throw new Error(result.detail || "Erreur de détection");
			drawDetections(result.detections);
		} catch (error) {
			setStatus(error.message, "error");
		} finally {
			requestInFlight = false;
		}
	}

	async function startCamera() {
		if (!navigator.mediaDevices?.getUserMedia) {
			setStatus("Caméra indisponible dans ce navigateur", "error");
			return;
		}
		try {
			setStatus("Ouverture de la caméra...");
			stream = await navigator.mediaDevices.getUserMedia({
				video: { width: { ideal: 640 }, height: { ideal: 480 } },
				audio: false,
			});
			video.srcObject = stream;
			await video.play();
			startButton.disabled = true;
			stopButton.disabled = false;
			timer = window.setInterval(detectFrame, 700);
			await detectFrame();
		} catch (error) {
			stopCamera();
			setStatus(`Caméra refusée ou inaccessible: ${error.message}`, "error");
		}
	}

	startButton.addEventListener("click", startCamera);
	window.setTimeout(startCamera, 250);

	stopButton.addEventListener("click", stopCamera);
}

const registrationVideo = document.querySelector("#registration-video");
const registrationCanvas = document.querySelector("#registration-canvas");
const registrationForm = document.querySelector("#registration-form");
const registrationCapture = document.querySelector("#registration-capture");
const registrationSubmit = document.querySelector("#registration-submit");
const registrationStatus = document.querySelector("#registration-status");
const registrationFiles = document.querySelector("#registration-files");

if (
	registrationVideo && registrationCanvas && registrationForm &&
	registrationCapture && registrationSubmit && registrationStatus
) {
	const captures = [];
	let registrationStream = null;

	function setRegistrationStatus(message, state = "") {
		registrationStatus.textContent = message;
		registrationStatus.className = `camera-status ${state}`;
	}

	async function openRegistrationCamera() {
		if (!navigator.mediaDevices?.getUserMedia) {
			setRegistrationStatus("Caméra indisponible", "error");
			return;
		}
		try {
			registrationStream = await navigator.mediaDevices.getUserMedia({
				video: { width: { ideal: 640 }, height: { ideal: 480 } },
				audio: false,
			});
			registrationVideo.srcObject = registrationStream;
			await registrationVideo.play();
			registrationCapture.disabled = false;
			setRegistrationStatus("Cadrez un seul visage");
		} catch (error) {
			setRegistrationStatus(`Caméra inaccessible: ${error.message}`, "error");
		}
	}

	registrationCapture.addEventListener("click", () => {
		if (captures.length >= 3 || registrationVideo.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) return;
		registrationCanvas.width = registrationVideo.videoWidth;
		registrationCanvas.height = registrationVideo.videoHeight;
		registrationCanvas.getContext("2d").drawImage(
			registrationVideo, 0, 0, registrationCanvas.width, registrationCanvas.height,
		);
		captures.push(registrationCanvas.toDataURL("image/jpeg", 0.9));
		registrationCapture.textContent = `Capturer ${captures.length}/3`;
		if (captures.length === 3) {
			registrationCapture.disabled = true;
			registrationSubmit.disabled = false;
			setRegistrationStatus("Captures prêtes", "active");
		} else {
			setRegistrationStatus(`Capture ${captures.length}/3 enregistrée`);
		}
	});

	registrationFiles?.addEventListener("change", async () => {
		const selectedFiles = Array.from(registrationFiles.files || []).slice(0, 3);
		if (selectedFiles.length < 3) {
			setRegistrationStatus("Sélectionnez au moins 3 photos", "error");
			return;
		}
		if (registrationStream) registrationStream.getTracks().forEach((track) => track.stop());
		captures.length = 0;
		try {
			for (const file of selectedFiles) {
				captures.push(await new Promise((resolve, reject) => {
					const reader = new FileReader();
					reader.onload = () => resolve(reader.result);
					reader.onerror = () => reject(new Error("Lecture de photo impossible"));
					reader.readAsDataURL(file);
				}));
			}
			registrationCapture.textContent = "Photos prêtes (3/3)";
			registrationCapture.disabled = true;
			registrationSubmit.disabled = false;
			setRegistrationStatus("Photos prêtes, visage unique par photo", "active");
		} catch (error) {
			setRegistrationStatus(error.message, "error");
		}
	});

	registrationForm.addEventListener("submit", async (event) => {
		event.preventDefault();
		registrationSubmit.disabled = true;
		setRegistrationStatus("Enregistrement en cours...");
		const formData = new FormData(registrationForm);
		const payload = Object.fromEntries(formData.entries());
		payload.frames = captures;
		try {
			const response = await fetch("/students/register", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(payload),
			});
			const result = await response.json();
			if (!response.ok) throw new Error(result.detail || "Inscription impossible");
			setRegistrationStatus(`${result.full_name} enregistré`, "active");
			registrationForm.reset();
			captures.length = 0;
			registrationCapture.textContent = "Capturer 0/3";
			registrationCapture.disabled = false;
			registrationSubmit.disabled = true;
			window.setTimeout(() => window.location.reload(), 900);
		} catch (error) {
			registrationSubmit.disabled = false;
			setRegistrationStatus(error.message, "error");
		}
	});

	openRegistrationCamera();
}
