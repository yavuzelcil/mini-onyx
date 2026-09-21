import { expect, test } from "bun:test";

import { formatPersonaName } from "@/lib/personas/format";

test("capitalizes the first letter of a persona name", () => {
  expect(formatPersonaName("teacher")).toBe("Teacher");
});

test("keeps an empty name empty", () => {
  expect(formatPersonaName("")).toBe("");
});
