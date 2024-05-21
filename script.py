import streamlit as st
import pandas as pd
import time
import random
import asyncio
from playwright.async_api import async_playwright

# Function to save the authentication state
async def save_auth_state():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set headless=False to see the browser
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False
        )

        # Open new page
        page = await context.new_page()

        # Go to Google login page
        await page.goto("https://accounts.google.com/signin")

        # Wait for user to complete login manually
        st.write("Please log in manually to your Google account...")

        # Wait for the element that has the aria-label containing "Google Account:"
        await page.wait_for_selector('a[aria-label*="Google Account:"]', timeout=60000)  # Wait for 1 minute for manual login

        # Save authentication state to a file
        await context.storage_state(path="auth_state.json")

        st.write("Authentication state saved to auth_state.json")
        await browser.close()

# Function to search for AI Overview
async def search_ai_overview(page, keyword):
    url = f"https://www.google.com/search?q={keyword}"
    await page.goto(url)
    
    try:
        # Wait for the page to load completely
        await page.wait_for_load_state('networkidle')
        
        # Give extra time for any dynamic content to load
        await page.wait_for_timeout(3000)  # Wait for 3 more seconds
        
        # Check for the "AI Overview" text within the main document
        ai_overview_found = await page.evaluate("""
            () => {
                const searchText = 'AI Overview';
                const bodyText = document.body.innerText;
                return bodyText.includes(searchText);
            }
        """)
        
        if ai_overview_found:
            return True

        # Check if the content is inside an iframe
        frames = page.frames
        for frame in frames:
            ai_overview_found_in_frame = await frame.evaluate("""
                () => {
                    const searchText = 'AI Overview';
                    const bodyText = document.body.innerText;
                    return bodyText.includes(searchText);
                }
            """)
            if ai_overview_found_in_frame:
                return True
        
        # Check if the content is within a shadow DOM
        ai_overview_shadow = await page.evaluate("""
            () => {
                const searchText = 'AI Overview';
                let found = false;
                function searchShadowDom(element) {
                    if (element.shadowRoot) {
                        const shadowText = element.shadowRoot.innerText;
                        if (shadowText.includes(searchText)) {
                            found = true;
                            return;
                        }
                        element.shadowRoot.querySelectorAll('*').forEach(searchShadowDom);
                    }
                }
                document.querySelectorAll('*').forEach(searchShadowDom);
                return found;
            }
        """)
        
        return ai_overview_shadow

    except Exception as e:
        st.write(f"Error occurred while searching for AI Overview for keyword: {keyword}. Exception: {e}")
        return False

# Function to run the AI Overview search
async def run_ai_overview_search(keywords):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Use headless=False to see the browser actions
        context = await browser.new_context(storage_state="auth_state.json")

        # Open a new page
        page = await context.new_page()

        results = []
        total_keywords = len(keywords)
        for index, keyword in enumerate(keywords, start=1):
            has_ai_overview = await search_ai_overview(page, keyword)
            if has_ai_overview is None:
                results.append({'Keyword': keyword, 'AI Overview Found': 'Error'})
            else:
                results.append({'Keyword': keyword, 'AI Overview Found': 'Yes' if has_ai_overview else 'No'})
            time.sleep(random.uniform(1, 3))
            remaining_keywords = total_keywords - index
            st.write(f"Processed keyword: {keyword}")
            st.write(f"Keywords left in queue: {remaining_keywords}")
            st.write("---")

        # Export the results to a new Excel spreadsheet
        output_file = 'ai_overview_results.xlsx'
        result_df = pd.DataFrame(results)
        result_df.to_excel(output_file, index=False)

        st.write(f"Results exported to {output_file}")

        await browser.close()

# Streamlit app
st.title("Google Auth and AI Overview Finder")

# Step 1: Authentication
if st.button("Start Authentication Process"):
    asyncio.run(save_auth_state())

# Step 2: AI Overview Search
uploaded_file = st.file_uploader("Choose a file")
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    keywords = df['Keyword'].tolist()
    
    if st.button("Start AI Overview Search"):
        asyncio.run(run_ai_overview_search(keywords))
