#!/usr/bin/env python3
"""
cleanup_unused_images.py

1. Scans all converted Markdown post files in peachy/src/*.md to find all referenced image filenames.
2. Identifies any image files in peachy/images/ that are NOT referenced in any post.
3. Moves unused image files (and their .json sidecars) into peachy/images/unused/.
"""

import os
import re
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "docs", "images")
UNUSED_DIR = os.path.join(PROJECT_ROOT, "unused")

LAYOUTS_DIR = os.path.join(PROJECT_ROOT, "page_layouts")
ALWAYS_KEEP = {"jeff-walking.jpg", "farm-logo.jpg", "farm-logo.png", "combine-contrast-1.png", "combine-contrast-2.png", "combine-contrast-3.png", "favicon.ico"}

def cleanup_unused():
    os.makedirs(UNUSED_DIR, exist_ok=True)

    # 1. Collect all image filenames referenced in src/*.md and page_layouts/
    used_filenames = set(ALWAYS_KEEP)
    for k in list(ALWAYS_KEEP):
        used_filenames.add(k.lower())

    if os.path.exists(SRC_DIR):
        for fname in os.listdir(SRC_DIR):
            if fname.endswith(".md"):
                filepath = os.path.join(SRC_DIR, fname)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    matches = re.findall(r'/(?:docs/)?images/([^\s"\)\'\\]+)', content)
                    for m in matches:
                        clean_m = m.split("#")[0].split("?")[0]
                        used_filenames.add(clean_m)
                        used_filenames.add(clean_m.lower())

    if os.path.exists(LAYOUTS_DIR):
        for root, _, files in os.walk(LAYOUTS_DIR):
            for fname in files:
                if fname.endswith(".html"):
                    filepath = os.path.join(root, fname)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        matches = re.findall(r'/(?:docs/)?images/([^\s"\)\'\\]+)', content)
                        for m in matches:
                            clean_m = m.split("#")[0].split("?")[0]
                            used_filenames.add(clean_m)
                            used_filenames.add(clean_m.lower())

    print(f"Total unique referenced image filenames (src & layout): {len(used_filenames)}")

    # 2. Iterate through files in docs/images/ (excluding subdirectories)
    image_files = []
    if os.path.exists(IMAGES_DIR):
        for fname in os.listdir(IMAGES_DIR):
            full_path = os.path.join(IMAGES_DIR, fname)
            if os.path.isfile(full_path) and not fname.endswith(".json"):
                image_files.append(fname)

    print(f"Total image files in docs/images/: {len(image_files)}")

    moved_count = 0
    kept_count = 0

    for img_fname in image_files:
        if img_fname in used_filenames or img_fname.lower() in used_filenames:
            kept_count += 1
        else:
            # Move unused image file
            src_img = os.path.join(IMAGES_DIR, img_fname)
            dest_img = os.path.join(UNUSED_DIR, img_fname)
            shutil.move(src_img, dest_img)

            # Move corresponding .json sidecar if present
            json_fname = img_fname + ".json"
            src_json = os.path.join(IMAGES_DIR, json_fname)
            if os.path.exists(src_json):
                dest_json = os.path.join(UNUSED_DIR, json_fname)
                shutil.move(src_json, dest_json)

            moved_count += 1

    print(f"\nCleanup complete!")
    print(f"  Images kept in docs/images/: {kept_count}")
    print(f"  Unused images moved to unused/: {moved_count}")

if __name__ == "__main__":
    cleanup_unused()
