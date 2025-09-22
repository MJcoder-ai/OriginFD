import { NextRequest, NextResponse } from "next/server";
import { getDocumentVersionHistory } from "../../../shared-data";

export async function GET(
  _request: NextRequest,
  { params }: { params: { id: string } },
) {
  const history = getDocumentVersionHistory(params.id);
  const versions = history
    .map(({ document, ...metadata }) => metadata)
    .sort((a, b) => b.version_number - a.version_number);

  return NextResponse.json(versions);
}
