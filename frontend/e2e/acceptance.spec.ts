import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("schedule discovery, filters, clocks, provenance and assistant fit accessible desktop/mobile views", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("System ready")).toBeVisible();
  await expect(page.getByText(/Schedule may be outdated/)).toBeVisible();
  await expect(page.getByRole("link", { name: "Australian Grand Prix", exact: true })).toBeVisible();
  await page.getByRole("combobox", { name: "Competition", exact: true }).selectOption({ label: "Formula One" });
  await page.getByLabel("From date").fill("2026-03-01");
  await page.getByLabel("Through date").fill("2026-03-08");
  await expect(page.getByRole("link", { name: "Chinese Grand Prix", exact: true })).toHaveCount(0);
  await page.getByRole("link", { name: "Australian Grand Prix", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Australian Grand Prix", exact: true })).toBeVisible();
  await page.getByRole("combobox", { name: "Display time zone" }).selectOption("UTC");
  await expect(page.locator("time").filter({ hasText: "01:30" }).first()).toBeVisible();
  await page.getByRole("combobox", { name: "Display time zone" }).selectOption("event");
  await expect(page.locator("time").filter({ hasText: "12:30" }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: /source/i }).first()).toHaveAttribute("href", /^https:/);
  await expect(page.getByText(/Retrieved/).first()).toBeVisible();
  await page.getByRole("button", { name: "Ask", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Ask Racing Hub" })).toBeVisible();
  await page.getByRole("radio", { name: "Compare rules" }).check();
  await expect(page.getByRole("group", { name: "Formula One vs NLS" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const accessibility = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(accessibility.violations.map(issue => ({ id: issue.id, targets: issue.nodes.map(node => node.target) }))).toEqual([]);
  await page.screenshot({ path: test.info().outputPath("schedule-assistant.png"), fullPage: true });
  await page.getByRole("button", { name: "Ask", exact: true }).click();
  await page.getByRole("link", { name: "Back to schedule" }).click();
  await expect(page.getByLabel("From date")).toHaveValue("2026-03-01");
  await page.getByLabel("From date").fill("");
  await page.getByLabel("Through date").fill("");
  await page.getByRole("combobox", { name: "Competition", exact: true }).selectOption({ label: "GT World Challenge Europe" });
  await expect(page.getByLabel("Prologue").first()).toBeVisible();
  await page.getByRole("combobox", { name: "Competition", exact: true }).selectOption({ label: "NLS" });
  await expect(page.getByText("Cancelled", { exact: true }).first()).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test("exports download the selected accepted publication and independent ontology", async ({ page }) => {
  await page.goto("/?view=exports");
  await expect(page.getByRole("button", { name: "Download publication", exact: true })).toBeEnabled();
  for (const format of ["json", "csv", "turtle"]) {
    await page.getByRole("combobox", { name: "Format" }).selectOption(format);
    const pending = page.waitForEvent("download");
    await page.getByRole("button", { name: "Download publication", exact: true }).click();
    const download = await pending;
    expect(await download.failure()).toBeNull();
    expect(download.suggestedFilename()).toMatch(/^racing-hub-[0-9a-f]{64}\.(json|csv|ttl)$/);
  }
  const pending = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download ontology", exact: true }).click();
  expect(await (await pending).failure()).toBeNull();
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});