import streamlit as st
import pandas as pd
import time
import random
import asyncio
from playwright.async_api import async_playwright

# Function to save authentication state
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

        # Wait for the element that has the aria-label containing "Google Account: Brandon Smith"
        await page.wait_for_selector('a[aria-label*="Google Account: Brandon Smith"]', timeout=60000)  # Wait for 1 minute for manual login

        # Save authentication state to a file
        await context.storage_state(path="auth_state.json")

        st.write("Authentication state saved to auth_state.json")
        await browser.close()

# Function to log page content for debugging
async def log_page_content(page, keyword):
    content = await page.content()
    with open(f"debug_{keyword}.html", "w", encoding="utf-8") as f:
        f.write(content)

# Function to search for AI Overview in search results
async def search_ai_overview(page, keyword):
    url = f"https://www.google.com/search?q={keyword}"
    await page.goto(url)
    
    try:
        # Wait for the page to load completely
        await page.wait_for_load_state('networkidle')
        
        # Give extra time for any dynamic content to load
        await page.wait_for_timeout(3000)  # Wait for 3 more seconds
        
        # Log the main page content
        await log_page_content(page, keyword)

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
            frame_content = await frame.content()
            with open(f"debug_{keyword}_iframe.html", "w", encoding="utf-8") as f:
                f.write(frame_content)
                
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

# Main function to process the keywords and search for AI Overview
async def process_keywords(uploaded_file):
    # Read keywords from the uploaded Excel spreadsheet
    df = pd.read_excel(uploaded_file)
    keywords = df['Keyword'].tolist()

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
    return output_file

# Streamlit app interface
st.title("AI Overview Search App")

st.write("""
This app allows you to:
1. Sign into your Google account.
2. Upload a keyword list.
3. Process the keywords to search for "AI Overview" in Google search results.
4. Download the findings as an Excel file.
""")

if st.button('Sign into Google Account'):
    asyncio.run(save_auth_state())
    st.write("Sign-in process completed.")

uploaded_file = st.file_uploader("Choose an Excel file with keywords", type="xlsx")

if uploaded_file is not None:
    st.write("Uploaded file: ", uploaded_file.name)
    if st.button('Process Keywords'):
        output_file = asyncio.run(process_keywords(uploaded_file))
        with open(output_file, "rb") as file:
            btn = st.download_button(
                label="Download Keyword Search Results",
                data=file,
                file_name=output_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        st.write("Keyword processing started. Please wait...")

        # Display the download button after processing
        if btn:
            st.write("Keyword search results are ready for download.")

# Requirements for the Streamlit app
requirements = """
streamlit
pandas
asyncio
playwright
openpyxl
"""

# Save the requirements to a file
with open("requirements.txt", "w") as file:
    file.write(requirements)
