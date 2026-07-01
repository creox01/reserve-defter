"""Yayin isi. Onaylanani siteye tasir, satiri Yayında'ya cevirir."""
import os

import notion_api
import render

REQUIRED = ["NOTION_TOKEN", "NOTION_DB_ID"]


def main():
    missing = [k for k in REQUIRED if not os.environ.get(k)]
    if missing:
        raise SystemExit(f"Eksik secret: {', '.join(missing)}")

    pages = notion_api.query_by_status(["Onaylandı", "Yayında"])
    count = render.build(pages, notion_api.page_body)
    print(f"render edilen yazi: {count}")

    for page in pages:
        if page["properties"]["Durum"]["select"]["name"] == "Onaylandı":
            notion_api.mark_published(page["id"])
            print(f"yayina alindi: {page['id']}")


if __name__ == "__main__":
    main()
