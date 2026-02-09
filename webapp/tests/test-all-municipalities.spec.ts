import { test, expect } from '@playwright/test';
import municipalities from '../public/municipalities.json';

/**
 * Test all municipalities to identify data/rendering issues
 *
 * This script:
 * 1. Loads each municipality page
 * 2. Checks for JavaScript errors
 * 3. Verifies the map loads correctly
 * 4. Reports any failures
 */

interface TestResult {
  slug: string;
  name: string;
  status: 'pass' | 'fail';
  error?: string;
  errorType?: string;
}

const results: TestResult[] = [];

// Filter out Nederland from test (it's too large and tested separately)
const municipalitiesToTest = municipalities.filter(m => m.slug !== 'nederland');

test.describe('Municipality Data Integrity', () => {
  // Set timeout per test to 30 seconds
  test.setTimeout(30000);

  for (const municipality of municipalitiesToTest) {
    test(`${municipality.name} (${municipality.slug})`, async ({ page }) => {
      const testResult: TestResult = {
        slug: municipality.slug,
        name: municipality.name,
        status: 'pass',
      };

      try {
        // Track console errors
        const consoleErrors: string[] = [];
        const pageErrors: string[] = [];

        page.on('console', (msg) => {
          if (msg.type() === 'error') {
            consoleErrors.push(msg.text());
          }
        });

        page.on('pageerror', (error) => {
          pageErrors.push(error.message);
        });

        // Navigate to the page
        await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });

        // Select the municipality
        await page.click('[data-testid="municipality-selector"]');
        await page.fill('input[type="text"]', municipality.name);
        await page.keyboard.press('Enter');

        // Wait for data to load
        await page.waitForTimeout(2000);

        // Check for errors
        if (pageErrors.length > 0) {
          testResult.status = 'fail';
          testResult.error = pageErrors[0];
          testResult.errorType = 'PageError';
        } else if (consoleErrors.some(e => e.includes('Invalid LatLng') || e.includes('bounds'))) {
          testResult.status = 'fail';
          testResult.error = consoleErrors.find(e => e.includes('Invalid LatLng') || e.includes('bounds'));
          testResult.errorType = 'BoundsError';
        } else if (consoleErrors.length > 0) {
          testResult.status = 'fail';
          testResult.error = consoleErrors[0];
          testResult.errorType = 'ConsoleError';
        }

        // Verify map is visible
        const mapVisible = await page.locator('.leaflet-container').isVisible();
        if (!mapVisible) {
          testResult.status = 'fail';
          testResult.error = 'Map container not visible';
          testResult.errorType = 'MapNotVisible';
        }

        results.push(testResult);

        if (testResult.status === 'fail') {
          throw new Error(`${testResult.errorType}: ${testResult.error}`);
        }

      } catch (error: any) {
        if (!testResult.error) {
          testResult.status = 'fail';
          testResult.error = error.message;
          testResult.errorType = 'UnknownError';
          results.push(testResult);
        }
        throw error;
      }
    });
  }
});

// After all tests, save results to file
test.afterAll(async () => {
  const fs = require('fs');
  const path = require('path');

  const failedMunicipalities = results.filter(r => r.status === 'fail');
  const passedMunicipalities = results.filter(r => r.status === 'pass');

  const report = {
    timestamp: new Date().toISOString(),
    total: results.length,
    passed: passedMunicipalities.length,
    failed: failedMunicipalities.length,
    failureRate: `${((failedMunicipalities.length / results.length) * 100).toFixed(2)}%`,
    failures: failedMunicipalities.map(r => ({
      slug: r.slug,
      name: r.name,
      errorType: r.errorType,
      error: r.error,
    })),
    summary: {
      byErrorType: failedMunicipalities.reduce((acc, r) => {
        const type = r.errorType || 'Unknown';
        acc[type] = (acc[type] || 0) + 1;
        return acc;
      }, {} as Record<string, number>),
    },
  };

  const reportPath = path.join(__dirname, '../test-results/municipality-test-report.json');
  fs.mkdirSync(path.dirname(reportPath), { recursive: true });
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

  console.log('\n' + '='.repeat(60));
  console.log('MUNICIPALITY TEST REPORT');
  console.log('='.repeat(60));
  console.log(`Total Municipalities: ${report.total}`);
  console.log(`Passed: ${report.passed} ✅`);
  console.log(`Failed: ${report.failed} ❌`);
  console.log(`Failure Rate: ${report.failureRate}`);
  console.log('\nFailures by Type:');
  Object.entries(report.summary.byErrorType).forEach(([type, count]) => {
    console.log(`  ${type}: ${count}`);
  });

  if (failedMunicipalities.length > 0) {
    console.log('\nFailed Municipalities:');
    failedMunicipalities.forEach(r => {
      console.log(`  - ${r.name} (${r.slug}): ${r.errorType}`);
    });
  }
  console.log('\nFull report saved to: test-results/municipality-test-report.json');
  console.log('='.repeat(60));
});
