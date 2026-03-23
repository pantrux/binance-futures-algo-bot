import { NextRequest } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

function normalizeBaseUrl(value: string | undefined) {
  return value?.trim().replace(/\/$/, "") || null;
}

function buildApiBaseUrl() {
  return normalizeBaseUrl(process.env.SYNOLOGY_API_BASE_URL) ?? normalizeBaseUrl(process.env.NEXT_PUBLIC_API_URL);
}

function buildLivePricingUrl(request: NextRequest, apiBaseUrl: string) {
  const url = new URL(`${apiBaseUrl}/dashboard/live-pricing`);
  request.nextUrl.searchParams.getAll("symbols").forEach((symbol) => {
    const normalized = symbol.trim().toUpperCase();
    if (normalized) {
      url.searchParams.append("symbols", normalized);
    }
  });
  return url;
}

export async function GET(request: NextRequest) {
  const apiBaseUrl = buildApiBaseUrl();
  if (!apiBaseUrl) {
    return Response.json({ detail: "live pricing unavailable: missing API base URL" }, { status: 503 });
  }

  const response = await fetch(buildLivePricingUrl(request, apiBaseUrl), {
    cache: "no-store",
    signal: request.signal,
  });

  const payload = await response.text();

  return new Response(payload, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") ?? "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}
