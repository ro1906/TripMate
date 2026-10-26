// Draws the trip map with Leaflet + OpenStreetMap tiles (no API key needed).
(function () {
  const el = document.getElementById("map");
  if (!el || typeof L === "undefined") return;

  const markers = JSON.parse(document.getElementById("markers-data").textContent);
  const center = JSON.parse(document.getElementById("center-data").textContent);

  const map = L.map(el).setView(center || [markers[0].lat, markers[0].lng], 11);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  const points = [];
  markers.forEach((m) => {
    // textContent-style escaping: build the popup from DOM nodes, not raw HTML
    const box = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = m.title;
    box.append(title, document.createElement("br"), "Day " + m.day + (m.place ? " · " + m.place : ""));
    L.marker([m.lat, m.lng]).addTo(map).bindPopup(box);
    points.push([m.lat, m.lng]);
  });
  if (points.length > 1) map.fitBounds(points, { padding: [30, 30] });
})();
