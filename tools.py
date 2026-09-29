import asyncio
from langchain_core.tools import tool
from playwright.async_api import async_playwright

@tool
async def scrape_competitor_syllabus(url: str) -> str:
    """
    Launches a headless browser to dynamically scrape educational content, 
    course syllabi, or job descriptions from a given live URL.
    Use this to pull real-time competitor training structures or market requirements.
    """
    try:
        async with async_playwright() as p:
            # Launch browser in headless mode
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to the page with a timeout configuration
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Extract text from core content areas while omitting headers/footers
            # Focus on paragraphs, headings, and list items where syllabus details live
            elements = await page.query_selector_all("p, h1, h2, h3, li")
            text_contents = []
            
            for el in elements:
                text = await el.inner_text()
                if text.strip():
                    text_contents.append(text.strip())
            
            await browser.close()
            
            # Combine text and truncate if it exceeds reasonable token boundaries
            full_text = "\n".join(text_contents)
            return full_text[:8000] if len(full_text) > 8000 else full_text
            
    except Exception as e:
        return f"Failed to extract live content from URL due to error: {str(e)}"
