import type { QueryParameters } from "../types/query-params.types";

/** Devuelve la query sin '?'; las listas usan claves repetidas y se conservan 0 y false. */
export function createQueryParams(parameters: QueryParameters): string {
  const searchParams = new URLSearchParams();

  for (const [key, value] of Object.entries(parameters)) {
    if (value === null || value === undefined) continue;

    const values = Array.isArray(value) ? value : [value];
    for (const item of values) {
      searchParams.append(key, String(item));
    }
  }

  return searchParams.toString();
}
