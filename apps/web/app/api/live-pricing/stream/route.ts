import { NextRequest } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const STREAM_INTERVAL_MS = 4_000;
const STREAM_FETCH_TIMEOUT_MS = 10_000;
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

function sleep(ms: number, signal?: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    const timeout = setTimeout(() => {
      signal?.removeEventListener("abort", onAbort);
      resolve();
    }, ms);

    const onAbort = () => {
      clearTimeout(timeout);
      signal?.removeEventListener("abort", onAbort);
      reject(new Error("sleep_aborted"));
    };

    if (signal) {
      if (signal.aborted) {
        onAbort();
        return;
      }
      signal.addEventListener("abort", onAbort, { once: true });
    }
  });
}

export async function GET(request: NextRequest) {
  const apiBaseUrl = buildApiBaseUrl();
  if (!apiBaseUrl) {
    return new Response("live pricing unavailable: missing API base URL", { status: 503 });
  }

  const targetUrl = buildLivePricingUrl(request, apiBaseUrl);
  const encoder = new TextEncoder();
  let closed = false;

  const sleepController = new AbortController();
  const closeStream = () => {
    if (closed) {
      return;
    }
    closed = true;
    sleepController.abort();
  };

  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      const safeClose = () => {
        if (closed) {
          return;
        }
        closeStream();
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
          const response = await fetch(targetUrl, {
            cache: "no-store",
            signal: AbortSignal.any([request.signal, AbortSignal.timeout(STREAM_FETCH_TIMEOUT_MS)]),
          });
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
          const message = error instanceof Error && error.name === "TimeoutError"
            ? "Live pricing upstream timeout"
            : error instanceof Error
              ? error.message
              : "Live pricing stream failed";
          sendError(message);
        }
      };

      request.signal.addEventListener("abort", safeClose, { once: true });

      void (async () => {
        while (!closed) {
          await fetchAndSend();
          if (closed) {
            break;
          }
          try {
            await sleep(STREAM_INTERVAL_MS, sleepController.signal);
          } catch {
            safeClose();
            break;
          }
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
