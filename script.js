document.addEventListener("DOMContentLoaded", () => {

  // ===============================
  // MAIN TAB SWITCHING
  // ===============================
  const mainTabs = document.querySelectorAll(".main-tab");
  const mainPanels = document.querySelectorAll(".main-panel");

  function activateMain(name) {
    mainTabs.forEach(t => t.classList.remove("active"));
    mainPanels.forEach(p => p.classList.remove("active"));

    const tab = document.querySelector(`.main-tab[data-main="${name}"]`);
    const panel = document.getElementById(`main-${name}`);

    if (tab) {
      tab.classList.add("active");
      if (window.innerWidth <= 768) {
        tab.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
      }
    }
    if (panel) panel.classList.add("active");
  }

  mainTabs.forEach(tab => {
    tab.addEventListener("click", () => activateMain(tab.dataset.main));
  });

  activateMain("dagskra");

  // ===============================
  // SUB TAB SWITCHING
  // ===============================
  const subTabs = document.querySelectorAll(".sub-tab");
  const subContents = document.querySelectorAll(".sub-content");

  function activateSub(id) {
    subTabs.forEach(t => t.classList.remove("active"));
    subContents.forEach(c => c.classList.remove("active"));

    const tab = document.querySelector(`.sub-tab[data-sub="${id}"]`);
    const content = document.getElementById(id);

    if (tab) {
      tab.classList.add("active");
      if (window.innerWidth <= 768) {
        tab.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
      }
    }
    if (content) content.classList.add("active");
  }

  subTabs.forEach(tab => {
    tab.addEventListener("click", () => activateSub(tab.dataset.sub));
  });

  activateSub("thu-content");

  // Reset food sub-tabs when food panel is opened
  document.querySelectorAll(".main-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      if (tab.dataset.main === "food") {
        setTimeout(() => activateSub("lunch-content"), 10);
      }
    });
  });

  // ===============================
  // COUNTDOWNS
  // ===============================
  function startCountdown(elementId, targetDate) {
    const el = document.getElementById(elementId);
    if (!el) return;

    function update() {
      const diff = targetDate - Date.now();
      if (diff <= 0) { el.textContent = "🍻 KOMIÐ!"; return; }

      const days    = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours   = Math.floor((diff / (1000 * 60 * 60)) % 24);
      const minutes = Math.floor((diff / (1000 * 60)) % 60);
      const seconds = Math.floor((diff / 1000) % 60);

      el.textContent = `${days} dagar · ${hours} klst · ${minutes} mín · ${seconds} sek`;
    }

    update();
    setInterval(update, 1000);
  }

  const BEER_TIME_UTC  = new Date("2026-03-12T17:00:00Z").getTime();
  const MATCH_TIME_UTC = new Date("2026-03-15T16:30:00Z").getTime();

  startCountdown("beerCounter", BEER_TIME_UTC);
  startCountdown("tripCounter", MATCH_TIME_UTC);

  // ===============================
  // FLIGHT STATUS
  // ===============================
  function updateFlightStatus(elementId, flightTimeUTC) {
    const box = document.getElementById(elementId);
    if (!box) return;
    const text = box.querySelector(".text");
    if (!text) return;

    const diffMinutes = (new Date(flightTimeUTC) - new Date()) / 1000 / 60;
    box.className = "flight-status";

    if (diffMinutes <= 0) {
      text.textContent = "Departed"; box.classList.add("departed");
    } else if (diffMinutes <= 15) {
      text.textContent = "Final call"; box.classList.add("final");
    } else if (diffMinutes <= 45) {
      text.textContent = "Boarding"; box.classList.add("boarding");
    } else {
      text.textContent = "On time";
    }
  }

  function updateAllFlights() {
    updateFlightStatus("outbound-status", "2026-03-12T18:50:00Z");
    updateFlightStatus("return-status",   "2026-03-16T08:35:00Z");
  }

  updateAllFlights();
  setInterval(updateAllFlights, 60000);

});

