"""Connettore X (Twitter) tramite API ufficiale v2. Niente scraping.

Cosa serve:
  1. Un account sviluppatore su https://developer.x.com con un piano che includa
     la ricerca dei post recenti (endpoint /2/tweets/search/recent). Il piano gratuito non basta.
  2. Il "Bearer Token" dell'app, da mettere nella variabile d'ambiente X_BEARER_TOKEN.
  3. Facoltativo: X_TENDENZE=1 per leggere le tendenze in Italia (/2/trends/by/woeid/23424853),
     disponibile solo su alcuni piani.

Per ogni storia tra le più calde cerca i post recenti in italiano con le parole chiave del titolo
e somma like, repost, risposte e citazioni: è il segnale di viralità social.
"""
import json
import os
import urllib.parse
import urllib.request

API = "https://api.x.com/2"
WOEID_ITALIA = 23424853


def configurato():
    return bool(os.environ.get("X_BEARER_TOKEN"))


def _get(percorso, parametri):
    url = f"{API}{percorso}?{urllib.parse.urlencode(parametri)}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {os.environ['X_BEARER_TOKEN']}",
        "User-Agent": "CentroNotizie/1.0",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def misura(parole):
    """Ritorna {"post": n, "interazioni": somma, "ricerca": url} per le parole chiave date."""
    if not parole:
        return None
    query = " ".join(f'"{p}"' if " " in p else p for p in parole[:3]) + " lang:it -is:retweet"
    dati = _get("/tweets/search/recent", {
        "query": query,
        "max_results": 50,
        "tweet.fields": "public_metrics,created_at",
    })
    post = dati.get("data", []) or []
    inter = 0
    for p in post:
        m = p.get("public_metrics", {})
        inter += m.get("like_count", 0) + 2 * m.get("retweet_count", 0) + m.get("reply_count", 0) + m.get("quote_count", 0)
    return {
        "post": len(post),
        "interazioni": inter,
        "ricerca": "https://x.com/search?" + urllib.parse.urlencode({"q": " ".join(parole[:3]), "f": "live"}),
    }


def tendenze():
    if not os.environ.get("X_TENDENZE"):
        return []
    dati = _get(f"/trends/by/woeid/{WOEID_ITALIA}", {"max_trends": 20})
    return [{"nome": t.get("trend_name"), "post": t.get("tweet_count")} for t in dati.get("data", [])]
