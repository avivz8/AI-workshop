import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  use: {
    baseURL: "http://localhost:3000",
    headless: true,
  },
  webServer: {
    command: "yarn start",
    url: "http://localhost:3000",
    timeout: 120_000,
    reuseExistingServer: !process.env.CI,
  },
});
