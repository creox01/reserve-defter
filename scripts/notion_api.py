"""Notion taslak kuyrugu I/O. Kendi token'iyla calisir."""
import os
import time
import requests

API = "https://api.notion.com/v1"
VERSION = "2022-06-28"

MAX_RETRIES = 5  # 429 icin ust sinir; asilirsa fail fast


def _headers():
    token = os.environ["NOTION_TOKEN"]  # yoksa fail fast
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": VERSION,
        "Content-Type": "application/json",
    }


def _db_id():
    return os.environ["NOTION_DB_ID"]  # yoksa fail fast


def _request(method, url, **kwargs):
    """Tek istek yolu. 429'da Notion'in Retry-After suresine uyup tekrar dener."""
    for attempt in range(MAX_RETRIES):
        r = requests.request(method, url, headers=_headers(), timeout=30, **kwargs)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", "1"))
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r
    raise RuntimeError(f"Notion rate limit: {MAX_RETRIES} denemede asilamadi ({url})")


def _paragraphs(markdown_body):
    blocks = []
    for line in markdown_body.split("\n"):
        text = line.strip()
        if not text:
            continue
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]},
        })
    return blocks


def create_draft(baslik, kategori, kaynaklar, yayin_tarihi, body):
    """Taslak olarak bir Notion sayfasi olusturur. Govde sayfa icerigine yazilir."""
    payload = {
        "parent": {"database_id": _db_id()},
        "properties": {
            "Başlık": {"title": [{"text": {"content": baslik}}]},
            "Kategori": {"select": {"name": kategori}},
            "Durum": {"select": {"name": "Taslak"}},
            "Kaynaklar": {"rich_text": [{"text": {"content": kaynaklar[:1900]}}]},
            "Yayın Tarihi": {"date": {"start": yayin_tarihi}},
        },
        "children": _paragraphs(body),
    }
    r = _request("POST", f"{API}/pages", json=payload)
    return r.json()["id"]


def query_by_status(statuses):
    """Verilen Durum degerlerindeki tum sayfalari getirir."""
    filt = {"or": [{"property": "Durum", "select": {"equals": s}} for s in statuses]}
    pages, cursor = [], None
    while True:
        body = {"filter": filt, "page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        r = _request("POST", f"{API}/databases/{_db_id()}/query", json=body)
        data = r.json()
        pages.extend(data["results"])
        if not data.get("has_more"):
            return pages
        cursor = data["next_cursor"]


def existing_source_links():
    """Daha once taslaga giren kaynak linklerini doner. Tekrar uretimini engeller."""
    links = set()
    for p in query_by_status(["Taslak", "Onaylandı", "Yayında", "Arşiv"]):
        rt = p["properties"]["Kaynaklar"]["rich_text"]
        text = "".join(t["plain_text"] for t in rt)
        for token in text.split():
            if token.startswith("http"):
                links.add(token.rstrip(".,)"))
    return links


def page_body(page_id):
    r = _request("GET", f"{API}/blocks/{page_id}/children?page_size=100")
    paras = []
    for b in r.json()["results"]:
        if b["type"] == "paragraph":
            txt = "".join(t["plain_text"] for t in b["paragraph"]["rich_text"])
            if txt:
                paras.append(txt)
    return paras


def mark_published(page_id):
    payload = {"properties": {"Durum": {"select": {"name": "Yayında"}}}}
    _request("PATCH", f"{API}/pages/{page_id}", json=payload)
