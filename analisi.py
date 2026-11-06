"""Raggruppamento dei titoli per tema, categoria e punteggio di viralità/importanza."""
import math
import re
import unicodedata
from collections import defaultdict

STOP = set("""
a ad al allo ai agli all agl alla alle con col coi da dal dallo dai dagli dall dagl dalla dalle di del dello dei degli
dell degl della delle in nel nello nei negli nell negl nella nelle su sul sullo sui sugli sull sugl sulla sulle per tra
fra il lo la i gli le un uno una e ed o od ma se che chi cui non ne ci vi si mi ti lui lei noi voi loro questo questa
questi queste quello quella quelli quelle come dove quando perche perché anche ancora gia già piu più meno molto poco
tutto tutti tutte ogni altro altri altra altre essere stato stata stati sono sara sarà era ha hanno ho abbiamo avere
fa fanno fare detto dice dopo prima oggi ieri domani ora anni anno giorno giorni mentre verso senza contro sotto sopra
nuovo nuova nuovi nuove due tre quattro cinque dieci cento mila milioni miliardi primo prima secondo video foto live
diretta news notizie ultima ultime ecco cosa così cosi sempre mai solo ecco via the of and to in for on with at by from
is are was were be has have had will would it its as an this that after over new says said more than about into up out
not no but or how what who why when where his her their they he she we you your our all can could may might
""".split())

PAROLE_CALDE = {
    # parola (radice) : peso
    "ultimor": 3, "urgent": 3, "breaking": 3, "esclusiv": 2, "allarme": 2, "emergen": 2, "strage": 3, "morti": 2,
    "morto": 2, "vittim": 2, "terremot": 3, "esplosi": 2, "attacco": 2, "attacch": 2, "attenta": 3, "guerra": 2,
    "missil": 2, "raid": 2, "bombard": 2, "crisi": 1, "dimissi": 3, "dimette": 3, "elezion": 1, "voto": 1,
    "scandal": 2, "arresta": 2, "arresto": 2, "indagat": 1, "inchiest": 1, "sciopero": 1, "alluvion": 3,
    "incendi": 2, "uragano": 3, "tsunami": 3, "evacua": 2, "killed": 2, "dead": 2, "war": 2, "strike": 1,
    "resign": 3, "earthqua": 3, "shooting": 3, "sparator": 3, "omicidi": 2, "femmini": 2, "record": 1,
    "storico": 1, "shock": 2, "choc": 2, "virale": 2, "polemic": 1, "bufera": 2, "caos": 1, "fiducia": 1,
}

CATEGORIE = {
    "politica": "governo meloni premier ministro ministra parlamento camera senato elezioni voto partito pd fdi lega forza m5s "
                "schlein conte salvini tajani opposizione maggioranza manovra decreto legge riforma quirinale mattarella "
                "palazzo chigi sondaggio referendum regionali comunali sindaco",
    "esteri": "trump putin zelensky netanyahu ucraina russia israele gaza hamas iran cina usa onu nato biden macron "
              "merz starmer xi guerra ue bruxelles commissione europea von der leyen world international",
    "economia": "borsa spread pil inflazione bce tassi mercati euro bitcoin aziende lavoro occupazione stipendi pensioni "
                "tasse fisco banca banche industria export dazi bollette prezzi benzina mutui istat",
    "cronaca": "omicidio arrestato arresto polizia carabinieri incidente morto morta morti indagine procura tribunale "
               "condanna processo femminicidio rapina incendio maltempo alluvione terremoto scomparsa",
    "sport": "calcio serie juventus inter milan napoli roma lazio champions formula ferrari sinner tennis gol partita "
             "allenatore campionato mondiali olimpiadi giro motogp nazionale",
    "spettacolo": "sanremo festival cinema film attore attrice cantante concerto tv serie netflix gossip vip amadeus "
                  "musica album influencer reality",
    "tecnologia": "intelligenza artificiale ia ai apple google meta microsoft openai smartphone app tecnologia social "
                  "cyber hacker spazio nasa",
    "salute": "salute sanità ospedale medici virus vaccino malattia tumore studio ricerca oms covid influenza",
}

_CAT_IDX = {}
for _cat, _parole in CATEGORIE.items():
    for _p in _parole.split():
        _CAT_IDX.setdefault(_p, _cat)


def senza_accenti(t):
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


def tokens(testo):
    """Token normalizzati (radice di 6 lettere) per confrontare i titoli."""
    t = senza_accenti(testo.lower()).replace("'", " ").replace("’", " ")
    out = []
    for w in re.findall(r"[a-z0-9]+", t):
        if len(w) < 3 or w in STOP or w.isdigit():
            continue
        out.append(w[:6])
    return out


def parole_chiave(testo, n=4):
    """Parole significative nella forma originale (per la ricerca sui social)."""
    out = []
    for w in re.findall(r"[\wÀ-ÿ'’]+", testo):
        w = w.strip("'’")
        lw = senza_accenti(w.lower())
        if len(w) < 4 or lw in STOP or w.isdigit():
            continue
        if w not in out:
            out.append(w)
    # preferisci nomi propri
    out.sort(key=lambda w: (not w[:1].isupper(), 0))
    return out[:n]


