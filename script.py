import streamlit as st
import pandas as pd
from io import BytesIO
from pyppeteer import launch
import asyncio

async def save_auth_state():
    try:
        browser = await launch(headless=False)
        page = await browser.newPage()
        await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        await page.setViewport({"width": 1280, "height": 800})
        await page.goto("https://accounts.google.com/signin")
        st.write("Please log in manually to your Google account...")
        await page.waitForSelector('a[aria-label*="Google Account:"]', timeout=60000)
        cookies = await page.cookies()
        await browser.close()
        return cookies
    except Exception as e:
        st.error(f"Error during authentication: {e}")
        return None

async def search_ai_overview(page, keyword):
    try:
        url = f"https://www.google.com/search?q={keyword}"
        await page.goto(url)
        await page.waitForSelector('body', timeout=10000)
        body_text = await page.evaluate('document.body.innerText')
        return 'AI Overview' in body_text
    except Exception as e:
        st.error(f"Error searching for keyword '{keyword}': {e}")
        return False

async def process_keywords(file, cookies):
    df = pd.read_excel(file)
    keywords = df['Keyword'].tolist()
    try:
        browser = await launch(headless=True)
        page = await browser.newPage()
        await page.setCookie(*cookies)
        results = []
        for keyword in keywords:
            has_ai_overview = await search_ai_overview(page, keyword)
            results.append({'Keyword': keyword, 'AI Overview Found': 'Yes' if has_ai_overview else 'No'})
        await browser.close()
        result_df = pd.DataFrame(results)
        output = BytesIO()
        result_df.to_excel(output, index=False)
        output.seek(0)
        return output
    except Exception as e:
        st.error(f"Error processing keywords: {e}")
        return None

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

if 'cookies' not in st.session_state:
    st.session_state.cookies = None

# Button to start the authentication process
if st.button("Sign into Google Account"):
    st.write("Please follow the instructions in the browser window that opens.")
    cookies = asyncio.run(save_auth_state())
    if cookies:
        st.session_state.cookies = cookies
        st.write("Authentication state saved. You can now upload your keyword list.")
    else:
        st.write("Failed to save authentication state. Please try again.")

# File uploader for the keyword list
uploaded_file = st.file_uploader("Upload Keyword List", type=["xlsx"])
if uploaded_file is not None:
    if st.button("Process Keywords"):
        with st.spinner("Processing keywords..."):
            if st.session_state.cookies:
                result_df = asyncio.run(process_keywords(uploaded_file, st.session_state.cookies))
                if result_df:
                    st.write("Processing complete. Download the results below.")
                    st.download_button(
                        label="Download Keyword Search Results",
                        data=result_df,
                        file_name="ai_overview_results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.error("Please sign in to your Google Account first.")
