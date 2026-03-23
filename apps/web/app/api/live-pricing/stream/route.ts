import { NextRequest } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const STREAM_INTERVAL_MS = 4_000;
const RETRY_MS = 3_000;

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

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function GET(request: NextRequest) {
  const apiBaseUrl = buildApiBaseUrl();
  if (!apiBaseUrl) {
    return new Response("live pricing unavailable: missing API base URL", { status: 503 });
  }

  const targetUrl = buildLivePricingUrl(request, apiBaseUrl);
  const encoder = new TextEncoder();
  let closed = false;

  let closeStream = () => {
    closed = true;
  };

  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      const safeClose = () => {
        if (closed) {
          return;
        }
        closed = true;
        try {
          controller.close();
        } catch {
          // Client already disconnected.
        }
      };

      const safeEnqueue = (chunk: string) => {
        if (closed) {
          return;
        }
        try {
          controller.enqueue(encoder.encode(chunk));
        } catch {
          safeClose();
        }
      };

      const sendPayload = (payload: unknown) => {
        safeEnqueue(`retry: ${RETRY_MS}\ndata: ${JSON.stringify(payload)}\n\n`);
      };

      const sendError = (message: string) => {
        sendPayload({ ok: false, error: message, timestamp: new Date().toISOString() });
      };

      const fetchAndSend = async () => {
        try {
          const response = await fetch(targetUrl, { cache: "no-store", signal: request.signal });
          if (!response.ok) {
            throw new Error(`Live pricing upstream failed (${response.status})`);
          }
          const payload = await response.json();
          sendPayload({ ok: true, payload });
        } catch (error) {
          if (request.signal.aborted || closed) {
            safeClose();
            return;
          }
          sendError(error instanceof Error ? error.message : "Live pricing stream failed");
        }
      };

      closeStream = safeClose;
      request.signal.addEventListener("abort", safeClose, { once: true });

      void (async () => {
        while (!closed) {
          await fetchAndSend();
          if (closed) {
            break;
          }
          await sleep(STREAM_INTERVAL_MS);
        }
      })();
    },
    cancel() {
      closeStream();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
