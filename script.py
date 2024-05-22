import streamlit as st
import pandas as pd
from io import BytesIO
import requests
from bs4 import BeautifulSoup

def authenticate_google(email, password):
    try:
        session = requests.Session()
        login_url = "https://accounts.google.com/signin"
        
        # Make a GET request to the login page
        response = session.get(login_url)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract the necessary form data
        form_data = {
            "email": email,
            "password": password,
            "lt": soup.find("input", {"name": "lt"})["value"],
            "continue": "https://www.google.com/"
        }
        
        # Submit the login form
        session.post(login_url, data=form_data)
        
        return session.cookies
    except Exception as e:
        st.error(f"Error during authentication: {e}")
        return None

def search_ai_overview(keyword, cookies):
    try:
        url = f"https://www.google.com/search?q={keyword}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, cookies=cookies)
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
1. **Sign in to your Google Account**: Enter your Google account email and password and click the "Sign in" button.
2. **Upload Your Keyword List**: Upload an Excel file (.xlsx) containing the keywords you want to check.
3. **Check for AI Overview**: Click the "Check Keywords" button to start the process. The tool will search for each keyword on Google and check if an AI Overview Snippet is present.
4. **Download Results**: Once the process is complete, you can download the results as an Excel file.
""")

# Google account credentials
email = st.text_input("Google Account Email")
password = st.text_input("Google Account Password", type="password")

# Authenticate Google account
if st.button("Sign in"):
    cookies = authenticate_google(email, password)
    if cookies:
        st.success("Authentication successful. You can now upload your keyword list.")
    else:
        st.error("Authentication failed. Please check your credentials and try again.")

# File uploader for the keyword list
uploaded_file = st.file_uploader("Upload Keyword List", type=["xlsx"])

if uploaded_file is not None and cookies:
    if st.button("Process Keywords"):
        with st.spinner("Processing keywords..."):
            result_df = process_keywords(uploaded_file, cookies)
            if result_df:
                st.write("Processing complete. Download the results below.")
                st.download_button(
                    label="Download Keyword Search Results",
                    data=result_df,
                    file_name="ai_overview_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
