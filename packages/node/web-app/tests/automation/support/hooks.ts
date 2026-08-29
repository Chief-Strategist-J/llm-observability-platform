import { Before, After, BeforeAll, AfterAll, Status } from '@cucumber/cucumber';
import { chromium, type Browser, type BrowserContext, type Page } from '@playwright/test';

export interface CustomWorld {
  browser?: Browser;
  context?: BrowserContext;
  page?: Page;
  testData?: Record<string, any>;
  attach: (data: string | Buffer, mediaType: string) => void;
}

let globalBrowser: Browser;

BeforeAll(async function () {
  globalBrowser = await chromium.launch({ headless: true });
});

AfterAll(async function () {
  if (globalBrowser) {
    await globalBrowser.close();
  }
});

Before(async function (this: CustomWorld) {
  this.browser = globalBrowser;
  this.context = await globalBrowser.newContext({
    viewport: { width: 1280, height: 720 },
  });
  this.page = await this.context.newPage();
  this.testData = {};
});

After(async function (this: CustomWorld, scenario) {
  if (scenario.result?.status === Status.FAILED && this.page) {
    const screenshot = await this.page.screenshot({ fullPage: true });
    this.attach(screenshot, 'image/png');
  }
  if (this.page) {
    await this.page.close();
  }
  if (this.context) {
    await this.context.close();
  }
});
