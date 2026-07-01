"""Toplama isi. Gunde 2 kez calisir. Tara, sec, yaz, Notion'a taslak."""
import datetime
import sys
import feedparser

import llm
import notion_api
from sources import SOURCES

REQUIRED = ["ANTHROPIC_API_KEY", "NOTION_TOKEN", "NOTION_DB_ID"]
WINDOW_DAYS = 7
MAX_PER_FEED = 5


def _check_env():
    import os
    missing = [k for k in REQUIRED if not os.environ.get(k)]
    if missing:
        raise SystemExit(f"Eksik secret: {', '.join(missing)}")


def _gather():
    """Tum kaynaklardan son WINDOW_DAYS icindeki adaylari toplar. Olu feed atlanir."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=WINDOW_DAYS)
    candidates = []
    for category, feeds in SOURCES.items():
        for url in feeds:
            try:
                parsed = feedparser.parse(url)
            except Exception as e:
                print(f"feed atlandi {url}: {e}", file=sys.stderr)
                continue
            for entry in parsed.entries[:MAX_PER_FEED]:
                pub = entry.get("published_parsed") or entry.get("updated_parsed")
                if pub:
                    when = datetime.datetime(*pub[:6], tzinfo=datetime.timezone.utc)
                    if when < cutoff:
                        continue
                candidates.append({
                    "title": entry.get("title", "").strip(),
                    "summary": entry.get("summary", "").strip(),
                    "link": entry.get("link", "").strip(),
                    "source": parsed.feed.get("title", url),
                    "category": category,
                })
    return candidates


def main():
    _check_env()
    candidates = _gather()
    if not candidates:
        print("aday yok")
        return

    seen = notion_api.existing_source_links()
    candidates = [c for c in candidates if c["link"] and c["link"] not in seen]
    if not candidates:
        print("yeni aday yok, hepsi daha once islendi")
        return

    chosen = llm.select(candidates)
    if not chosen:
        print("secim bos, bu turda yazi yok")
        return

    today = datetime.date.today().isoformat()
    for pick in chosen:
        item = candidates[pick["index"]]
        item["kategori"] = pick["kategori"]

        written = llm.draft(item)
        kaynaklar = f"{item['source']} :: {item['link']}"

        page_id = notion_api.create_draft(
            baslik=written["baslik"],
            kategori=item["kategori"],
            kaynaklar=kaynaklar,
            yayin_tarihi=today,
            body=written["govde"],
        )
        print(f"taslak yazildi: {written['baslik']} ({page_id})")


if __name__ == "__main__":
    main()
