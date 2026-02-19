function login() {
  const inputEl = document.getElementById("password");
  const error = document.getElementById("error");

  if (!inputEl) {
    alert("Password input fannst ekki");
    return;
  }

  const input = inputEl.value.trim();
  const correctPassword = "YNWA2026";

  if (input === correctPassword) {
    localStorage.setItem("loggedIn", "true");
    window.location.href = "./index.html";
  } else {
    error.textContent = "Vitlaust lykilorð 🍺";
  }
}
