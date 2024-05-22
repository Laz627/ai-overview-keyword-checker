import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import BytesIO
import json

def search_ai_overview(keyword, cookies):
    try:
        url = f"https://www.google.com/search?q={keyword}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])
        response = session.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        body_text = soup.get_text()
        return "AI Overview" in body_text
    except Exception as e:
        st.error(f"Error searching for keyword '{keyword}': {e}")
        return False

def process_keywords(file, cookies):
    df = pd.read_excel(file)
    keywords = df["Keyword"].tolist()
    results = []
    for keyword in keywords:
        has_ai_overview = search_ai_overview(keyword, cookies)
        results.append({"Keyword": keyword, "AI Overview Found": "Yes" if has_ai_overview else "No"})
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
1. **Log into your Google Account**: Log into your Google account using your web browser.
2. **Extract Cookies**: Use a browser extension to export your Google account cookies in JSON format.
3. **Provide Cookies**: Paste the JSON-formatted cookies into the input field below.
4. **Upload Your Keyword List**: Upload an Excel file (.xlsx) containing the keywords you want to check.
5. **Check for AI Overview**: Click the "Check Keywords" button to start the process. The tool will search for each keyword on Google and check if an AI Overview Snippet is present.
6. **Download Results**: Once the process is complete, you can download the results as an Excel file.
""")

# Input field for Google account cookies
cookies_input = st.text_area("Enter your Google account cookies (in JSON format)")

# File uploader for the keyword list
uploaded_file = st.file_uploader("Upload Keyword List", type=["xlsx"])

# Check and process keywords if cookies and file are provided
if uploaded_file is not None and cookies_input:
    try:
        cookies = json.loads(cookies_input)
    except json.JSONDecodeError:
        st.error("Invalid JSON format for cookies")
        cookies = None

    if st.button("Process Keywords") and cookies:
        with st.spinner("Processing keywords..."):
            result_df = process_keywords(uploaded_file, cookies)
            if result_df is not None:
                st.write("Processing complete. Download the results below.")
                st.download_button(
                    label="Download Keyword Search Results",
                    data=result_df,
                    file_name="ai_overview_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
else:
    st.write("Please provide cookies and upload a keyword list.")
