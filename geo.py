"""Geolocalizzazione dei titoli tramite un dizionario di luoghi (italiano + inglese).

Nessun servizio esterno: si cercano nomi di città, regioni, Paesi e istituzioni nel testo.
Le voci più specifiche (città) vincono su quelle generiche (Paesi).
Per aggiungere un luogo basta una riga in LUOGHI: "nome": ("Etichetta", lat, lon, "Paese", livello)
livello: 3 = città/istituzione, 2 = regione, 1 = Paese
"""
import re
import unicodedata

L = {}


def _add(nomi, etichetta, lat, lon, paese, livello):
    for n in nomi.split("|"):
        L[n.strip().lower()] = (etichetta, lat, lon, paese, livello)


# --- Italia: istituzioni e luoghi della politica -> Roma
_add("palazzo chigi|montecitorio|quirinale|palazzo madama|viminale|farnesina|campidoglio|governo meloni|consiglio dei ministri", "Roma", 41.9028, 12.4964, "Italia", 3)
_add("vaticano|santa sede|papa leone|papa francesco|pontefice", "Città del Vaticano", 41.9029, 12.4534, "Vaticano", 3)

# --- Italia: città
for riga in """roma|Roma|41.9028|12.4964
milano|Milano|45.4642|9.19
napoli|Napoli|40.8518|14.2681
torino|Torino|45.0703|7.6869
palermo|Palermo|38.1157|13.3615
genova|Genova|44.4056|8.9463
bologna|Bologna|44.4949|11.3426
firenze|Firenze|43.7696|11.2558
bari|Bari|41.1171|16.8719
catania|Catania|37.5079|15.083
venezia|Venezia|45.4408|12.3155
verona|Verona|45.4384|10.9916
messina|Messina|38.1938|15.554
padova|Padova|45.4064|11.8768
trieste|Trieste|45.6495|13.7768
brescia|Brescia|45.5416|10.2118
taranto|Taranto|40.4644|17.247
prato|Prato|43.8777|11.1022
parma|Parma|44.8015|10.3279
modena|Modena|44.6471|10.9252
reggio calabria|Reggio Calabria|38.1113|15.6473
reggio emilia|Reggio Emilia|44.6989|10.6297
perugia|Perugia|43.1107|12.3908
livorno|Livorno|43.5485|10.3106
ravenna|Ravenna|44.4184|12.2035
cagliari|Cagliari|39.2238|9.1217
foggia|Foggia|41.4622|15.5446
rimini|Rimini|44.0678|12.5695
salerno|Salerno|40.6824|14.7681
ferrara|Ferrara|44.8381|11.6198
sassari|Sassari|40.7259|8.5557
latina|Latina|41.4676|12.9037
bergamo|Bergamo|45.6983|9.6773
pescara|Pescara|42.4618|14.2161
trento|Trento|46.0748|11.1217
bolzano|Bolzano|46.4983|11.3548
vicenza|Vicenza|45.5455|11.5354
ancona|Ancona|43.6158|13.5189
l'aquila|L'Aquila|42.3498|13.3995
potenza|Potenza|40.6404|15.8056
campobasso|Campobasso|41.5603|14.6627
aosta|Aosta|45.7375|7.3154
lecce|Lecce|40.3515|18.175
pisa|Pisa|43.7228|10.4017
siena|Siena|43.3188|11.3308
como|Como|45.8081|9.0852
monza|Monza|45.5845|9.2744
novara|Novara|45.4469|8.6215
udine|Udine|46.0711|13.2346
caserta|Caserta|41.0723|14.3311
cosenza|Cosenza|39.2983|16.2537
catanzaro|Catanzaro|38.9098|16.5877
siracusa|Siracusa|37.0755|15.2866
agrigento|Agrigento|37.311|13.5765
trapani|Trapani|38.0176|12.5365
lampedusa|Lampedusa|35.5016|12.6056
crotone|Crotone|39.0808|17.1275
brindisi|Brindisi|40.6327|17.9418
andria|Andria|41.2265|16.2958
pompei|Pompei|40.7462|14.5007
ischia|Ischia|40.7317|13.9431
capri|Capri|40.5532|14.2222
cortina|Cortina d'Ampezzo|46.5405|12.1357
sanremo|Sanremo|43.8159|7.7761
olbia|Olbia|40.9234|9.4964
nuoro|Nuoro|40.3209|9.3296
treviso|Treviso|45.6669|12.243
piacenza|Piacenza|45.0526|9.693
cremona|Cremona|45.1336|10.0227
mantova|Mantova|45.1564|10.7914
lucca|Lucca|43.8429|10.5027
arezzo|Arezzo|43.4633|11.8796
terni|Terni|42.5636|12.6427
viterbo|Viterbo|42.4207|12.1077
frosinone|Frosinone|41.6396|13.3424
avellino|Avellino|40.9146|14.7906
benevento|Benevento|41.1298|14.7826
matera|Matera|40.6664|16.6043
alessandria|Alessandria|44.9133|8.6152
asti|Asti|44.9008|8.2064
cuneo|Cuneo|44.3845|7.5427
savona|Savona|44.3091|8.4772
la spezia|La Spezia|44.1025|9.824
varese|Varese|45.8206|8.8251
lodi|Lodi|45.3138|9.5018
pavia|Pavia|45.1847|9.1582
belluno|Belluno|46.1424|12.2167
pordenone|Pordenone|45.9564|12.6615
gorizia|Gorizia|45.9409|13.6216
teramo|Teramo|42.6589|13.7044
chieti|Chieti|42.351|14.1675
campi flegrei|Campi Flegrei|40.827|14.139
etna|Etna|37.751|14.9934
stromboli|Stromboli|38.7936|15.2133
vesuvio|Vesuvio|40.8224|14.4289""".splitlines():
    n, e, la, lo = riga.split("|")
    _add(n, e, float(la), float(lo), "Italia", 3)

