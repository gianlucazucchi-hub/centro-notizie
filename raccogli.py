#!/usr/bin/env python3
"""Centro di controllo notizie: raccoglie i feed, raggruppa, assegna il punteggio e scrive site/data/notizie.json.

Uso:
  python3 raccogli.py            # un giro di raccolta (per cron o GitHub Actions)
  python3 raccogli.py --serve    # raccolta continua + sito su http://localhost:8000
  python3 raccogli.py --demo     # usa i feed di prova in tests/fixtures (senza internet)

Solo libreria standard di Python 3.9+: nessuna installazione richiesta.
"""
import argparse
import concurrent.futures as cf
import email.utils
import hashlib
import html
import json
import os
import re
import sys
import threading
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

import analisi
import geo
from connettori import instagram, x_twitter

BASE = Path(__file__).resolve().parent
SITO = BASE / "site"
DATI = SITO / "data"
ARCHIVIO = DATI / "archivio"
CACHE_SOCIAL = BASE / "cache_social.json"
UA = "Mozilla/5.0 (compatible; CentroNotizie/1.0; rassegna stampa personale)"


def carica_json(p, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def scrivi_json(p, dati):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(dati, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, p)


# ---------------------------------------------------------------- lettura feed

def scarica(url, demo=False):
    if demo:
        return (BASE / "tests" / "fixtures" / f"{url}.xml").read_bytes()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, text/xml, */*"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def _testo(el):
    if el is None:
        return ""
    return "".join(el.itertext()).strip()


def pulisci(t, n=None):
    t = html.unescape(re.sub(r"<[^>]+>", " ", html.unescape(t or "")))
    t = re.sub(r"\s+", " ", t).strip()
    if n and len(t) > n:
        t = t[: n - 1].rsplit(" ", 1)[0] + "…"
    return t


def data_da(t):
    if not t:
        return None
    t = t.strip()
    try:
        d = email.utils.parsedate_to_datetime(t)
    except (TypeError, ValueError):
        d = None
    if d is None:
        try:
            d = datetime.fromisoformat(t.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=ZoneInfo("Europe/Rome"))
    return d.astimezone(timezone.utc)


def analizza_feed(xml_bytes):
    """Legge RSS 2.0, RDF/RSS 1.0 e Atom. Ritorna [{titolo, link, sommario, data, immagine}]."""
    radice = ET.fromstring(xml_bytes)
    voci = []
    for el in radice.iter():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag not in ("item", "entry"):
            continue
        campi = {}
        immagine = None
        for c in el:
            ct = c.tag.rsplit("}", 1)[-1].lower()
            if ct == "link":
                href = c.get("href")
                if href and c.get("rel", "alternate") == "alternate":
                    campi.setdefault("link", href)
                elif _testo(c):
                    campi.setdefault("link", _testo(c))
            elif ct in ("title",):
                campi["titolo"] = _testo(c)
            elif ct in ("enclosure", "content", "thumbnail") and c.get("url"):
                if (c.get("type") or c.get("medium") or "image").startswith("image") or ct == "thumbnail":
                    immagine = immagine or c.get("url")
            elif ct in ("description", "summary", "content", "encoded") and not campi.get("sommario"):
                campi["sommario"] = _testo(c)
            elif ct in ("pubdate", "published", "updated", "date", "issued"):
                campi.setdefault("data", _testo(c))
        if not campi.get("titolo"):
            continue
        if not immagine and campi.get("sommario"):
            m = re.search(r'<img[^>]+src="([^"]+)"', html.unescape(campi["sommario"]))
            if m:
                immagine = m.group(1)
        voci.append({
            "titolo": pulisci(campi["titolo"]),
            "link": (campi.get("link") or "").strip(),
            "sommario": pulisci(campi.get("sommario"), 320),
            "data": data_da(campi.get("data")),
            "immagine": immagine,
        })
    return voci


def leggi_fonte(fonte, adesso, finestra, demo):
    stato = {"id": fonte["id"], "nome": fonte["nome"], "tipo": fonte["tipo"], "ok": False, "articoli": 0}
    try:
        voci = analizza_feed(scarica(fonte["id"] if demo else fonte["url"], demo))
    except Exception as e:  # rete, XML non valido, ecc.
        stato["errore"] = f"{type(e).__name__}: {str(e)[:120]}"
        return stato, []
    articoli = []
    for v in voci:
        d = v["data"] or adesso
        if d > adesso + timedelta(minutes=10):
            d = adesso
        if adesso - d > finestra:
            continue
        # Google Notizie aggiunge " - Testata" in fondo al titolo
        titolo = v["titolo"]
        testata = fonte["nome"]
        if fonte["tipo"] == "aggregatore" and " - " in titolo:
            titolo, testata = titolo.rsplit(" - ", 1)
            testata = f"{testata} (via {fonte['nome']})"
        articoli.append({
            "titolo": titolo,
            "link": v["link"],
            "sommario": v["sommario"] if v["sommario"] != titolo else "",
            "data": d,
            "immagine": v["immagine"],
            "fonte": testata,
            "fonte_id": fonte["id"],
            "gruppo": fonte["id"].split("-")[0] if fonte["tipo"] != "aggregatore" else "agg:" + testata.lower(),
            "tipo": fonte["tipo"],
            "peso": float(fonte.get("peso", 1.0)),
            "categoria_fonte": fonte.get("categoria"),
        })
    stato.update(ok=True, articoli=len(articoli))
    return stato, articoli


# ---------------------------------------------------------------- social

def arricchisci_social(storie, imp, adesso):
    stato = {
        "x": "attivo" if x_twitter.configurato() else "non configurato (manca X_BEARER_TOKEN)",
        "instagram": "attivo" if instagram.configurato() else "non configurato (mancano IG_USER_ID e IG_ACCESS_TOKEN)",
    }
    tendenze = []
    if not (x_twitter.configurato() or instagram.configurato()):
        return stato, tendenze
    cache = carica_json(CACHE_SOCIAL, {})
    oggi = adesso.date().isoformat()
    ig_usati_oggi = sum(1 for v in cache.values() if v.get("ig_giorno") == oggi)
    for s in storie[: imp.get("social_storie_da_verificare", 15)]:
        chiave = hashlib.sha1(" ".join(s["parole_chiave"]).lower().encode()).hexdigest()[:12]
        voce = cache.get(chiave, {})
        s.setdefault("social", {})
        if x_twitter.configurato():
            if voce.get("x") and time.time() - voce.get("x_ts", 0) < 3600:
                s["social"]["x"] = voce["x"]
            else:
                try:
                    voce["x"] = x_twitter.misura(s["parole_chiave"])
                    voce["x_ts"] = time.time()
                    s["social"]["x"] = voce["x"]
                except Exception as e:
                    stato["x"] = f"errore: {str(e)[:100]}"
        if instagram.configurato():
            if voce.get("ig"):
                s["social"]["instagram"] = voce["ig"]
            elif ig_usati_oggi < 4:   # Meta: max 30 hashtag/settimana
                try:
                    voce["ig"] = instagram.misura(s["parole_chiave"])
                    voce["ig_giorno"] = oggi
                    ig_usati_oggi += 1
                    s["social"]["instagram"] = voce["ig"]
                except Exception as e:
                    stato["instagram"] = f"errore: {str(e)[:100]}"
        cache[chiave] = voce
    if x_twitter.configurato():
        try:
            tendenze = x_twitter.tendenze()
        except Exception as e:
            stato["x_tendenze"] = f"errore: {str(e)[:100]}"
    scrivi_json(CACHE_SOCIAL, cache)
    return stato, tendenze


# ---------------------------------------------------------------- raccolta

def costruisci_storia(gruppo, adesso):
    gruppo.sort(key=lambda a: (-a["peso"], a["data"]))
    rif = gruppo[0]
    testo = " ".join(a["titolo"] + ". " + a["sommario"] for a in gruppo[:6])
    luogo = geo.localizza(" ".join(a["titolo"] for a in gruppo[:6])) or geo.localizza(testo)
    cat = analisi.categoria(" ".join(a["titolo"] for a in gruppo), rif.get("categoria_fonte") or next((a["categoria_fonte"] for a in gruppo if a["categoria_fonte"]), None))
    if luogo and luogo["paese"] not in ("Italia", "Vaticano") and cat in ("cronaca", "politica", "altro"):
        cat = "esteri"
    if luogo is None and cat == "politica":
        luogo = {"luogo": "Roma", "lat": 41.9028, "lon": 12.4964, "paese": "Italia", "livello": 0}
    fonti, visti = [], set()
    for a in sorted(gruppo, key=lambda a: a["data"]):
        if (a["fonte"], a["titolo"]) in visti:
            continue
        visti.add((a["fonte"], a["titolo"]))
        fonti.append({"fonte": a["fonte"], "titolo": a["titolo"], "link": a["link"], "data": a["data"].isoformat(), "tipo": a["tipo"]})
    sommario = next((a["sommario"] for a in gruppo if len(a["sommario"]) > 40), "")
    return {
        "id": hashlib.sha1((rif["link"] or rif["titolo"]).encode()).hexdigest()[:10],
        "titolo": rif["titolo"],
        "sommario": sommario,
        "link": rif["link"],
        "immagine": next((a["immagine"] for a in gruppo if a["immagine"]), None),
        "fonte": rif["fonte"],
        "categoria": cat,
        "luogo": luogo,
        "prima": min(a["data"] for a in gruppo).isoformat(),
        "ultima": max(a["data"] for a in gruppo).isoformat(),
        "fonti": fonti[:25],
        "parole_chiave": analisi.parole_chiave(rif["titolo"]),
        "_gruppo": gruppo,
    }


def raccogli(demo=False):
    imp = carica_json(BASE / "config" / "impostazioni.json", {})
    fonti = [f for f in carica_json(BASE / "config" / "fonti.json", {"fonti": []})["fonti"] if f.get("attiva", True)]
    adesso = datetime.now(timezone.utc)
    if demo:
        adesso = datetime.fromisoformat(carica_json(BASE / "tests" / "fixtures" / "demo.json", {}).get("adesso", adesso.isoformat()))
    finestra = timedelta(hours=imp.get("finestra_ore", 36))

    if demo:
        fonti = [f for f in fonti if (BASE / "tests" / "fixtures" / f"{f['id']}.xml").exists()]
    articoli, stati = [], []
    with cf.ThreadPoolExecutor(max_workers=12) as ex:
        for stato, arts in ex.map(lambda f: leggi_fonte(f, adesso, finestra, demo), fonti):
            stati.append(stato)
            articoli.extend(arts)

    # elimina doppioni esatti (stesso link)
    unici = {}
    for a in articoli:
        unici.setdefault(a["link"] or a["titolo"], a)
    articoli = list(unici.values())

    gruppi = analisi.raggruppa(articoli)
    storie = [costruisci_storia(g, adesso) for g in gruppi]
    for s in storie:
        s["punteggio"], s["dettagli"], s["etichetta"] = analisi.punteggio(s["_gruppo"], adesso)
    storie.sort(key=lambda s: -s["punteggio"])

    social_stato, tendenze = arricchisci_social(storie, imp, adesso) if not demo else (
        {"x": "non configurato (manca X_BEARER_TOKEN)", "instagram": "non configurato (mancano IG_USER_ID e IG_ACCESS_TOKEN)"}, [])
    for s in storie:
        if s.get("social"):
            s["punteggio"], s["dettagli"], s["etichetta"] = analisi.punteggio(s["_gruppo"], adesso, s["social"])
    storie.sort(key=lambda s: (-s["punteggio"], s["ultima"]))
    for i, s in enumerate(storie, 1):
        s["posizione"] = i
        s.pop("_gruppo", None)
    storie = storie[: imp.get("storie_massime", 300)]

    fuso = ZoneInfo(imp.get("fuso_orario", "Europe/Rome"))
    risultato = {
        "aggiornato": adesso.isoformat(),
        "fuso_orario": imp.get("fuso_orario", "Europe/Rome"),
        "demo": demo,
        "articoli_letti": len(articoli),
        "fonti": sorted(stati, key=lambda s: (s["ok"], s["nome"])),
        "social": social_stato,
        "tendenze_x": tendenze,
        "storie": storie,
    }
    scrivi_json(DATI / "notizie.json", risultato)
    salva_rassegna(risultato, imp, adesso.astimezone(fuso))
    ok = sum(1 for s in stati if s["ok"])
    print(f"[{adesso.astimezone(fuso):%d/%m %H:%M}] fonti ok {ok}/{len(stati)} · articoli {len(articoli)} · storie {len(storie)}", flush=True)
    return risultato


def salva_rassegna(risultato, imp, ora_locale):
    """La prima raccolta dopo l'ora della rassegna (es. 07:00) congela la classifica del mattino."""
    hh, mm = map(int, imp.get("ora_rassegna_mattino", "07:00").split(":"))
    if (ora_locale.hour, ora_locale.minute) < (hh, mm):
        return
    giorno = ora_locale.date().isoformat()
    file = ARCHIVIO / f"{giorno}.json"
    if file.exists() and not risultato.get("demo") and not carica_json(file, {}).get("demo"):
        return  # la rassegna di oggi è già stata congelata
    n = imp.get("storie_in_rassegna", 30)
    scrivi_json(file, {
        "giorno": giorno,
        "creata": risultato["aggiornato"],
        "demo": risultato.get("demo", False),
        "storie": risultato["storie"][:n],
    })
    giorni = sorted((p.stem for p in ARCHIVIO.glob("????-??-??.json")), reverse=True)
    scrivi_json(ARCHIVIO / "indice.json", {"giorni": giorni[:60]})


# ---------------------------------------------------------------- server locale

def servi(imp, demo):
    porta = int(os.environ.get("PORT", imp.get("porta", 8000)))
    intervallo = max(int(imp.get("intervallo_minuti", 10)), 2) * 60

    def ciclo():
        while True:
            try:
                raccogli(demo)
            except Exception as e:
                print("Errore nella raccolta:", e, file=sys.stderr, flush=True)
            time.sleep(intervallo)

    threading.Thread(target=ciclo, daemon=True).start()

    class Gestore(SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def end_headers(self):
            if self.path.startswith("/data/"):
                self.send_header("Cache-Control", "no-store")
            super().end_headers()

    srv = ThreadingHTTPServer(("0.0.0.0", porta), partial(Gestore, directory=str(SITO)))
    print(f"Centro di controllo attivo su http://localhost:{porta}  (aggiornamento ogni {intervallo // 60} minuti, Ctrl+C per uscire)", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Centro di controllo notizie")
    ap.add_argument("--serve", action="store_true", help="raccolta continua + sito locale")
    ap.add_argument("--demo", action="store_true", help="usa i feed di prova offline")
    args = ap.parse_args()
    if args.serve:
        servi(carica_json(BASE / "config" / "impostazioni.json", {}), args.demo)
    else:
        raccogli(args.demo)
