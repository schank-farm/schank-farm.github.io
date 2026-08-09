#!/usr/bin/env python3
"""
process_hashed_images.py

1. Scans feed.atom for all Google Photos hashed URLs (/img/a/...).
2. For each hashed URL in an article (e.g. 'chana-masala'):
   - Generates a descriptive filename: <slug>-img-1.jpg, <slug>-img-2.jpg, etc.
   - Downloads the image at full resolution (=s0).
   - Computes the MD5 file signature.
   - Checks if a file in peachy/images/ already has the exact same MD5 signature.
     If matched, renames/copies the local file to <slug>-img-N.jpg and discards download.
     If not matched, saves the downloaded file as peachy/images/<slug>-img-N.jpg.
3. Builds an exact url_to_clean_filename map for convert_blogger.py.
"""

import os
import re
import html
import json
import hashlib
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlparse
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEED_PATH = os.path.join(PROJECT_ROOT, "tools", "feed.atom")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "docs", "images")
MAPPING_CACHE_PATH = os.path.join(PROJECT_ROOT, "tools", "image_hash_map.json")

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "blogger": "http://schemas.google.com/blogger/2018"
}

def compute_file_md5(filepath):
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def get_local_md5_map():
    md5_map = {}
    if not os.path.exists(IMAGES_DIR):
        return md5_map
    for fname in os.listdir(IMAGES_DIR):
        if fname.endswith(".json"):
            continue
        filepath = os.path.join(IMAGES_DIR, fname)
        if os.path.isfile(filepath):
            try:
                file_hash = compute_file_md5(filepath)
                md5_map[file_hash] = fname
            except Exception:
                pass
    return md5_map

def generate_slug(title, filename):
    if filename:
        basename = os.path.basename(filename)
        slug = re.sub(r'\.html$', '', basename, flags=re.IGNORECASE)
        if slug:
            return slug
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
    return slug or "recipe"

def process_images():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    print("Computing MD5 hashes of existing files in docs/images/...")
    local_md5_map = get_local_md5_map()
    print(f"Indexed {len(local_md5_map)} unique local file hashes.")

    tree = ET.parse(FEED_PATH)
    root = tree.getroot()

    url_to_clean_file = {}
    if os.path.exists(MAPPING_CACHE_PATH):
        try:
            with open(MAPPING_CACHE_PATH, "r", encoding="utf-8") as f:
                url_to_clean_file = json.load(f)
            print(f"Loaded {len(url_to_clean_file)} cached URL mappings.")
        except Exception:
            pass

    used_slugs = set()
    downloads_performed = 0
    local_hash_hits = 0

    posts = []
    for entry in root.findall("atom:entry", NS):
        btype = entry.find("blogger:type", NS)
        if btype is not None and btype.text in ["POST", "PAGE"]:
            title_elem = entry.find("atom:title", NS)
            title = title_elem.text.strip() if (title_elem is not None and title_elem.text) else "recipe"
            fn_elem = entry.find("blogger:filename", NS)
            fn = fn_elem.text if fn_elem is not None else ""
            pub_elem = entry.find("atom:published", NS)
            pub_date = pub_elem.text if pub_elem is not None else ""
            content_elem = entry.find("atom:content", NS)
            raw_html = (content_elem.text or "") if content_elem is not None else ""
            posts.append((title, fn, pub_date, raw_html))

    print(f"Processing image references in {len(posts)} articles...")

    for title, fn, pub_date, raw_html in posts:
        slug = generate_slug(title, fn)
        srcs = re.findall(r'src=["\']([^"\']+)["\']', raw_html)

        img_idx = 1
        for s in srcs:
            clean_url = s.split("?")[0].split("#")[0]
            basename = unquote(os.path.basename(clean_url))

            # If URL already has a human-readable filename (e.g. 20years.jpg), Stage 1 handles it
            if re.search(r'\.(jpg|jpeg|png|gif|webp)$', basename, re.IGNORECASE) and not basename.startswith("AVvXs"):
                continue

            # If already processed in cache and file exists
            if s in url_to_clean_file:
                target_name = url_to_clean_file[s]
                if os.path.exists(os.path.join(IMAGES_DIR, target_name)):
                    img_idx += 1
                    continue

            # Determine extension
            ext = ".jpg"
            if ".png" in s.lower():
                ext = ".png"
            elif ".webp" in s.lower():
                ext = ".webp"

            target_filename = f"{slug}-img-{img_idx}{ext}"
            target_path = os.path.join(IMAGES_DIR, target_filename)

            # Download URL at full resolution (=s0)
            dl_url = clean_url
            if not dl_url.endswith("=s0"):
                dl_url = dl_url.split("=")[0] + "=s0"

            try:
                req = urllib.request.Request(dl_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=12) as response:
                    img_bytes = response.read()
                    dl_md5 = hashlib.md5(img_bytes).hexdigest()

                    # Check if an image with this exact MD5 hash already exists locally
                    if dl_md5 in local_md5_map:
                        existing_local_name = local_md5_map[dl_md5]
                        existing_local_path = os.path.join(IMAGES_DIR, existing_local_name)
                        # Copy or save to improved name
                        with open(target_path, "wb") as out_f:
                            with open(existing_local_path, "rb") as in_f:
                                out_f.write(in_f.read())
                        local_hash_hits += 1
                    else:
                        with open(target_path, "wb") as out_f:
                            out_f.write(img_bytes)
                        local_md5_map[dl_md5] = target_filename
                        downloads_performed += 1

                    url_to_clean_file[s] = target_filename
                    print(f"Mapped: {slug} img {img_idx} -> {target_filename}")
            except Exception as e:
                print(f"Warning: Could not download {s}: {e}")

            img_idx += 1

    # Save mapping cache
    with open(MAPPING_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(url_to_clean_file, f, indent=2)

    print(f"\nProcessing complete! Local hash matches: {local_hash_hits}, Downloads saved: {downloads_performed}")
    print(f"Mapping saved to {MAPPING_CACHE_PATH}")

if __name__ == "__main__":
    process_images()