// ===============================
// TRAIN SCHEDULE
// ===============================
function updateTrainSchedule() {
  const box = document.getElementById("train-schedule");
  if (!box) return;

  const today = new Date();
  const day   = today.getUTCDate();
  const month = today.getUTCMonth() + 1;

  const schedules = {
    "12-3": { route: "Manchester Airport → Liverpool Lime Street",  times: ["19:07","19:30","20:07","20:30","21:07","21:30"] },
    "14-3": { route: "Liverpool Lime Street → Wigan North Western", times: ["11:40","12:10","12:40","13:10","13:40","14:10"] },
    "16-3": { route: "Liverpool Lime Street → Manchester Airport",  times: ["05:30","06:00","06:30","07:00","07:30"] }
  };

  const key = `${day}-${month}`;
  if (!schedules[key]) { box.innerHTML = "No train journey scheduled today."; return; }

  const s = schedules[key];
  let html = `<div style="font-weight:600;margin-bottom:8px;">${s.route}</div>`;
  html += `<div style="display:flex;flex-wrap:wrap;gap:8px;">`;
  s.times.forEach(t => {
    html += `<div style="padding:6px 10px;background:#f4f4f4;border:1px solid #ddd;border-radius:8px;font-size:14px;">${t}</div>`;
  });
  html += `</div>`;
  box.innerHTML = html;
}

updateTrainSchedule();

// ===============================
// LOGOUT
// ===============================
function logout() {
  localStorage.removeItem("loggedIn");
  window.location.href = "login.html";
}

// ===============================
// FIREBASE SETUP
// ===============================
const firebaseConfig = {
  apiKey: "AIzaSyCxl3Gi4_E7yJyMjcLTphMNkLI18Dh3iiU",
  authDomain: "liverpool2026.firebaseapp.com",
  databaseURL: "https://liverpool2026-default-rtdb.europe-west1.firebasedatabase.app",
  projectId: "liverpool2026",
  storageBucket: "liverpool2026.firebasestorage.app",
  messagingSenderId: "966731065796",
  appId: "1:966731065796:web:c4fc3cffce0accea705c91"
};

firebase.initializeApp(firebaseConfig);
const db = firebase.database();
const storage = firebase.storage();
const notesRef = db.ref("liverpool2026/notes");

// ===============================
// SHARED NOTES (Firebase Realtime DB + Storage)
// ===============================
let cachedNotes = [];

function renderNotes(notes) {
  const list = document.getElementById("notes-list");
  if (!list) return;

  if (notes.length === 0) {
    list.innerHTML = `<p style="color:#aaa;font-size:14px;text-align:center;padding:20px 0;">Engar athugasemdir enn 🍺</p>`;
    return;
  }

  let html = `<table style="width:100%;border-collapse:collapse;">`;
  notes.forEach(n => {
    const content = n.imageUrl
      ? `<img src="${n.imageUrl}" style="max-width:100%;max-height:300px;border-radius:8px;display:block;margin-top:4px;cursor:pointer;" onclick="window.open('${n.imageUrl}','_blank')">`
      : n.text;
    html += `
      <tr style="border-bottom:1px solid #eee;">
        <td style="padding:10px 12px;font-size:14px;line-height:1.5;word-break:break-word;">${content}</td>
        <td style="padding:10px 8px;font-size:11px;color:#aaa;white-space:nowrap;text-align:right;vertical-align:top;">${n.time}</td>
        <td style="padding:10px 8px;text-align:right;width:30px;vertical-align:top;">
          <td style="padding:10px 8px;text-align:right;width:10px;"></td>
      </tr>`;
  });
  html += `</table>`;
  list.innerHTML = html;
}

// Firebase listener
notesRef.orderByChild("timestamp").on("value", (snapshot) => {
  console.log("Firebase data received, notes count:", snapshot.numChildren());
  cachedNotes = [];
  snapshot.forEach(child => {
    try {
      const val = child.val();
      if (val && (val.text || val.imageUrl)) {
        cachedNotes.push({ id: child.key, ...val });
      }
    } catch(e) {
      console.log("Skipping broken note:", child.key);
    }
  });
  cachedNotes.reverse();
  console.log("cachedNotes:", cachedNotes);
  renderNotes(cachedNotes);
});

