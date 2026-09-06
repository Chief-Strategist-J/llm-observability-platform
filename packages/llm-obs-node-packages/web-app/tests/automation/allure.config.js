/**
 * Allure Reporter Configuration for BDD Playwright & Cucumber Automation
 */

module.exports = {
  resultsDir: 'allure-results',
  reportDir: 'allure-report',
  clean: true,
  environmentInfo: {
    Framework: 'Playwright + Cucumber BDD',
    Platform: 'LLM Observability Platform',
    Browser: 'Chromium / Playwright Headless',
    Environment: 'Development / Integration Staging',
  },
};
