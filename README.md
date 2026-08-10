# Schank Farms — Conversion & Maintenance Tools

This project contains standalone Python 3.13 tools, project configuration (`pyproject.toml`), environment settings (`.envrc`), and build scripts to manage the this Hugo static site.

---

## 1. Environment Setup & Execution

### Environment (`.envrc` / `pyproject.toml`)

Targets **Python 3.13** using zero external pip runtime dependencies (`xml.etree.ElementTree`, `hashlib`, `urllib.request`, `json`, `shutil`).

### Python Setup

Assuming `.envrc` is present in the workspace:

1. **Enable Environment (`direnv`)**:
   If using `direnv`, allow the directory environment to automatically set `PROJECT_ROOT`, `PYTHON_VERSION="3.13"`, and add system paths:

   ```bash
   direnv allow
   ```

2. **Virtual Environment & Dependencies (Optional)**:
   The conversion scripts use standard library modules exclusively and require no external runtime dependencies.
   If you wish to set up a virtual environment or install development tools (`pytest`, `ruff`):

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

---

## 2. Previous Conversion

Previously, this website was converted from the /tools/feed.atom that was exported from Blogger.  That code remains in /tools in case it is needed again.

### 1. Blogger Export Conversion (`python3 tools/convert_blogger.py`)

All Blogger import and conversion responsibilities are handled by `tools/convert_blogger.py`:

- **Image Processing**: Scans `tools/feed.atom` for Google Photos hashed URLs (`/img/a/...`), matches MD5 file signatures, and saves clean image filenames into `docs/images/`.
- **Feed Conversion**: Parses `tools/feed.atom` and converts Blogger posts into clean Hugo Markdown files in `src/` with YAML frontmatter.
- **Unused Image Cleanup**: Scans `src/*.md` and `page_layouts/`, protecting branding assets while archiving unreferenced export images into `unused/`.

## 3. Current Development

### 1. Creating a New Article (`./gen.sh --new`)

To create a new article draft Leaf Bundle directory by providing the title in quotes:

```bash
./gen.sh --new "My New Article Title"
```

This automatically:

- Converts the title into a clean hyphenated slug (e.g. `my-new-article-title`).
- Creates the Leaf Bundle directory `src/my-new-article-title/index.md`.
- Sets `title: "My New Article Title"`.
- Sets `slug: "my-new-article-title"`.
- Sets `draft: true`.
- Populates `index.md` with default frontmatter ready for editing.

### 2. Site Rebuilding (`./gen.sh`)

The `./gen.sh` script rebuilds the static website into `docs/`:

```bash
./gen.sh
```

---

## 4. Running Local Development Server (`hugo server`)

To preview the site locally with live reloading on port 8080 without Hugo adding live-reload script code to static HTML files in `docs/`:

```bash
hugo server --renderToMemory --port 8080
```

Options:

- To render in memory (prevents Hugo from adding live-reload script code to HTML files on disk): `--renderToMemory` (or `-M`)
- To include draft posts: `hugo server --renderToMemory --port 8080 -D`
- To include future-dated posts: `hugo server --renderToMemory --port 8080 --buildFuture`

The development server serves the site at `http://localhost:8080/` and automatically watches `src/`, `page_layouts/`, `docs/css/`, and `docs/images/` for live updates.

---

## 5. Search Index Generation & GitHub Pages

The search system operates statically on GitHub Pages:

- **Hugo Index Template**: `page_layouts/index.json` generates `docs/index.json` during site build.
- **Search Execution**: Clicking the 🔍 icon in the header toggles the inline search field; pressing **Return / Enter** or clicking 🔍 submits `/?q=query`.
- **Edge CDN**: Fuse.js is referenced via jsDelivr CDN (`https://cdn.jsdelivr.net/npm/fuse.js@7.0.0/dist/fuse.basic.min.js`) with `defer` for static client-side search.
