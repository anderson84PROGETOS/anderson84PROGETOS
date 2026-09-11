const domainsEl = document.getElementById("domains");
const searchEl = document.getElementById("search");
const countEl = document.getElementById("count");
let allDomains = [];

// Heurística simples: nomes de domínio com termos frequentemente usados
// por sites adultos. Não consulta o conteúdo dos sites.
const ADULT_TERMS = [
  "porn", "xxx", "xvideos", "xnxx", "pornhub", "redtube", "xhamster",
  "spankbang", "brazzers", "chaturbate", "stripchat", "onlyfans",
  "sexcam", "camgirl", "camgirls", "adult", "hentai", "rule34",
  "erome", "youporn", "tube8", "motherless", "pornhd", "pornone",
  "pornpics", "nsfw"
];

function cleanDomain(domain) { return domain.replace(/^\\.+/, ""); }
function isAdultDomain(domain) {
  const d = domain.toLowerCase().replace(/^www\\./, "");
  return ADULT_TERMS.some(term => d.includes(term));
}

function render() {
  const q = searchEl.value.trim().toLowerCase();
  const list = allDomains.filter(d => d.domain.toLowerCase().includes(q));
  countEl.textContent = `${list.length} domínio${list.length === 1 ? "" : "s"}`;

  if (!list.length) {
    domainsEl.innerHTML = `<div class="empty">Nenhum domínio encontrado.</div>`;
    return;
  }

  domainsEl.innerHTML = "";
  for (const item of list) {
    const adult = isAdultDomain(item.domain);
    const row = document.createElement("div");
    row.className = "item" + (adult ? " adult" : "");

    const info = document.createElement("div");
    info.className = "domain";
    info.textContent = item.domain;

    const details = document.createElement("span");
    details.textContent = adult
      ? `⚠ conteúdo adulto • ${item.cookies} cookie${item.cookies === 1 ? "" : "s"}`
      : `${item.cookies} cookie${item.cookies === 1 ? "" : "s"}`;
    info.appendChild(details);

    const btn = document.createElement("button");
    btn.className = "item-delete";
    btn.textContent = "Apagar";
    btn.title = `Apagar cookies de ${item.domain}`;
    btn.addEventListener("click", () => deleteDomain(item.domain));

    const view = document.createElement("button");
    view.className = "view-cookies";
    view.textContent = "Ver cookies";
    view.addEventListener("click", () => showCookies(item.domain));

    const actions = document.createElement("div");
    actions.className = "actions";
    actions.append(view, btn);

    row.appendChild(info);
    row.appendChild(actions);
    domainsEl.appendChild(row);
  }
}

async function loadDomains() {
  domainsEl.innerHTML = `<div class="loading">Carregando cookies...</div>`;
  try {
    const cookies = await chrome.cookies.getAll({});
    const map = new Map();
    for (const cookie of cookies) {
      const domain = cleanDomain(cookie.domain || "");
      if (!domain) continue;
      map.set(domain, (map.get(domain) || 0) + 1);
    }
    allDomains = [...map.entries()]
      .map(([domain, cookies]) => ({domain, cookies}))
      .sort((a,b) => a.domain.localeCompare(b.domain));
    render();
  } catch (e) {
    domainsEl.innerHTML = `<div class="empty">Erro ao ler cookies: ${escapeHtml(e.message)}</div>`;
  }
}

async function deleteDomain(domain) {
  if (!confirm(`Apagar TODOS os cookies de "${domain}"?\n\nIsso pode encerrar sua sessão nesse site.`)) return;
  try {
    const cookies = await chrome.cookies.getAll({domain});
    for (const cookie of cookies) {
      const protocol = cookie.secure ? "https:" : "http:";
      const host = cookie.domain.replace(/^\./, "");
      const url = `${protocol}//${host}${cookie.path || "/"}`;
      await chrome.cookies.remove({
        url, name: cookie.name, storeId: cookie.storeId,
        ...(cookie.partitionKey ? {partitionKey: cookie.partitionKey} : {})
      });
    }
    await loadDomains();
  } catch (e) {
    alert("Não foi possível apagar o domínio: " + e.message);
  }
}

function getFilteredDomains() {
  const q = searchEl.value.trim().toLowerCase();
  return allDomains.filter(d => d.domain.toLowerCase().includes(q));
}

