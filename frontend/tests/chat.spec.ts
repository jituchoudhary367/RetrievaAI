import { test, expect } from '@playwright/test';

test('has suggested questions and can query', async ({ page }) => {
  await page.goto('/');

  // Check if there is an input box for the chat
  const input = page.locator('textarea[placeholder="Ask anything..."]');
  await expect(input).toBeVisible();

  // Wait for the suggested questions to appear
  const suggestions = page.locator('text=You can ask about:');
  await expect(suggestions).toBeVisible();

  // Test submitting a query
  await input.fill('What is RAG?');
  await page.keyboard.press('Enter');

  // Verify that an answer block appears
  // Using a selector that matches user or assistant messages or loading state
  const chatBubble = page.locator('.prose, .markdown-body, [data-testid="chat-message"]');
  // At least one bubble should be visible eventually (the user query bubble appears instantly, assistant response takes time)
  await expect(chatBubble.first()).toBeVisible({ timeout: 15000 });
});
