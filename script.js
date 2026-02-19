function startCountdown(elementId, targetDate) {
  const element = document.getElementById(elementId);

  function update() {
    const now = new Date().getTime();
    const distance = targetDate - now;

    if (distance < 0) {
      element.innerHTML = "🍻 KOMIÐ!";
      return;
    }

    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
    const hours = Math.floor((distance / (1000 * 60 * 60)) % 24);
    const minutes = Math.floor((distance / (1000 * 60)) % 60);
    const seconds = Math.floor((distance / 1000) % 60);

    element.innerHTML =
      `${days} dagar · ${hours} klst · ${minutes} mín · ${seconds} sek`;
  }

  update();
  setInterval(update, 1000);
}

// Use UTC time to avoid timezone issues
const tripDate = new Date("2026-03-12T18:50:00Z").getTime();
const beerDate = new Date("2026-03-12T17:00:00Z").getTime();

startCountdown("tripCounter", tripDate);
startCountdown("beerCounter", beerDate);

function logout() {
  localStorage.removeItem("loggedIn");
  window.location.href = "login.html";
}