const videoElement = document.getElementById("camera-preview");
const cameraPlaceholder = document.getElementById("camera-placeholder");
const capturedPreview = document.getElementById("captured-preview");
const captureCanvas = document.getElementById("capture-canvas");
const emotionResult = document.getElementById("emotion-result");
const musicResult = document.getElementById("music-result");
const startButton = document.getElementById("start-camera");
const captureButton = document.getElementById("capture-emotion");
const stopButton = document.getElementById("stop-camera");
const playerShell = document.getElementById("player-shell");
const playerTitle = document.getElementById("player-title");
const playerSubtitle = document.getElementById("player-subtitle");
const playerAudio = document.getElementById("built-in-player");
const playerLink = document.getElementById("player-link");

let currentStream = null;
let currentTracks = [];


function setCameraPlaceholderVisible(visible) {
    cameraPlaceholder.hidden = !visible;
    cameraPlaceholder.classList.toggle("is-hidden", !visible);
}


function escapeHtml(value) {
    return String(value)
        .split("&").join("&amp;")
        .split("<").join("&lt;")
        .split(">").join("&gt;")
        .split("\"").join("&quot;")
        .split("'").join("&#39;");
}


function setStatus(message, isError = false) {
    emotionResult.textContent = message;
    emotionResult.classList.toggle("is-error", isError);
}


function updateCameraState() {
    const hasStream = Boolean(currentStream);
    captureButton.disabled = !hasStream;
    stopButton.disabled = !hasStream;
    startButton.disabled = hasStream;
    setCameraPlaceholderVisible(!hasStream);
}


function sleep(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
}


async function parseApiResponse(response) {
    const text = await response.text();

        setCameraPlaceholderVisible(!hasStream);
        return {};
    }

    try {
        return JSON.parse(text);
    } catch (error) {
        throw new Error(`Server returned an invalid response (${response.status}).`);
    }
}


function updatePlayer(track, autoplay = false) {
    if (!track) {
        playerShell.classList.add("is-empty");
        playerShell.classList.remove("is-unavailable");
        playerTitle.textContent = "Built-in music player";
        playerSubtitle.textContent = "Click any suggested track to load it here.";
        playerAudio.pause();
        playerAudio.removeAttribute("src");
        playerAudio.load();
        playerLink.hidden = true;
        playerLink.removeAttribute("href");
        return;
    }

    playerTitle.textContent = track.song || "Selected track";
    playerSubtitle.textContent = track.artist || "Unknown artist";

    if (track.url) {
        playerLink.href = track.url;
        playerLink.hidden = false;
    } else {
        playerLink.hidden = true;
        playerLink.removeAttribute("href");
    }

    if (track.preview) {
        playerShell.classList.remove("is-empty", "is-unavailable");
        playerAudio.src = track.preview;
        playerAudio.load();

        if (autoplay) {
            playerAudio.play().catch(() => {
                playerSubtitle.textContent = `${playerSubtitle.textContent} | Press play to start audio.`;
        setCameraPlaceholderVisible(true);
        }
        return;
    }

    playerShell.classList.remove("is-empty");
    playerShell.classList.add("is-unavailable");
    playerSubtitle.textContent = `${playerSubtitle.textContent} | Preview audio is unavailable for this track.`;
    videoElement.addEventListener("playing", () => setCameraPlaceholderVisible(false));
    videoElement.addEventListener("emptied", () => {
        if (!currentStream) {
            setCameraPlaceholderVisible(true);
        }
    });
    playerAudio.pause();
    playerAudio.removeAttribute("src");
    playerAudio.load();
}
    setCameraPlaceholderVisible(true);


function highlightActiveTrack(index) {
    const cards = musicResult.querySelectorAll(".track-card");

    cards.forEach((card, cardIndex) => {
        card.classList.toggle("is-active", cardIndex === index);
    });
}


async function startCamera() {
    if (currentStream) {
        return;
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setStatus("This browser does not support camera preview.", true);
        return;
    }

    try {
        currentStream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: "user",
                width: { ideal: 960 },
                height: { ideal: 720 },
            },
            audio: false,
        });
        videoElement.srcObject = currentStream;
        await videoElement.play().catch(() => {
            // Browser may block autoplay until user interaction in some contexts.
        });
        setCameraPlaceholderVisible(false);
        setStatus("Camera is live. Look straight and hold still for better emotion detection.");
    } catch (error) {
        setCameraPlaceholderVisible(true);
        setStatus("Unable to access the camera. Check browser permissions.", true);
        console.error(error);
    }

    updateCameraState();
}


function stopCamera() {
    if (!currentStream) {
        return;
    }

    currentStream.getTracks().forEach((track) => track.stop());
    currentStream = null;
    videoElement.srcObject = null;
    setCameraPlaceholderVisible(true);
    updateCameraState();
    setStatus("Camera stopped. Start it again for another preview.");
}


function captureFrame(maxWidth = 480, quality = 0.78) {
    const width = videoElement.videoWidth || 640;
    const height = videoElement.videoHeight || 480;
    const scale = Math.min(1, maxWidth / width);
    const outputWidth = Math.max(1, Math.round(width * scale));
    const outputHeight = Math.max(1, Math.round(height * scale));

    captureCanvas.width = outputWidth;
    captureCanvas.height = outputHeight;

    const context = captureCanvas.getContext("2d");
    context.drawImage(videoElement, 0, 0, outputWidth, outputHeight);

    const imageData = captureCanvas.toDataURL("image/jpeg", quality);
    capturedPreview.src = imageData;
    capturedPreview.hidden = false;

    return imageData;
}


async function captureBurst(frameCount = 3, delayMs = 160) {
    const frames = [];

    for (let index = 0; index < frameCount; index += 1) {
        frames.push(captureFrame());

        if (index < frameCount - 1) {
            await sleep(delayMs);
        }
    }

    return frames;
}


