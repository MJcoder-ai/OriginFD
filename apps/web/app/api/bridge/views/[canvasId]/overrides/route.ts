import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

export async function GET(
  _req: NextRequest,
  { params }: { params: { canvasId: string } },
) {
  const { canvasId } = params;
  try {
    const rows = await prisma.viewOverride.findMany({ where: { canvasId } });
    const map: Record<string, { x: number; y: number; rotation?: number }> = {};
    for (const r of rows)
      map[r.instanceId] = { x: r.x, y: r.y, rotation: r.rotation ?? undefined };
    return NextResponse.json(map);
  } catch (error) {
    // Fallback to empty if DB not available
    console.warn("DB not available for view overrides:", error);
    return NextResponse.json({});
  }
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: { canvasId: string } },
) {
  const { canvasId } = params;
  try {
    const body = (await req.json().catch(() => ({}))) as Record<
      string,
      { x: number; y: number; rotation?: number }
    >;
    if (!body || typeof body !== "object") {
      return NextResponse.json({ error: "Invalid body" }, { status: 400 });
    }
    const ops = Object.entries(body).map(([instanceId, p]) =>
      prisma.viewOverride.upsert({
        where: { canvasId_instanceId: { canvasId, instanceId } },
        create: {
          canvasId,
          instanceId,
          x: p.x,
          y: p.y,
          rotation: p.rotation ?? null,
        },
        update: { x: p.x, y: p.y, rotation: p.rotation ?? null },
      }),
    );
    await prisma.$transaction(ops);
    return NextResponse.json({ ok: true });
  } catch (error) {
    console.warn("Failed to persist view overrides:", error);
    return NextResponse.json(
      { ok: false, error: "Database unavailable" },
      { status: 500 },
    );
  }
}
