const { test, expect } = require('@playwright/test');

test.describe('Game Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/state', async route => {
      await route.fulfill({ json: { phase: 'investigation' } });
    });
    await page.route('**/api/blockchain/genesis', async route => {
      await route.fulfill({ json: { genesisBlockHash: '0xgenesis', chainId: 31337 } });
    });
    await page.route('**/content/dossier', async route => {
      await route.fulfill({ json: { title: '测试案件', content: '这是一个测试案件的卷宗。' } });
    });
    await page.route('**/content/evidence', async route => {
      await route.fulfill({ json: [] });
    });
    await page.route('**/content/witnesses', async route => {
      await route.fulfill({ json: [] });
    });
    await page.route('**/jurors', async route => {
      await route.fulfill({ json: [
        { id: 'juror1', name: '陪审员1' },
        { id: 'juror2', name: '陪审员2' }
      ] });
    });
    await page.route('**/juror/*', async route => {
      await route.fulfill({ json: { id: 'juror1', name: '陪审员1', first_message: '你好' } });
    });
    await page.route('**/phase/*', async route => {
      await route.fulfill({ json: { status: 'ok' } });
    });
  });

  test('Complete game flow walkthrough', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/AI审判/);
    await expect(page.locator('#phase-indicator')).toHaveText('调查阶段');
    await expect(page.locator('#dossier-content')).toContainText('测试案件');

    await page.click('[data-tab="evidence"]');
    await expect(page.locator('#evidence-panel')).toBeVisible();
    await page.click('[data-tab="witnesses"]');
    await expect(page.locator('#witnesses-panel')).toBeVisible();

    await page.click('#enter-persuasion-btn');
    await page.route('**/state', async route => route.fulfill({ json: { phase: 'persuasion' } }));
    await expect(page.locator('#phase-indicator')).toHaveText('说服阶段');
    await expect(page.locator('#persuasion-phase')).toBeVisible();

    await page.click('.juror-card:first-child');
    await expect(page.locator('#chat-input')).toBeEnabled();

    await page.route('**/chat/*', async route => {
      await route.fulfill({ json: { reply: '收到' } });
    });
    await page.fill('#chat-input', '你好');
    await page.click('#send-btn');
    await expect(page.locator('.message.player')).toContainText('你好');
    await expect(page.locator('.message.juror').last()).toContainText('收到');

    await page.route('**/vote', async route => {
      await route.fulfill({
        json: {
          verdict: 'GUILTY',
          votes: [{ name: '陪审员1', vote: true }, { name: '陪审员2', vote: false }],
          guilty_votes: 1, not_guilty_votes: 1,
          tx_hashes: ['0xvotehash']
        }
      });
    });
    await page.route('**/api/votes/verification', async route => {
      await route.fulfill({
        json: {
          verified: true,
          chainData: { chainName: 'Anvil Local', blockNumber: 100, timestamp: Date.now() / 1000, txHash: '0xvotehash', confirmations: 1 },
          voteData: { guiltyVotes: 1, notGuiltyVotes: 1 }
        }
      });
    });

    await page.click('#enter-verdict-btn');
    await expect(page.locator('#voting-modal')).toBeVisible();
    await expect(page.locator('#verdict-result')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('#verdict-text')).toHaveText('有罪');
    await expect(page.locator('#verification-panel')).toBeVisible();
    await expect(page.locator('#verification-status')).toContainText('已验证');
  });
});