# --- Italia: regioni
for riga in """lombardia|Lombardia|45.5850|9.9300
lazio|Lazio|41.9|12.7
campania|Campania|40.85|14.6
sicilia|Sicilia|37.6|14.15
veneto|Veneto|45.6|11.9
emilia-romagna|emilia romagna|Emilia-Romagna|44.5|11.0
piemonte|Piemonte|45.05|7.9
puglia|Puglia|41.0|16.6
toscana|Toscana|43.4|11.1
calabria|Calabria|39.0|16.5
sardegna|Sardegna|40.1|9.0
liguria|Liguria|44.3|8.7
marche|Marche|43.3|13.1
abruzzo|Abruzzo|42.2|13.8
friuli|friuli venezia giulia|Friuli-Venezia Giulia|46.1|13.1
trentino|alto adige|Trentino-Alto Adige|46.4|11.3
umbria|Umbria|42.95|12.5
basilicata|Basilicata|40.5|16.1
molise|Molise|41.6|14.6
valle d'aosta|Valle d'Aosta|45.73|7.4""".splitlines():
    parti = riga.split("|")
    *nomi, e, la, lo = parti
    _add("|".join(nomi), e, float(la), float(lo), "Italia", 2)

# --- Mondo: città e luoghi simbolo
for riga in """washington|casa bianca|white house|pentagono|pentagon|campidoglio usa|capitol hill|Washington|38.9072|-77.0369|Stati Uniti
new york|onu|nazioni unite|united nations|wall street|New York|40.7128|-74.006|Stati Uniti
los angeles|Los Angeles|34.0522|-118.2437|Stati Uniti
chicago|Chicago|41.8781|-87.6298|Stati Uniti
miami|Miami|25.7617|-80.1918|Stati Uniti
san francisco|silicon valley|San Francisco|37.7749|-122.4194|Stati Uniti
texas|Texas|31.0|-99.0|Stati Uniti
california|California|36.8|-119.4|Stati Uniti
florida|Florida|27.8|-81.7|Stati Uniti
mosca|moscow|cremlino|kremlin|Mosca|55.7558|37.6173|Russia
kiev|kyiv|Kiev|50.4501|30.5234|Ucraina
kharkiv|kharkov|Kharkiv|49.9935|36.2304|Ucraina
odessa|Odessa|46.4825|30.7233|Ucraina
donbass|donbas|donetsk|Donbass|48.0159|37.8028|Ucraina
zaporizhzhia|zaporizhia|Zaporizhzhia|47.8388|35.1396|Ucraina
crimea|Crimea|44.95|34.1|Ucraina
gaza|striscia di gaza|gaza strip|rafah|Gaza|31.5017|34.4668|Palestina
cisgiordania|west bank|Cisgiordania|31.95|35.3|Palestina
gerusalemme|jerusalem|Gerusalemme|31.7683|35.2137|Israele
tel aviv|Tel Aviv|32.0853|34.7818|Israele
beirut|Beirut|33.8938|35.5018|Libano
damasco|damascus|Damasco|33.5138|36.2765|Siria
teheran|tehran|Teheran|35.6892|51.389|Iran
baghdad|Baghdad|33.3152|44.3661|Iraq
il cairo|cairo|Il Cairo|30.0444|31.2357|Egitto
istanbul|Istanbul|41.0082|28.9784|Turchia
ankara|Ankara|39.9334|32.8597|Turchia
bruxelles|brussels|commissione europea|european commission|parlamento europeo|european parliament|Bruxelles|50.8503|4.3517|Belgio
strasburgo|strasbourg|Strasburgo|48.5734|7.7521|Francia
parigi|paris|eliseo|elysee|Parigi|48.8566|2.3522|Francia
londra|london|downing street|Londra|51.5074|-0.1278|Regno Unito
berlino|berlin|Berlino|52.52|13.405|Germania
madrid|Madrid|40.4168|-3.7038|Spagna
barcellona|barcelona|Barcellona|41.3874|2.1686|Spagna
lisbona|lisbon|Lisbona|38.7223|-9.1393|Portogallo
vienna|Vienna|48.2082|16.3738|Austria
ginevra|geneva|Ginevra|46.2044|6.1432|Svizzera
davos|Davos|46.8027|9.836|Svizzera
amsterdam|Amsterdam|52.3676|4.9041|Paesi Bassi
l'aia|the hague|aja|L'Aia|52.0705|4.3007|Paesi Bassi
atene|athens|Atene|37.9838|23.7275|Grecia
varsavia|warsaw|Varsavia|52.2297|21.0122|Polonia
budapest|Budapest|47.4979|19.0402|Ungheria
belgrado|belgrade|Belgrado|44.7866|20.4489|Serbia
pechino|beijing|Pechino|39.9042|116.4074|Cina
shanghai|Shanghai|31.2304|121.4737|Cina
hong kong|Hong Kong|22.3193|114.1694|Cina
taipei|taiwan|Taiwan|23.7|121.0|Taiwan
tokyo|Tokyo|35.6762|139.6503|Giappone
seul|seoul|Seul|37.5665|126.978|Corea del Sud
pyongyang|corea del nord|north korea|Pyongyang|39.0392|125.7625|Corea del Nord
nuova delhi|new delhi|Nuova Delhi|28.6139|77.209|India
mumbai|Mumbai|19.076|72.8777|India
kabul|Kabul|34.5553|69.2075|Afghanistan
islamabad|Islamabad|33.6844|73.0479|Pakistan
dubai|Dubai|25.2048|55.2708|Emirati Arabi Uniti
riad|riyadh|Riad|24.7136|46.6753|Arabia Saudita
doha|Doha|25.2854|51.531|Qatar
tripoli|Tripoli|32.8872|13.1913|Libia
tunisi|tunis|Tunisi|36.8065|10.1815|Tunisia
algeri|algiers|Algeri|36.7538|3.0588|Algeria
khartoum|Khartoum|15.5007|32.5599|Sudan
nairobi|Nairobi|-1.2921|36.8219|Kenya
lagos|Lagos|6.5244|3.3792|Nigeria
johannesburg|Johannesburg|-26.2041|28.0473|Sudafrica
kinshasa|Kinshasa|-4.4419|15.2663|Congo
caracas|Caracas|10.4806|-66.9036|Venezuela
buenos aires|Buenos Aires|-34.6037|-58.3816|Argentina
brasilia|Brasilia|-15.7975|-47.8919|Brasile
rio de janeiro|Rio de Janeiro|-22.9068|-43.1729|Brasile
san paolo|sao paulo|San Paolo|-23.5505|-46.6333|Brasile
città del messico|mexico city|Città del Messico|19.4326|-99.1332|Messico
l'avana|havana|L'Avana|23.1136|-82.3666|Cuba
ottawa|Ottawa|45.4215|-75.6972|Canada
toronto|Toronto|43.6532|-79.3832|Canada
sydney|Sydney|-33.8688|151.2093|Australia
canberra|Canberra|-35.2809|149.13|Australia""".splitlines():
    parti = riga.split("|")
    *nomi, e, la, lo, paese = parti
    _add("|".join(nomi), e, float(la), float(lo), paese, 3)

