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
// LOGOUT
// ===============================
function logout() {
  localStorage.removeItem("loggedIn");
  window.location.href = "login.html";
}