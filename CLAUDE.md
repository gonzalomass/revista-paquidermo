# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Revista Paquidermo is a Costa Rican literary/political magazine (~1,400 articles, 44 authors, 2010–2021) rebuilt as an **Astro 6 static site**. Content was migrated from WordPress/MariaDB SQL dumps.

## Build Commands

```bash
# Node.js must be accessed via:
export PATH="/opt/homebrew/opt/node@22/bin:/opt/homebrew/bin:$PATH"

npm run dev        # Start dev server
npm run build      # Build site + Pagefind index
npm run preview    # Preview built site
```

The build command runs `astro build && npx pagefind --site dist`.

## Architecture

- **Framework:** Astro 6 with Content Collections (glob loader API)
- **Styling:** Tailwind CSS v4 via `@tailwindcss/vite` plugin (config in `src/styles/global.css`, not a JS config file)
- **Search:** Pagefind (static, indexed at build time)
- **Typography:** `@tailwindcss/typography` for article prose
- **Content:** Markdown with YAML frontmatter in `src/content/`
- **Content language:** Spanish

## Project Structure

```
src/
  content.config.ts      # Collection schemas (posts, authors, pages)
  content/
    posts/               # 1,395 markdown articles (date-slug.md)
    authors/             # 40 author profiles
    pages/               # 6 static pages
  layouts/
    BaseLayout.astro     # Shared layout with header, nav, footer
  components/
    PostCard.astro       # Article card for listings
    Pagination.astro     # Paginated navigation
  lib/
    authors.ts           # Author slug→name lookup utility
  pages/
    index.astro          # Homepage (paginated)
    [slug].astro         # Individual article pages
    pagina/[page].astro  # Pagination pages
    autor/[slug].astro   # Author pages
    categoria/[slug].astro # Category pages
    autores.astro        # Authors index
    categorias.astro     # Categories index
    archivo.astro        # Archive by year
    buscar.astro         # Pagefind search UI
  styles/
    global.css           # Tailwind v4 theme (custom colors, fonts)
scripts/
  extract_content.py     # SQL→Markdown extraction script
public/
  logo.svg               # Paquidermo logo
```

## Key Design Decisions

- **No images in content:** Image files were not included in the SQL dumps. Image tags are stripped during extraction. Image recovery from Wayback Machine is a future task.
- **Image service disabled:** `astro.config.mjs` uses noop image service since there are no local images.
- **Author names:** Posts store author slugs in frontmatter. Display names are resolved at render time via `src/lib/authors.ts`.
- **Pagefind loaded at runtime:** The search page (`buscar.astro`) loads Pagefind JS/CSS via DOM injection (`is:inline` script) to avoid Vite build-time resolution issues.
- **Tailwind v4 (not v3):** Uses CSS-based config (`@theme` block in `global.css`), not `tailwind.config.js`.

## Content Extraction

`scripts/extract_content.py` parses raw SQL INSERT statements from two dump files:
- `revistapaquidermo_2021-06-04.sql` (full dump) — authors, terms, taxonomies, relationships
- `wp_posts.sql` (from `/Users/gonzalomass/Desktop/gmass/paquidermo/`) — post content

Re-running extraction: `python3 scripts/extract_content.py` (overwrites `src/content/`)

## Custom Colors

Defined in `src/styles/global.css` as CSS custom properties:
- `--color-paqui-red: #c41e3a` (primary accent, links, category badges)
- `--color-paqui-dark: #1a1a1a` (text)
- `--color-paqui-gray: #4a4a4a` (secondary text)
- `--color-paqui-light: #f8f7f4` (background)

## Remaining Work

- Image recovery from Wayback Machine / external sources
- Comment extraction from full SQL dump
- URL redirects from old WordPress patterns (`/archives/...`)
- Deployment to Vercel or Netlify
- Domain recovery or new domain setup
