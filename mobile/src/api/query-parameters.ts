export type QueryParameterScalar = boolean | number | string;

export type QueryParameterValue =
  | QueryParameterScalar
  | readonly QueryParameterScalar[]
  | null
  | undefined;

export function serializeQueryParameters(parameters?: object): string {
  const searchParameters = new URLSearchParams();

  if (!parameters) {
    return "";
  }

  for (const [key, value] of Object.entries(
    parameters as Record<string, unknown>,
  )) {
    if (value === null || value === undefined) {
      continue;
    }

    const values = Array.isArray(value) ? value : [value];

    for (const item of values) {
      if (
        typeof item !== "string" &&
        typeof item !== "number" &&
        typeof item !== "boolean"
      ) {
        throw new TypeError(`Unsupported query parameter value for ${key}`);
      }

      searchParameters.append(key, String(item));
    }
  }

  return searchParameters.toString();
}
