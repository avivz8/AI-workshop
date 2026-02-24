import { test, expect } from "@playwright/test";

test.describe("Todo App", () => {
  test("renders todo items from the API", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByTestId("todo-list")).toBeVisible();

    const items = page.getByTestId(/^todo-item-/);
    await expect(items.first()).toBeVisible();
    expect(await items.count()).toBeGreaterThan(0);
  });

  test("displays a checkbox for each todo item", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByTestId("todo-list")).toBeVisible();

    const checkbox = page.getByTestId(/^todo-checkbox-/);
    await expect(checkbox.first()).toBeVisible();
  });
});
