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

/**
 * The selected tag IDs as the `tagId` query value: unique and sorted by UUID.
 *
 * The filter is an OR over the set (docs/api-contract.md 4.1), so the order carries no meaning.
 * Fixing it keeps the search key of an unchanged selection identical however the catalog is
 * reordered or in whichever order the tags were picked, which would otherwise start a new
 * search for nothing. The order the tags are shown in stays the catalog order.
 */
export function selectedTagIds(selected: readonly PublicTag[]): string[] {
  return [...new Set(selected.map((tag) => tag.id))].sort((left, right) =>
    left < right ? -1 : left > right ? 1 : 0,
  );
}