# --- Mondo: Paesi (nomi, forme inglesi, aggettivi frequenti nei titoli)
for riga in """italia|italy|italiano|italiana|italiani|Italia|42.5|12.5
stati uniti|usa|u.s.|america|united states|americano|americani|statunitense|Stati Uniti|39.8|-98.6
russia|russo|russa|russi|russian|Russia|61.5|90.0
ucraina|ukraine|ucraino|ucraini|ukrainian|Ucraina|48.4|31.2
israele|israel|israeliano|israeliani|israeli|Israele|31.0|34.85
palestina|palestinesi|palestinians|hamas|Palestina|31.9|35.2
libano|lebanon|hezbollah|Libano|33.85|35.86
siria|syria|Siria|34.8|39.0
iran|iraniano|iraniani|Iran|32.4|53.7
iraq|Iraq|33.2|43.7
yemen|houthi|Yemen|15.55|48.5
arabia saudita|saudi arabia|Arabia Saudita|23.9|45.1
egitto|egypt|Egitto|26.8|30.8
turchia|turkey|turkiye|erdogan|Turchia|39.0|35.2
grecia|greece|Grecia|39.07|21.8
francia|france|francese|francesi|macron|Francia|46.6|2.2
germania|germany|tedesco|tedeschi|Germania|51.2|10.45
spagna|spain|spagnolo|Spagna|40.4|-3.7
portogallo|portugal|Portogallo|39.4|-8.2
regno unito|uk|gran bretagna|inghilterra|britain|britannico|Regno Unito|54.0|-2.5
irlanda|ireland|Irlanda|53.4|-8.2
belgio|belgium|Belgio|50.5|4.47
olanda|paesi bassi|netherlands|Paesi Bassi|52.13|5.29
svizzera|switzerland|Svizzera|46.8|8.2
austria|Austria|47.5|14.55
polonia|poland|Polonia|51.9|19.1
ungheria|hungary|orban|Ungheria|47.16|19.5
romania|Romania|45.94|24.97
bulgaria|Bulgaria|42.73|25.49
serbia|Serbia|44.0|21.0
croazia|croatia|Croazia|45.1|15.2
slovenia|Slovenia|46.15|14.99
albania|Albania|41.15|20.17
kosovo|Kosovo|42.6|20.9
bosnia|Bosnia|43.9|17.7
moldavia|moldova|Moldavia|47.4|28.4
bielorussia|belarus|Bielorussia|53.7|27.95
georgia|Georgia|42.3|43.36
armenia|Armenia|40.07|45.04
azerbaigian|azerbaijan|Azerbaigian|40.14|47.58
svezia|sweden|Svezia|60.13|18.64
norvegia|norway|Norvegia|60.47|8.47
finlandia|finland|Finlandia|61.92|25.75
danimarca|denmark|Danimarca|56.26|9.5
groenlandia|greenland|Groenlandia|71.7|-42.6
islanda|iceland|Islanda|64.96|-19.0
cina|china|cinese|cinesi|chinese|Cina|35.86|104.2
giappone|japan|giapponese|Giappone|36.2|138.25
corea del sud|south korea|Corea del Sud|35.9|127.77
india|indiano|Nuova Delhi|20.6|78.96
pakistan|Pakistan|30.38|69.35
afghanistan|talebani|taliban|Afghanistan|33.94|67.71
bangladesh|Bangladesh|23.68|90.36
indonesia|Indonesia|-0.79|113.92
filippine|philippines|Filippine|12.88|121.77
vietnam|Vietnam|14.06|108.28
thailandia|thailand|Thailandia|15.87|100.99
myanmar|birmania|Myanmar|21.9|95.96
australia|Australia|-25.27|133.78
nuova zelanda|new zealand|Nuova Zelanda|-40.9|174.89
canada|Canada|56.13|-106.35
messico|mexico|Messico|23.63|-102.55
cuba|Cuba|21.52|-77.78
venezuela|maduro|Venezuela|6.42|-66.59
colombia|Colombia|4.57|-74.3
brasile|brazil|lula|Brasile|-14.24|-51.93
argentina|milei|Argentina|-38.42|-63.62
cile|chile|Cile|-35.68|-71.54
perù|peru|Perù|-9.19|-75.02
ecuador|Ecuador|-1.83|-78.18
bolivia|Bolivia|-16.29|-63.59
haiti|Haiti|18.97|-72.29
libia|libya|Libia|26.34|17.23
tunisia|Tunisia|33.89|9.54
algeria|Algeria|28.03|1.66
marocco|morocco|Marocco|31.79|-7.09
sudan|Sudan|12.86|30.22
etiopia|ethiopia|Etiopia|9.15|40.49
somalia|Somalia|5.15|46.2
kenya|Kenya|-0.02|37.91
nigeria|Nigeria|9.08|8.68
niger|Niger|17.6|8.08
mali|Mali|17.57|-4.0
senegal|Senegal|14.5|-14.45
congo|Congo|-4.04|21.76
sudafrica|south africa|Sudafrica|-30.56|22.94
ghana|Ghana|7.95|-1.02
tunisia|Tunisia|33.89|9.54
qatar|Qatar|25.35|51.18
emirati|emirati arabi|uae|Emirati Arabi Uniti|23.42|53.85
giordania|jordan|Giordania|30.59|36.24
kazakistan|kazakhstan|Kazakistan|48.02|66.92
corea|Corea|36.5|127.8
europa|ue|unione europea|european union|eu|Unione Europea|50.85|4.35
nato|alleanza atlantica|NATO (Bruxelles)|50.876|4.42""".splitlines():
    parti = riga.split("|")
    *nomi, e, la, lo = parti
    _add("|".join(nomi), e, float(la), float(lo), e, 1)


