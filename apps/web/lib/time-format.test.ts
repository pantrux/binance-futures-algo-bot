import test from "node:test";
import assert from "node:assert/strict";
import { buildLiveLagStatus, buildLiveStateLabel, formatElapsedMs, formatRelativeAge } from "./time-format.ts";

const NOW = Date.parse("2026-03-17T20:00:00.000Z");

test("formatRelativeAge handles seconds", () => {
  assert.equal(formatRelativeAge("2026-03-17T19:59:48.000Z", NOW), "hace 12s");
  assert.equal(formatRelativeAge("2026-03-17T19:59:01.000Z", NOW), "hace 59s");
  assert.equal(formatRelativeAge("2026-03-17T19:59:00.000Z", NOW), "hace 1m");
});

test("formatRelativeAge handles minutes", () => {
  assert.equal(formatRelativeAge("2026-03-17T19:57:00.000Z", NOW), "hace 3m");
  assert.equal(formatRelativeAge("2026-03-17T19:01:00.000Z", NOW), "hace 59m");
  assert.equal(formatRelativeAge("2026-03-17T19:00:00.000Z", NOW), "hace 1h");
});

test("formatRelativeAge handles hours", () => {
  assert.equal(formatRelativeAge("2026-03-17T17:00:00.000Z", NOW), "hace 3h");
  assert.equal(formatRelativeAge("2026-03-16T21:00:00.000Z", NOW), "hace 23h");
  assert.equal(formatRelativeAge("2026-03-16T20:00:00.000Z", NOW), "hace 1d");
});

test("formatRelativeAge handles days", () => {
  assert.equal(formatRelativeAge("2026-03-15T20:00:00.000Z", NOW), "hace 2d");
});

test("formatRelativeAge returns null for invalid timestamps", () => {
  assert.equal(formatRelativeAge("not-a-date", NOW), null);
});

test("formatElapsedMs handles seconds and minutes", () => {
  assert.equal(formatElapsedMs(800), "ahora");
  assert.equal(formatElapsedMs(12_000), "12s");
  assert.equal(formatElapsedMs(65_000), "1m 5s");
  assert.equal(formatElapsedMs(120_000), "2m");
});

test("buildLiveStateLabel appends age when available", () => {
  assert.equal(buildLiveStateLabel("live fresco", null), "live fresco");
  assert.equal(buildLiveStateLabel("live fresco", 4_000), "live fresco · 4s");
  assert.equal(buildLiveStateLabel("live pausado", 65_000), "live pausado · 1m 5s");
});

test("buildLiveLagStatus ignores fresh or invalid data", () => {
  assert.equal(buildLiveLagStatus("2026-03-17T19:59:58.000Z", "2026-03-17T20:00:00.000Z"), null);
  assert.equal(buildLiveLagStatus("not-a-date", "2026-03-17T20:00:00.000Z"), null);
  assert.equal(buildLiveLagStatus("2026-03-17T19:59:00.000Z", null), null);
});

test("buildLiveLagStatus flags warn and danger thresholds", () => {
  assert.deepEqual(buildLiveLagStatus("2026-03-17T19:59:48.000Z", "2026-03-17T20:00:00.000Z"), {
    tone: "warn",
    label: "envejeciendo vs live · 12s detrás del último tick live",
    detail: "12s detrás del último tick live",
    deltaMs: 12_000,
  });

  assert.deepEqual(buildLiveLagStatus("2026-03-17T19:59:45.000Z", "2026-03-17T20:00:00.000Z"), {
    tone: "warn",
    label: "envejeciendo vs live · 15s detrás del último tick live",
    detail: "15s detrás del último tick live",
    deltaMs: 15_000,
  });

  assert.deepEqual(buildLiveLagStatus("2026-03-17T19:59:28.000Z", "2026-03-17T20:00:00.000Z"), {
    tone: "danger",
    label: "stale vs live · 32s detrás del último tick live",
    detail: "32s detrás del último tick live",
    deltaMs: 32_000,
  });

  assert.deepEqual(buildLiveLagStatus("2026-03-17T19:59:20.000Z", "2026-03-17T20:00:00.000Z"), {
    tone: "danger",
    label: "stale vs live · 40s detrás del último tick live",
    detail: "40s detrás del último tick live",
    deltaMs: 40_000,
  });
});
