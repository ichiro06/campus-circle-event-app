import type { PublicTag } from "./types";

/**
 * The tags to offer as choices: the catalog in API order, followed by selected tags that the
 * catalog no longer contains.
 *
 * A tag that was selected and then deactivated on the server leaves the catalog, yet the search
 * keeps working on its `tagId` (DEC-068 H5). Keeping it as a choice lets the user see and clear
 * that condition, while it can never be chosen again once cleared, because only catalog tags
 * are offered to start with.
 */
export function mergeTagChoices(
  catalog: readonly PublicTag[],
  selected: readonly PublicTag[],
): PublicTag[] {
  const catalogIds = new Set(catalog.map((tag) => tag.id));

  return [...catalog, ...selected.filter((tag) => !catalogIds.has(tag.id))];
}

export function toggleTag(
  selected: readonly PublicTag[],
  tag: PublicTag,
): PublicTag[] {
  return selected.some((current) => current.id === tag.id)
    ? selected.filter((current) => current.id !== tag.id)
    : [...selected, tag];
}

/** Selected tag IDs in choice order, so equal selections always produce the same query. */
export function selectedTagIds(
  choices: readonly PublicTag[],
  selected: readonly PublicTag[],
): string[] {
  const selectedIds = new Set(selected.map((tag) => tag.id));

  return choices.filter((tag) => selectedIds.has(tag.id)).map((tag) => tag.id);
}
