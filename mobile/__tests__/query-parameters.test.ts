import { serializeQueryParameters } from "../src/api/query-parameters";

describe("serializeQueryParameters", () => {
  it("serializes a single parameter", () => {
    expect(serializeQueryParameters({ limit: 20 })).toBe("limit=20");
  });

  it("repeats the same key for array values", () => {
    const result = serializeQueryParameters({ weekday: ["1", "2"] });

    expect(result).toBe("weekday=1&weekday=2");
  });

  it("serializes multiple different keys", () => {
    const result = serializeQueryParameters({
      officialStatus: ["official", "unofficial"],
      sort: "newest",
    });

    expect(result).toBe(
      "officialStatus=official&officialStatus=unofficial&sort=newest",
    );
  });

  it("omits undefined, null, and empty array values", () => {
    expect(
      serializeQueryParameters({
        cursor: undefined,
        q: null,
        tagId: [],
      }),
    ).toBe("");
  });

  it("preserves cursor and q semantics while URLSearchParams encodes them", () => {
    const cursor = "opaque+/=value";
    const q = "軽音 100%";
    const result = new URLSearchParams(
      serializeQueryParameters({ cursor, q }),
    );

    expect(result.get("cursor")).toBe(cursor);
    expect(result.get("q")).toBe(q);
  });
});
