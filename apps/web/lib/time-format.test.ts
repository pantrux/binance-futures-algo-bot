import test from "node:test";
import assert from "node:assert/strict";
import { formatRelativeAge } from "./time-format.ts";

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
