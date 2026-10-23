import { expect, test } from "@playwright/test";

test("trang khám phá tải được", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Nghe thành phố kể/ })).toBeVisible();
});
