import streamlit as st
from pyppeteer import launch
import asyncio

async def run_pyppeteer_test():
    try:
        browser = await launch(headless=True)
        page = await browser.newPage()
        await page.goto("https://www.google.com")
        content = await page.content()
        await browser.close()
        return "Pyppeteer successfully launched and fetched content."
    except Exception as e:
        return f"Error: {e}"

# Streamlit app interface
st.title("Pyppeteer Environment Test")

st.write("""
## Testing Pyppeteer Setup
Click the button below to run a basic Pyppeteer test to check if the environment supports launching a browser.
""")

if st.button("Run Pyppeteer Test"):
    result = asyncio.run(run_pyppeteer_test())
    st.write(result)
