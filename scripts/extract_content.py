#!/usr/bin/env python3
"""
Extract WordPress content from SQL dumps into Markdown files for Astro.
Parses raw SQL INSERT statements without needing a running MySQL instance.
"""

import re
import os
import json
import html
from datetime import datetime
from urllib.parse import unquote

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.environ.get("PAQUIDERMO_DATA", os.path.join(PROJECT_DIR, "..", "..", "Desktop", "gmass", "paquidermo"))

FULL_DUMP = os.path.join(DATA_DIR, "revistapaquidermo_2021-06-04.sql")
WP_POSTS_DUMP = os.path.join(DATA_DIR, "wp_posts.sql")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "src", "content")

# ---------------------------------------------------------------------------
# SQL value parser — handles escaped quotes, nested parens, etc.
# ---------------------------------------------------------------------------

def parse_sql_values(line):
    """Parse a SQL INSERT line and return list of row tuples (as strings)."""
    # Find VALUES section
    m = re.search(r'VALUES\s*', line, re.IGNORECASE)
    if not m:
        return []
    rest = line[m.end():]
    rows = []
    i = 0
    while i < len(rest):
        if rest[i] == '(':
            # Parse one row
            i += 1
            fields = []
            current = []
            in_string = False
            escape = False
            while i < len(rest):
                ch = rest[i]
                if escape:
                    current.append(ch)
                    escape = False
                    i += 1
                    continue
                if ch == '\\':
                    escape = True
                    current.append(ch)
                    i += 1
                    continue
                if ch == "'" and not in_string:
                    in_string = True
                    i += 1
                    continue
                if ch == "'" and in_string:
                    # Check for ''
                    if i + 1 < len(rest) and rest[i + 1] == "'":
                        current.append("'")
                        i += 2
                        continue
                    in_string = False
                    i += 1
                    continue
                if in_string:
                    current.append(ch)
                    i += 1
                    continue
                # Not in string
                if ch == ',':
                    fields.append(''.join(current).strip())
                    current = []
                    i += 1
                    continue
                if ch == ')':
                    fields.append(''.join(current).strip())
                    rows.append(fields)
                    i += 1
                    break
                current.append(ch)
                i += 1
        else:
            i += 1
    return rows


def unescape_sql(s):
    """Unescape SQL string escapes."""
    if s == 'NULL':
        return ''
    s = s.replace("\\'", "'")
    s = s.replace('\\"', '"')
    s = s.replace('\\n', '\n')
    s = s.replace('\\r', '\r')
    s = s.replace('\\t', '\t')
    s = s.replace('\\\\', '\\')
    return s


# ---------------------------------------------------------------------------
# Extract tables from a SQL dump file
# ---------------------------------------------------------------------------

def extract_table(filepath, table_name, column_names):
    """Extract rows from a specific table in a SQL dump file.
    Handles Sequel Pro multiline format where INSERT and VALUES are on separate lines."""
    rows = []
    target = f"INSERT INTO `{table_name}`"
    print(f"  Scanning for {table_name}...")
    in_insert = False
    buffer = ''
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if target in line:
                in_insert = True
                buffer = line
                # Check if VALUES is on this same line
                if 'VALUES' in line:
                    pass  # will be parsed below
                else:
                    continue
            elif in_insert:
                buffer += line
            else:
                continue

            # Check if we have a complete statement
            if in_insert and buffer.rstrip().endswith(';'):
                parsed = parse_sql_values(buffer)
                for fields in parsed:
                    if len(fields) >= len(column_names):
                        row = {}
                        for j, col in enumerate(column_names):
                            row[col] = unescape_sql(fields[j])
                        rows.append(row)
                in_insert = False
                buffer = ''
    print(f"  Found {len(rows)} rows in {table_name}")
    return rows


# ---------------------------------------------------------------------------
# WordPress HTML to Markdown (basic)
# ---------------------------------------------------------------------------