function downloadBlob(content, filename, type) {
  const blob = new Blob([content], {type});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function getExportData() {
  const list = getFilteredDomains();
  const result = [];
  for (const item of list) {
    const cookies = await chrome.cookies.getAll({domain: item.domain});
    result.push({
      domain: item.domain,
      adult: isAdultDomain(item.domain),
      cookies
    });
  }
  return result;
}

function cookieFields(cookie) {
  return [
    ["Nome", cookie.name || ""],
    ["Valor", cookie.value || ""],
    ["Domínio", cookie.domain || ""],
    ["Caminho", cookie.path || "/"],
    ["Secure", cookie.secure ? "Sim" : "Não"],
    ["HttpOnly", cookie.httpOnly ? "Sim" : "Não"],
    ["SameSite", cookie.sameSite || "unspecified"],
    ["Sessão", cookie.session ? "Sim" : "Não"],
    ["Expiração", cookie.expirationDate ? new Date(cookie.expirationDate * 1000).toLocaleString("pt-BR") : "Sessão"],
    ["Store ID", cookie.storeId || ""],
    ["HostOnly", cookie.hostOnly ? "Sim" : "Não"],
    ["Partition Key", cookie.partitionKey ? JSON.stringify(cookie.partitionKey) : ""],
    ["SameParty", cookie.sameParty ? "Sim" : "Não"]
  ];
}

async function saveTXT() {
  try {
    const data = await getExportData();
    const totalCookies = data.reduce((n, d) => n + d.cookies.length, 0);
    const lines = [
      "GERENCIADOR DE DOMÍNIOS E COOKIES",
      "=================================",
      `Gerado em: ${new Date().toLocaleString("pt-BR")}`,
      `Total de domínios: ${data.length}`,
      `Total de cookies: ${totalCookies}`,
      "",
      "OS DADOS ABAIXO CORRESPONDEM AOS COOKIES EXIBIDOS NA EXTENSÃO.",
      "ATENÇÃO: cookies podem conter tokens de sessão e outros dados sensíveis.",
      ""
    ];

    for (const d of data) {
      lines.push("============================================================");
      lines.push(`${d.adult ? "[ADULTO]" : "[NORMAL]"} DOMÍNIO: ${d.domain}`);
      lines.push(`TOTAL DE COOKIES: ${d.cookies.length}`);
      lines.push("============================================================");

      if (!d.cookies.length) {
        lines.push("Nenhum cookie encontrado.", "");
        continue;
      }

      d.cookies.forEach((cookie, i) => {
        lines.push(`COOKIE #${i + 1}`);
        lines.push("------------------------------");
        for (const [label, value] of cookieFields(cookie)) {
          lines.push(`${label}: ${value}`);
        }
        lines.push("");
      });
    }

    downloadBlob(lines.join("\n"), "dominios_e_cookies_completos.txt", "text/plain;charset=utf-8");
  } catch (e) {
    alert("Não foi possível salvar o TXT: " + e.message);
  }
}

async function saveHTML() {
  try {
    const data = await getExportData();
    const totalCookies = data.reduce((n, d) => n + d.cookies.length, 0);
    const blocks = data.map(d => {
      const cookieCards = d.cookies.length ? d.cookies.map((cookie, i) => {
        const fields = cookieFields(cookie).map(([label, value]) =>
          `<div class="field"><span>${escapeHtml(label)}</span><code>${escapeHtml(value)}</code></div>`
        ).join("");
        return `<article class="cookie ${d.adult ? "adult-cookie" : ""}"><h3>Cookie #${i + 1}: ${escapeHtml(cookie.name || "(sem nome)")}</h3><div class="grid">${fields}</div></article>`;
      }).join("") : `<p class="empty">Nenhum cookie encontrado.</p>`;

      return `<section class="domain ${d.adult ? "adult-domain" : ""}"><h2>${d.adult ? "⚠ [ADULTO]" : "[NORMAL]"} ${escapeHtml(d.domain)}</h2><p class="summary">${d.cookies.length} cookie${d.cookies.length === 1 ? "" : "s"}</p>${cookieCards}</section>`;
    }).join("");

    const html = `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Domínios e Cookies — Resultado Completo</title>
<style>
*{box-sizing:border-box}body{font-family:Arial,sans-serif;background:#080b0f;color:#e8eef5;margin:0;padding:24px;line-height:1.4}h1{color:#ff7518;margin:0 0 6px}header{border-bottom:1px solid #303a46;padding-bottom:18px;margin-bottom:20px}.meta{color:#9aa6b3}.domain{background:#10171f;border:1px solid #303c49;border-radius:10px;padding:18px;margin:0 0 18px}.adult-domain{border-color:#9c3030;background:#1b1012}.domain h2{margin:0;color:#ff7518;font-size:19px}.adult-domain h2{color:#ff6b6b}.summary{color:#8996a4;margin:5px 0 14px}.cookie{background:#0b1117;border:1px solid #273440;border-radius:8px;padding:14px;margin:10px 0}.adult-cookie{border-color:#663030}.cookie h3{margin:0 0 10px;font-size:14px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.field{background:#111922;border:1px solid #202d38;border-radius:6px;padding:8px;min-width:0}.field span{display:block;color:#7e8b99;font-size:10px;margin-bottom:4px}.field code{display:block;color:#d2dae2;font-family:Consolas,monospace;font-size:12px;white-space:pre-wrap;word-break:break-word}.empty{color:#778391}@media(max-width:700px){.grid{grid-template-columns:1fr}}footer{margin-top:20px;color:#687583;font-size:11px}
</style></head><body><header><h1>🌐 GERENCIADOR DE DOMÍNIOS E COOKIES</h1><div class="meta">Gerado em ${escapeHtml(new Date().toLocaleString("pt-BR"))} • ${data.length} domínios • ${totalCookies} cookies </div></header>${blocks}<footer>Este arquivo contém os mesmos detalhes de cookies apresentados na extensão. Proteja este arquivo, pois valores de cookies podem permitir acesso a sessões.</footer></body></html>`;
    downloadBlob(html, "dominios_e_cookies_completos.html", "text/html;charset=utf-8");
  } catch (e) {
    alert("Não foi possível salvar o HTML: " + e.message);
  }
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;"}[c]));
}

document.getElementById("refresh").addEventListener("click", loadDomains);
searchEl.addEventListener("input", render);
document.getElementById("saveTxt").addEventListener("click", saveTXT);
document.getElementById("saveHtml").addEventListener("click", saveHTML);

async function saveDomainsHTML() {
  try {
    const data = await getExportData();
    const domains = data.map(d => d.domain);
    const adultCount = data.filter(d => d.adult).length;
    const normalCount = data.length - adultCount;
    const rows = data.map((d, i) =>
      `<tr class="${d.adult ? "adult" : ""}"><td>${i + 1}</td><td>${d.adult ? "⚠ [ADULTO]" : "[NORMAL]"}</td><td>${escapeHtml(d.domain)}</td></tr>`
    ).join("");

    const html = `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lista de Domínios</title>
<style>
*{box-sizing:border-box}body{font-family:Arial,sans-serif;background:#080b0f;color:#e8eef5;margin:0;padding:24px}header{border-bottom:1px solid #303a46;padding-bottom:18px;margin-bottom:20px}h1{color:#ff7518;margin:0 0 8px}.meta{color:#9aa6b3}.stats{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}.stat{background:#10171f;border:1px solid #303c49;border-radius:8px;padding:10px 14px}.stat b{color:#ff7518}table{width:100%;border-collapse:collapse;background:#10171f;border-radius:10px;overflow:hidden}th,td{padding:12px;border-bottom:1px solid #28333e;text-align:left}th{background:#18212a;color:#ff7518}tr.adult{background:#241315}tr.adult td:nth-child(2),tr.adult td:nth-child(3){color:#ff6b6b;font-weight:bold}footer{margin-top:18px;color:#687583;font-size:11px}
</style></head><body><header><h1>🌐 LISTA DE DOMÍNIOS</h1><div class="meta">Gerado em ${escapeHtml(new Date().toLocaleString("pt-BR"))} • Somente os domínios encontrados na extensão</div></header><div class="stats"><div class="stat">Total: <b>${domains.length}</b></div><div class="stat">Normais: <b>${normalCount}</b></div><div class="stat">Adultos: <b>${adultCount}</b></div></div><table><thead><tr><th>#</th><th>Classificação</th><th>Domínio</th></tr></thead><tbody>${rows || '<tr><td colspan="3">Nenhum domínio encontrado.</td></tr>'}</tbody></table><footer>Este arquivo contém somente a lista de domínios. Nenhum valor ou detalhe de cookie foi incluído.</footer></body></html>`;
    downloadBlob(html, "apenas_dominios.html", "text/html;charset=utf-8");
  } catch (e) {
    alert("Não foi possível salvar os domínios: " + e.message);
  }
}

document.getElementById("saveDomainsHtml").addEventListener("click", saveDomainsHTML);

async function showCookies(domain) {
  const panel = document.getElementById("cookiePanel");
  const cookiesEl = document.getElementById("cookies");
  const title = document.getElementById("cookieTitle");
  const count = document.getElementById("cookieCount");

  panel.classList.remove("hidden");
  title.textContent = domain;
  cookiesEl.innerHTML = `<div class="loading">Carregando cookies...</div>`;

  try {
    const cookies = await chrome.cookies.getAll({domain});
    count.textContent = `${cookies.length} cookie${cookies.length === 1 ? "" : "s"}`;

    if (!cookies.length) {
      cookiesEl.innerHTML = `<div class="empty">Nenhum cookie encontrado.</div>`;
      return;
    }

    cookiesEl.innerHTML = "";

    for (const cookie of cookies) {
      const card = document.createElement("div");
      card.className = "cookie-card";

      const top = document.createElement("div");
      top.className = "cookie-top";

      const name = document.createElement("strong");
      name.textContent = cookie.name || "(sem nome)";

      const del = document.createElement("button");
      del.className = "cookie-delete";
      del.textContent = "Apagar";
      del.addEventListener("click", () => deleteCookie(cookie, domain));

      top.append(name, del);

      const grid = document.createElement("div");
      grid.className = "cookie-grid";

      const fields = [
        ["Valor", cookie.value || ""],
        ["Domínio", cookie.domain || ""],
        ["Caminho", cookie.path || "/"],
        ["Secure", cookie.secure ? "Sim" : "Não"],
        ["HttpOnly", cookie.httpOnly ? "Sim" : "Não"],
        ["SameSite", cookie.sameSite || "unspecified"],
        ["Sessão", cookie.session ? "Sim" : "Não"],
        ["Expiração", cookie.expirationDate ? new Date(cookie.expirationDate * 1000).toLocaleString() : "Sessão"]
      ];

      for (const [label, value] of fields) {
        const f = document.createElement("div");
        f.className = "cookie-field";
        const l = document.createElement("span");
        l.textContent = label;
        const v = document.createElement("code");
        v.textContent = value;
        f.append(l, v);
        grid.appendChild(f);
      }

      card.append(top, grid);
      cookiesEl.appendChild(card);
    }
  } catch (e) {
    cookiesEl.innerHTML = `<div class="empty">Erro: ${escapeHtml(e.message)}</div>`;
  }
}

async function deleteCookie(cookie, domain) {
  if (!confirm(`Apagar o cookie "${cookie.name}"?`)) return;

  try {
    const protocol = cookie.secure ? "https:" : "http:";
    const host = cookie.domain.replace(/^\./, "");
    const url = `${protocol}//${host}${cookie.path || "/"}`;

    await chrome.cookies.remove({
      url,
      name: cookie.name,
      storeId: cookie.storeId,
      ...(cookie.partitionKey ? {partitionKey: cookie.partitionKey} : {})
    });

    await loadDomains();
    await showCookies(domain);
  } catch (e) {
    alert("Não foi possível apagar o cookie: " + e.message);
  }
}

document.getElementById("closeCookies").addEventListener("click", () => {
  document.getElementById("cookiePanel").classList.add("hidden");
});

loadDomains();


// Divisor arrastável entre a lista de domínios e os cookies.
(() => {
  const workspace = document.querySelector('.workspace');
  const resizer = document.getElementById('resizer');
  if (!workspace || !resizer) return;

  let dragging = false;

  const setWidth = (clientX) => {
    const rect = workspace.getBoundingClientRect();
    let pct = ((clientX - rect.left) / rect.width) * 100;
    pct = Math.max(25, Math.min(65, pct));
    workspace.style.gridTemplateColumns = `minmax(230px, ${pct}%) minmax(340px, ${100-pct}%)`;
    resizer.style.left = `calc(${pct}% - 4px)`;
  };

  resizer.addEventListener('mousedown', (e) => {
    dragging = true;
    resizer.classList.add('dragging');
    document.body.style.userSelect = 'none';
    e.preventDefault();
  });

  window.addEventListener('mousemove', (e) => {
    if (dragging) setWidth(e.clientX);
  });

  window.addEventListener('mouseup', () => {
    if (!dragging) return;
    dragging = false;
    resizer.classList.remove('dragging');
    document.body.style.userSelect = '';
  });
})();
