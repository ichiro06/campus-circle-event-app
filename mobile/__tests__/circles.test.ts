import {
  createCirclesApi,
  type ListCirclesQuery,
} from "../src/api/circles";
import { serializeQueryParameters } from "../src/api/query-parameters";
import type { ApiTransport } from "../src/api/transport";

function createTransportMock(): {
  request: jest.Mock;
  transport: ApiTransport;
} {
  const request = jest.fn().mockResolvedValue({ data: [] });

  return {
    request,
    transport: { request },
  };
}

describe("createCirclesApi", () => {
  it("uses the formal list path and approved query", async () => {
    const { request, transport } = createTransportMock();
    const api = createCirclesApi(transport);
    const query: ListCirclesQuery = {
      cursor: "opaque+/=cursor",
      limit: 20,
      q: "軽音",
      tagId: ["00000000-0000-0000-0000-000000000001"],
      weekday: ["1", "2"],
    };

    await api.listCircles(query);

    expect(request).toHaveBeenCalledWith({
      method: "GET",
      path: "/api/v1/circles",
      query,
      signal: undefined,
    });
  });

  it("encodes the detail path parameter", async () => {
    const { request, transport } = createTransportMock();
    const api = createCirclesApi(transport);

    await api.getCircle("00000000-0000-0000-0000-000000000001/unsafe");

    expect(request).toHaveBeenCalledWith({
      method: "GET",
      path: "/api/v1/circles/00000000-0000-0000-0000-000000000001%2Funsafe",
      signal: undefined,
    });
  });

  it("forwards the caller AbortSignal", async () => {
    const { request, transport } = createTransportMock();
    const api = createCirclesApi(transport);
    const controller = new AbortController();

    await api.getCircle("00000000-0000-0000-0000-000000000001", {
      signal: controller.signal,
    });

    expect(request).toHaveBeenCalledWith(
      expect.objectContaining({ signal: controller.signal }),
    );
  });

  it("uses the public tag catalog path with only cursor and limit", async () => {
    const { request, transport } = createTransportMock();
    const api = createCirclesApi(transport);

    await api.listTags({ cursor: "opaque+/=cursor", limit: 50 });

    expect(request).toHaveBeenCalledWith({
      method: "GET",
      path: "/api/v1/tags",
      query: { cursor: "opaque+/=cursor", limit: 50 },
      signal: undefined,
    });
  });

  it("requests the first tag page without a query and forwards the AbortSignal", async () => {
    const { request, transport } = createTransportMock();
    const api = createCirclesApi(transport);
    const controller = new AbortController();

    await api.listTags(undefined, { signal: controller.signal });

    expect(request).toHaveBeenCalledWith({
      method: "GET",
      path: "/api/v1/tags",
      query: {},
      signal: controller.signal,
    });
  });

  it("repeats tagId for every selected tag in the circle list query", () => {
    const first = "20000000-0000-0000-0000-000000000001";
    const second = "20000000-0000-0000-0000-000000000002";
    const query: ListCirclesQuery = {
      officialStatus: ["official"],
      q: "軽音",
      sort: "newest",
      tagId: [first, second],
    };

    expect(new URLSearchParams(serializeQueryParameters(query)).getAll("tagId")).toEqual([
      first,
      second,
    ]);
    expect(serializeQueryParameters(query)).toBe(
      `officialStatus=official&q=${encodeURIComponent("軽音")}&sort=newest&tagId=${first}&tagId=${second}`,
    );
  });
});
