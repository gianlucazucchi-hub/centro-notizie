"""Connettore Instagram tramite Instagram Graph API ufficiale (Meta). Niente scraping.

Cosa serve:
  1. Un account Instagram Business o Creator collegato a una Pagina Facebook.
  2. Un'app su https://developers.facebook.com con il permesso "instagram_basic" e la funzione
     "Instagram Public Content Access" (richiede la revisione dell'app da parte di Meta).
  3. Variabili d'ambiente:
       IG_USER_ID       = ID numerico dell'account Instagram Business
       IG_ACCESS_TOKEN  = token di accesso a lunga durata

Limite di Meta: al massimo 30 hashtag diversi ogni 7 giorni per account, quindi il connettore
interroga solo poche storie al giorno (quelle in cima alla classifica) e ricorda gli hashtag già usati.
Per ogni storia prende un hashtag dalla parola chiave principale e somma like e commenti dei post più popolari.
"""
import json
import os
import re
import urllib.parse
import urllib.request

API = "https://graph.facebook.com/v21.0"


def configurato():
    return bool(os.environ.get("IG_USER_ID") and os.environ.get("IG_ACCESS_TOKEN"))


def _get(percorso, parametri):
    parametri = dict(parametri, access_token=os.environ["IG_ACCESS_TOKEN"])
    url = f"{API}{percorso}?{urllib.parse.urlencode(parametri)}"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "CentroNotizie/1.0"}), timeout=20) as r:
        return json.load(r)


def hashtag_da(parole):
    for p in parole:
        h = re.sub(r"[^\w]", "", p.lower())
        if len(h) >= 4:
            return h
    return None


def misura(parole):
    tag = hashtag_da(parole)
    if not tag:
        return None
    uid = os.environ["IG_USER_ID"]
    ris = _get("/ig_hashtag_search", {"user_id": uid, "q": tag}).get("data", [])
    if not ris:
        return {"post": 0, "interazioni": 0, "hashtag": tag}
    media = _get(f"/{ris[0]['id']}/top_media", {"user_id": uid, "fields": "like_count,comments_count,permalink", "limit": 30}).get("data", [])
    inter = sum((m.get("like_count") or 0) + 2 * (m.get("comments_count") or 0) for m in media)
    return {
        "post": len(media),
        "interazioni": inter,
        "hashtag": tag,
        "ricerca": f"https://www.instagram.com/explore/tags/{tag}/",
    }
