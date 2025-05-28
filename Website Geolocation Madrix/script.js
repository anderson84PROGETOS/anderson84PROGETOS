let map1, map2, marker1, marker2;

async function getGeo() {
  const domain = document.getElementById('domainInput').value.trim();
  const alertBox = document.getElementById('alert');
  const resultDiv = document.getElementById('result');

  // Reset previous alerts and results
  alertBox.style.display = 'none';
  resultDiv.innerHTML = '';

  if (!domain) {
    alertBox.innerText = 'Por favor, insira um domínio ou IP válido.';
    alertBox.style.display = 'block';
    return;
  }

  try {
    const response = await fetch(`http://ip-api.com/json/${domain}`);
    const data = await response.json();

    if (data.status !== 'success') {
      alertBox.innerText = `Erro: ${data.message}`;
      alertBox.style.display = 'block';
      return;
    }

    const { lat, lon, city, country, isp, query, as } = data;

    // Split AS field into AS number and organization name
    let asNumber = '';
    let orgName = '';
    let bgpLink = '';
    if (as && as.match(/^AS\d+/)) {
      const match = as.match(/^(AS\d+)\s*(.*)$/);
      if (match) {
        asNumber = match[1];
        orgName = match[2] || '';
        bgpLink = `<a href="https://bgp.he.net/${asNumber}" target="_blank">https://bgp.he.net/${asNumber}</a>`;
      }
    }

    const googleMapsLink = `https://www.google.com/maps/place/${lat},${lon}`;
    const streetViewLink = `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${lat},${lon}&heading=-45&pitch=38&fov=80`;

    // Build result HTML
    let resultHTML = `
      <h5>Resultado da Geolocalização</h5>
      <p><strong>IP:</strong> ${query}</p>
      <p><strong>Cidade:</strong> ${city}</p>
      <p><strong>País:</strong> ${country}</p>
      
    `;
    if (asNumber) {
      resultHTML += `
        <p><strong>Organização:</strong> ${orgName || 'Não disponível'}</p>
        <p><strong>Número AS:</strong> ${asNumber}</p>
        <p><strong>Detalhes AS:</strong> ${bgpLink}</p>
      `;
    }
    resultHTML += `
      <p><strong>Latitude:</strong> ${lat}</p>
      <p><strong>Longitude:</strong> ${lon}</p>
      <p><strong>Geolocalização:</strong> ${lat},${lon}</p>
      <p><strong>Google Map:</strong> <a href="${googleMapsLink}" target="_blank">${googleMapsLink}</a></p>
      <p><strong>Street View:</strong> <a href="${streetViewLink}" target="_blank">${streetViewLink}</a></p>

    `;
    resultDiv.innerHTML = resultHTML;

    // Build popup content
    let popupContent = `<b>${city}, ${country}</b><br>IP: ${query}`;
    if (asNumber) {
      popupContent += `<br>Organização: ${orgName || 'Não disponível'}<br>AS: ${asNumber}<br><a href="https://bgp.he.net/${asNumber}" target="_blank">Detalhes AS</a>`;
    }


    // Initialize or update maps
    if (!map1) {
      map1 = L.map('map1').setView([lat, lon], 10);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      }).addTo(map1);
      marker1 = L.marker([lat, lon]).addTo(map1)
        .bindPopup(popupContent).openPopup();
    } else {
      map1.setView([lat, lon], 10);
      if (marker1) map1.removeLayer(marker1);
      marker1 = L.marker([lat, lon]).addTo(map1)
        .bindPopup(popupContent).openPopup();
    }

    if (!map2) {
      map2 = L.map('map2').setView([lat, lon], 10);
      L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
            attribution: '© <a href="https://www.google.com/maps">Google Maps</a>'
      }).addTo(map2);
      marker2 = L.marker([lat, lon]).addTo(map2)
        .bindPopup(popupContent).openPopup();
    } else {
      map2.setView([lat, lon], 10);
      if (marker2) map2.removeLayer(marker2);
      marker2 = L.marker([lat, lon]).addTo(map2)
        .bindPopup(popupContent).openPopup();
    }
  } catch (error) {
    console.error('Erro na requisição:', error);
    alertBox.innerText = 'Erro ao buscar dados. Verifique sua conexão ou o domínio/IP informado.';
    alertBox.style.display = 'block';
  }
}

// Attach form submit event
document.getElementById('geolocationForm').addEventListener('submit', function (e) {
  e.preventDefault();
  getGeo();
});
