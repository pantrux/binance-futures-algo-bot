export const LIVE_STALE_WARN_MS = 12_000;
export const LIVE_STALE_DANGER_MS = 32_000;

export type LiveLagStatus = {
  tone: "warn" | "danger";
  label: string;
  detail: string;
  deltaMs: number;
};

export function formatRelativeAge(value: string, nowMs = Date.now()) {
  const timestampMs = Date.parse(value);
  if (Number.isNaN(timestampMs)) return null;

  const diffSeconds = Math.max(0, Math.floor((nowMs - timestampMs) / 1000));
  if (diffSeconds < 60) return `hace ${diffSeconds}s`;

  const diffMinutes = Math.floor(diffSeconds / 60);
  if (diffMinutes < 60) return `hace ${diffMinutes}m`;

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `hace ${diffHours}h`;

  const diffDays = Math.floor(diffHours / 24);
  return `hace ${diffDays}d`;
}

export function formatElapsedMs(value: number) {
  if (value < 1_000) {
    return "ahora";
  }

  const totalSeconds = Math.floor(value / 1_000);
  if (totalSeconds < 60) {
    return `${totalSeconds}s`;
  }

  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return seconds === 0 ? `${minutes}m` : `${minutes}m ${seconds}s`;
}

export function buildLiveLagStatus(snapshotValue: string | null | undefined, liveValue: string | null | undefined): LiveLagStatus | null {
  if (!snapshotValue || !liveValue) return null;

  const snapshotMs = Date.parse(snapshotValue);
  const liveMs = Date.parse(liveValue);
  if (Number.isNaN(snapshotMs) || Number.isNaN(liveMs)) return null;

  const deltaMs = Math.max(0, liveMs - snapshotMs);
  if (deltaMs < LIVE_STALE_WARN_MS) return null;

  const detail = `${formatElapsedMs(deltaMs)} detrás del último tick live`;
  if (deltaMs >= LIVE_STALE_DANGER_MS) {
    return {
      tone: "danger",
      label: `stale vs live · ${detail}`,
      detail,
      deltaMs,
    };
  }

  return {
    tone: "warn",
    label: `envejeciendo vs live · ${detail}`,
    detail,
    deltaMs,
  };
}