async function requestDetection(payload) {
    const response = await fetch("/detect-emotion", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });
    const data = await parseApiResponse(response);

    if (!response.ok) {
        throw new Error(data.error || "Face analysis failed.");
    }

    return data;
}


function renderMusic(recommendation) {
    if (!recommendation) {
        musicResult.innerHTML = '<div class="empty-state">No recommendation data received.</div>';
        currentTracks = [];
        updatePlayer(null);
        return;
    }

    currentTracks = Array.isArray(recommendation.tracks) ? recommendation.tracks : [];
    const sourceLabel = String(recommendation.source || "suggested")
        .split("-")
        .join(" ");

    const trackMarkup = currentTracks.map((track, index) => {
        const artwork = track.artwork
            ? `<img class="track-artwork" src="${escapeHtml(track.artwork)}" alt="${escapeHtml(track.song)} artwork">`
            : `<div class="track-artwork placeholder-artwork">${index + 1}</div>`;

        const actionLabel = track.preview ? "Play in player" : "Load details";
        const actionClass = track.preview
            ? "track-action"
            : "track-action track-action-muted";
        const linkMarkup = track.url
            ? `<a class="track-link" href="${escapeHtml(track.url)}" target="_blank" rel="noreferrer">Open track</a>`
            : "";

        return `
            <article class="track-card" data-track-index="${index}">
                ${artwork}
                <div class="track-body">
                    <h3>${escapeHtml(track.song)}</h3>
                    <p class="track-artist">${escapeHtml(track.artist)}</p>
                    <div class="track-controls">
                        <button
                            type="button"
                            class="${actionClass}"
                            data-track-index="${index}"
                        >
                            ${actionLabel}
                        </button>
                        ${linkMarkup}
                    </div>
                </div>
            </article>
        `;
    }).join("");

    musicResult.innerHTML = `
        <div class="summary-grid">
            <div class="summary-card">
                <span class="summary-label">Detected Emotion</span>
                <strong>${escapeHtml(recommendation.emotion)}</strong>
            </div>
            <div class="summary-card">
                <span class="summary-label">Music Mood</span>
                <strong>${escapeHtml(recommendation.mood)}</strong>
            </div>
            <div class="summary-card">
                <span class="summary-label">Playlist</span>
                <strong>${escapeHtml(recommendation.recommended_playlist)}</strong>
            </div>
            <div class="summary-card">
                <span class="summary-label">Track Source</span>
                <strong>${escapeHtml(sourceLabel)}</strong>
            </div>
        </div>
        <div class="track-list">
            ${trackMarkup || '<div class="empty-state">No tracks found for this emotion.</div>'}
        </div>
    `;

    if (!currentTracks.length) {
        updatePlayer(null);
        return;
    }

    const defaultTrack = currentTracks.find((track) => track.preview) || currentTracks[0];
    const defaultIndex = currentTracks.indexOf(defaultTrack);
    updatePlayer(defaultTrack, false);
    highlightActiveTrack(defaultIndex);
}


function buildDetectionStatus(data) {
    let baseMessage;

    if (!data.face_detected) {
        baseMessage = "Face was not detected clearly. Use brighter light and face the camera directly.";
    } else {
        const confidence = Math.round((Number(data.confidence) || 0) * 100);
        baseMessage = `Detected emotion: ${data.detected_emotion} (${confidence}% confidence, ${data.used_frames}/${data.sampled_frames} frames used)`;
    }

    if (data.warning) {
        return `${baseMessage} ${data.warning}`;
    }

    return baseMessage;
}


async function captureEmotion() {
    if (!currentStream) {
        setStatus("Start the camera before capturing a frame.", true);
        return;
    }

    setStatus("Capturing a short burst of frames. Hold still and keep your face centered.");
    musicResult.innerHTML = '<div class="empty-state">Analyzing frames and preparing a playable track list...</div>';

    try {
        const frames = await captureBurst();
        let data;

        try {
            data = await requestDetection({ images: frames });
        } catch (error) {
            data = await requestDetection({
                image: frames[Math.floor(frames.length / 2)],
            });
            data.warning = data.warning || "Burst analysis failed, so a single frame was used.";
        }

        let recommendation = data.recommendation;
        if (!recommendation && data.detected_emotion) {
            const suggestionResponse = await fetch(
                `/recommend-music/${encodeURIComponent(data.detected_emotion)}`
            );
            recommendation = await parseApiResponse(suggestionResponse);
        }

        setStatus(buildDetectionStatus(data), !data.face_detected);
        renderMusic(recommendation);
    } catch (error) {
        setStatus(error.message || "Face analysis failed.", true);
        musicResult.innerHTML = '<div class="empty-state">Could not load music suggestions.</div>';
        currentTracks = [];
        updatePlayer(null);
        console.error(error);
    }
}


musicResult.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-track-index]");
    if (!trigger) {
        return;
    }

    const index = Number(trigger.getAttribute("data-track-index"));
    const track = currentTracks[index];

    if (!track) {
        return;
    }

    updatePlayer(track, Boolean(track.preview));
    highlightActiveTrack(index);
});


startButton.addEventListener("click", startCamera);
captureButton.addEventListener("click", captureEmotion);
stopButton.addEventListener("click", stopCamera);
videoElement.addEventListener("playing", () => setCameraPlaceholderVisible(false));
videoElement.addEventListener("emptied", () => {
    if (!currentStream) {
        setCameraPlaceholderVisible(true);
    }
});

window.addEventListener("beforeunload", stopCamera);

updatePlayer(null);
setCameraPlaceholderVisible(true);
updateCameraState();