def categoria(testo, categoria_fonte=None):
    voti = defaultdict(float)
    if categoria_fonte:
        voti[categoria_fonte] += 3
    t = senza_accenti(testo.lower())
    for w in re.findall(r"[a-z0-9]+", t):
        c = _CAT_IDX.get(w)
        if c:
            voti[c] += 1
    for frase in ("palazzo chigi", "intelligenza artificiale", "von der leyen", "serie a", "formula 1"):
        if frase in t:
            voti[_CAT_IDX.get(frase.split()[0], "politica")] += 1
    if not voti:
        return "altro"
    return max(voti.items(), key=lambda kv: kv[1])[0]


def raggruppa(articoli, soglia=0.42):
    """Raggruppa articoli che parlano dello stesso fatto.

    Similarità = somma IDF dei token in comune / somma IDF del titolo più corto, con almeno 2 token in comune.
    """
    df = defaultdict(int)
    for a in articoli:
        a["_tok"] = set(tokens(a["titolo"]))
        for t in a["_tok"]:
            df[t] += 1
    n = max(len(articoli), 1)
    idf = {t: math.log(1 + n / c) for t, c in df.items()}

    def peso(s):
        return sum(idf.get(t, 0) for t in s)

    gruppi = []           # liste di articoli
    indice = defaultdict(set)  # token -> indici dei gruppi
    # prima le fonti più autorevoli, così il titolo di riferimento è il loro
    for a in sorted(articoli, key=lambda x: -x["peso"]):
        if not a["_tok"]:
            continue
        candidati = set()
        for t in a["_tok"]:
            if df[t] <= max(25, n * 0.05):  # ignora token troppo comuni (es. "governo")
                candidati |= indice[t]
        migliore, best = None, 0.0
        for gi in candidati:
            for b in gruppi[gi][:12]:
                comuni = a["_tok"] & b["_tok"]
                if len(comuni) < 2:
                    continue
                sim = peso(comuni) / max(min(peso(a["_tok"]), peso(b["_tok"])), 1e-6)
                if sim > best:
                    best, migliore = sim, gi
        if migliore is not None and best >= soglia:
            gruppi[migliore].append(a)
            gi = migliore
        else:
            gruppi.append([a])
            gi = len(gruppi) - 1
        for t in a["_tok"]:
            indice[t].add(gi)
    return gruppi


def calore(testo):
    tok = tokens(testo)
    punti = 0
    for t in tok:
        for radice, p in PAROLE_CALDE.items():
            r = radice[:6]
            if (len(r) == 6 and t == r) or (len(r) < 6 and (t == r or (len(r) >= 5 and t.startswith(r)))):
                punti += p
                break
    return min(punti, 8)


def punteggio(gruppo, adesso, social=None):
    """Ritorna (punteggio 0-100, dettagli)."""
    testate = {}
    for a in gruppo:
        g = a["gruppo"]
        testate[g] = max(testate.get(g, 0), a["peso"])
    copertura = sum(sorted(testate.values(), reverse=True)[:12])
    ore_ultima = min((adesso - a["data"]).total_seconds() / 3600 for a in gruppo)
    ore_prima = max((adesso - a["data"]).total_seconds() / 3600 for a in gruppo)
    freschezza = 0.5 ** (max(ore_ultima, 0) / 8)
    recenti = sum(1 for a in gruppo if (adesso - a["data"]).total_seconds() < 2 * 3600)
    velocita = recenti / max(min(ore_prima, 6), 1)
    caldo = max(calore(a["titolo"]) for a in gruppo)
    agenzia = any(a["tipo"] == "agenzia" for a in gruppo)
    tg = any(a["tipo"] == "tg" for a in gruppo)

    grezzo = (copertura * 9 + velocita * 6 + caldo * 3 + (4 if agenzia else 0) + (3 if tg else 0)) * (0.35 + 0.65 * freschezza)

    soc = 0.0
    if social:
        for v in social.values():
            inter = (v or {}).get("interazioni") or 0
            if inter:
                soc += 12 * math.log10(1 + inter / 50)
    grezzo += soc

    valore = round(100 * (1 - math.exp(-grezzo / 70)))

    if (len(testate) >= 6 and ore_ultima < 6) or soc >= 30:
        etichetta = "virale"
    elif velocita >= 1.5 and ore_prima < 6:
        etichetta = "in crescita"
    elif caldo >= 3 and len(testate) <= 2:
        etichetta = "potenziale"
    else:
        etichetta = ""

    return valore, {
        "testate": len(testate),
        "copertura": round(copertura, 2),
        "freschezza": round(freschezza, 2),
        "velocita": round(velocita, 2),
        "parole_calde": caldo,
        "social": round(soc, 1),
    }, etichetta
