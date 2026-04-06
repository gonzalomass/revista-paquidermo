# Revista Paquidermo — Database & Content Audit Report

**Date:** April 6, 2026
**Source directory:** `/Users/gonzalomass/Desktop/gmass/paquidermo`

---

## 1. Inventory of Available Files

| File | Size | Date | Readable | Notes |
|------|------|------|----------|-------|
| `revistapaquidermo_2021-06-04.sql` | 131 MB | Jun 4, 2021 | No (file lock) | Full DB dump — likely the most complete |
| `revistapaquidermo_2021-07-18.sql` | 45 MB | Jul 18, 2021 | No (file lock) | Full DB dump — newer but smaller (possibly partial) |
| `revistapaquidermo_2021-07-18.sql.zip` | 11.4 MB | Jul 18, 2021 | No (file lock) | Compressed version of above |
| `wp_posts.sql` | 59 MB | Jul 18, 2021 | **Yes** | Single-table export (wp_posts only) |
| `wp_posts.sql.zip` | 11.1 MB | Jul 18, 2021 | No (file lock) | Compressed version of above |
| `data pulls/` | — | — | Yes | Manually extracted content (see below) |

### Key Observations on SQL Files

- The **June 4 dump (131 MB)** is almost 3× larger than the July 18 dump (45 MB). This strongly suggests the June dump is a **full database export** (all tables), while the July dump may be a partial export or was created with different options (e.g., without revisions or transient data).
- The `wp_posts.sql` file (59 MB) was exported on the same day as the July dump, but it's larger than the full dump — this is because it contains the complete wp_posts table with all content blobs, while the full dump may have been compressed or exported with structure-only for some tables.
- **Recommendation:** The June 4, 2021 dump (`revistapaquidermo_2021-06-04.sql`) is most likely the **most complete backup** and should be the primary source for migration. The file lock issues need to be resolved (likely by copying the file or adjusting permissions).

---

## 2. wp_posts Table Analysis (from wp_posts.sql)

### Database Metadata
- **Engine:** MariaDB 10.4.12
- **Database name:** `revistapaquidermo`
- **Export tool:** Sequel Pro (Version 4541)
- **Export date:** July 18, 2021

### Content Summary

| Metric | Value |
|--------|-------|
| Total records | 9,331 |
| Published posts | 1,396 |
| Published pages | 6 |
| Attachments (media) | 1,835 |
| Revisions | 5,389 |
| Unique authors | 44 |
| Date range | Feb 19, 2010 → Jul 17, 2021 |
| Content span | ~11 years, 5 months |

### Post Types Breakdown
- **revision** — 5,389 (57.8%) — historical edits of posts
- **attachment** — 1,835 (19.7%) — media files (images, PDFs)
- **post** — 1,396 (15.0%) — actual articles
- **revisr_commits** — 294 (3.2%) — git version control plugin data
- **feedback** — 85 (0.9%) — contact form submissions
- **nav_menu_item** — 65 (0.7%) — menu entries
- **wpdiscuz_form** — 23 (0.2%) — comment form templates
- **page** — 6 (0.1%) — static pages
- **slidedeck_slide/slidedeck** — 10 — slideshow content
- **safecss** — 1 — custom CSS

### Post Status Distribution
- **inherit** — 6,758 (72.4%) — child objects (revisions, attachments)
- **publish** — 1,710 (18.3%) — live content
- **private** — 39 (0.4%)
- **draft** — 7 (0.1%)
- **auto-draft** — 1

---

## 3. Data Pulls (Manually Extracted Content)

### 3a. Maria Luisa Ávila Interview
- Available in both `.md` and `.html` formats
- Interview from April 25, 2010
- Contains WordPress image class references (`wp-image-1087`)
- Images reference `revistapaquidermo.loc` (local dev domain)

### 3b. Roberto Herrera Posts Collection
- **35 markdown files** with YAML frontmatter
- Date range: June 2010 → July 2015
- Each file includes: `title`, `date`, `author`, `slug`, `wp_id`
- Content: political commentary, philosophical essays, cultural criticism
- Image references point to `revistapaquidermo.loc/wp-content/uploads/`

### Assessment
These are manually extracted/converted posts — not a standard WordPress XML export. They represent a subset of the total 1,396 published posts and serve as a proof of concept for content migration.

---

## 4. Image & Media Assessment

### What We Have
- **1,835 attachment records** in `wp_posts` with metadata (titles, dates, slugs, GUID URLs)
- **1,770 unique image URLs** extractable from attachment GUIDs
- Image formats: JPG (79%), PNG (14.5%), GIF (2%), plus some PDFs
- WordPress upload structure: standard `YYYY/MM/` folders covering **2008–2017**

### What We're Missing
- **The actual image files are NOT included in any of the dumps.** SQL backups only contain metadata and URLs — not binary files.
- All image URLs point to local development domains:
  - `revistapaquidermo.loc` — 92% of images (HTTP)
  - `cdn.revistapaquidermo.loc` — ~4% (HTTPS, 2017 era)
  - `quelthalas.cdn.ar-soluciones.com` — minor (2014 CDN)

### Where to Recover Images

1. **Wayback Machine (archive.org)** — The Wayback Machine CDX API did not return results for `revistapaquidermo.com` in our tests, but this should be verified manually by browsing `web.archive.org/web/*/revistapaquidermo.com`. The Wayback Machine may have crawled the site when it was active and cached images along with pages. This is the **highest probability source** for recovering original images.

