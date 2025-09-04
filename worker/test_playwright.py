#!/usr/bin/env python3
"""
Simple test to check if Playwright can open a browser window
"""
import asyncio
from playwright.async_api import async_playwright

async def test_browser_window():
    """Test if Playwright can open a visible browser window"""
    
    print("🚀 Testing Playwright browser window...")
    
    async with async_playwright() as p:
        try:
            print("1. Launching Chromium browser (headless=False)...")
            browser = await p.chromium.launch(headless=False)  # Visual mode
            
            print("2. Creating new context...")
            context = await browser.new_context()
            
            print("3. Creating new page...")
            page = await context.new_page()
            
            print("4. Navigating to AppFolio login page...")
            await page.goto("https://sairealty.appfolio.com/users/sign_in", wait_until="domcontentloaded", timeout=30000)
            
            print("✅ Browser opened successfully!")
            print("🔍 You should see a Chrome window with AppFolio login page")
            print("⏳ Keeping browser open for 10 seconds...")
            
            await page.wait_for_timeout(10000)  # Keep open for 10 seconds
            
            print("5. Closing browser...")
            await browser.close()
            
            print("✅ Test completed successfully!")
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    print("🧪 Playwright Browser Window Test")
    asyncio.run(test_browser_window())