/**
 * VocalOS Desktop Assistant — Core Application Logic
 * Stitch Architecture: WebSockets + Web Audio API + Speech Recognition + Biometrics
 * Author: Owen Badel Hooker
 */

document.addEventListener("DOMContentLoaded", () => {
  // Estado de la aplicación
  const state = {
    audioContext: null,
    analyser: null,
    mediaStream: null,
    isListening: false,
    ws: null,
    recordedSamples: [],
    profile: null
  };

  // Elementos del DOM
  const clockDisplay = document.getElementById("clockDisplay");
  const micOrb = document.getElementById("micOrb");
  const micStatusText = document.getElementById("micStatusText");
  const transcriptionDisplay = document.getElementById("transcriptionDisplay");
  const executionResultBadge = document.getElementById("executionResultBadge");
  const terminalConsole = document.getElementById("terminalConsole");
  const oscCanvas = document.getElementById("oscCanvas");
  const vuStrip = document.getElementById("vuStrip");
  const labelBiometricOwner = document.getElementById("labelBiometricOwner");
  const badgeBiometrics = document.getElementById("badgeBiometrics");
  const sliderThreshold = document.getElementById("sliderThreshold");
  const labelThreshold = document.getElementById("labelThreshold");
  const btnTrainProfile = document.getElementById("btnTrainProfile");
  const inputUserName = document.getElementById("inputUserName");
  const biometricFeedback = document.getElementById("biometricFeedback");

  // 1. Reloj de telemetría en tiempo real
  function updateClock() {
    const now = new Date();
    clockDisplay.textContent = now.toTimeString().split(" ")[0];
  }
  setInterval(updateClock, 1000);
  updateClock();

  // 2. Generar 24 segmentos de VU Meter
  for (let i = 0; i < 24; i++) {
    const seg = document.createElement("div");
    seg.className = "vu-segment";
    seg.id = `vu-seg-${i}`;
    vuStrip.appendChild(seg);
  }

  // 3. Inicializar WebSocket para Terminal
  function initWebSocket() {
    const loc = window.location;
    const wsProto = loc.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProto}//${loc.host}/ws/terminal`;

    state.ws = new WebSocket(wsUrl);

    state.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        appendTerminalLine(data.line || data.message || JSON.stringify(data), data.type || "stdout");
      } catch (e) {
        appendTerminalLine(event.data, "stdout");
      }
    };

    state.ws.onclose = () => {
      setTimeout(initWebSocket, 3000);
    };
  }

  function appendTerminalLine(text, type = "stdout") {
    const line = document.createElement("div");
    line.className = `term-line ${type}`;
    line.textContent = text;
    terminalConsole.appendChild(line);
    terminalConsole.scrollTop = terminalConsole.scrollHeight;
  }

  // 4. Inicializar Web Audio API y Visualizador Acústico
  async function initAudioVisualizer() {
    try {
      if (!state.audioContext) {
        state.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (!state.mediaStream) {
        state.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      }

      const source = state.audioContext.createMediaStreamSource(state.mediaStream);
      state.analyser = state.audioContext.createAnalyser();
      state.analyser.fftSize = 256;
      source.connect(state.analyser);

      drawOscilloscope();
    } catch (err) {
      console.warn("No se pudo acceder al micrófono para el osciloscopio:", err);
    }
  }

  function drawOscilloscope() {
    requestAnimationFrame(drawOscilloscope);
    if (!state.analyser) return;

    const bufferLength = state.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    state.analyser.getByteTimeDomainData(dataArray);

    const ctx = oscCanvas.getContext("2d");
    const width = oscCanvas.width = oscCanvas.clientWidth;
    const height = oscCanvas.height = oscCanvas.clientHeight;

    // Fondo oscuro con rejilla suave
    ctx.fillStyle = "#060913";
    ctx.fillRect(0, 0, width, height);

    ctx.lineWidth = 1.5;
    ctx.strokeStyle = "#06b6d4";
    ctx.shadowBlur = 6;
    ctx.shadowColor = "rgba(6, 182, 212, 0.6)";

    ctx.beginPath();
    const sliceWidth = width / bufferLength;
    let x = 0;

    let sumSquares = 0;
    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i] / 128.0;
      const y = (v * height) / 2;
      const deviation = v - 1.0;
      sumSquares += deviation * deviation;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
      x += sliceWidth;
    }
    ctx.lineTo(width, height / 2);
    ctx.stroke();

    // Actualizar 24 segmentos de VU Meter según el volumen RMS
    const rms = Math.sqrt(sumSquares / bufferLength);
    const litCount = Math.min(24, Math.floor(rms * 90));

    for (let i = 0; i < 24; i++) {
      const seg = document.getElementById(`vu-seg-${i}`);
      if (!seg) continue;
      seg.className = "vu-segment";
      if (i < litCount) {
        if (i < 16) {
          seg.classList.add("lit-cyan");
        } else if (i < 21) {
          seg.classList.add("lit-violet");
        } else {
          seg.classList.add("lit-red");
        }
      }
    }
  }

  // 5. Speech Recognition (Web Speech API)
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null;

  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.lang = "es-ES";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      state.isListening = true;
      micOrb.classList.add("recording");
      micStatusText.textContent = "Escuchando voz... Habla ahora";
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      transcriptionDisplay.innerHTML = `<strong>Transcripción:</strong> "${transcript}"`;
      processVoiceCommand(transcript);
    };

    recognition.onerror = (event) => {
      micStatusText.textContent = `Error de escucha: ${event.error}`;
      micOrb.classList.remove("recording");
      state.isListening = false;
    };

    recognition.onend = () => {
      micOrb.classList.remove("recording");
      state.isListening = false;
      micStatusText.textContent = "Haz clic en el micrófono para hablar";
    };
  } else {
    micStatusText.textContent = "SpeechRecognition no disponible. Puedes escribir comandos manuales.";
  }

  // Manejador del botón del micrófono
  micOrb.addEventListener("click", () => {
    initAudioVisualizer();
    if (!recognition) return;
    if (state.isListening) {
      recognition.stop();
    } else {
      recognition.start();
    }
  });

  // 6. Procesar comando vocal contra el backend
  async function processVoiceCommand(transcript) {
    // Generar vector de características de audio sintético/actual para el filtro biométrico
    const audioFeatures = extractLiveAudioVector();

    try {
      const res = await fetch("/api/voice/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          transcript: transcript,
          audio_features: audioFeatures,
          bypass_biometrics: false
        })
      });
      const data = await res.json();
      displayExecutionResult(data);
    } catch (err) {
      appendTerminalLine(`[Error al procesar voz] ${err.message}`, "stderr");
    }
  }

  function displayExecutionResult(data) {
    executionResultBadge.style.display = "block";
    if (data.authorized) {
      executionResultBadge.style.background = "rgba(16, 185, 129, 0.12)";
      executionResultBadge.style.border = "1px solid rgba(16, 185, 129, 0.35)";
      executionResultBadge.style.color = "#34d399";
      executionResultBadge.innerHTML = `✅ ${data.message} &bull; Intención: <strong>${data.execution?.intent}</strong>`;
      appendTerminalLine(`[VocalOS Biometría OK] ${data.message}`, "success");

      if (data.execution?.result?.message) {
        appendTerminalLine(`[Acción Ejecutada] ${data.execution.result.message}`, "stdout");
      }
      if (data.execution?.result?.stdout) {
        appendTerminalLine(data.execution.result.stdout, "stdout");
      }
      if (data.execution?.result?.stderr) {
        appendTerminalLine(data.execution.result.stderr, "stderr");
      }
    } else {
      executionResultBadge.style.background = "rgba(244, 63, 94, 0.15)";
      executionResultBadge.style.border = "1px solid rgba(244, 63, 94, 0.4)";
      executionResultBadge.style.color = "#fb7185";
      executionResultBadge.innerHTML = `🚫 ${data.message}`;
      appendTerminalLine(`[VocalOS Seguridad] ${data.message}`, "stderr");
    }
  }

  // Genera un vector acústico representativo de 64 dimensiones a partir del analyser
  function extractLiveAudioVector() {
    if (!state.analyser) {
      // Vector patrón por defecto con semilla de consistencia
      return Array.from({ length: 64 }, (_, i) => Math.sin(i * 0.15) * 0.5 + 0.5);
    }
    const freqData = new Uint8Array(state.analyser.frequencyBinCount);
    state.analyser.getByteFrequencyData(freqData);
    const vector = [];
    const step = Math.max(1, Math.floor(freqData.length / 64));
    for (let i = 0; i < 64; i++) {
      const val = freqData[i * step] || 0;
      vector.push(val / 255.0);
    }
    return vector;
  }

  // 7. Enrolamiento y Calibración del Perfil de Voz
  sliderThreshold.addEventListener("input", (e) => {
    labelThreshold.textContent = `${e.target.value}%`;
  });

  function setupSampleButton(btnId, sampleIndex) {
    const btn = document.getElementById(btnId);
    btn.addEventListener("click", async () => {
      await initAudioVisualizer();
      btn.textContent = "Grabando...";
      btn.style.color = "#fb7185";

      setTimeout(() => {
        const vec = extractLiveAudioVector();
        state.recordedSamples[sampleIndex] = vec;
        btn.textContent = "✓ Calibrada";
        btn.style.color = "#34d399";
        appendTerminalLine(`[Laboratorio] Muestra #${sampleIndex + 1} de calibración registrada con éxito.`, "meta");
      }, 1500);
    });
  }

  setupSampleButton("btnRecordSample1", 0);
  setupSampleButton("btnRecordSample2", 1);
  setupSampleButton("btnRecordSample3", 2);

  btnTrainProfile.addEventListener("click", async () => {
    const userName = inputUserName.value.trim() || "Owen Badel Hooker";
    const threshold = parseFloat(sliderThreshold.value) / 100.0;

    // Asegurar 3 muestras (rellenar si no ha grabado todas)
    while (state.recordedSamples.length < 3) {
      state.recordedSamples.push(extractLiveAudioVector());
    }

    try {
      const res = await fetch("/api/profile/enroll", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_name: userName,
          samples: state.recordedSamples,
          threshold: threshold
        })
      });
      const data = await res.json();
      if (data.success) {
        biometricFeedback.style.display = "block";
        biometricFeedback.textContent = `Huella acústica sellada para ${userName} con umbral de ${threshold * 100}%.`;
        labelBiometricOwner.textContent = `Voz: ${userName}`;
        badgeBiometrics.className = "badge-status active";
        appendTerminalLine(`[Biometría] Perfil de voz entrenado y sellado para ${userName}.`, "success");
      }
    } catch (err) {
      appendTerminalLine(`[Error Enrolamiento] ${err.message}`, "stderr");
    }
  });

  // 8. Ejecución Manual de Comandos en Terminal
  const inputManualCommand = document.getElementById("inputManualCommand");
  const btnExecuteManual = document.getElementById("btnExecuteManual");

  function sendManualCommand() {
    const cmd = inputManualCommand.value.trim();
    if (!cmd) return;
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
      state.ws.send(JSON.stringify({ action: "run", command: cmd }));
      inputManualCommand.value = "";
    } else {
      // Fallback REST
      fetch("/api/terminal/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: cmd })
      })
      .then(r => r.json())
      .then(res => {
        if (res.stdout) appendTerminalLine(res.stdout, "stdout");
        if (res.stderr) appendTerminalLine(res.stderr, "stderr");
      });
      inputManualCommand.value = "";
    }
  }

  btnExecuteManual.addEventListener("click", sendManualCommand);
  inputManualCommand.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendManualCommand();
  });

  document.getElementById("btnClearTerminal").addEventListener("click", () => {
    terminalConsole.innerHTML = '<div class="term-line meta">[Terminal Limpia]</div>';
  });

  // 9. Acciones Rápidas de Entretenimiento (R.E.P.O., PEAK, Steam, Anime, Spotify)
  document.getElementById("cardLaunchRepo").addEventListener("click", () => {
    fetch("/api/entertainment/game", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_name: "repo" })
    }).then(r => r.json()).then(d => appendTerminalLine(d.message, "success"));
  });

  document.getElementById("cardLaunchPeak").addEventListener("click", () => {
    fetch("/api/entertainment/game", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_name: "peak" })
    }).then(r => r.json()).then(d => appendTerminalLine(d.message, "success"));
  });

  document.getElementById("cardLaunchSteam").addEventListener("click", () => {
    fetch("/api/entertainment/game", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_name: "steam" })
    }).then(r => r.json()).then(d => appendTerminalLine(d.message, "success"));
  });

  document.getElementById("cardAnimeFLV").addEventListener("click", () => {
    fetch("/api/browser/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: "anime popular", engine: "animeflv" })
    }).then(r => r.json()).then(d => appendTerminalLine(d.message, "stdout"));
  });

  document.getElementById("cardCrunchyroll").addEventListener("click", () => {
    fetch("/api/browser/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: "anime", engine: "crunchyroll" })
    }).then(r => r.json()).then(d => appendTerminalLine(d.message, "stdout"));
  });

  document.getElementById("cardLocalAnime").addEventListener("click", () => {
    fetch("/api/folder/open", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ folder: "anime" })
    }).then(r => r.json()).then(d => appendTerminalLine(d.message, "success"));
  });

  document.getElementById("btnSpotifyPlay").addEventListener("click", () => {
    const q = document.getElementById("inputSpotifySearch").value.trim();
    fetch("/api/entertainment/spotify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: q || null })
    }).then(r => r.json()).then(d => appendTerminalLine(d.message, "success"));
  });

  // 10. Acciones de Carpetas y Archivos
  function setupFolderBtn(btnId, folderName) {
    document.getElementById(btnId).addEventListener("click", () => {
      fetch("/api/folder/open", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder: folderName })
      }).then(r => r.json()).then(d => appendTerminalLine(d.message, "success"));
    });
  }

  setupFolderBtn("btnOpenDownloads", "descargas");
  setupFolderBtn("btnOpenProjects", "proyectos");
  setupFolderBtn("btnOpenDocuments", "documentos");

  // Crear, Editar y Borrar Archivos
  const inputFilePath = document.getElementById("inputFilePath");
  const inputFileContent = document.getElementById("inputFileContent");

  document.getElementById("btnCreateFile").addEventListener("click", () => {
    const path = inputFilePath.value.trim();
    if (!path) return alert("Indica una ruta o nombre de archivo.");
    fetch("/api/files/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: path, content: inputFileContent.value })
    }).then(r => r.json()).then(d => appendTerminalLine(d.message || d.error, d.success ? "success" : "stderr"));
  });

  document.getElementById("btnEditFile").addEventListener("click", () => {
    const path = inputFilePath.value.trim();
    if (!path) return alert("Indica una ruta o nombre de archivo.");
    fetch("/api/files/edit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: path, content: inputFileContent.value, append: true })
    }).then(r => r.json()).then(d => appendTerminalLine(d.message || d.error, d.success ? "success" : "stderr"));
  });

  document.getElementById("btnDeleteFile").addEventListener("click", () => {
    const path = inputFilePath.value.trim();
    if (!path) return alert("Indica una ruta o nombre de archivo.");
    if (!confirm(`¿Confirmas borrar '${path}'?`)) return;
    fetch("/api/files/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: path })
    }).then(r => r.json()).then(d => appendTerminalLine(d.message || d.error, d.success ? "success" : "stderr"));
  });

  // Conectar WebSocket y cargar estado inicial
  initWebSocket();
  fetch("/api/status")
    .then(r => r.json())
    .then(data => {
      if (data.biometrics?.enrolled) {
        labelBiometricOwner.textContent = `Voz: ${data.biometrics.user_name}`;
        badgeBiometrics.className = "badge-status active";
        biometricFeedback.style.display = "block";
        biometricFeedback.textContent = `Perfil cargado: ${data.biometrics.user_name} (Umbral: ${data.biometrics.threshold * 100}%).`;
      }
    });
});
