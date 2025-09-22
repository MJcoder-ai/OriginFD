import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/server/api-config";

const ACCESS_COOKIE = "originfd_access_token";

function buildTargetUrl(request: NextRequest, pathSegments: string[]): string {
  const baseUrl = getApiBaseUrl();
  const path = pathSegments.join("/");
  const url = new URL(request.url);
  const search = url.search ? url.search : "";
  const normalizedPath = path ? `/${path}` : "";
  return `${baseUrl}${normalizedPath}${search}`;
}

function filterHeaders(headers: Headers, token?: string): Headers {
  const result = new Headers();

  headers.forEach((value, key) => {
    const lowerKey = key.toLowerCase();
    if (["host", "connection", "accept-encoding"].includes(lowerKey)) {
      return;
    }

    if (lowerKey === "cookie") {
      return;
    }

    result.set(key, value);
  });

  if (token) {
    result.set("Authorization", `Bearer ${token}`);
  }

  return result;
}

async function proxyRequest(request: NextRequest, path: string[]) {
  const token = cookies().get(ACCESS_COOKIE)?.value;
  const targetUrl = buildTargetUrl(request, path);
  const headers = filterHeaders(new Headers(request.headers), token);

  const init: RequestInit = {
    method: request.method,
    headers,
    redirect: "manual",
    cache: "no-store",
  };

  if (![
    "GET",
    "HEAD",
  ].includes(request.method.toUpperCase())) {
    if (request.body) {
      init.body = request.body;
      (init as any).duplex = "half";
    }
  }

  let backendResponse: Response;

  try {
    backendResponse = await fetch(targetUrl, init);
  } catch (error) {
    return NextResponse.json(
      { detail: "Upstream request failed" },
      { status: 502 },
    );
  }
  const responseHeaders = new Headers();
  backendResponse.headers.forEach((value, key) => {
    if (key.toLowerCase() === "transfer-encoding") {
      return;
    }
    responseHeaders.set(key, value);
  });

  return new NextResponse(backendResponse.body, {
    status: backendResponse.status,
    headers: responseHeaders,
  });
}

export async function GET(
  request: NextRequest,
  context: { params: { path: string[] } },
) {
  return proxyRequest(request, context.params.path);
}

export async function POST(
  request: NextRequest,
  context: { params: { path: string[] } },
) {
  return proxyRequest(request, context.params.path);
}

export async function PUT(
  request: NextRequest,
  context: { params: { path: string[] } },
) {
  return proxyRequest(request, context.params.path);
}

export async function PATCH(
  request: NextRequest,
  context: { params: { path: string[] } },
) {
  return proxyRequest(request, context.params.path);
}

export async function DELETE(
  request: NextRequest,
  context: { params: { path: string[] } },
) {
  return proxyRequest(request, context.params.path);
}

export async function OPTIONS(
  request: NextRequest,
  context: { params: { path: string[] } },
) {
  return proxyRequest(request, context.params.path);
}
