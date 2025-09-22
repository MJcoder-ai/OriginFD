import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const ACCESS_COOKIE = "originfd_access_token";
const REFRESH_COOKIE = "originfd_refresh_token";

export async function POST() {
  const response = NextResponse.json({ success: true });
  const cookieStore = cookies();

  if (cookieStore.get(ACCESS_COOKIE)) {
    response.cookies.delete(ACCESS_COOKIE);
  }

  if (cookieStore.get(REFRESH_COOKIE)) {
    response.cookies.delete(REFRESH_COOKIE);
  }

  return response;
}
