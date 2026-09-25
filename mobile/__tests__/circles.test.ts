import {
  createCirclesApi,
  type ListCirclesQuery,
} from "../src/api/circles";
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
});
