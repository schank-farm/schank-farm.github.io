#!/usr/bin/env python3
"""
convert_blogger.py - Blogger Atom XML Feed to Hugo Markdown Converter

Converts Google Takeout export for 'Peachy Keen Green':
- Reads feed.atom and images/ in the project root.
- Uses tools/image_hash_map.json (built by process_hashed_images.py) for exact URL -> file mapping.
- Converts HTML content to clean Markdown format without Blogger table/style clutter.
- Generates individual Hugo Markdown post files in src/ with YAML frontmatter.
"""

import os
import re
import html
import json
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlparse
from datetime import datetime

# Namespaces used in Blogger Takeout Atom feed
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "blogger": "http://schemas.google.com/blogger/2018"
}

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEED_PATH = os.path.join(PROJECT_ROOT, "tools", "feed.atom")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "docs", "images")
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
HASH_MAP_PATH = os.path.join(PROJECT_ROOT, "tools", "image_hash_map.json")

def get_image_resolution_maps():
    """
    Build:
    1. local_file_map: lowercase filename -> actual filename
    2. hash_map: URL string -> clean target filename (from process_hashed_images.py)
    """
    local_file_map = {}
    if os.path.exists(IMAGES_DIR):
        for fname in os.listdir(IMAGES_DIR):
            if not fname.endswith(".json"):
                local_file_map[fname.lower()] = fname

    hash_map = {}
    if os.path.exists(HASH_MAP_PATH):
        try:
            with open(HASH_MAP_PATH, "r", encoding="utf-8") as f:
                hash_map = json.load(f)
        except Exception:
            pass

    return local_file_map, hash_map

def extract_filename_from_url(url):
    """Extract and unquote the trailing filename from a Blogger image URL."""
    if not url:
        return ""
    clean_url = url.split("?")[0].split("#")[0]
    path = urlparse(clean_url).path
    filename = unquote(os.path.basename(path))
    return filename

def resolve_image_path(url, local_file_map, hash_map):
    """
    Resolution Order:
    1. Hash map lookup (from process_hashed_images.py)
    2. Exact URL filename lookup in local_file_map (e.g. 20years.jpg)
    """
    if url in hash_map:
        target_name = hash_map[url]
        return f"/images/{target_name}", target_name

    filename = extract_filename_from_url(url)
    if filename and filename.lower() in local_file_map:
        actual_name = local_file_map[filename.lower()]
        return f"/images/{actual_name}", actual_name

    return url, ""

