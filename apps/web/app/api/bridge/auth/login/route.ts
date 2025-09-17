import { NextRequest, NextResponse } from "next/server";

// Mock user data for authentication
const MOCK_USER = {
  id: "user-1",
  email: "admin@originfd.com",
  full_name: "System Administrator",
  is_active: true,
  roles: ["admin", "user"],
};

const MOCK_CREDENTIALS = {
  email: "admin@originfd.com",
  password: "admin",
};

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, password } = body;

    console.log("Login attempt:", { email, password: "***" });

    // Validate credentials
    if (
      email !== MOCK_CREDENTIALS.email ||
      password !== MOCK_CREDENTIALS.password
    ) {
      return NextResponse.json(
        { detail: "Invalid email or password" },
        { status: 401 },
      );
    }

    // Generate mock tokens
    const tokenResponse = {
      access_token: `mock-access-token-${Date.now()}`,
      refresh_token: `mock-refresh-token-${Date.now()}`,
      token_type: "bearer",
      expires_in: 3600,
      user: MOCK_USER,
    };

    console.log("Login successful for:", email);

    return NextResponse.json(tokenResponse);
  } catch (error) {
    console.error("Login error:", error);
    return NextResponse.json({ detail: "Login failed" }, { status: 500 });
  }
}
