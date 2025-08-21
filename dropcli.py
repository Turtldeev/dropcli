import asyncio
import os
from playwright.async_api import async_playwright, expect

async def get_and_parse_temp_email():
    async with async_playwright() as p:
        print("Launching browser in headless mode...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to dropmail.me...")
        try:
            await page.goto("https://dropmail.me/", wait_until="domcontentloaded")
            print("Waiting for temporary email address generation...")
            
            email_element = page.locator("span.address").first
            await expect(email_element).to_contain_text("@", timeout=30000)
            temp_email = await email_element.inner_text()
            
            print("\n" + "="*35)
            print(f"  Temporary email: {temp_email}")
            print("="*35 + "\n")

            print("Waiting for new emails. Press Ctrl+C to exit.")
            processed_emails = set()

            while True:
                email_list_items = page.locator("ul.messages-list > li")
                count = await email_list_items.count()

                if count > len(processed_emails):
                    for i in range(count):
                        email_item = email_list_items.nth(i)
                        
                        try:
                            if "mail-hidden" in (await email_item.get_attribute("class") or ""):
                                await email_item.click()
                                await page.wait_for_timeout(500)

                            subject_el = email_item.locator('dd.mail-subject').first
                            sender_el = email_item.locator('dt:has-text("Sender:") + dd').first
                            
                            await expect(subject_el).to_be_visible(timeout=5000)
                            
                            subject = await subject_el.inner_text()
                            sender = await sender_el.inner_text()
                            email_id = f"{sender}:{subject}"

                            if email_id not in processed_emails:
                                print(f"\n--- New email found! ---")
                                
                                body_element = email_item.locator('pre[data-bind*="linkifiedText"]').first
                                await expect(body_element).to_be_visible(timeout=10000)
                                body = await body_element.inner_text()

                                print(f"From: {sender.strip()}")
                                print(f"Subject: {subject.strip()}")
                                print("-" * 20)
                                print(body)
                                print("="*30)

                                processed_emails.add(email_id)
                        except Exception as e:
                            print(f"\n[Info] Could not process an email element, it might still be loading. Error: {e}")
                            continue
                
                print(".", end="", flush=True)
                await asyncio.sleep(5)

        except KeyboardInterrupt:
            print("\nExiting program.")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            await browser.close()
            print("Browser closed.")

async def main():
    print("Checking Playwright installation...")
    try:
        async with async_playwright() as p:
            await p.chromium.launch(headless=True)
    except Exception:
        print("Playwright or its browsers are not installed.")
        print("Please run the following two commands in your terminal:")
        print("1. pip install playwright")
        print("2. playwright install")
        return

    await get_and_parse_temp_email()

if __name__ == "__main__":
    asyncio.run(main())
