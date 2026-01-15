const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

const buildUrl = (path: string) => {
  if (path.startsWith("http")) {
    return path;
  }
  return `${API_BASE_URL}${path.startsWith("/") ? "" : "/"}${path}`;
};

// Fix LaTeX backslash sequences that get corrupted during JSON parsing
// JSON interprets \f as form-feed, \b as backspace, \v as vertical tab, etc.
// When the backend sends improperly escaped LaTeX, these become control characters
// We only fix control characters that are unlikely to appear in normal content
const fixLatexEscapes = (value: unknown): unknown => {
  if (typeof value === "string") {
    // Replace control characters with proper backslash sequences
    // Only fix chars that are very unlikely to appear in normal content
    return value
      .replace(/\f/g, "\\f")   // form-feed (U+000C) -> \f for \frac
      .replace(/\v/g, "\\v")   // vertical tab (U+000B) -> \v for \vec
      .replace(/\x08/g, "\\b"); // backspace (U+0008) -> \b for \begin, \binom
  }
  if (Array.isArray(value)) {
    return value.map(fixLatexEscapes);
  }
  if (value !== null && typeof value === "object") {
    const result: Record<string, unknown> = {};
    for (const [key, val] of Object.entries(value)) {
      result[key] = fixLatexEscapes(val);
    }
    return result;
  }
  return value;
};

export { fixLatexEscapes };

const parseJson = async <T>(response: Response): Promise<T> => {
  const text = await response.text();
  if (!text) {
    return {} as T;
  }
  const parsed = JSON.parse(text);
  // Fix LaTeX escape sequences after parsing
  return fixLatexEscapes(parsed) as T;
};

export const apiGet = async <T>(path: string): Promise<T> => {
  const response = await fetch(buildUrl(path), {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`GET ${path} failed: ${response.status} ${errorBody}`);
  }

  return parseJson<T>(response);
};

export const apiPost = async <T, B = unknown>(path: string, body: B): Promise<T> => {
  const response = await fetch(buildUrl(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`POST ${path} failed: ${response.status} ${errorBody}`);
  }

  return parseJson<T>(response);
};
