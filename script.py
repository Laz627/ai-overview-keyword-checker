import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright, Error as PlaywrightError
from io import BytesIO
import subprocess
import os
import sys

def run_subprocess(command):
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    st.write(f"Running command: {' '.join(command)}")
    st.write(f"Return code: {result.returncode}")
    st.write(f"Standard output: {result.stdout}")
    st.write(f"Standard error: {result.stderr}")
    return result.returncode, result.stdout, result.stderr

# Function to install Playwright and the necessary dependencies
def install_playwright_and_deps():
    st.write("Installing Playwright and necessary dependencies...")

    # Install Playwright
    return_code, stdout, stderr = run_subprocess([sys.executable, "-m", "pip", "install", "playwright"])
    if return_code != 0:
        st.error("Failed to install Playwright")
        return False

    # Install system dependencies for Playwright
    return_code, stdout, stderr = run_subprocess(["playwright", "install-deps"])
    if return_code != 0:
        st.error("Failed to install Playwright system dependencies")
        return False

    # Install Chromium for Playwright
    return_code, stdout, stderr = run_subprocess(["playwright", "install", "chromium"])
    if return_code != 0:
        st.error("Failed to install Chromium for Playwright")
        return False

    st.write("Playwright and necessary dependencies have been successfully installed.")
    return True

# Function to save authentication state
def save_auth_state():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False
        )
        page = context.new_page()
        page.goto("https://accounts.google.com/signin")
        st.write("Please log in manually to your Google account...")
        page.wait_for_selector('a[aria-label*="Google Account:"]', timeout=60000)
        context.storage_state(path="auth_state.json")
        browser.close()

# Function to search for "AI Overview" in Google search results
def search_ai_overview(page, keyword):
    url = f"https://www.google.com/search?q={keyword}"
    page.goto(url)
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(3000)
    ai_overview_found = page.evaluate("""
        () => {
            const searchText = 'AI Overview';
            const bodyText = document.body.innerText;
            return bodyText.includes(searchText);
        }
    """)
    return ai_overview_found

# Main function to process the keywords
def process_keywords(file):
    df = pd.read_excel(file)
    keywords = df['Keyword'].tolist()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="auth_state.json")
        page = context.new_page()
        results = []
        for keyword in keywords:
            has_ai_overview = search_ai_overview(page, keyword)
            results.append({'Keyword': keyword, 'AI Overview Found': 'Yes' if has_ai_overview else 'No'})
        result_df = pd.DataFrame(results)
        output = BytesIO()
        result_df.to_excel(output, index=False)
        output.seek(0)
        return output

# Ensure Playwright and browsers are installed
st.write("Checking Playwright installation...")
if install_playwright_and_deps():
    st.write("Playwright and necessary dependencies have been successfully installed.")
else:
    st.write("Failed to install Playwright and necessary dependencies. Please check the logs for more details.")

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
        save_auth_state()
        st.write("Authentication state saved. You can now upload your keyword list.")
    except PlaywrightError as e:
        st.error(f"Error during authentication: {e}")

# File uploader for the keyword list
uploaded_file = st.file_uploader("Upload Keyword List", type=["xlsx"])
if uploaded_file is not None:
    if st.button("Process Keywords"):
        with st.spinner("Processing keywords..."):
            try:
                result_df = process_keywords(uploaded_file)
                st.write("Processing complete. Download the results below.")
                st.download_button(
                    label="Download Keyword Search Results",
                    data=result_df,
                    file_name="ai_overview_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except PlaywrightError as e:
                st.error(f"Error processing keywords: {e}")
