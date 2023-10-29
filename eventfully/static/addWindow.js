document.addEventListener("DOMContentLoaded", (event) => {
  const form = document.querySelector("form");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(form);
    const data = Object.fromEntries(formData);

    const response = await fetch("Server hier", {
      // Hier Server eintragen
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (response.ok) {
      console.log("Daten erfolgreich gesendet");
    } else {
      console.log("Fehler beim Senden der Daten");
    }
  });
});
