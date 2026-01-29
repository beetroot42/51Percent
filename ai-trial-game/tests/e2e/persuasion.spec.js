const { test, expect } = require('@playwright/test');

test.describe('Persuasion Phase', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/state', async route => route.fulfill({ json: { phase: 'persuasion' } }));
    await page.route('**/api/blockchain/genesis', async route => route.fulfill({ json: { genesisBlockHash: '0x1', chainId: 31337 } }));
    await page.route('**/jurors', async route => {
      await route.fulfill({ json: [
        { id: 'j1', name: '陪审员A', first_message: '你好' },
        { id: 'j2', name: '陪审员B' }
      ] });
    });
    await page.route('**/juror/j1', async route => {
      await route.fulfill({ json: { id: 'j1', name: '陪审员A', first_message: '你好' } });
    });
    await page.route('**/chat/j1', async route => {
      const body = JSON.parse(route.request().postData());
      await route.fulfill({ json: { reply: `回复: ${body.message}` } });
    });
    await page.route('**/phase/*', async route => route.fulfill({ json: { status: 'ok' } }));
    await page.route('**/reset', async route => route.fulfill({ json: { status: 'ok' } }));
    await page.goto('/');
  });

  test('Should display juror list', async ({ page }) => {
    const jurors = page.locator('.juror-card');
    await expect(jurors).toHaveCount(2);
    await expect(jurors.first()).toContainText('陪审员A');
  });

  test('Should handle chat interaction', async ({ page }) => {
    await page.click('.juror-card[data-id="j1"]');
    await expect(page.locator('.juror-card[data-id="j1"]')).toHaveClass(/selected/);
    await expect(page.locator('#current-juror-name')).toHaveText('陪审员A');
    await expect(page.locator('.message.juror')).toContainText('你好');

    const input = page.locator('#chat-input');
    await input.fill('他有罪吗?');
    await page.click('#send-btn');
    await expect(page.locator('.message.player').last()).toHaveText('他有罪吗?');
    await expect(page.locator('.message.juror').last()).toContainText('回复: 他有罪吗?');
  });

  test('Should persist chat history when switching jurors', async ({ page }) => {
    await page.click('.juror-card[data-id="j1"]');
    await page.fill('#chat-input', '给J1的消息');
    await page.click('#send-btn');
    await expect(page.locator('.message.juror').last()).toContainText('给J1的消息');

    await page.route('**/juror/j2', async route => route.fulfill({ json: { id: 'j2', name: '陪审员B' } }));
    await page.click('.juror-card[data-id="j2"]');
    await expect(page.locator('#chat-messages')).toBeEmpty();

    await page.click('.juror-card[data-id="j1"]');
    await expect(page.locator('.message.player').last()).toHaveText('给J1的消息');
  });
});
