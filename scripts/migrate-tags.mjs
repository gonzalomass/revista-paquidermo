#!/usr/bin/env node
/**
 * migrate-tags.mjs
 *
 * Parses all post markdown files and splits the flat `tags` array into
 * three separate fields:
 *   - columna: string (optional) — extracted from "Columna: ..." or "Columna ..." tags
 *   - seccion: string (optional) — extracted from "Sección: ..." or "Sección ..." tags
 *   - tags: string[] — everything else
 *
 * Rewrites each file's YAML frontmatter in place.
 */

import fs from 'fs';
import path from 'path';

const POSTS_DIR = path.resolve('src/content/posts');

function slugify(str) {
  return str
    .toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '') // strip accents
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function extractColumna(tag) {
  // Match "Columna: ..." or "Columna ..." (the one without colon: "Columna Bífida")
  const match = tag.match(/^Columna[:\s]\s*(.*)/i);
  return match ? match[1].trim() : null;
}

function extractSeccion(tag) {
  // Match "Sección: ..." or "Sección ..." or "Seccion: ..."
  const match = tag.match(/^Secci[oó]n[:\s]\s*(.*)/i);
  return match ? match[1].trim() : null;
}

const files = fs.readdirSync(POSTS_DIR).filter(f => f.endsWith('.md'));
let modified = 0;
let columnaCount = 0;
let seccionCount = 0;

const allColumnas = new Set();
const allSecciones = new Set();
const allTags = new Set();

for (const file of files) {
  const filePath = path.join(POSTS_DIR, file);
  const content = fs.readFileSync(filePath, 'utf8');

  // Split frontmatter from body
  const fmMatch = content.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  if (!fmMatch) {
    console.warn(`⚠ No frontmatter: ${file}`);
    continue;
  }

  const frontmatter = fmMatch[1];
  const body = fmMatch[2];

  // Extract the tags array
  const tagsMatch = frontmatter.match(/tags:\s*\[([\s\S]*?)\]/);
  if (!tagsMatch) {
    // No tags field or empty — skip
    continue;
  }

  const rawTags = tagsMatch[1];
  const tags = rawTags.match(/"([^"]*)"/g)?.map(t => t.replace(/"/g, '')) || [];

  if (tags.length === 0) continue;

  // Classify tags
  const columnas = [];
  const secciones = [];
  const regularTags = [];

  for (const tag of tags) {
    const col = extractColumna(tag);
    if (col) {
      columnas.push(col);
      allColumnas.add(col);
      continue;
    }
    const sec = extractSeccion(tag);
    if (sec) {
      secciones.push(sec);
      allSecciones.add(sec);
      continue;
    }
    regularTags.push(tag);
    allTags.add(tag);
  }

  // Only modify if there were columnas or secciones to extract
  if (columnas.length === 0 && secciones.length === 0) continue;

  // Build the new tags line
  const newTagsLine = `tags: [${regularTags.map(t => `"${t}"`).join(', ')}]`;

  // Build columna/seccion lines (take first if multiple)
  let newLines = [];
  if (columnas.length > 0) {
    newLines.push(`columna: "${columnas[0]}"`);
    columnaCount++;
  }
  if (secciones.length > 0) {
    newLines.push(`seccion: "${secciones[0]}"`);
    seccionCount++;
  }

  // Replace tags line and add new fields after it
  let newFrontmatter = frontmatter.replace(
    /tags:\s*\[[\s\S]*?\]/,
    newTagsLine + '\n' + newLines.join('\n')
  );

  const newContent = `---\n${newFrontmatter}\n---\n${body}`;
  fs.writeFileSync(filePath, newContent, 'utf8');
  modified++;
}

console.log(`\n✅ Migration complete`);
console.log(`   Files modified: ${modified} / ${files.length}`);
console.log(`   Columnas extracted: ${columnaCount} (${allColumnas.size} unique)`);
console.log(`   Secciones extracted: ${seccionCount} (${allSecciones.size} unique)`);
console.log(`   Remaining regular tags: ${allTags.size} unique`);
console.log(`\n📋 Unique columnas:`);
[...allColumnas].sort().forEach(c => console.log(`   • ${c}`));
console.log(`\n📋 Unique secciones:`);
[...allSecciones].sort().forEach(s => console.log(`   • ${s}`));