// Re-render when Notes tab clicked
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".main-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      if (tab.dataset.main === "notes") {
        setTimeout(() => renderNotes(cachedNotes), 50);
      }
    });
  });
});

function loadNotes() {}

function addNote() {
  const input = document.getElementById("note-input");
  if (!input) return;
  const text = input.value.trim();
  if (!text) return;

  const now = new Date();
  const time = now.toLocaleDateString("is-IS", { day: "numeric", month: "numeric" }) +
               " " + now.toLocaleTimeString("is-IS", { hour: "2-digit", minute: "2-digit" });

  notesRef.push({ text, time, timestamp: Date.now() });
  input.value = "";
}

function uploadImage(input) {
  const file = input.files[0];
  if (!file) return;

  const progress = document.getElementById("upload-progress");
  if (progress) { progress.style.display = "block"; progress.textContent = "Hleð upp mynd... ⏳"; }

  // Use FileReader to convert to base64 - works on all mobile browsers
  const reader = new FileReader();
  reader.onload = function(e) {
    const base64 = e.target.result.split(',')[1];
    const contentType = file.type || 'image/jpeg';
    const fileName = `notes/${Date.now()}_${file.name.replace(/[^a-zA-Z0-9._]/g, '_')}`;
    const ref = storage.ref(fileName);

    ref.putString(base64, 'base64', { contentType })
      .then((snapshot) => snapshot.ref.getDownloadURL())
      .then((url) => {
        if (progress) progress.style.display = "none";
        const now = new Date();
        const time = now.toLocaleDateString("is-IS", { day: "numeric", month: "numeric" }) +
                     " " + now.toLocaleTimeString("is-IS", { hour: "2-digit", minute: "2-digit" });
        notesRef.push({ text: "📷 Mynd", imageUrl: url, time, timestamp: Date.now() });
        input.value = "";
      })
      .catch((err) => {
        if (progress) progress.style.display = "none";
        alert("Villa við að hlaða upp mynd: " + err.message);
      });
  };
  reader.onerror = () => {
    if (progress) progress.style.display = "none";
    alert("Gat ekki lesið myndina");
  };
  reader.readAsDataURL(file);
}

function deleteNote(id) {
  notesRef.child(id).remove();
}

// ===============================
// CURRENCY CONVERTER
// ===============================
let iskGbpRate = null;

async function fetchRate() {
  const display = document.getElementById("rate-display");
  if (!display) return;

  try {
    const res = await fetch("https://api.frankfurter.app/latest?from=GBP&to=ISK");
    const data = await res.json();
    iskGbpRate = data.rates.ISK;
    display.textContent = `1 GBP = ${iskGbpRate.toFixed(0)} ISK  ·  1 ISK = ${(1/iskGbpRate).toFixed(5)} GBP`;
  } catch (e) {
    iskGbpRate = 175;
    display.textContent = `1 GBP ≈ 175 ISK (offline gisting)`;
  }
}

function convertCurrency(from) {
  if (!iskGbpRate) return;
  const iskInput = document.getElementById("isk-input");
  const gbpInput = document.getElementById("gbp-input");
  if (!iskInput || !gbpInput) return;

  if (from === "isk") {
    const val = parseFloat(iskInput.value) || 0;
    gbpInput.value = val > 0 ? (val / iskGbpRate).toFixed(2) : "";
  } else {
    const val = parseFloat(gbpInput.value) || 0;
    iskInput.value = val > 0 ? Math.round(val * iskGbpRate) : "";
  }
}

function quickConvert(isk) {
  if (!iskGbpRate) return;
  document.getElementById("isk-input").value = isk;
  document.getElementById("gbp-input").value = (isk / iskGbpRate).toFixed(2);
}

fetchRate();