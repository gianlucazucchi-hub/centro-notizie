/* Centro di controllo notizie: mappa, classifica e popup. */
(function () {
  "use strict";

  const CATEGORIE = {
    tutte: { nome: "Tutte", colore: "#8b949e" },
    politica: { nome: "Politica", colore: "#e5484d" },
    esteri: { nome: "Mondo", colore: "#3e9bff" },
    economia: { nome: "Economia", colore: "#30a46c" },
    cronaca: { nome: "Cronaca", colore: "#f5a524" },
    sport: { nome: "Sport", colore: "#12a594" },
    spettacolo: { nome: "Spettacolo", colore: "#d6409f" },
    tecnologia: { nome: "Tecnologia", colore: "#8e4ec6" },
    salute: { nome: "Salute", colore: "#46a758" },
    altro: { nome: "Altro", colore: "#7d8590" },
  };
  const AGGIORNA_OGNI_MS = 2 * 60 * 1000;
  const GIRO_OGNI_MS = 9000;

  const stato = { vista: "diretta", categoria: "tutte", testo: "", dati: null, storie: [], marker: new Map(), giroIdx: 0, giroTimer: null, sel: null };
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const linkSicuro = (u) => (/^https?:\/\//i.test(u || "") ? u : "#");

  // ---------------------------------------------------------------- mappa
  const mappa = L.map("mappa", { worldCopyJump: true, zoomControl: true, minZoom: 2 }).setView([42.5, 12.5], 4);
  const scuro = window.matchMedia("(prefers-color-scheme: dark)").matches;
  L.tileLayer(`https://{s}.basemaps.cartocdn.com/${scuro ? "dark_all" : "light_all"}/{z}/{x}/{y}{r}.png`, {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
    subdomains: "abcd", maxZoom: 18,
  }).addTo(mappa);
  // sagome dei Paesi sotto le tessere: la mappa resta leggibile anche se le tessere non si caricano
  mappa.createPane("sagome").style.zIndex = 150;
  fetch("vendor/mondo.geojson").then((r) => r.json()).then((g) => {
    L.geoJSON(g, { pane: "sagome", interactive: false, style: { color: scuro ? "#3a4757" : "#b8c2cc", weight: 0.8, fillColor: scuro ? "#1c2632" : "#e9edf1", fillOpacity: 1 } }).addTo(mappa);
  }).catch(() => {});
  const strato = L.layerGroup().addTo(mappa);

  function colorePunteggio(p) {
    if (p >= 80) return "#ff3b30";
    if (p >= 60) return "#ff6b2c";
    if (p >= 40) return "#ff9f0a";
    if (p >= 20) return "#d4a72c";
    return "#6e7681";
  }

  function tempoFa(iso) {
    const min = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
    if (min < 1) return "adesso";
    if (min < 60) return `${min} min fa`;
    const h = Math.round(min / 60);
    if (h < 24) return `${h} ${h === 1 ? "ora" : "ore"} fa`;
    return new Date(iso).toLocaleDateString("it-IT", { day: "numeric", month: "short" });
  }
  const ora = (iso) => new Date(iso).toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });

  function badge(et) {
    if (!et) return "";
    const testo = { virale: "Virale", "in crescita": "In crescita", potenziale: "Potenziale" }[et] || et;
    return `<span class="badge ${et.replace(" ", "-")}">${testo}</span>`;
  }

  function socialHtml(s) {
    const out = [];
    const x = s.social && s.social.x;
    const ig = s.social && s.social.instagram;
    if (x) out.push(`<a href="${esc(linkSicuro(x.ricerca))}" target="_blank" rel="noopener">X: ${x.post} post, ${x.interazioni.toLocaleString("it-IT")} interazioni</a>`);
    if (ig) out.push(`<a href="${esc(linkSicuro(ig.ricerca))}" target="_blank" rel="noopener">Instagram #${esc(ig.hashtag)}: ${ig.interazioni.toLocaleString("it-IT")} interazioni</a>`);
    return out.join("");
  }

  function popupHtml(s) {
    const cat = CATEGORIE[s.categoria] || CATEGORIE.altro;
    const fonti = s.fonti.slice(-8).reverse().map((f) =>
      `<li><a href="${esc(linkSicuro(f.link))}" target="_blank" rel="noopener">${esc(f.fonte)}</a> · ${ora(f.data)}</li>`).join("");
    return `<div class="pop">
      <div class="pop-testa">
        <span class="pop-calore" style="background:${colorePunteggio(s.punteggio)}">${s.punteggio}</span>
        ${badge(s.etichetta)}
        <span class="cat" style="color:${cat.colore}">${cat.nome}</span>
        <span>· ${esc(s.luogo ? s.luogo.luogo : "")}</span>
      </div>
      ${s.immagine ? `<img src="${esc(linkSicuro(s.immagine))}" alt="" loading="lazy" onerror="this.remove()">` : ""}
      <h3><a href="${esc(linkSicuro(s.link))}" target="_blank" rel="noopener">${esc(s.titolo)}</a></h3>
      ${s.sommario ? `<p>${esc(s.sommario)}</p>` : ""}
      <b>${s.dettagli.testate} ${s.dettagli.testate === 1 ? "testata" : "testate"} ne parlano</b>
      <ul>${fonti}</ul>
      <div class="piede"><span>Prima uscita ${tempoFa(s.prima)}</span>${socialHtml(s)}</div>
    </div>`;
  }

  // ---------------------------------------------------------------- dati
  function filtrate() {
    const q = stato.testo.trim().toLowerCase();
    return stato.storie.filter((s) =>
      (stato.categoria === "tutte" || s.categoria === stato.categoria) &&
      (!q || (s.titolo + " " + s.sommario + " " + (s.luogo ? s.luogo.luogo : "") + " " + s.fonti.map((f) => f.titolo).join(" ")).toLowerCase().includes(q)));
  }

  function disegna() {
    const storie = filtrate();
    // classifica
    const lista = $("#lista");
    $("#conteggio").textContent = `${storie.length} storie`;
    if (!storie.length) {
      lista.innerHTML = `<li class="vuoto">Nessuna notizia con questi filtri.</li>`;
    } else {
      lista.innerHTML = storie.slice(0, 150).map((s, i) => {
        const cat = CATEGORIE[s.categoria] || CATEGORIE.altro;
        return `<li class="voce" data-id="${s.id}">
          <div class="calore" style="background:${colorePunteggio(s.punteggio)}" title="Indice di calore">${s.punteggio}</div>
          <div>
            <h3>${i + 1}. ${esc(s.titolo)}</h3>
            <div class="meta">${badge(s.etichetta)}
              <span class="cat" style="color:${cat.colore}">${cat.nome}</span>
              <span>${s.dettagli.testate} testate</span>
              <span>${esc(s.luogo ? s.luogo.luogo : "senza luogo")}</span>
              <span>${tempoFa(s.ultima)}</span>
            </div>
          </div></li>`;
      }).join("");
    }
    // mappa
    strato.clearLayers();
    stato.marker.clear();
    const posti = new Map();
    const conLuogo = storie.filter((s) => s.luogo).slice(0, 200);
    conLuogo.slice().reverse().forEach((s) => {
      const k = `${s.luogo.lat},${s.luogo.lon}`;
      const n = posti.get(k) || 0;
      posti.set(k, n + 1);
      // le storie nello stesso luogo si dispongono a spirale
      const ang = n * 2.4, r = n ? 0.25 + 0.12 * Math.sqrt(n) : 0;
      const lat = s.luogo.lat + r * Math.sin(ang), lon = s.luogo.lon + r * Math.cos(ang) * 1.3;
      const rank = conLuogo.indexOf(s);
      let m;
      if (rank < 5) {
        const d = 26 + Math.round(s.punteggio / 8);
        m = L.marker([lat, lon], {
          icon: L.divIcon({ className: "", html: `<div class="marker-caldo" style="width:${d}px;height:${d}px;background:${colorePunteggio(s.punteggio)}">${s.punteggio}</div>`, iconSize: [d, d], iconAnchor: [d / 2, d / 2], popupAnchor: [0, -d / 2] }),
          zIndexOffset: 1000 - rank,
        });
      } else {
        const cat = CATEGORIE[s.categoria] || CATEGORIE.altro;
        m = L.circleMarker([lat, lon], { radius: 4 + s.punteggio / 9, color: "#fff", weight: 1, fillColor: cat.colore, fillOpacity: 0.85 });
      }
      m.bindPopup(popupHtml(s), { maxWidth: 360, autoPanPadding: [30, 30] });
      m.bindTooltip(esc(s.titolo), { direction: "top", offset: [0, -6] });
      m.on("click", () => { fermaGiro(); evidenzia(s.id); });
      m.addTo(strato);
      stato.marker.set(s.id, m);
    });
  }

  function evidenzia(id) {
    stato.sel = id;
    document.querySelectorAll(".voce.sel").forEach((e) => e.classList.remove("sel"));
    const el = document.querySelector(`.voce[data-id="${id}"]`);
    if (el) { el.classList.add("sel"); el.scrollIntoView({ block: "nearest", behavior: "smooth" }); }
  }

  function apri(id, vola) {
    const m = stato.marker.get(id);
    evidenzia(id);
    if (!m) {
      const s = stato.storie.find((x) => x.id === id);
      if (s) window.open(linkSicuro(s.link), "_blank", "noopener");
      return;
    }
    if (vola) mappa.flyTo(m.getLatLng(), Math.max(mappa.getZoom(), 5), { duration: 1.2 });
    setTimeout(() => m.openPopup(), vola ? 1250 : 0);
  }

  // giro automatico tra le 10 storie più calde con un luogo
  function avviaGiro() {
    fermaGiro();
    if (!$("#giro").checked) return;
    const passo = () => {
      const top = filtrate().filter((s) => s.luogo).slice(0, 10);
      if (!top.length) return;
      const s = top[stato.giroIdx % top.length];
      stato.giroIdx++;
      apri(s.id, true);
    };
    passo();
    stato.giroTimer = setInterval(passo, GIRO_OGNI_MS);
  }
  function fermaGiro() { clearInterval(stato.giroTimer); stato.giroTimer = null; }

  async function carica(url) {
    const r = await fetch(url + (url.includes("?") ? "&" : "?") + "t=" + Date.now(), { cache: "no-store" });
    if (!r.ok) throw new Error(r.status);
    return r.json();
  }

  async function aggiornaDiretta() {
    try {
      const d = await carica("data/notizie.json");
      stato.dati = d;
      if (stato.vista !== "diretta") return;
      stato.storie = d.storie;
      $("#aggiornato").textContent = `Aggiornato alle ${ora(d.aggiornato)} · ${d.articoli_letti} articoli da ${d.fonti.filter((f) => f.ok).length} fonti`;
      $("#avviso-demo").hidden = !d.demo;
      $("#titolo-lista").textContent = "Le più calde ora";
      tendenze(d.tendenze_x);
      disegna();
    } catch (e) {
      $("#aggiornato").textContent = "Dati non ancora disponibili: avvia la raccolta (vedi LEGGIMI).";
    }
  }

  function tendenze(t) {
    const box = $("#tendenze");
    if (!t || !t.length || stato.vista !== "diretta") { box.hidden = true; return; }
    box.hidden = false;
    box.innerHTML = `<b>Tendenze su X in Italia</b><br>` + t.slice(0, 12).map((x) =>
      `<a href="https://x.com/search?q=${encodeURIComponent(x.nome)}" target="_blank" rel="noopener">${esc(x.nome)}</a>`).join("");
  }

  async function caricaMattino(giorno) {
    try {
      const d = await carica(`data/archivio/${giorno}.json`);
      stato.storie = d.storie;
      $("#avviso-demo").hidden = !d.demo;
      const data = new Date(giorno + "T12:00:00").toLocaleDateString("it-IT", { weekday: "long", day: "numeric", month: "long" });
      $("#titolo-lista").textContent = `Rassegna di ${data}`;
      $("#aggiornato").textContent = `Classifica congelata alle ${ora(d.creata)}`;
      disegna();
      avviaGiro();
    } catch (e) {
      stato.storie = [];
      $("#titolo-lista").textContent = "Rassegna del mattino";
      $("#lista").innerHTML = `<li class="vuoto">La rassegna di oggi viene creata alla prima raccolta dopo le 7:00.</li>`;
    }
  }

  async function vistaMattino() {
    const sel = $("#giorno");
    $("#tendenze").hidden = true;
    try {
      const ind = await carica("data/archivio/indice.json");
      sel.innerHTML = ind.giorni.map((g) => `<option value="${g}">${new Date(g + "T12:00:00").toLocaleDateString("it-IT", { weekday: "short", day: "numeric", month: "short" })}</option>`).join("");
      sel.hidden = !ind.giorni.length;
      if (ind.giorni.length) return caricaMattino(sel.value);
    } catch (e) { /* nessun archivio ancora */ }
    sel.hidden = true;
    caricaMattino("oggi-non-disponibile");
  }

  // ---------------------------------------------------------------- interfaccia
  function chips() {
    $("#categorie").innerHTML = Object.entries(CATEGORIE).map(([k, c]) =>
      `<button class="chip${k === stato.categoria ? " attivo" : ""}" data-cat="${k}"><span class="pallino" style="background:${c.colore}"></span>${c.nome}</button>`).join("");
    $("#legenda").innerHTML = Object.entries(CATEGORIE).filter(([k]) => k !== "tutte").map(([, c]) =>
      `<span><i style="background:${c.colore}"></i>${c.nome}</span>`).join("") + `<span>· cerchi numerati = le 5 più calde</span>`;
  }

  $("#categorie").addEventListener("click", (e) => {
    const b = e.target.closest(".chip");
    if (!b) return;
    stato.categoria = b.dataset.cat;
    chips(); disegna(); stato.giroIdx = 0; avviaGiro();
  });
  $("#cerca").addEventListener("input", (e) => { stato.testo = e.target.value; disegna(); });
  $("#giro").addEventListener("change", avviaGiro);
  $("#lista").addEventListener("click", (e) => {
    const v = e.target.closest(".voce");
    if (!v) return;
    fermaGiro(); $("#giro").checked = false;
    apri(v.dataset.id, true);
  });
  document.querySelectorAll(".vista").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll(".vista").forEach((x) => x.classList.toggle("attiva", x === b));
    stato.vista = b.dataset.vista;
    $("#giorno").hidden = stato.vista !== "mattino";
    if (stato.vista === "mattino") vistaMattino(); else aggiornaDiretta().then(avviaGiro);
  }));
  $("#giorno").addEventListener("change", (e) => caricaMattino(e.target.value));

  $("#btn-fonti").addEventListener("click", () => {
    const d = stato.dati;
    if (!d) return;
    $("#social-stato").innerHTML = `<b>Social</b>: X: ${esc(d.social.x)} · Instagram: ${esc(d.social.instagram)}`;
    $("#tab-fonti").innerHTML = d.fonti.map((f) => `<tr><td>${esc(f.nome)}</td><td>${esc(f.tipo)}</td><td>${f.articoli}</td>
      <td class="${f.ok ? "ok" : "ko"}">${f.ok ? "OK" : "Errore: " + esc(f.errore || "")}</td></tr>`).join("");
    $("#dlg-fonti").showModal();
  });

  chips();
  aggiornaDiretta().then(avviaGiro);
  setInterval(() => { if (stato.vista === "diretta") aggiornaDiretta(); }, AGGIORNA_OGNI_MS);
})();