def _norm(t):
    t = unicodedata.normalize("NFC", t.lower())
    return t.replace("’", "'").replace("`", "'")


# Regex unica, nomi più lunghi prima (così "reggio calabria" vince su "calabria")
_NOMI = sorted(L.keys(), key=len, reverse=True)
_RE = re.compile(r"(?<![\w])(" + "|".join(re.escape(n) for n in _NOMI) + r")(?![\w])")

# Nomi ambigui che contano solo se scritti con maiuscola nel testo originale
_SOLO_MAIUSCOLO = {"georgia", "niger", "eu", "uk", "usa", "nato", "onu", "ue", "india", "corea", "lula", "messina", "cile", "como", "asti", "lodi", "monza", "terni", "trento", "chieti"}


def localizza(testo):
    """Ritorna il luogo più specifico citato nel testo, o None.
    Formato: {"luogo": str, "lat": float, "lon": float, "paese": str, "livello": int}
    """
    if not testo:
        return None
    norm = _norm(testo)
    migliori = []
    for m in _RE.finditer(norm):
        nome = m.group(1)
        if nome in _SOLO_MAIUSCOLO:
            originale = testo[m.start():m.end()]
            if not originale[:1].isupper():
                continue
        etichetta, lat, lon, paese, livello = L[nome]
        # posizione: a parità di livello vince il primo citato
        migliori.append((-livello, m.start(), etichetta, lat, lon, paese, livello))
    if not migliori:
        return None
    migliori.sort()
    _, _, etichetta, lat, lon, paese, livello = migliori[0]
    return {"luogo": etichetta, "lat": lat, "lon": lon, "paese": paese, "livello": livello}
