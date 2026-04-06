import { getCollection } from 'astro:content';

let _authorMap: Map<string, string> | null = null;

export async function getAuthorMap(): Promise<Map<string, string>> {
  if (_authorMap) return _authorMap;
  const authors = await getCollection('authors');
  _authorMap = new Map(authors.map((a) => [a.data.slug, a.data.name]));
  return _authorMap;
}

export function getAuthorName(map: Map<string, string>, slug: string): string {
  return map.get(slug) || slug;
}
