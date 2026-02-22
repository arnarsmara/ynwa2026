// ===================================
// SAFE START – WAIT FOR DOM
// ===================================
document.addEventListener("DOMContentLoaded", () => {

  // ===============================
  // COUNTDOWNS (Beer + Match)
  // ===============================
  function startCountdown(elementId, targetDate) {
    const el = document.getElementById(elementId);
    if (!el) return;

    function update() {
      const diff = targetDate - Date.now();

      if (diff <= 0) {
        el.textContent = "🍻 KOMIÐ!";
        return;
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
      const minutes = Math.floor((diff / (1000 * 60)) % 60);
      const seconds = Math.floor((diff / 1000) % 60);

      el.textContent =
        `${days} dagar · ${hours} klst · ${minutes} mín · ${seconds} sek`;
    }

    update();
    setInterval(update, 1000);
  }

  // ⏱️ UTC times
  const BEER_TIME_UTC  = new Date("2026-03-12T17:00:00Z").getTime();
  const MATCH_TIME_UTC = new Date("2026-03-15T16:30:00Z").getTime();

  startCountdown("beerCounter", BEER_TIME_UTC);
  startCountdown("tripCounter", MATCH_TIME_UTC);


  // ===============================
  // FLIGHT STATUS (AUTO)
  // ===============================
  function updateFlightStatus(elementId, flightTimeUTC) {
    const box = document.getElementById(elementId);
    if (!box) return;

    const text = box.querySelector(".text");
    if (!text) return;

    const flightTime = new Date(flightTimeUTC);
    const diffMinutes = (flightTime - new Date()) / 1000 / 60;

    box.className = "flight-status";

    if (diffMinutes <= 0) {
      text.textContent = "Departed";
      box.classList.add("departed");
    } else if (diffMinutes <= 15) {
      text.textContent = "Final call";
      box.classList.add("final");
    } else if (diffMinutes <= 45) {
      text.textContent = "Boarding";
      box.classList.add("boarding");
    } else {
      text.textContent = "On time";
    }
  }

  const OUTBOUND_FLIGHT_UTC = "2026-03-12T18:50:00Z";
  const RETURN_FLIGHT_UTC   = "2026-03-16T08:35:00Z";

  function updateAllFlights() {
    updateFlightStatus("outbound-status", OUTBOUND_FLIGHT_UTC);
    updateFlightStatus("return-status", RETURN_FLIGHT_UTC);
  }

  updateAllFlights();
  setInterval(updateAllFlights, 60000);

});

// ===============================
// TRAIN SCHEDULE (STATIC DATA)
// ===============================
function updateTrainSchedule() {
  const box = document.getElementById("train-schedule");
  if (!box) return;

  const today = new Date();
  const day = today.getUTCDate();
  const month = today.getUTCMonth() + 1;

  const schedules = {
    "12-3": {
      route: "Manchester Airport → Liverpool Lime Street",
      times: ["19:07", "19:30", "20:07", "20:30", "21:07", "21:30"]
    },
    "14-3": {
      route: "Liverpool Lime Street → Wigan North Western",
      times: ["11:40", "12:10", "12:40", "13:10", "13:40", "14:10"]
    },
    "16-3": {
      route: "Liverpool Lime Street → Manchester Airport",
      times: ["05:30", "06:00", "06:30", "07:00", "07:30"]
    }
  };

  const key = `${day}-${month}`;

  if (!schedules[key]) {
    box.innerHTML = "No train journey scheduled today.";
    return;
  }

  const schedule = schedules[key];

  let html = `<div style="font-weight:600;margin-bottom:8px;">${schedule.route}</div>`;
  html += `<div style="display:flex;flex-wrap:wrap;gap:8px;">`;

  schedule.times.forEach(time => {
    html += `
      <div style="
        padding:6px 10px;
        background:#f4f4f4;
        border:1px solid #ddd;
        border-radius:8px;
        font-size:14px;
      ">
        ${time}
      </div>
    `;
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