#!/usr/bin/env python3
"""
Script to inspect AppFolio DOM structure and find correct selectors
"""
import asyncio
from playwright.async_api import async_playwright

async def inspect_appfolio_form():
    """Inspect the AppFolio form to get correct selectors"""
    
    print("🔍 Starting AppFolio DOM inspection...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to AppFolio tenant receipts page
            print("🌐 Navigating to AppFolio...")
            await page.goto("https://sairealty.appfolio.com/accounting/tenant_receipts/new")
            
            print("⚠️ Please login manually and navigate to the tenant receipts form")
            print("⏳ Waiting 30 seconds for you to login and reach the form...")
            await page.wait_for_timeout(30000)
            
            # Inspect the form structure
            print("🔍 Inspecting form elements...")
            
            # Check for tenant search field
            tenant_selectors = [
                "#new_form .js-payer input[type='search']",
                "#new_form .js-payer input[type='text']",
                "input[data-select2-id]",
                ".select2-selection__rendered",
                ".select2-search__field"
            ]
            
            for selector in tenant_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        tag = await element.evaluate("el => el.tagName")
                        attrs = await element.evaluate("el => Array.from(el.attributes).map(a => `${a.name}='${a.value}'`).join(' ')")
                        print(f"✅ Found tenant field: {selector}")
                        print(f"   Tag: {tag}, Attrs: {attrs}")
                except:
                    print(f"❌ Not found: {selector}")
            
            # Check for amount field
            amount_selectors = [
                "#receivable_payment_amount",
                "input[name='receivable_payment[amount]']",
                "#amount"
            ]
            
            for selector in amount_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        attrs = await element.evaluate("el => Array.from(el.attributes).map(a => `${a.name}='${a.value}'`).join(' ')")
                        print(f"✅ Found amount field: {selector}")
                        print(f"   Attrs: {attrs}")
                except:
                    print(f"❌ Not found: {selector}")
            
            # Check for cash account dropdown
            cash_selectors = [
                "#receivable_payment_cash_account_id",
                "select[name='receivable_payment[cash_account_id]']",
                "#cash_account_id"
            ]
            
            for selector in cash_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        attrs = await element.evaluate("el => Array.from(el.attributes).map(a => `${a.name}='${a.value}'`).join(' ')")
                        print(f"✅ Found cash account: {selector}")
                        print(f"   Attrs: {attrs}")
                except:
                    print(f"❌ Not found: {selector}")
            
            # Check for payment type dropdown  
            payment_selectors = [
                "#receivable_payment_payment_type_id",
                "select[name='receivable_payment[payment_type_id]']",
                "#payment_type_id"
            ]
            
            for selector in payment_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        attrs = await element.evaluate("el => Array.from(el.attributes).map(a => `${a.name}='${a.value}'`).join(' ')")
                        print(f"✅ Found payment type: {selector}")
                        print(f"   Attrs: {attrs}")
                except:
                    print(f"❌ Not found: {selector}")
            
            # Get all form inputs for reference
            print("\n📋 All form inputs found:")
            inputs = await page.query_selector_all("form input, form select, form textarea")
            for i, inp in enumerate(inputs):
                try:
                    tag = await inp.evaluate("el => el.tagName")
                    name = await inp.get_attribute("name") or "no-name"
                    id_attr = await inp.get_attribute("id") or "no-id"
                    type_attr = await inp.get_attribute("type") or "no-type"
                    print(f"  {i+1}. {tag} id='{id_attr}' name='{name}' type='{type_attr}'")
                except:
                    pass
            
            print("\n✅ Inspection complete. Check the output above for working selectors!")
            
        except Exception as e:
            print(f"❌ Error during inspection: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_appfolio_form())