def wp_content_to_markdown(content):
    """Convert WordPress HTML content to basic Markdown."""
    if not content:
        return ''
    text = content

    # Decode HTML entities
    text = html.unescape(text)

    # Remove WordPress shortcodes
    text = re.sub(r'\[/?(?:caption|gallery|embed|audio|video|slidedeck|vc_\w+|mk_\w+)[^\]]*\]', '', text)

    # Convert headings
    for i in range(6, 0, -1):
        text = re.sub(rf'<h{i}[^>]*>(.*?)</h{i}>', lambda m: f'\n{"#" * i} {m.group(1).strip()}\n', text, flags=re.DOTALL | re.IGNORECASE)

    # Convert bold/italic
    text = re.sub(r'<(?:strong|b)>(.*?)</(?:strong|b)>', r'**\1**', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<(?:em|i)>(.*?)</(?:em|i)>', r'*\1*', text, flags=re.DOTALL | re.IGNORECASE)

    # Convert links
    text = re.sub(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.DOTALL | re.IGNORECASE)

    # Remove images — we don't have the actual files yet
    text = re.sub(r'<img[^>]*/?>',  '', text, flags=re.IGNORECASE)

    # Convert blockquotes
    text = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', lambda m: '\n> ' + m.group(1).strip().replace('\n', '\n> ') + '\n', text, flags=re.DOTALL | re.IGNORECASE)

    # Convert lists
    text = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'</?(?:ul|ol)[^>]*>', '\n', text, flags=re.IGNORECASE)

    # Convert paragraphs and line breaks
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<p[^>]*>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '', text, flags=re.IGNORECASE)

    # Remove remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    return text


def yaml_safe(s):
    """Make a string safe for YAML double-quoted values."""
    s = s.replace('\\', '\\\\')
    s = s.replace('"', '\\"')
    s = s.replace('\n', ' ')
    s = s.replace('\r', '')
    s = s.replace('\t', ' ')
    # Remove any other control characters
    s = re.sub(r'[\x00-\x1f\x7f]', '', s)
    return s


def slugify(text):
    """Create a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[áàäâ]', 'a', text)
    text = re.sub(r'[éèëê]', 'e', text)
    text = re.sub(r'[íìïî]', 'i', text)
    text = re.sub(r'[óòöô]', 'o', text)
    text = re.sub(r'[úùüû]', 'u', text)
    text = re.sub(r'[ñ]', 'n', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text[:80]


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------

def main():
    print("=== Revista Paquidermo Content Extraction ===\n")

    # 1. Extract users from full dump
    print("[1/5] Extracting authors...")
    user_cols = ['ID', 'user_login', 'user_pass', 'user_nicename', 'user_email',
                 'user_url', 'user_registered', 'user_activation_key', 'user_status',
                 'display_name']
    users = extract_table(FULL_DUMP, 'wp_users', user_cols)
    user_map = {u['ID']: u for u in users}

    # 2. Extract terms (categories + tags)
    print("\n[2/5] Extracting categories and tags...")
    term_cols = ['term_id', 'name', 'slug', 'term_group']
    terms = extract_table(FULL_DUMP, 'wp_terms', term_cols)
    term_map = {t['term_id']: t for t in terms}

    tax_cols = ['term_taxonomy_id', 'term_id', 'taxonomy', 'description', 'parent', 'count']
    taxonomies = extract_table(FULL_DUMP, 'wp_term_taxonomy', tax_cols)
    tax_map = {t['term_taxonomy_id']: t for t in taxonomies}

    rel_cols = ['object_id', 'term_taxonomy_id', 'term_order']
    relationships = extract_table(FULL_DUMP, 'wp_term_relationships', rel_cols)

    # Build post_id -> categories/tags mapping
    post_terms = {}  # post_id -> {'categories': [...], 'tags': [...]}
    for rel in relationships:
        post_id = rel['object_id']
        tax_id = rel['term_taxonomy_id']
        if tax_id in tax_map:
            tax = tax_map[tax_id]
            term_id = tax['term_id']
            if term_id in term_map:
                term_name = term_map[term_id]['name']
                taxonomy_type = tax['taxonomy']
                if post_id not in post_terms:
                    post_terms[post_id] = {'categories': [], 'tags': []}
                if taxonomy_type == 'category':
                    post_terms[post_id]['categories'].append(term_name)
                elif taxonomy_type == 'post_tag':
                    post_terms[post_id]['tags'].append(term_name)

    # 3. Extract posts from wp_posts.sql (more complete for post content)
    print("\n[3/5] Extracting posts...")
    post_cols = ['ID', 'post_author', 'post_date', 'post_date_gmt', 'post_content',
                 'post_title', 'post_excerpt', 'post_status', 'comment_status',
                 'ping_status', 'post_password', 'post_name', 'to_ping', 'pinged',
                 'post_modified', 'post_modified_gmt', 'post_content_filtered',
                 'post_parent', 'guid', 'menu_order', 'post_type', 'post_mime_type',
                 'comment_count']
    posts = extract_table(WP_POSTS_DUMP, 'wp_posts', post_cols)

    # Filter to published posts only
    published = [p for p in posts if p['post_status'] == 'publish' and p['post_type'] == 'post']
    print(f"  Published posts: {len(published)}")

    # Also extract pages
    pages = [p for p in posts if p['post_status'] == 'publish' and p['post_type'] == 'page']
    print(f"  Published pages: {len(pages)}")

    # 4. Write author data
    print("\n[4/5] Writing author files...")
    authors_dir = os.path.join(OUTPUT_DIR, 'authors')
    os.makedirs(authors_dir, exist_ok=True)

    # Find which authors have published posts
    active_author_ids = set(p['post_author'] for p in published)
    author_count = 0
    for uid in active_author_ids:
        if uid in user_map:
            u = user_map[uid]
            slug = slugify(u['display_name']) or u['user_nicename']
            content = f"""---
