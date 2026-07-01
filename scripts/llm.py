"""Secim ve yazim. Ses spesifikasyonu sistem talimati olarak kullanilir."""
import pathlib
import anthropic

from sources import KATEGORILER

SELECT_MODEL = "claude-haiku-4-5-20251001"
DRAFT_MODEL = "claude-sonnet-4-6"

_SPEC = pathlib.Path(__file__).with_name("voice_spec.md").read_text(encoding="utf-8")
_client = anthropic.Anthropic()  # ANTHROPIC_API_KEY env'den, yoksa fail fast

_SELECT_TOOL = {
    "name": "secimleri_bildir",
    "description": "Secilen adaylari yapilandirilmis olarak dondur.",
    "input_schema": {
        "type": "object",
        "properties": {
            "secimler": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer"},
                        "kategori": {"type": "string", "enum": KATEGORILER},
                    },
                    "required": ["index", "kategori"],
                },
            }
        },
        "required": ["secimler"],
    },
}

_DRAFT_TOOL = {
    "name": "yaziyi_bildir",
    "description": "Tamamlanan yaziyi yapilandirilmis olarak dondur.",
    "input_schema": {
        "type": "object",
        "properties": {
            "baslik": {"type": "string"},
            "govde": {"type": "string"},
        },
        "required": ["baslik", "govde"],
    },
}


def _tool_input(msg, tool_name):
    for block in msg.content:
        if block.type == "tool_use" and block.name == tool_name:
            return block.input
    raise RuntimeError(f"{tool_name} araci cagrilmadi")


def select(candidates):
    """Adaylardan en fazla 2 yazilmaya degeri secer. candidates: [{title, summary, source, category}]."""
    listing = "\n".join(
        f"[{i}] ({c['category']}) {c['title']} :: {c['summary'][:200]}"
        for i, c in enumerate(candidates)
    )
    system = (
        _SPEC + "\n\nGOREV: Asagidaki adaylardan en fazla 2 tanesini sec. "
        "Bir aday ancak somut bir Reserve cikarimi varsa, 16 kategoriden birine net oturuyorsa "
        "ve genel gecer trend tekrari degilse secilir. kategori alanina nihai kategoriyi ata. "
        "Hicbiri uygun degilse bos liste don."
    )
    msg = _client.messages.create(
        model=SELECT_MODEL, max_tokens=600,
        system=system,
        tools=[_SELECT_TOOL],
        tool_choice={"type": "tool", "name": "secimleri_bildir"},
        messages=[{"role": "user", "content": listing}],
    )
    return _tool_input(msg, "secimleri_bildir")["secimler"]


def draft(item):
    """Secilen tek bir adayi Cem'in sesinde tam yaziya cevirir."""
    user = (
        f"Kategori: {item['kategori']}\n"
        f"Kaynak yayin: {item['source']}\nKaynak baglanti: {item['link']}\n"
        f"Haber basligi: {item['title']}\nHaber ozeti: {item['summary']}\n\n"
        "Bu gelismeyi ses spesifikasyonuna gore tam yaziya cevir. "
        "Govde uc bolumden olusur, her biri kendi basligiyla ve sirasiyla: Ozet, Neden Onemli, Marka Stratejisi."
    )
    msg = _client.messages.create(
        model=DRAFT_MODEL, max_tokens=1500,
        system=_SPEC,
        tools=[_DRAFT_TOOL],
        tool_choice={"type": "tool", "name": "yaziyi_bildir"},
        messages=[{"role": "user", "content": user}],
    )
    return _tool_input(msg, "yaziyi_bildir")
