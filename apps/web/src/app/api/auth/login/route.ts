import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/server/api-config";

interface LoginRequestBody {
  email?: string;
  password?: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type?: string;
  expires_in?: number;
  user?: unknown;
}

const ACCESS_COOKIE = "originfd_access_token";
const REFRESH_COOKIE = "originfd_refresh_token";

const isProduction = process.env.NODE_ENV === "production";

const secureCookieOptions = {
  httpOnly: true,
  secure: isProduction,
  sameSite: "lax" as const,
  path: "/",
};

async function fetchCurrentUser(accessToken: string) {
  const baseUrl = getApiBaseUrl();
  const response = await fetch(`${baseUrl}/auth/me`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Response(errorBody || "Failed to fetch user", {
      status: response.status,
    });
  }

  return response.json();
}

export async function POST(request: NextRequest) {
  const baseUrl = getApiBaseUrl();
  let body: LoginRequestBody;

  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { detail: "Invalid login payload" },
      { status: 400 },
    );
  }

  if (!body.email || !body.password) {
    return NextResponse.json(
      { detail: "Email and password are required" },
      { status: 400 },
    );
  }

  let backendResponse: Response;

  try {
    backendResponse = await fetch(`${baseUrl}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email: body.email, password: body.password }),
      cache: "no-store",
    });
  } catch (error) {
    return NextResponse.json(
      { detail: "Unable to reach authentication service" },
      { status: 502 },
    );
  }

  const responseData = (await backendResponse
    .json()
    .catch(() => null)) as TokenResponse | null;

  if (!backendResponse.ok || !responseData) {
    const errorDetail =
      (responseData as any)?.detail || "Authentication failed";
    return NextResponse.json(
      { detail: errorDetail },
      { status: backendResponse.status || 500 },
    );
  }

  const { access_token: accessToken, refresh_token: refreshToken } =
    responseData;

  if (!accessToken || !refreshToken) {
    return NextResponse.json(
      { detail: "Authentication tokens missing from response" },
      { status: 500 },
    );
  }

  let userPayload = responseData.user ?? null;

  if (!userPayload) {
    try {
      userPayload = await fetchCurrentUser(accessToken);
    } catch (error: unknown) {
      if (error instanceof Response) {
        return NextResponse.json(
          { detail: "Authenticated but failed to load user" },
          { status: error.status },
        );
      }

      return NextResponse.json(
        { detail: "Authenticated but failed to load user" },
        { status: 502 },
      );
    }
  }

  const response = NextResponse.json({ user: userPayload });

  const accessTokenMaxAge = responseData.expires_in
    ? Math.max(responseData.expires_in, 60)
    : 60 * 30;

  response.cookies.set(ACCESS_COOKIE, accessToken, {
    ...secureCookieOptions,
    maxAge: accessTokenMaxAge,
  });

  response.cookies.set(REFRESH_COOKIE, refreshToken, {
    ...secureCookieOptions,
    maxAge: 60 * 60 * 24 * 30,
  });

  return response;
}