2. **Facebook page** (`facebook.com/revistapaquidermo`) — The publication has an active Facebook presence where article images may have been shared. These would be lower resolution but could serve as fallbacks.

3. **Google Cache / Google Images** — Searching for `site:revistapaquidermo.com` currently shows the domain has been **hijacked by a Thai gambling spam site**. However, Google Images may still have indexed versions of the original images.

4. **Universidad de Costa Rica references** — UCR shared Paquidermo content on their Facebook; some images may be recoverable from those posts.

5. **GAM Cultural listing** (`gamcultural.com/cr/p/revistapaquidermo`) — May contain profile images or logos.

6. **Original hosting provider** — If the original hosting account (likely with ar-soluciones.com based on CDN references) still has backups, the `wp-content/uploads/` directory could be recovered.

7. **Local backups** — Check if any team member has a local copy of the WordPress `wp-content/uploads/` folder, which would contain all original images.

---

## 5. Comments Assessment

### What We Have
- The `wp_posts` table includes `comment_status` and `comment_count` fields per post
- The presence of `wpdiscuz_form` post types (23 records) confirms the site used the **wpDiscuz** comment plugin
- **Actual comment data (wp_comments, wp_commentmeta tables) is NOT in `wp_posts.sql`**

### Where Comments Might Be
- **The June 4 full dump (131 MB)** most likely contains the `wp_comments` and `wp_commentmeta` tables since it's a full database export. This is the **primary source** for comment recovery.
- The July 18 full dump (45 MB) may also contain comments.
- Neither can be read currently due to file system lock issues.

### Recovery Plan
1. Resolve file lock issues on `revistapaquidermo_2021-06-04.sql` (copy to another location, or decompress the zip)
2. Extract `wp_comments` and `wp_commentmeta` tables
3. Cross-reference with wpDiscuz plugin data if available

---

## 6. Domain Status

**revistapaquidermo.com has been hijacked.** The domain currently serves Thai-language gambling spam (UFABET). The original WordPress site URL structure (`/archives/author/`, `/archives/category/sociedad`) is still visible in Google's index but serves spam content.

There is also a `revistapaquidermo.wordpress.com` presence, which may have been an earlier version or mirror of the site.

---

## 7. Tech Stack Recommendation for the New Site

Given the nature of Revista Paquidermo (a literary/political magazine with ~1,400 articles, 44 authors, 11+ years of content), here is the recommended tech stack:

### Option A: Static Site Generator (Recommended)

**Framework:** [Astro](https://astro.build)
- Perfect for content-heavy sites with minimal interactivity
- Built-in Markdown/MDX support matches the existing content format
- Content Collections API for type-safe content management
- Excellent performance (ships zero JS by default)
- Easy image optimization with built-in `<Image>` component

**Content:** Markdown files with frontmatter (already partially done in data pulls)

**Styling:** Tailwind CSS — fast utility-first styling, great for editorial layouts

**Hosting:** Vercel or Netlify (free tier handles this scale easily)

**Search:** Pagefind (static search, no server needed)

**Comments:** Giscus (GitHub Discussions-based) or Disqus

**CMS (optional):** Decap CMS (formerly Netlify CMS) for non-technical editors — writes directly to the Git repo

**Why Astro?**
- The site is primarily reading content — no complex interactivity needed
- Markdown-first workflow matches the data we already have
- 1,400 articles build in seconds
- Near-perfect Lighthouse scores out of the box
- No database to maintain, no server to manage, no WordPress to patch

### Option B: Headless CMS + Framework

**CMS:** Strapi or Sanity
**Frontend:** Next.js or Nuxt
**Hosting:** Vercel

This adds more complexity but gives editors a rich admin UI. Best if multiple non-technical editors need to publish regularly.

### Option C: Modern WordPress (Not Recommended)

A fresh WordPress install with a modern theme. While familiar, it reintroduces the same maintenance burden, security risks (as evidenced by the domain hijacking), and performance issues that plague WordPress sites.

### Migration Path (for Option A)

1. Parse `wp_posts.sql` → extract all published posts as Markdown with frontmatter
2. Map authors from `post_author` IDs to author profiles
3. Recover images from Wayback Machine / Facebook / backups
4. Extract categories and tags from the full DB dump
5. Build Astro site with content collections
6. Set up redirects from old URL patterns (`/archives/...`) to new structure
7. Deploy to Vercel/Netlify with new domain or recovered domain

---

## 8. Immediate Next Steps

1. **Fix file locks** — Copy the large SQL files to a different location to resolve the "Resource deadlock" errors. This will unlock the full DB dump for analysis.
2. **Extract full table list** — From the June 4 dump, identify all WordPress tables present (wp_comments, wp_users, wp_terms, wp_options, etc.)
3. **Check Wayback Machine manually** — Browse `web.archive.org` for cached versions of revistapaquidermo.com to assess image recovery potential.
4. **Contact ar-soluciones.com** — The CDN references suggest this was the hosting provider; they may still have backup files.
5. **Secure the domain** — If revistapaquidermo.com is still owned by the team, reclaim it from the spam hijackers. If not, consider a new domain.
6. **Export content to Markdown** — Write a script to parse wp_posts.sql and generate clean Markdown files for all 1,396 published posts.
