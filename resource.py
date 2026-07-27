import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Page configuration
st.set_page_config(page_title="Google Sheets Connection Test", layout="centered")

st.title("🧪 Google Sheets Connection Test")
st.write("Checking if Streamlit can talk to your Google Sheet...")

try:
    # Initialize the Google Sheets connection
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Try reading the sheet data (ttl=0 ensures it doesn't use cached data)
    data = conn.read(ttl=0)
    
    # If successful, show success message and print the data frame
    st.success("✅ Connection successful! Your Google Sheet is reachable.")
    st.write("Here is what was read from the database:")
    st.dataframe(data)

except Exception as e:
    st.error("❌ Connection failed.")
    st.exception(e)
