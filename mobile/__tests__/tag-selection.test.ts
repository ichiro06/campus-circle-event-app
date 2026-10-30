import {
  mergeTagChoices,
  selectedTagIds,
  toggleTag,
} from "../src/circles/tag-selection";
import { makeTag } from "../test-support/circles";

describe("tag selection", () => {
  const tag1 = makeTag(1);
  const tag2 = makeTag(2);
  const tag3 = makeTag(3);

  it("offers the catalog in API order, not sorted by id or name", () => {
    expect(mergeTagChoices([tag3, tag1, tag2], [])).toEqual([tag3, tag1, tag2]);
  });

  it("keeps a selected tag that left the catalog, after the catalog tags", () => {
    expect(mergeTagChoices([tag2, tag3], [tag1])).toEqual([tag2, tag3, tag1]);
  });

  it("does not duplicate a selected tag that is still in the catalog", () => {
    expect(mergeTagChoices([tag1, tag2], [tag2])).toEqual([tag1, tag2]);
  });

  it("toggles a tag on and off by id", () => {
    const selected = toggleTag([], tag1);

    expect(selected).toEqual([tag1]);
    expect(toggleTag(selected, { ...tag1, name: "renamed" })).toEqual([]);
    expect(toggleTag(selected, tag2)).toEqual([tag1, tag2]);
  });

  it("lists the selected IDs sorted by UUID whatever the selection or catalog order", () => {
    expect(selectedTagIds([tag2, tag3])).toEqual([tag2.id, tag3.id]);
    expect(selectedTagIds([tag3, tag2])).toEqual([tag2.id, tag3.id]);
    expect(selectedTagIds([tag3, tag1, tag2])).toEqual([tag1.id, tag2.id, tag3.id]);
    expect(selectedTagIds([])).toEqual([]);
  });

  it("gives the same IDs for the same selection when the catalog order changes", () => {
    const selected = [tag1, tag2];
    const idsBefore = selectedTagIds(selected);

    // Choices are derived from the catalog; only their display order changes.
    expect(mergeTagChoices([tag2, tag1], selected)).toEqual([tag2, tag1]);
    expect(selectedTagIds(selected)).toEqual(idsBefore);
  });

  it("lists a repeated tag once", () => {
    expect(selectedTagIds([tag1, tag1])).toEqual([tag1.id]);
  });
});
