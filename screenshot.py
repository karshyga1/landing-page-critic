import asyncio
from playwright.async_api import async_playwright

async def take_screenshot(url: str, output_path: str = "screenshot.png") -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        await page.screenshot(path=output_path, full_page=True)
        await browser.close()
    return output_path

