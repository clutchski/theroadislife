#!/usr/bin/env python3
"""Extract individual blog entries into Markdown without changing raw captures."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup, SoupStrainer
from markdownify import markdownify

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
CONTENT = ROOT / "content"
PHOTOS = ROOT / "photos"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff", ".ico"}


def yaml_string(value: str) -> str:
    # JSON strings are valid YAML scalars and safely quote punctuation/unicode.
    return json.dumps(value, ensure_ascii=False)


def parse_date(value: str) -> str | None:
    value = " ".join(value.split())
    for fmt in ("%B %d, %Y %I:%M %p", "%B %d, %Y"):
        try:
            return datetime.strptime(value, fmt).isoformat()
        except ValueError:
            pass
    return None


def post_records(manifest: dict, inventory: dict):
    records = []
    failures = []
    for url, index_record in sorted(inventory.items()):
        entry = manifest.get(url)
        if not entry or entry.get("status") != "downloaded" or not entry.get("response"):
            continue
        response = entry["response"]
        source = ROOT / response["path"]
        body = source.read_bytes()
        if hashlib.sha256(body).hexdigest() != response.get("sha256"):
            raise ValueError(f"Raw capture checksum mismatch: {source}")

        # Parsing only #main avoids building the often very large comment subtree.
        soup = BeautifulSoup(body, "html.parser", parse_only=SoupStrainer(id="main"))
        main = soup.select_one("#main")
        if not main:
            failures.append({"source_url": url, "reason": "No #main content region in capture"})
            continue
        title_node = main.find("h1")
        date_node = main.find("h2")
        if not title_node or not date_node:
            failures.append({"source_url": url, "reason": "Post title/date heading not found"})
            continue
        title = " ".join(title_node.get_text(" ", strip=True).split())
        date_text = " ".join(date_node.get_text(" ", strip=True).split())
        published = parse_date(date_text)
        if not published:
            failures.append({"source_url": url, "reason": f"Could not parse publication date: {date_text}"})
            continue

        # Individual pages have previous/next links before the date heading.
        nodes = []
        reached_title = False
        for node in list(main.children):
            if node is title_node:
                reached_title = True
                continue
            if not reached_title:
                continue
            if getattr(node, "name", None) == "h2" and node.get("id") == "comments":
                break
            if node is date_node or (getattr(node, "name", None) == "h2" and node is not title_node):
                continue
            if getattr(node, "name", None) == "h1":
                continue
            if getattr(node, "name", None) == "div" and "info" in (node.get("class") or []):
                continue
            nodes.append(str(node))

        html = "\n".join(nodes)
        fragment = BeautifulSoup(html, "html.parser")
        image_urls = []
        path_part = urlsplit(url).path.lstrip("/")
        output = CONTENT / Path(path_part).with_suffix(".md")
        for image in fragment.find_all("img"):
            src = image.get("src") or image.get("data-src")
            if not src:
                continue
            src = src.strip()
            image["src"] = src
            image_urls.append(src)
            image_entry = manifest.get(canonical(src))
            if image_entry and image_entry.get("status") == "downloaded" and image_entry.get("response"):
                local_path = copy_image(image_entry)
                image["src"] = Path(os.path.relpath(local_path, output.parent)).as_posix()
            # Keep image and following prose distinct in the Markdown rendering.
            if image.parent.name == "a":
                image.parent.insert_after(fragment.new_tag("br"))
                image.parent.insert_after(fragment.new_tag("br"))

        markdown = markdownify(str(fragment), heading_style="ATX", bullets="-").strip()
        permalink = url
        frontmatter = [
            "---",
            f"title: {yaml_string(title)}",
            f"date: {yaml_string(published)}",
            "author: null",
            f"source_url: {yaml_string(permalink)}",
            f"source_capture: {yaml_string(response.get('final_url', ''))}",
            f"source_capture_timestamp: {yaml_string(response.get('capture_timestamp') or '')}",
            f"source_sha256: {yaml_string(response['sha256'])}",
        ]
        if image_urls:
            frontmatter.append("images:")
            frontmatter.extend(f"  - {yaml_string(src)}" for src in dict.fromkeys(image_urls))
        else:
            frontmatter.append("images: []")
        frontmatter += ["comments: preserved_in_raw_capture_not_extracted", "---", "", markdown, ""]

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("\n".join(frontmatter), encoding="utf-8")
        records.append(output)
    return records, failures


def canonical(url: str) -> str:
    p = urlsplit(url)
    host = (p.hostname or "").lower()
    if host in {"theroadislife.com", "www.theroadislife.com"}:
        host = "theroadislife.com"
    return f"https://{host}{p.path or '/'}" + (f"?{p.query}" if p.query else "")


def copy_image(entry: dict) -> Path:
    response = entry["response"]
    source = ROOT / response["path"]
    digest = response["sha256"]
    suffix = Path(urlsplit(entry["original_url"]).path).suffix.lower()
    if suffix not in IMAGE_SUFFIXES:
        suffix = ".img"
    target = PHOTOS / f"{digest}{suffix}"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copyfile(source, target)
    return target


def supporting_records(manifest: dict):
    pages = {
        "https://theroadislife.com/about.htm": ("about", "About Us"),
        "https://theroadislife.com/faq.htm": ("faq", "FAQ"),
        "https://theroadislife.com/thankyou.php": ("thank-you", "Thank You"),
    }
    results = []
    failures = []
    for url, (slug, title) in pages.items():
        entry = manifest.get(url)
        if not entry or entry.get("status") != "downloaded" or not entry.get("response"):
            failures.append({"source_url": url, "reason": "No downloaded raw capture"})
            continue
        response = entry["response"]
        source = ROOT / response["path"]
        body = source.read_bytes()
        if hashlib.sha256(body).hexdigest() != response.get("sha256"):
            raise ValueError(f"Raw capture checksum mismatch: {source}")
        soup = BeautifulSoup(body, "html.parser", parse_only=SoupStrainer(id="main"))
        main = soup.select_one("#main")
        if not main:
            failures.append({"source_url": url, "reason": "No #main content region in capture"})
            continue
        for node in main.select("script,style,form"):
            node.decompose()
        image_urls = []
        output = CONTENT / "pages" / f"{slug}.md"
        for image in main.find_all("img"):
            src = (image.get("src") or image.get("data-src") or "").strip()
            if not src:
                continue
            image["src"] = src
            image_urls.append(src)
            image_entry = manifest.get(canonical(src))
            if image_entry and image_entry.get("status") == "downloaded" and image_entry.get("response"):
                local_path = copy_image(image_entry)
                image["src"] = Path(os.path.relpath(local_path, output.parent)).as_posix()
        markdown = markdownify(str(main), heading_style="ATX", bullets="-").strip()
        frontmatter = [
            "---", f"title: {yaml_string(title)}", "date: null", "author: null",
            "page_type: supporting", f"source_url: {yaml_string(url)}",
            f"source_capture: {yaml_string(response.get('final_url', ''))}",
            f"source_capture_timestamp: {yaml_string(response.get('capture_timestamp') or '')}",
            f"source_sha256: {yaml_string(response['sha256'])}",
        ]
        if image_urls:
            frontmatter.append("images:")
            frontmatter.extend(f"  - {yaml_string(src)}" for src in dict.fromkeys(image_urls))
        else:
            frontmatter.append("images: []")
        frontmatter.extend(["---", "", markdown, ""])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("\n".join(frontmatter), encoding="utf-8")
        results.append(str(output.relative_to(ROOT)))
    return results, failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean", action="store_true", help="Replace generated content/ and photos/ before extraction")
    parser.add_argument("--supporting-only", action="store_true", help="Extract About, FAQ, and Thank You pages without reprocessing posts")
    args = parser.parse_args()
    manifest = json.loads((RAW / "manifest.json").read_text())
    inventory = json.loads((RAW / "post-inventory.json").read_text())
    if args.clean:
        if CONTENT.exists():
            shutil.rmtree(CONTENT)
        if PHOTOS.exists():
            shutil.rmtree(PHOTOS)
    report_path = CONTENT / "extraction-report.json"
    report = json.loads(report_path.read_text()) if args.supporting_only and report_path.exists() else {}
    if args.clean and args.supporting_only:
        parser.error("--clean cannot be combined with --supporting-only")
    if not args.supporting_only:
        records, failures = post_records(manifest, inventory)
        report.update({
            "extracted": len(records), "failed": failures,
            "source_posts": len(inventory),
            "source_capture_unavailable": sum(1 for item in inventory.values() if item.get("status") != "downloaded"),
            "images_downloaded": sum(1 for p in PHOTOS.glob("*")) if PHOTOS.exists() else 0,
        })
        print(f"Extracted {len(records)} posts to content/; copied available local images to photos/")
        print(f"{len(failures)} post source pages could not be extracted.")
    support, support_failures = supporting_records(manifest)
    report["supporting_pages"] = support
    report["supporting_page_failures"] = support_failures
    report["note"] = "Flickr image URLs remain external; raw captures are unchanged."
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"Extracted {len(support)} supporting pages: {', '.join(support)}")


if __name__ == "__main__":
    main()
