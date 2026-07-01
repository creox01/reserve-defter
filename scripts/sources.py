# Reserve Defter besleme kaynaklari. Sistematik neffies'ten, icerik Reserve.
# Iki ayak: Hot Dinners native feed (Londra restoran sahnesi) ve tek trade
# sitesinin kapsamadigi kategoriler icin Google News RSS sorgulari.
# Bir feed olse bile tum calisma durmaz, o feed atlanir.

import urllib.parse

_BASE = "https://news.google.com/rss/search"
_LOC = "hl=en-GB&gl=GB&ceid=GB:en"


def _gnews(query):
    return f"{_BASE}?q={urllib.parse.quote(query)}&{_LOC}"


HOT_DINNERS = (
    "https://hot-dinners.com/index.php"
    "?Itemid=2709&format=feed&id=2:hot-dinners-rss-feed"
    "&option=com_joomrss&task=feed"
)

# Anahtarlar kaba ipucu. Nihai kategoriyi LLM, KATEGORILER listesinden atar.
SOURCES = {
    "Londra restoran sahnesi": [HOT_DINNERS],
    "Restoran kapanislari": [_gnews('"London restaurant" (closes OR closed OR closure OR "to close" OR shuts)')],
    "Otel acilislari": [_gnews('London ("hotel opening" OR "new hotel" OR "hotel to open") (restaurant OR dining OR bar)')],
    "Sef transferleri": [_gnews('London chef ("head chef" OR "executive chef" OR joins OR appointed OR departs)')],
    "Michelin": [_gnews('Michelin London (star OR guide OR "Bib Gourmand")')],
    "Yatirim": [_gnews('(restaurant OR hospitality OR "wine bar") UK (investment OR funding OR raises OR acquisition OR "private equity" OR stake)')],
    "Ekonomi": [_gnews('UK hospitality (sales OR trading OR "like-for-like" OR insolvency OR administration OR profit)')],
    "Kira piyasasi": [_gnews('London (restaurant OR hospitality OR leisure OR retail) (rent OR "rent review" OR lease OR "business rates")')],
    "Is gucu": [_gnews('UK hospitality (staff OR wages OR "minimum wage" OR "national insurance" OR recruitment OR shortage)')],
    "Tuketici": [_gnews('UK ("eating out" OR dining OR restaurant) (spending OR consumer OR demand OR trends)')],
    "Mahalleler": [_gnews('London (Fitzrovia OR Clerkenwell OR Marylebone OR Soho OR Shoreditch) (restaurant OR "food scene" OR opening)')],
    "Yasal": [_gnews('UK hospitality (licensing OR regulation OR legislation OR "business rates" OR policy)')],
}

# LLM her secilen yaziya bu 16 etiketten birini atar.
KATEGORILER = [
    "Yeni restoran açılışları",
    "Restoran kapanışları",
    "Otel açılışları",
    "Yeni kafeler",
    "Yeni barlar",
    "Şef transferleri",
    "Michelin haberleri",
    "Pop-up konseptler",
    "Yeni yatırım",
    "Ekonomik gelişmeler",
    "Kira piyasası",
    "İş gücü piyasası",
    "Tüketici davranışı",
    "Öne çıkan mahalleler",
    "Yeni konseptler",
    "Yasal değişiklikler",
]
