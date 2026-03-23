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

  try {
    const response = await fetch(buildLivePricingUrl(request, apiBaseUrl), {
      cache: "no-store",
      signal: AbortSignal.any([request.signal, AbortSignal.timeout(10_000)]),
    });

    const payload = await response.text();

    return new Response(payload, {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("Content-Type") ?? "application/json; charset=utf-8",
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    if (request.signal.aborted) {
      return new Response(null, { status: 499 });
    }

    const detail = error instanceof Error && error.name === "TimeoutError"
      ? "live pricing upstream timeout"
      : "live pricing upstream unavailable";
    const status = error instanceof Error && error.name === "TimeoutError" ? 504 : 503;
    return Response.json({ detail }, { status });
  }
}
