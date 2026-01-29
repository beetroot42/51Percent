const { test, expect } = require('@playwright/test');

test.describe('Verdict Phase', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/state', async route => route.fulfill({ json: { phase: 'persuasion' } }));
    await page.route('**/api/blockchain/genesis', async route => route.fulfill({ json: { genesisBlockHash: '0x1', chainId: 31337 } }));
    await page.route('**/jurors', async route => route.fulfill({ json: [] }));
    await page.route('**/phase/*', async route => route.fulfill({ json: { status: 'ok' } }));

    await page.route('**/vote', async route => {
      await new Promise(r => setTimeout(r, 500));
      await route.fulfill({
        json: {
          verdict: 'NOT GUILTY',
          votes: [{ name: '陪审员1', vote: false }, { name: '陪审员2', vote: false }],
          guilty_votes: 0, not_guilty_votes: 2,
          tx_hashes: ['0xabc123']
        }
      });
    });

    await page.route('**/api/votes/verification', async route => {
      await route.fulfill({
        json: {
          verified: true,
          chainData: { chainName: 'Local', blockNumber: 50, timestamp: 1234567890, txHash: '0xabc123', confirmations: 5 },
          voteData: { guiltyVotes: 0, notGuiltyVotes: 2 }
        }
      });
    });

    await page.goto('/');
  });

  test('Should handle voting process and display verdict', async ({ page }) => {
    await page.click('#enter-verdict-btn');
    const modal = page.locator('#voting-modal');
    await expect(modal).toBeVisible();
    await expect(page.locator('#step-1')).toBeVisible();
    await expect(modal).toBeHidden({ timeout: 10000 });

    const result = page.locator('#verdict-result');
    await expect(result).toBeVisible();
    await expect(page.locator('#verdict-text')).toHaveText('无罪');
    await expect(page.locator('#verdict-description')).toContainText('重获自由');

    const verifyPanel = page.locator('#verification-panel');
    await expect(verifyPanel).toBeVisible();
    await expect(page.locator('#tx-hash-value')).toContainText('0xabc123');
    await expect(page.locator('#verification-status')).toContainText('已验证');
  });

  test('Should handle voting error', async ({ page }) => {
    await page.route('**/vote', async route => {
      await route.abort('failed');
    });

    await page.click('#enter-verdict-btn');
    await expect(page.locator('#voting-error-actions')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('#voting-status-text')).toContainText('投票失败');
    await expect(page.locator('#retry-vote-btn')).toBeVisible();
  });
});