def clean_html_content(raw_html, local_file_map, hash_map):
    """
    Convert Blogger HTML content into clean Markdown.
    """
    if not raw_html:
        return "", ""

    content = raw_html

    # Remove style tags and interior CSS rules completely
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'(?:(?:p|span|div|a|img|table|td|tr|body|html)[a-z0-9_.-]*\s*\{[^{}]*\})+', '', content, flags=re.IGNORECASE | re.DOTALL)

    # Extract featured image first (first image tag)
    first_img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE)
    featured_image = ""
    if first_img_match:
        raw_src = first_img_match.group(1)
        resolved_src, _ = resolve_image_path(raw_src, local_file_map, hash_map)
        featured_image = resolved_src

    # Clean up Blogger image caption tables
    def replace_caption_table(match):
        table_html = match.group(0)
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', table_html, re.IGNORECASE)
        caption_match = re.search(r'<td[^>]*class=["\']tr-caption["\'][^>]*>(.*?)</td>', table_html, re.IGNORECASE | re.DOTALL)
        
        img_md = ""
        if img_match:
            img_src = img_match.group(1)
            resolved_src, _ = resolve_image_path(img_src, local_file_map, hash_map)
            caption_text = ""
            if caption_match:
                caption_text = re.sub(r'<[^>]+>', '', caption_match.group(1)).strip()
            img_md = f"\n\n![{caption_text}]({resolved_src})\n\n"
        return img_md

    content = re.sub(r'<table[^>]*class=["\'][^"\']*tr-caption-container[^"\']*["\'][^>]*>.*?</table>', replace_caption_table, content, flags=re.IGNORECASE | re.DOTALL)

    # Process remaining standalone <img> tags
    def replace_img(match):
        img_tag = match.group(0)
        src_match = re.search(r'src=["\']([^"\']+)["\']', img_tag, re.IGNORECASE)
        alt_match = re.search(r'alt=["\']([^"\']+)["\']', img_tag, re.IGNORECASE)
        alt_text = alt_match.group(1) if alt_match else ""
        if src_match:
            raw_src = src_match.group(1)
            resolved_src, _ = resolve_image_path(raw_src, local_file_map, hash_map)
            return f"\n\n![{alt_text}]({resolved_src})\n\n"
        return ""

    content = re.sub(r'<img[^>]+>', replace_img, content, flags=re.IGNORECASE)

    # Remove remaining HTML layout tables, divs, spans attributes
    content = re.sub(r'</?(?:table|tbody|tr|td|th|div|span|font)[^>]*>', '\n', content, flags=re.IGNORECASE)

    # Convert Headings
    content = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n\n# \1\n\n', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n\n## \1\n\n', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<h3[^>]*>(.*?)3</h3>', r'\n\n### \1\n\n', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n\n#### \1\n\n', content, flags=re.IGNORECASE | re.DOTALL)

    # Convert Bold and Italic
    content = re.sub(r'<(?:b|strong)[^>]*>(.*?)</(?:b|strong)>', r'**\1**', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<(?:i|em)[^>]*>(.*?)</(?:i|em)>', r'*\1*', content, flags=re.IGNORECASE | re.DOTALL)

    # Convert Links
    def replace_link(match):
        href = match.group(1)
        link_text = match.group(2).strip()
        if not link_text:
            return ""
        return f"[{link_text}]({href})"
    content = re.sub(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', replace_link, content, flags=re.IGNORECASE | re.DOTALL)

    # Convert Lists
    content = re.sub(r'<li[^>]*>(.*?)</li>', r'\n- \1', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'</?(?:ul|ol)[^>]*>', '\n', content, flags=re.IGNORECASE)

    # Convert line breaks and paragraph tags
    content = re.sub(r'<br\s*/?>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'</?p[^>]*>', '\n\n', content, flags=re.IGNORECASE)

    # Remove remaining HTML tags
    content = re.sub(r'<[^>]+>', '', content)

    # Unescape HTML entities
    content = html.unescape(content)

    # Clean up whitespace and excess empty lines
    lines = [line.rstrip() for line in content.splitlines()]
    clean_text = re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip()

    return clean_text, featured_image

def generate_unique_slug(title, filename, used_slugs):
    """Generate a clean, unique slug from title or filename (without date)."""
    base_slug = ""
    if filename:
        basename = os.path.basename(filename)
        base_slug = re.sub(r'\.html$', '', basename, flags=re.IGNORECASE)

    if not base_slug:
        base_slug = title.lower()
        base_slug = re.sub(r'[^a-z0-9]+', '-', base_slug).strip('-')

    base_slug = base_slug or "recipe"
    
    slug = base_slug
    counter = 2
    while slug in used_slugs:
        slug = f"{base_slug}-{counter}"
        counter += 1

    used_slugs.add(slug)
    return slug

def convert_feed():
    """Main conversion routine."""
    if not os.path.exists(FEED_PATH):
        print(f"Error: Feed file not found at {FEED_PATH}")
        return

    os.makedirs(SRC_DIR, exist_ok=True)
    local_file_map, hash_map = get_image_resolution_maps()
    print(f"Loaded {len(local_file_map)} local image files and {len(hash_map)} URL hash mappings.")

    tree = ET.parse(FEED_PATH)
    root = tree.getroot()

    used_slugs = set()
    posts_processed = 0
    drafts_processed = 0

    for entry in root.findall("atom:entry", NS):
        type_elem = entry.find("blogger:type", NS)
        entry_type = type_elem.text if type_elem is not None else ""

        # Ignore reader comments
        if entry_type == "COMMENT":
            continue

        if entry_type not in ["POST", "PAGE"]:
            continue

        title_elem = entry.find("atom:title", NS)
        title = title_elem.text.strip() if (title_elem is not None and title_elem.text) else "Untitled Post"

        status_elem = entry.find("blogger:status", NS)
        status = status_elem.text if status_elem is not None else "LIVE"
        is_draft = (status != "LIVE")

        pub_elem = entry.find("atom:published", NS)
        date_str = pub_elem.text if pub_elem is not None else datetime.now().isoformat()

        updated_elem = entry.find("atom:updated", NS)
        lastmod_str = updated_elem.text if updated_elem is not None else date_str

        fn_elem = entry.find("blogger:filename", NS)
        filename = fn_elem.text if fn_elem is not None else ""

        desc_elem = entry.find("blogger:metaDescription", NS)
        description = desc_elem.text.strip() if (desc_elem is not None and desc_elem.text) else ""

        # Extract Categories
        categories = []
        for cat in entry.findall("atom:category", NS):
            term = cat.attrib.get("term", "").strip()
            if term and not term.startswith("tag:blogger") and not "kind#" in term:
                categories.append(term.title())

        # Extract content
        content_elem = entry.find("atom:content", NS)
        raw_html = (content_elem.text or "") if content_elem is not None else ""

        md_body, featured_image = clean_html_content(raw_html, local_file_map, hash_map)

        # Generate clean date-less slug
        slug = generate_unique_slug(title, filename, used_slugs)
        date_prefix = date_str[:10]
        out_filename = f"{date_prefix}-{slug}.md"
        out_filepath = os.path.join(SRC_DIR, out_filename)

        # Build permalink alias
        aliases = []
        if filename:
            aliases.append(filename)

        is_updated_later = (date_str[:10] != lastmod_str[:10])

        yaml_lines = ["---"]
        yaml_lines.append(f"title: {json.dumps(title)}")
        yaml_lines.append(f"slug: {json.dumps(slug)}")
        yaml_lines.append(f"date: {json.dumps(date_str)}")
        if is_updated_later:
            yaml_lines.append(f"lastmod: {json.dumps(lastmod_str)}")
        else:
            yaml_lines.append(f"# lastmod: {json.dumps(lastmod_str)}")
        yaml_lines.append(f"draft: {'true' if is_draft else 'false'}")
        if categories:
            formatted_cats = ", ".join([json.dumps(c) for c in categories])
            yaml_lines.append(f"categories: [{formatted_cats}]")
        else:
            yaml_lines.append("categories: []")
        if aliases:
            formatted_aliases = ", ".join([json.dumps(a) for a in aliases])
            yaml_lines.append(f"aliases: [{formatted_aliases}]")
        else:
            yaml_lines.append("aliases: []")
        yaml_lines.append(f"featured_image: {json.dumps(featured_image)}")
        yaml_lines.append(f"description: {json.dumps(description or f'{title} recipe.')}")
        yaml_lines.append("---")

        full_md_content = "\n".join(yaml_lines) + "\n\n" + md_body + "\n"

        with open(out_filepath, "w", encoding="utf-8") as f:
            f.write(full_md_content)

        posts_processed += 1
        if is_draft:
            drafts_processed += 1

    print(f"Successfully converted {posts_processed} articles ({drafts_processed} drafts) into {SRC_DIR}/")

def main():
    print("==================================================")
    print("📦 Blogger Conversion Pipeline")
    print("==================================================")
    print("[1/3] Processing image URLs and matching MD5 file signatures...")
    try:
        from process_hashed_images import process_images
        process_images()
    except Exception as e:
        print(f"Warning during image processing: {e}")

    print("\n[2/3] Converting Blogger Atom feed to Markdown articles...")
    convert_feed()

    print("\n[3/3] Moving unused images into unused/...")
    try:
        from cleanup_unused_images import cleanup_unused
        cleanup_unused()
    except Exception as e:
        print(f"Warning during image cleanup: {e}")

    print("==================================================")
    print("✅ Blogger conversion complete!")
    print("==================================================")

if __name__ == "__main__":
    main()
