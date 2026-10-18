"""Render the public overview with explicit pagination and verify every page."""
import argparse
import json
from pathlib import Path
import re
import unicodedata

import pymupdf as fitz


def ascii_text(value: str) -> str:
    value = value.replace("—", " - ").replace("–", "-").replace("’", "'").replace("≤", "<=")
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    text = args.source.read_text(encoding="utf-8")
    sections = re.findall(r"^# Page (\d+) — (.*?)\n\n(.*?)(?=^# Page |\Z)", text, re.M | re.S)
    if len(sections) != 12:
        raise ValueError("Overview requires twelve source sections")
    doc = fitz.open()
    for number, title, body in sections:
        page = doc.new_page(width=595, height=842)
        page.draw_rect(fitz.Rect(0, 0, 595, 82), color=None, fill=(0.06, 0.11, 0.08))
        page.insert_text((44, 41), "SynqHarbor AI", fontsize=22, fontname="hebo", color=(0.87, 0.93, 0.7))
        page.insert_text((44, 61), "One workspace. Human-led. Agent-powered.", fontsize=9, color=(0.86, 0.9, 0.82))
        title_room = page.insert_textbox(fitz.Rect(44, 108, 551, 170), ascii_text(title),
                                        fontsize=20, fontname="hebo", color=(0.12, 0.2, 0.14))
        remaining = page.insert_textbox(fitz.Rect(44, 180, 551, 773), ascii_text(body.strip()),
                                       fontsize=10.5, fontname="helv", lineheight=1.45,
                                       color=(0.2, 0.25, 0.2))
        if remaining < 0 or title_room < 0:
            raise ValueError("Page text overflow: " + number)
        page.draw_line((44, 791), (551, 791), color=(0.8, 0.84, 0.76), width=0.5)
        version = json.loads((Path(__file__).resolve().parents[1] / "package.json").read_text())["version"]
        page.insert_text((44, 809), f"Zahidul Islam | Public technical overview | {version}", fontsize=8, color=(0.35, 0.4, 0.31))
        page.insert_text((503, 809), number + " / 12", fontsize=8, color=(0.35, 0.4, 0.31))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    doc.set_metadata({"title": "SynqHarbor AI - Technical Overview", "author": "Zahidul Islam", "subject": "Architecture, security, operations and scalable platform roadmap"})
    doc.save(args.output, garbage=4, deflate=True)
    doc.close()
    with fitz.open(args.output) as checked:
        if checked.page_count != 12 or any(len(page.get_text()) < 1000 for page in checked):
            raise ValueError("Invalid or incomplete PDF")
    print("Verified public PDF: 12 non-empty pages; no text overflow.")


if __name__ == "__main__":
    main()
