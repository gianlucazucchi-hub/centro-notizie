"""Genera feed RSS di PROVA (titoli inventati) per testare il sito senza internet: python3 tests/genera_fixture.py"""
import json
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

ADESSO = datetime(2026, 11, 5, 7, 30, tzinfo=timezone.utc)
CART = Path(__file__).parent / "fixtures"

# (minuti fa, fonte, titolo)
STORIE = [
    [(40, "ansa-politica", "Manovra, il Consiglio dei ministri approva il testo: le misure su pensioni e tasse"),
     (35, "corriere", "Manovra approvata dal Consiglio dei ministri: cosa cambia per pensioni e tasse"),
     (30, "repubblica", "Manovra, via libera del Consiglio dei ministri. Opposizione all'attacco su pensioni"),
     (25, "skytg24", "Manovra, ok del Consiglio dei ministri: le novità su pensioni e tasse"),
     (20, "ilpost", "Cosa c'è nella manovra approvata dal Consiglio dei ministri"),
     (15, "rainews", "Consiglio dei ministri approva la manovra: pensioni, tasse e bonus"),
     (12, "fanpage", "Manovra approvata, cosa cambia su pensioni e tasse per le famiglie"),
     (10, "gnews-it", "Manovra, il Consiglio dei ministri approva: tutte le misure su pensioni - Il Sole 24 Ore")],
    [(90, "ansa-mondo", "Terremoto di magnitudo 6.8 in Giappone, allerta tsunami sulla costa vicino Tokyo"),
     (80, "bbc", "Japan earthquake: magnitude 6.8 quake triggers tsunami warning near Tokyo"),
     (75, "corriere", "Terremoto in Giappone di magnitudo 6.8, scatta l'allerta tsunami"),
     (60, "skytg24", "Giappone, terremoto magnitudo 6.8: allerta tsunami ed evacuazioni"),
     (50, "tgcom24", "Forte terremoto in Giappone, magnitudo 6.8: allerta tsunami"),
     (30, "open", "Terremoto in Giappone, magnitudo 6.8: le immagini dell'allerta tsunami")],
    [(120, "ansa-mondo", "Gaza, nuovi raid nella notte: decine di vittime nella Striscia"),
     (100, "repubblica", "Gaza, raid nella notte sulla Striscia: decine di vittime"),
     (70, "aljazeera", "Gaza: dozens killed in overnight Israeli raids across the Strip"),
     (65, "rainews", "Striscia di Gaza, raid notturni: decine di vittime")],
    [(200, "ansa-economia", "Borsa di Milano in rialzo, spread in calo sotto i 100 punti"),
     (150, "sole24ore", "Piazza Affari apre in rialzo, spread sotto quota 100 punti"),
     (130, "tgcom24", "Borsa Milano positiva, spread in calo sotto i 100 punti")],
    [(45, "ansa-cronaca", "Alluvione in Toscana, evacuate 300 persone a Prato: allerta rossa"),
     (40, "repubblica", "Maltempo, alluvione a Prato: evacuate 300 persone, allerta rossa in Toscana"),
     (32, "fanpage", "Alluvione Prato, 300 evacuati: allerta rossa in Toscana"),
     (28, "skytg24", "Allerta rossa in Toscana, alluvione a Prato: 300 persone evacuate"),
     (18, "today", "Alluvione a Prato, evacuate 300 persone: le immagini")],
    [(300, "ansa-mondo", "Ucraina, attacco con droni su Kharkiv nella notte: feriti e blackout"),
     (280, "bbc", "Ukraine: drone attack on Kharkiv leaves injured and blackouts"),
     (260, "skytg24", "Kharkiv, attacco con droni russi nella notte: feriti e blackout")],
    [(70, "ansa", "Sanremo, annunciati i conduttori del Festival: polemica sui social"),
     (55, "fanpage", "Festival di Sanremo, i conduttori annunciati: la polemica sui social")],
    [(25, "ansa-politica", "Ultim'ora: si dimette il presidente della Regione Liguria, indagine a Genova"),
     (20, "open", "Genova, dimissioni del presidente della Regione Liguria dopo l'inchiesta")],
    [(400, "nyt", "White House announces new tariffs on European imports"),
     (380, "ansa-mondo", "Casa Bianca, nuovi dazi sulle importazioni europee"),
     (350, "sole24ore", "Dazi, la Casa Bianca annuncia nuove tariffe sulle importazioni europee"),
     (300, "corriere", "Nuovi dazi della Casa Bianca su importazioni europee: la reazione di Bruxelles")],
    [(150, "guardian", "Brazil: floods in Rio de Janeiro leave thousands displaced")],
    [(60, "ilpost", "Il nuovo stadio di Milano, a che punto è il progetto")],
    [(95, "ansa", "Inter, vittoria in Champions League: tre gol a Madrid"),
     (85, "skytg24", "Champions League, Inter vince a Madrid con tre gol"),
     (80, "tgcom24", "Inter, tre gol a Madrid in Champions League")],
    [(500, "internazionale", "In Sudan la crisi umanitaria peggiora: milioni di sfollati a Khartoum")],
    [(35, "ansa", "Intelligenza artificiale, il Parlamento europeo vota le nuove regole a Strasburgo"),
     (30, "huffpost", "Strasburgo, il Parlamento europeo vota le regole sull'intelligenza artificiale")],
]

def main():
    CART.mkdir(parents=True, exist_ok=True)
    per_fonte = {}
    for i, storia in enumerate(STORIE):
        for minuti, fonte, titolo in storia:
            per_fonte.setdefault(fonte, []).append((ADESSO - timedelta(minutes=minuti), titolo, f"https://esempio.invalid/{fonte}/{i}-{minuti}"))
    for fonte, voci in per_fonte.items():
        items = "".join(
            f"<item><title>{escape(t)}</title><link>{escape(l)}</link><description>{escape('Testo di prova: ' + t + '. Questo articolo non esiste, serve solo a provare il sito.')}</description><pubDate>{format_datetime(d)}</pubDate></item>"
            for d, t, l in voci)
        (CART / f"{fonte}.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{fonte} (prova)</title>{items}</channel></rss>', encoding="utf-8")
    (CART / "demo.json").write_text(json.dumps({"adesso": ADESSO.isoformat()}))
    print(f"{len(per_fonte)} feed di prova scritti in {CART}")

if __name__ == "__main__":
    main()
