/**
 * Auth helper for Playwright E2E tests.
 *
 * Logs in via the backend /auth/login endpoint, stores the returned
 * token in localStorage so the frontend picks it up on page load.
 */

import { Page } from '@playwright/test';

const BACKEND = 'http://localhost:8001';
const TEST_EMAIL = 'terrence@kinetix.com';
const TEST_PASSWORD = '...'; // replace with actual test credentials if login works

/**
 * Log in and store the JWT in localStorage.
 * Falls back to a pre-issued token if the login endpoint is unavailable.
 */
export async function loginAsTerrence(page: Page): Promise<void> {
  // Attempt real login first
  try {
    const resp = await page.request.post(`${BACKEND}/auth/login`, {
      data: { email: TEST_EMAIL, password: TEST_PASSWORD },
    });
    if (resp.ok()) {
      const body = await resp.json() as { access_token: string };
      await page.evaluate((token) => {
        localStorage.setItem('auth_token', token);
        localStorage.setItem('auth_user', JSON.stringify({ email: 'terrence@kinetix.com' }));
      }, body.access_token);
      return;
    }
  } catch {
    // login endpoint may not exist — fall through to token generation
  }

  // Fallback: generate a token via backend's internal service
  const tokenResp = await page.request.post(`${BACKEND}/api/v1/auth/test-token`, {
    data: { tenant_id: 'ae6b27c7-8a77-4167-add7-3a498d59536a', user_id: '9f3e7b11-e529-4cf8-82a6-2a62e4e5b643' },
  });
  if (tokenResp.ok()) {
    const body = await tokenResp.json() as { access_token: string };
    await page.evaluate((token) => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_user', JSON.stringify({ email: 'terrence@kinetix.com' }));
    }, body.access_token);
  }
}
