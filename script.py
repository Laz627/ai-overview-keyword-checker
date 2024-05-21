import os
import subprocess
import streamlit as st
import pandas as pd
import asyncio
from playwright.async_api import async_playwright
from io import BytesIO

# Run the setup script to install Playwright browsers
setup_script = './setup.sh'
if os.path.exists(setup_script):
    subprocess.run([setup_script], check=True)

# Function to save authentication state
async def save_auth_state():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False
        )
        page = await context.new_page()
        await page.goto("https://accounts.google.com/signin")
        st.write("Please log in manually to your Google account...")
        await page.wait_for_selector('a[aria-label*="Google Account:"]', timeout=60000)
        await context.storage_state(path="auth_state.json")
        await browser.close()
        st.write("Authentication state saved.")

# Function to search for "AI Overview" in Google search results
async def search_ai_overview(page, keyword):
    url = f"https://www.google.com/search?q={keyword}"
    await page.goto(url)
    await page.wait_for_load_state('networkidle')
    await page.wait_for_timeout(3000)
    ai_overview_found = await page.evaluate("""
        () => {
            const searchText = 'AI Overview';
            const bodyText = document.body.innerText;
            return bodyText.includes(searchText);
        }
    """)
    return ai_overview_found

# Main function to process the keywords
async def process_keywords(file):
    df = pd.read_excel(file)
    keywords = df['Keyword'].tolist()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state="auth_state.json")
        page = await context.new_page()
        results = []
        for keyword in keywords:
            has_ai_overview = await search_ai_overview(page, keyword)
            results.append({'Keyword': keyword, 'AI Overview Found': 'Yes' if has_ai_overview else 'No'})
        result_df = pd.DataFrame(results)
        output = BytesIO()
        result_df.to_excel(output, index=False)
        output.seek(0)
        return output

# Streamlit app interface
st.title("SGE Keyword Checker Tool")

st.write("""
## Description
The SGE Keyword Checker Tool validates at scale if an AI Overview Snippet is generated for your list of keywords. 

### How to Use the Tool:
1. **Sign in to your Google Account**: Click the "Sign in to Google" button and follow the instructions to log in (being signed into a Google Account is required by Google to display AI Overview results for your queries).
2. **Upload Your Keyword List**: Upload an Excel file (.xlsx) containing the keywords you want to check.
3. **Check for AI Overview**: Click the "Check Keywords" button to start the process. The tool will search for each keyword on Google and check if an AI Overview Snippet is present.
4. **Download Results**: Once the process is complete, you can download the results as an Excel file.
""")

# Button to start the authentication process
if st.button("Sign into Google Account"):
    st.write("Please follow the instructions in the browser window that opens.")
    try:
        asyncio.run(save_auth_state())
        st.write("Authentication state saved. You can now upload your keyword list.")
    except Exception as e:
        st.error(f"Error during authentication: {e}")

# File uploader for the keyword list
uploaded_file = st.file_uploader("Upload Keyword List", type=["xlsx"])
if uploaded_file is not None:
    if st.button("Process Keywords"):
        with st.spinner("Processing keywords..."):
            try:
                result_df = asyncio.run(process_keywords(uploaded_file))
                st.write("Processing complete. Download the results below.")
                st.download_button(
                    label="Download Keyword Search Results",
                    data=result_df,
                    file_name="ai_overview_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Error processing keywords: {e}")

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
