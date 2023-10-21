document.addEventListener("DOMContentLoaded", (event) => {
  const searchButton = document.querySelector('button[type="submit"]');
  const searchText = document.querySelector("#search");
  const category = document.querySelector("#kategorie");
  const distance = document.querySelector("#distanz");
  const PUBLIC_BACKEND_SERVER = "Ihr Server hier"; // Ersetzen Sie dies durch Ihren Server

  searchButton.addEventListener("click", async (event) => {
    event.preventDefault();

    let search_route;
    if (searchText.value === "" && category.value === "") {
      search_route = "all";
      console.log("Search All");
    } else {
      search_route = `search?therm=${searchText.value}&category=${category.value}`;
      console.log("Search specific");
    }

    const response = await fetch(
      `${PUBLIC_BACKEND_SERVER}/api/${search_route}`
    );
    const data = await response.json();

    if (!data.Code) {
      console.log(data);
    } else {
      console.log("Keine Ergebnisse gefunden");
    }
  });
});
