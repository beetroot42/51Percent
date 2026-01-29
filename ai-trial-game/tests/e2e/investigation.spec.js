const { test, expect } = require('@playwright/test');

test.describe('Investigation Phase', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/state', async route => route.fulfill({ json: { phase: 'investigation' } }));
    await page.route('**/api/blockchain/genesis', async route => route.fulfill({ json: { genesisBlockHash: '0x1', chainId: 31337 } }));
    await page.route('**/content/dossier', async route => {
      await route.fulfill({ json: { title: '谋杀案', content: '尸体在房间内被发现。' } });
    });
    await page.route('**/content/evidence', async route => {
      await route.fulfill({ json: [
        { id: 'knife', name: '带血的刀', description: '一把沾血的刀。' },
        { id: 'letter', name: '遗书', description: '一封信。' }
      ] });
    });
    await page.route('**/content/evidence/knife', async route => {
      await route.fulfill({ json: { id: 'knife', name: '带血的刀', description: '一把沾血的刀。' } });
    });
    await page.route('**/content/witnesses', async route => {
      await route.fulfill({ json: [{ id: 'witness1', name: '张三', description: '邻居。' }] });
    });
    await page.route('**/content/witness/witness1', async route => {
      await route.fulfill({ json: {
        id: 'witness1', name: '张三',
        dialogues: [
          { id: 'start', text: '我什么都没看到。', options: [{ text: '真的吗?', next: 'node2' }] },
          { id: 'node2', text: '好吧，可能看到了一些。', options: [] }
        ]
      } });
    });
    await page.route('**/phase/*', async route => route.fulfill({ json: { status: 'ok' } }));
    await page.route('**/reset', async route => route.fulfill({ json: { status: 'ok' } }));
    await page.goto('/');
  });

  test('Should display dossier by default', async ({ page }) => {
    await expect(page.locator('#dossier-panel')).toHaveClass(/active/);
    await expect(page.locator('#dossier-content h2')).toHaveText('谋杀案');
  });

  test('Should load and display evidence', async ({ page }) => {
    await page.click('[data-tab="evidence"]');
    await expect(page.locator('#evidence-panel')).toHaveClass(/active/);
    const evidenceItems = page.locator('.evidence-card');
    await expect(evidenceItems).toHaveCount(2);
    await expect(evidenceItems.first()).toContainText('带血的刀');

    page.on('dialog', async dialog => {
      expect(dialog.message()).toContain('带血的刀');
      await dialog.accept();
    });
    await evidenceItems.first().click();
  });

  test('Should load and display witnesses', async ({ page }) => {
    await page.click('[data-tab="witnesses"]');
    await expect(page.locator('#witnesses-panel')).toHaveClass(/active/);
    const witnessItems = page.locator('.witness-card');
    await expect(witnessItems).toHaveCount(1);
    await expect(witnessItems.first()).toContainText('张三');
  });

  test('Should handle witness dialogue', async ({ page }) => {
    await page.click('[data-tab="witnesses"]');
    await page.click('.witness-card:first-child');
    const modal = page.locator('#witness-dialogue-modal');
    await expect(modal).toBeVisible();
    await expect(page.locator('#witness-text')).toHaveText('我什么都没看到。');
    await page.click('#close-dialogue-btn');
    await expect(modal).toBeHidden();
  });
});