name: "{yaml_safe(u['display_name'])}"
slug: "{slug}"
wp_id: {u['ID']}
---
"""
            filepath = os.path.join(authors_dir, f"{slug}.md")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            author_count += 1
    print(f"  Wrote {author_count} author files")

    # 5. Write post files
    print("\n[5/5] Writing post files...")
    posts_dir = os.path.join(OUTPUT_DIR, 'posts')
    os.makedirs(posts_dir, exist_ok=True)

    written = 0
    skipped = 0
    for p in published:
        title = yaml_safe(p['post_title'])
        if not title.strip():
            skipped += 1
            continue

        # Build slug — decode URL-encoded chars, then clean to ASCII
        raw_slug = p['post_name'] if p['post_name'] else ''
        if raw_slug:
            slug = slugify(unquote(raw_slug))
        else:
            slug = slugify(p['post_title'])
        if not slug:
            skipped += 1
            continue

        # Date
        date_str = p['post_date']
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            date_iso = dt.strftime('%Y-%m-%dT%H:%M:%S')
        except ValueError:
            date_iso = date_str

        # Author
        author_name = ''
        author_slug = ''
        if p['post_author'] in user_map:
            author_name = user_map[p['post_author']]['display_name']
            author_slug = slugify(author_name) or user_map[p['post_author']]['user_nicename']

        # Categories and tags
        terms_data = post_terms.get(p['ID'], {'categories': [], 'tags': []})
        categories = terms_data['categories']
        tags = terms_data['tags']

        # Excerpt
        excerpt = p['post_excerpt'].strip()
        if not excerpt:
            # Generate from content
            plain = re.sub(r'<[^>]+>', '', html.unescape(p['post_content']))
            plain = re.sub(r'\s+', ' ', plain).strip()
            excerpt = plain[:200] + '...' if len(plain) > 200 else plain

        excerpt = yaml_safe(excerpt)

        # Convert content
        md_content = wp_content_to_markdown(p['post_content'])

        # Build frontmatter
        cats_yaml = json.dumps(categories, ensure_ascii=False)
        tags_yaml = json.dumps(tags, ensure_ascii=False)

        frontmatter = f"""---
title: "{title}"
date: "{date_iso}"
author: "{author_slug}"
slug: "{slug}"
excerpt: "{excerpt}"
categories: {cats_yaml}
tags: {tags_yaml}
wp_id: {p['ID']}
---"""

        # Write file
        # Use date prefix for sorting
        date_prefix = date_iso[:10] if date_iso else '0000-00-00'
        filename = f"{date_prefix}-{slug}.md"
        # Truncate filename if too long
        if len(filename) > 200:
            filename = filename[:196] + '.md'

        filepath = os.path.join(posts_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(frontmatter + '\n\n' + md_content + '\n')
        written += 1

    print(f"  Wrote {written} posts, skipped {skipped}")

    # Write pages too
    pages_dir = os.path.join(OUTPUT_DIR, 'pages')
    os.makedirs(pages_dir, exist_ok=True)
    for p in pages:
        title = yaml_safe(p['post_title'])
        slug = p['post_name'] if p['post_name'] else slugify(p['post_title'])
        if not slug:
            continue
        md_content = wp_content_to_markdown(p['post_content'])
        content = f"""---
title: "{title}"
slug: "{slug}"
wp_id: {p['ID']}
---

{md_content}
"""
        filepath = os.path.join(pages_dir, f"{slug}.md")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    print(f"  Wrote {len(pages)} pages")
    print("\n=== Done! ===")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
