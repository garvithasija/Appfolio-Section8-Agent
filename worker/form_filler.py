import asyncio
import json
import os
import pandas as pd
import yaml
from datetime import datetime
from typing import Dict, List, Any
from playwright.async_api import async_playwright, Browser, Page
import traceback

class FormFiller:
    def __init__(self):
        self.browser: Browser = None
        self.page: Page = None
        self.results = []
        
    async def initialize(self, headless: bool = True):
        """Initialize Playwright browser"""
        print(f"🚀 Initializing Playwright browser (headless={headless})...")
        self.playwright = await async_playwright().start()
        print("✅ Playwright started")
        self.browser = await self.playwright.chromium.launch(headless=headless)
        print(f"✅ Browser launched (headless={headless})")
        context = await self.browser.new_context()
        print("✅ Browser context created")
        self.page = await context.new_page()
        print("✅ New page created - browser should be visible!")
    
    async def close(self):
        """Close browser and cleanup"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def _handle_appfolio_tenant_search(self, css_selector: str, tenant_name: str):
        """Handle AppFolio tenant search dropdown"""
        try:
            print(f"🔍 Searching for tenant: {tenant_name}")
            
            # For AppFolio Select2, we need to click the visible Select2 container instead of hidden input
            select2_selectors = [
                ".select2-selection__rendered",  # The visible Select2 element
                ".select2-container",
                "#select2-receivable_payment_payer_id-container"
            ]
            
            working_selector = None
            
            # First try Select2 visible elements
            for selector in select2_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000, state="visible")
                    working_selector = selector
                    print(f"✅ Found visible Select2 element: {selector}")
                    break
                except:
                    continue
            
            # If no visible Select2, try original selectors
            if not working_selector:
                selectors = [s.strip() for s in css_selector.split(',')]
                for selector in selectors:
                    try:
                        await self.page.wait_for_selector(selector, timeout=3000, state="attached")
                        working_selector = selector
                        break
                    except:
                        continue
            
            if not working_selector:
                raise Exception(f"No valid tenant search selector found in: {css_selector}")
            
            print(f"Using selector: {working_selector}")
            
            # Click on the Select2 element to open dropdown
            await self.page.click(working_selector)
            await self.page.wait_for_timeout(1000)
            
            # For Select2, we need to type in the search field that appears after clicking
            try:
                # Wait for the Select2 search input to appear after clicking
                search_input = ".select2-search__field"
                await self.page.wait_for_selector(search_input, timeout=5000, state="visible")
                
                # Type the tenant name in the search field
                await self.page.fill(search_input, tenant_name)
                await self.page.wait_for_timeout(1000)
                
                print(f"✅ Typed '{tenant_name}' in Select2 search field")
                
            except Exception as e:
                print(f"⚠️ Could not find Select2 search field, trying alternative: {e}")
                # Fallback: try typing directly in the clicked element
                await self.page.type(working_selector, tenant_name, delay=100)
                await self.page.wait_for_timeout(1000)
            
            # Wait for search results to appear
            try:
                # Look for the dropdown results container
                results_selector = ".select2-results, .select2-results__options, ul[class*='select2-results']"
                await self.page.wait_for_selector(results_selector, timeout=5000)
                
                # Try to find a result that matches the tenant name
                result_items = await self.page.query_selector_all(".select2-results li, .select2-results__option")
                
                for item in result_items:
                    item_text = await item.text_content()
                    if item_text and tenant_name.lower() in item_text.lower():
                        print(f"✅ Found matching tenant: {item_text}")
                        await item.click()
                        # Add 5-second wait after tenant selection
                        print("⏳ Waiting 5 seconds after tenant selection...")
                        await self.page.wait_for_timeout(5000)
                        return
                
                # If no exact match, try clicking the first result
                if result_items:
                    first_result = result_items[0]
                    first_text = await first_result.text_content()
                    print(f"⚠️ No exact match, selecting first result: {first_text}")
                    await first_result.click()
                    # Add 5-second wait after tenant selection
                    print("⏳ Waiting 5 seconds after tenant selection...")
                    await self.page.wait_for_timeout(5000)
                else:
                    print(f"❌ No search results found for tenant: {tenant_name}")
                    
            except Exception as search_error:
                print(f"⚠️ Search results not found, trying alternative approach: {search_error}")
                # Try pressing Enter to select first match
                await self.page.keyboard.press("ArrowDown")
                await self.page.keyboard.press("Enter")
                # Add 5-second wait after tenant selection
                print("⏳ Waiting 5 seconds after tenant selection...")
                await self.page.wait_for_timeout(5000)
                
        except Exception as e:
            print(f"❌ Failed to handle tenant search: {str(e)}")
            raise e
    
    async def select2_pick_by_select_id(self, css_selector: str, value: str, field_name: str):
        """Handle AppFolio Select2 dropdown fields like Cash Account and Payment Type"""
        try:
            print(f"🔽 Handling {field_name} Select2 dropdown with value: {value}")
            
            # For AppFolio Select2, we need to find the visible Select2 container
            select2_selectors = [
                ".select2-selection__rendered",  # The visible Select2 element
                ".select2-container",
                f"#select2-receivable_payment_{field_name.lower().replace(' ', '_')}_id-container"
            ]
            
            working_selector = None
            
            # First try Select2 visible elements
            for selector in select2_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000, state="visible")
                    working_selector = selector
                    print(f"✅ Found visible Select2 element: {selector}")
                    break
                except:
                    continue
            
            # If no visible Select2, try original selectors
            if not working_selector:
                selectors = [s.strip() for s in css_selector.split(',')]
                for selector in selectors:
                    try:
                        await self.page.wait_for_selector(selector, timeout=3000, state="attached")
                        working_selector = selector
                        break
                    except:
                        continue
            
            if not working_selector:
                raise Exception(f"No valid {field_name} selector found in: {css_selector}")
            
            print(f"Using selector: {working_selector}")
            
            # Click on the Select2 element to open dropdown
            await self.page.click(working_selector)
            await self.page.wait_for_timeout(1000)
            
            # For Select2, we need to type in the search field that appears after clicking
            try:
                # Wait for the Select2 search input to appear after clicking
                search_input = ".select2-search__field"
                await self.page.wait_for_selector(search_input, timeout=5000, state="visible")
                
                # Type the value in the search field
                await self.page.fill(search_input, value)
                await self.page.wait_for_timeout(1000)
                
                print(f"✅ Typed '{value}' in Select2 search field")
                
            except Exception as e:
                print(f"⚠️ Could not find Select2 search field, trying alternative: {e}")
                # Fallback: try typing directly in the clicked element
                await self.page.type(working_selector, value, delay=100)
                await self.page.wait_for_timeout(1000)
            
            # Wait for search results to appear
            try:
                # Look for the dropdown results container
                results_selector = ".select2-results, .select2-results__options, ul[class*='select2-results']"
                await self.page.wait_for_selector(results_selector, timeout=5000)
                
                # Try to find a result that matches the value
                result_items = await self.page.query_selector_all(".select2-results li, .select2-results__option")
                
                for item in result_items:
                    item_text = await item.text_content()
                    if item_text and (value.lower() in item_text.lower() or "operating" in item_text.lower()):
                        print(f"✅ Found matching {field_name}: {item_text}")
                        await item.click()
                        return
                
                # If no exact match, try clicking the first result
                if result_items:
                    first_result = result_items[0]
                    first_text = await first_result.text_content()
                    print(f"⚠️ No exact match, selecting first result: {first_text}")
                    await first_result.click()
                else:
                    print(f"❌ No search results found for {field_name}: {value}")
                    
            except Exception as search_error:
                print(f"⚠️ Search results not found, trying alternative approach: {search_error}")
                # Try pressing Enter to select first match
                await self.page.keyboard.press("ArrowDown")
                await self.page.keyboard.press("Enter")
                
        except Exception as e:
            print(f"❌ Failed to handle {field_name} dropdown: {str(e)}")
            raise e
    
    async def choose_cash_account(self, value: str):
        """
        Select cash account using AppFolio's Select2 focusser approach
        DOM shows: #s2id_autogen1 (focusser) and #receivable_payment_cash_gl_account_id (hidden select)
        """
        try:
            print(f"🏦 Selecting cash account: {value}")
            
            # Click the Select2 focusser for cash account
            focusser_selector = "#s2id_autogen1"
            await self.page.wait_for_selector(focusser_selector, timeout=5000, state="visible")
            await self.page.click(focusser_selector)
            await self.page.wait_for_timeout(1000)
            
            # Look for the search input that appears after clicking
            search_selectors = [
                "#s2id_autogen1_search",  # Expected pattern based on tenant field
                "input[id*='s2id_autogen1'][id$='_search']",
                ".select2-dropdown input[type='text']",
                ".select2-search input"
            ]
            
            search_found = False
            for search_selector in search_selectors:
                try:
                    await self.page.wait_for_selector(search_selector, timeout=3000, state="visible")
                    await self.page.fill(search_selector, value)
                    await self.page.wait_for_timeout(1000)
                    print(f"✅ Typed '{value}' in cash account search: {search_selector}")
                    search_found = True
                    break
                except:
                    continue
            
            if not search_found:
                # Fallback: try typing in the focusser directly
                await self.page.type(focusser_selector, value, delay=100)
                await self.page.wait_for_timeout(1000)
            
            # Try to select from results
            await self._select_from_dropdown_results(value)
            
        except Exception as e:
            print(f"❌ Failed to select cash account: {e}")
            raise e
    
    async def choose_payment_type(self, value: str):
        """
        Select payment type using AppFolio's Select2 focusser approach  
        DOM shows: #s2id_autogen2 (focusser) and #receivable_payment_additional_data_attributes_alternative_payment_type (hidden select)
        """
        try:
            print(f"💳 Selecting payment type: {value}")
            
            # Click the Select2 focusser for payment type
            focusser_selector = "#s2id_autogen2"
            await self.page.wait_for_selector(focusser_selector, timeout=5000, state="visible")
            await self.page.click(focusser_selector)
            await self.page.wait_for_timeout(1000)
            
            # Look for the search input that appears after clicking
            search_selectors = [
                "#s2id_autogen2_search",  # Expected pattern based on tenant field
                "input[id*='s2id_autogen2'][id$='_search']",
                ".select2-dropdown input[type='text']",
                ".select2-search input"
            ]
            
            search_found = False
            for search_selector in search_selectors:
                try:
                    await self.page.wait_for_selector(search_selector, timeout=3000, state="visible")
                    await self.page.fill(search_selector, value)
                    await self.page.wait_for_timeout(1000)
                    print(f"✅ Typed '{value}' in payment type search: {search_selector}")
                    search_found = True
                    break
                except:
                    continue
            
            if not search_found:
                # Fallback: try typing in the focusser directly
                await self.page.type(focusser_selector, value, delay=100)
                await self.page.wait_for_timeout(1000)
            
            # Try to select from results
            await self._select_from_dropdown_results(value)
            
        except Exception as e:
            print(f"❌ Failed to select payment type: {e}")
            raise e
    
    async def _select_from_dropdown_results(self, value: str):
        """Helper method to select from Select2 dropdown results"""
        try:
            # Wait for results to appear
            results_selectors = [
                ".select2-results li",
                ".select2-results__option", 
                ".select2-dropdown li",
                "[role='option']"
            ]
            
            for results_selector in results_selectors:
                try:
                    await self.page.wait_for_selector(results_selector, timeout=3000)
                    results = await self.page.query_selector_all(results_selector)
                    
                    for result in results:
                        result_text = await result.text_content()
                        if result_text and (value.lower() in result_text.lower() or 
                                          result_text.lower() in value.lower()):
                            print(f"✅ Found matching option: {result_text}")
                            await result.click()
                            return True
                    
                    # If no exact match, click first result
                    if results:
                        first_text = await results[0].text_content()
                        print(f"⚠️ No exact match, selecting first: {first_text}")
                        await results[0].click()
                        return True
                        
                except:
                    continue
            
            # Last resort: press Enter
            print("⚠️ No results found, trying Enter key")
            await self.page.keyboard.press("Enter")
            
        except Exception as e:
            print(f"⚠️ Error selecting from results: {e}")
            await self.page.keyboard.press("Enter")
    
    async def navigate_to_website(self, url: str, wait_timeout: int = 30000):
        """Navigate to the specified website"""
        try:
            print(f"🌐 Navigating to {url}...")
            await self.page.goto(url, wait_until="domcontentloaded", timeout=wait_timeout)
            print("✅ Page loaded - waiting for network idle...")
            
            # Check if we're on a login page (AppFolio specific)
            current_url = self.page.url
            if "sign_in" in current_url or "login" in current_url:
                print("🔐 Detected login page - user needs to authenticate manually")
                print("⏳ Waiting for user to login manually (60 seconds timeout)...")
                
                # Wait for user to login (URL will change)
                try:
                    await self.page.wait_for_function(
                        "window.location.href.includes('tenant_receipts') || !window.location.href.includes('sign_in')",
                        timeout=60000
                    )
                    print("✅ Authentication successful - continuing...")
                except:
                    print("⚠️ Login timeout - continuing anyway...")
            
            await self.page.wait_for_load_state("networkidle", timeout=10000)  # Reduced timeout
            print("✅ Navigation completed successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to navigate to {url}: {str(e)}")
            return False
    
    async def fill_form_with_data(self, row_data: Dict[str, Any], field_mapping: Dict[str, str], 
                                 row_index: int = 0) -> Dict[str, Any]:
        """Fill form fields with data from Excel row"""
        result = {
            "row_index": row_index,
            "status": "success",
            "filled_fields": [],
            "errors": [],
            "screenshot_path": None
        }
        
        try:
            # Wait for page to be ready
            await self.page.wait_for_timeout(2000)
            
            # Fill each field according to mapping
            for excel_column, css_selector in field_mapping.items():
                if excel_column in row_data and row_data[excel_column] is not None:
                    try:
                        value = str(row_data[excel_column])
                        
                        # Wait for element to be available (but may be hidden)
                        await self.page.wait_for_selector(css_selector, timeout=10000, state="attached")
                        
                        # Special handling for AppFolio dropdowns using specific focusser approach 
                        if excel_column == "TenantName" and ("receivable_payment_payer_id" in css_selector or "select2" in css_selector):
                            await self._handle_appfolio_tenant_search(css_selector, value)
                        elif excel_column == "CashAccount":
                            await self.choose_cash_account(value)
                        elif excel_column == "PaymentType":
                            await self.choose_payment_type(value)
                        else:
                            # Check if element is input, textarea, or select
                            # Handle multiple selectors separated by commas
                            try:
                                element_type = await self.page.evaluate(f"""
                                    document.querySelector(`{css_selector}`).tagName.toLowerCase()
                                """)
                            except Exception as eval_error:
                                # If evaluation fails, try with individual selectors
                                selectors = [s.strip() for s in css_selector.split(',')]
                                element_found = False
                                for selector in selectors:
                                    try:
                                        await self.page.wait_for_selector(selector, timeout=2000)
                                        element_type = await self.page.evaluate(f"""
                                            document.querySelector(`{selector}`).tagName.toLowerCase()
                                        """)
                                        css_selector = selector  # Use the working selector
                                        element_found = True
                                        break
                                    except:
                                        continue
                                
                                if not element_found:
                                    raise Exception(f"No valid selector found in: {css_selector}")
                            
                            if element_type in ['input', 'textarea']:
                                # Clear and fill text fields - force interaction even if hidden
                                try:
                                    await self.page.fill(css_selector, value, force=True)
                                except Exception as fill_error:
                                    print(f"⚠️ Force fill failed, trying evaluate: {fill_error}")
                                    # Last resort: use JavaScript to set value
                                    await self.page.evaluate(f"""
                                        document.querySelector(`{css_selector}`).value = '{value}';
                                        document.querySelector(`{css_selector}`).dispatchEvent(new Event('input', {{ bubbles: true }}));
                                        document.querySelector(`{css_selector}`).dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    """)
                            elif element_type == 'select':
                                # Handle select dropdowns
                                await self.page.select_option(css_selector, value)
                            else:
                                # Try clicking for checkboxes, radio buttons, etc.
                                await self.page.click(css_selector)
                        
                        result["filled_fields"].append({
                            "field": excel_column,
                            "selector": css_selector,
                            "value": value
                        })
                        
                        # Small delay between field fills
                        await self.page.wait_for_timeout(500)
                        
                    except Exception as field_error:
                        error_msg = f"Failed to fill {excel_column} ({css_selector}): {str(field_error)}"
                        result["errors"].append(error_msg)
                        print(error_msg)
            
            # Take screenshot after filling
            screenshot_dir = "screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = f"{screenshot_dir}/row_{row_index}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await self.page.screenshot(path=screenshot_path)
            result["screenshot_path"] = screenshot_path
            
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(f"Form filling failed: {str(e)}")
            print(f"Error filling form for row {row_index}: {str(e)}")
            print(traceback.format_exc())
            
            # Take error screenshot
            try:
                screenshot_dir = "screenshots"
                os.makedirs(screenshot_dir, exist_ok=True)
                error_screenshot = f"{screenshot_dir}/error_row_{row_index}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await self.page.screenshot(path=error_screenshot)
                result["screenshot_path"] = error_screenshot
            except:
                pass
        
        return result
    
    async def submit_form(self, submit_selector: str = None) -> bool:
        """Submit the form"""
        try:
            if submit_selector:
                print(f"🔘 Clicking submit button: {submit_selector}")
                await self.page.wait_for_selector(submit_selector, timeout=10000)
                await self.page.click(submit_selector)
            else:
                # Try AppFolio specific and common submit button selectors
                submit_selectors = [
                    '#save_button',  # AppFolio save button
                    'input[type="submit"][value="Save"]',
                    'button:has-text("Save")',
                    'input[type="submit"]',
                    'button[type="submit"]',
                    'button:has-text("Submit")',
                    'button:has-text("Apply")',
                    'button:has-text("Send")'
                ]
                
                for selector in submit_selectors:
                    try:
                        print(f"🔍 Trying submit selector: {selector}")
                        await self.page.wait_for_selector(selector, timeout=5000)
                        await self.page.click(selector)
                        print(f"✅ Successfully clicked: {selector}")
                        break
                    except Exception as e:
                        print(f"❌ Failed {selector}: {str(e)}")
                        continue
            
            # Wait for navigation or success message
            try:
                await self.page.wait_for_load_state("networkidle", timeout=15000)
                return True
            except:
                return True  # Form might have been submitted without navigation
                
        except Exception as e:
            print(f"Failed to submit form: {str(e)}")
            return False
    
    async def wait_for_confirmation(self, success_indicators: List[str] = None, 
                                   error_indicators: List[str] = None) -> Dict[str, Any]:
        """Wait for and detect form submission confirmation"""
        result = {"success": False, "message": ""}
        
        try:
            # Wait a bit for page to update
            await self.page.wait_for_timeout(3000)
            
            # Check for success indicators
            if success_indicators:
                for indicator in success_indicators:
                    try:
                        element = await self.page.wait_for_selector(indicator, timeout=5000)
                        if element:
                            text = await element.text_content()
                            result = {"success": True, "message": f"Success: {text}"}
                            return result
                    except:
                        continue
            
            # Check for error indicators
            if error_indicators:
                for indicator in error_indicators:
                    try:
                        element = await self.page.query_selector(indicator)
                        if element:
                            text = await element.text_content()
                            result = {"success": False, "message": f"Error: {text}"}
                            return result
                    except:
                        continue
            
            # Check page content for common success/error messages
            page_content = await self.page.content()
            success_keywords = ["success", "submitted", "thank you", "application received"]
            error_keywords = ["error", "failed", "invalid", "required"]
            
            content_lower = page_content.lower()
            for keyword in success_keywords:
                if keyword in content_lower:
                    result = {"success": True, "message": f"Detected success keyword: {keyword}"}
                    return result
            
            for keyword in error_keywords:
                if keyword in content_lower:
                    result = {"success": False, "message": f"Detected error keyword: {keyword}"}
                    return result
            
            # Default to success if no indicators found
            result = {"success": True, "message": "Form submitted (no confirmation detected)"}
            
        except Exception as e:
            result = {"success": False, "message": f"Error checking confirmation: {str(e)}"}
        
        return result
    
    async def process_excel_file(self, excel_path: str, website_url: str, 
                                field_mapping: Dict[str, str],
                                submit_selector: str = None,
                                success_indicators: List[str] = None,
                                error_indicators: List[str] = None,
                                delay_between_rows: int = 2) -> List[Dict[str, Any]]:
        """Process Excel or CSV file and fill forms for each row"""
        
        # Read Excel or CSV file
        try:
            if excel_path.endswith('.csv'):
                df = pd.read_csv(excel_path)
            else:
                df = pd.read_excel(excel_path)
        except Exception as e:
            print(f"Failed to read file {excel_path}: {str(e)}")
            return [{"error": f"Failed to read file: {str(e)}"}]
        results = []
        
        print(f"Starting form filling for {len(df)} rows...")
        print(f"Website: {website_url}")
        print(f"Field mapping: {field_mapping}")
        
        for index, row in df.iterrows():
            print(f"\nProcessing row {index + 1}/{len(df)}...")
            
            try:
                # Navigate to website for each row
                nav_success = await self.navigate_to_website(website_url)
                if not nav_success:
                    results.append({
                        "row_index": index,
                        "status": "error",
                        "errors": [f"Failed to navigate to {website_url}"],
                        "filled_fields": [],
                        "screenshot_path": None
                    })
                    continue
                
                # Convert row to dict
                row_data = row.to_dict()
                
                # Fill form with row data
                fill_result = await self.fill_form_with_data(row_data, field_mapping, index)
                
                # Submit form if no errors occurred during filling
                if fill_result["status"] == "success" and len(fill_result["errors"]) == 0:
                    submit_success = await self.submit_form(submit_selector)
                    if submit_success:
                        # Wait for confirmation
                        confirmation = await self.wait_for_confirmation(success_indicators, error_indicators)
                        fill_result["submission"] = confirmation
                    else:
                        fill_result["errors"].append("Failed to submit form")
                else:
                    fill_result["submission"] = {"success": False, "message": "Skipped submission due to fill errors"}
                
                results.append(fill_result)
                
                # Delay between rows
                if index < len(df) - 1:  # Don't delay after last row
                    await self.page.wait_for_timeout(delay_between_rows * 1000)
                
            except Exception as e:
                error_result = {
                    "row_index": index,
                    "status": "error",
                    "errors": [f"Unexpected error: {str(e)}"],
                    "filled_fields": [],
                    "screenshot_path": None
                }
                results.append(error_result)
                print(f"Unexpected error processing row {index}: {str(e)}")
        
        return results

async def main():
    """Example usage of FormFiller"""
    
    # Example configuration
    config = {
        "website_url": "https://example.com/application-form",
        "field_mapping": {
            "ApplicantFirstName": "#first_name",
            "ApplicantLastName": "#last_name", 
            "DOB": "#date_of_birth",
            "Email": "#email",
            "Phone": "#phone"
        },
        "submit_selector": "#submit_button",
        "success_indicators": [".success-message", ".confirmation"],
        "error_indicators": [".error-message", ".alert-danger"]
    }
    
    # Initialize form filler
    filler = FormFiller()
    await filler.initialize(headless=False)  # Set to True for production
    
    try:
        # Process Excel file
        results = await filler.process_excel_file(
            excel_path="example_applicants.xlsx",
            website_url=config["website_url"],
            field_mapping=config["field_mapping"],
            submit_selector=config.get("submit_selector"),
            success_indicators=config.get("success_indicators"),
            error_indicators=config.get("error_indicators"),
            delay_between_rows=3
        )
        
        # Save results
        with open("form_filling_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nCompleted! Processed {len(results)} rows.")
        successful = sum(1 for r in results if r["status"] == "success")
        print(f"Successful: {successful}, Failed: {len(results) - successful}")
        
    finally:
        await filler.close()

if __name__ == "__main__":
    asyncio.run(main())