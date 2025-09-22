import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/server/api-config";

const ACCESS_COOKIE = "originfd_access_token";

export async function GET() {
  const cookieStore = cookies();
  const token = cookieStore.get(ACCESS_COOKIE)?.value;

  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const baseUrl = getApiBaseUrl();
  let response: Response;

  try {
    response = await fetch(`${baseUrl}/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    });
  } catch (error) {
    return NextResponse.json(
      { detail: "Unable to reach authentication service" },
      { status: 502 },
    );
  }

  const body = await response.text();
  const contentType = response.headers.get("content-type") || "application/json";

  return new NextResponse(body || "{}", {
    status: response.status,
    headers: {
      "content-type": contentType,
    },
  });
}
