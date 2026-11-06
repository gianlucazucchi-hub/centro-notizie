# Centro di controllo notizie

Un sito che raccoglie le notizie da agenzie, quotidiani, telegiornali, testate indipendenti e stampa estera, raggruppa gli articoli che parlano dello stesso fatto, li ordina per **indice di calore** (viralità + importanza) e li mostra su una **mappa del mondo navigabile** con popup e una classifica a lato.
Ogni mattina alle 7:00 congela la **Rassegna del mattino** e la conserva in archivio.

## Avvio in 1 minuto (sul tuo computer)

Serve solo Python 3.9 o più recente (su Mac e Linux c'è già; su Windows da python.org). Nessun pacchetto da installare.

```bash
cd centro-notizie
python3 raccogli.py --serve
```

Apri **http://localhost:8000**. La raccolta parte subito e si ripete ogni 10 minuti finché la finestra resta aperta.

Per provarlo senza internet: `python3 raccogli.py --serve --demo` (titoli inventati, segnalati da una fascia gialla).

## Pubblicarlo online gratis, aggiornato da solo (GitHub Pages)

1. Crea un repository **pubblico** su GitHub (es. `centro-notizie`) e caricaci questa cartella.
2. Nel repository: **Settings → Pages → Source: GitHub Actions**.
3. Vai su **Actions → Aggiorna notizie → Run workflow** per il primo giro.

Da lì il sito si aggiorna ogni 15 minuti all'indirizzo `https://<tuo-utente>.github.io/centro-notizie/`, anche a computer spento, e la rassegna delle 7:00 viene salvata nel repository.
(Con un repository privato GitHub Pages richiede un piano a pagamento.)

## Come funziona l'indice di calore (0-100)

Per ogni storia (gruppo di articoli sullo stesso fatto) si sommano:

| Segnale | Cosa misura |
|---|---|
| Copertura | quante testate diverse ne parlano, pesate per autorevolezza (ANSA, Corriere, Rai pesano più di un aggregatore) |
| Velocità | quanti articoli escono nelle ultime 2 ore rispetto a quando la storia è nata |
| Parole calde | "ultim'ora", "terremoto", "dimissioni", "strage", "guerra"... |
| Agenzie e TG | bonus se la riprendono un'agenzia di stampa o un telegiornale |
| Social | interazioni su X e Instagram (quando collegati) |
| Freschezza | tutto si dimezza ogni 8 ore dall'ultimo articolo |

Etichette: **Virale** (6+ testate nelle ultime 6 ore o forte risposta social), **In crescita** (molti articoli in poco tempo), **Potenziale** (parole forti ma ancora poche testate: da tenere d'occhio).

## Personalizzare

- **Fonti**: `config/fonti.json`. Aggiungi o togli feed RSS, cambia il `peso`, disattiva con `"attiva": false`. Il pulsante *Stato fonti* nel sito mostra quali feed rispondono.
- **Orari e finestra**: `config/impostazioni.json` (ora della rassegna, ore di notizie considerate, intervallo di aggiornamento, porta).
- **Luoghi sulla mappa**: `geo.py`, una riga per luogo. Le notizie di politica italiana senza un luogo vengono messe a Roma.
- **Parole calde e categorie**: `analisi.py`.

## Instagram e X (Twitter)

Non si fa scraping: entrambe le piattaforme lo vietano e bloccano gli account. Il programma usa le API ufficiali, che richiedono credenziali.

**X**: serve un account sviluppatore su developer.x.com con un piano che includa la ricerca dei post recenti (il piano gratuito non basta, quelli che la includono sono a pagamento). Poi:
- in locale: `export X_BEARER_TOKEN=...` prima di avviare;
- su GitHub: *Settings → Secrets and variables → Actions → New secret* `X_BEARER_TOKEN`.
- facoltativo: variabile `X_TENDENZE=1` per mostrare le tendenze in Italia (solo con piani che le includono).

**Instagram**: serve un account Instagram Business o Creator collegato a una Pagina Facebook e un'app Meta con accesso "Instagram Public Content Access" (richiede la revisione di Meta). Poi i segreti `IG_USER_ID` e `IG_ACCESS_TOKEN`. Meta consente al massimo 30 hashtag diversi a settimana, quindi il programma controlla solo le 4 storie più calde al giorno.

Senza credenziali tutto il resto funziona normalmente; nel pannello *Stato fonti* vedi "non configurato".

## Struttura

```
raccogli.py            raccolta, raggruppamento, punteggio, rassegna, server locale
analisi.py             raggruppamento titoli, categorie, indice di calore
geo.py                 dizionario dei luoghi per la mappa
connettori/            X e Instagram (API ufficiali)
config/                fonti e impostazioni
site/                  il sito (HTML, CSS, JS, Leaflet incluso)
site/data/             dati generati: notizie.json e archivio delle rassegne
tests/                 feed di prova per la modalità --demo
.github/workflows/     aggiornamento automatico su GitHub
```

Mappa: © OpenStreetMap, © CARTO. Sagome dei Paesi: Natural Earth via world-atlas.
