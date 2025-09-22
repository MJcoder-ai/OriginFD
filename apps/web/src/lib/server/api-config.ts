const API_ENV_KEYS = [
  "ORIGINFD_API_URL",
  "NEXT_PUBLIC_API_URL",
  "API_URL",
];

export function getApiBaseUrl(): string {
  for (const key of API_ENV_KEYS) {
    const value = process.env[key];
    if (value && value.trim().length > 0) {
      return value.replace(/\/+$/, "");
    }
  }

  return "http://localhost:8000";
}
