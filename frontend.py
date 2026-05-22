import streamlit as st
import requests

# 1. Configuration
# This is the address of your FastAPI Server
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Mechanic AI Agency", page_icon="🔧", layout="centered")

st.title("🔧 Mechanic AI Dashboard")
st.write("Internal Tool for Diagnosis & Reporting")

# 2. Create Tabs for Organization
tab1, tab2 = st.tabs(["🚗 Diagnose Issue", "📜 History Feed"])

# --- TAB 1: UPLOAD (The Input) ---
with tab1:
    st.header("New Car Diagnosis")

    # Input Fields
    col1, col2 = st.columns(2)
    with col1:
        caption = st.text_input("Issue Description", placeholder="E.g. Engine making rattling noise")
    with col2:
        image_file = st.file_uploader("Upload Car Image", type=["jpg", "png", "jpeg"])

    # The Button
    if st.button("Analyze & Save", type="primary"):
        if image_file is not None and caption:
            with st.spinner("Uploading to AI Server..."):
                try:
                    # Prepare the data for the API
                    files = {"file": (image_file.name, image_file, image_file.type)}
                    data = {"caption": caption}

                    # SEND REQUEST TO FASTAPI
                    response = requests.post(f"{API_URL}/upload", files=files, data=data)

                    if response.status_code == 200:
                        st.success("✅ Report Saved Successfully!")
                        st.json(response.json())  # Show the raw response from API
                    else:
                        st.error(f"Server Error: {response.status_code}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")
        else:
            st.warning("⚠️ Please provide both a description and an image.")

# --- TAB 2: FEED (The Output) ---
with tab2:
    st.header("Recent Diagnoses")

    if st.button("Refresh Feed"):
        try:
            # GET REQUEST TO FASTAPI
            response = requests.get(f"{API_URL}/feed")

            if response.status_code == 200:
                data = response.json()
                posts = data.get("posts", [])

                if not posts:
                    st.info("No reports found yet.")

                for post in posts:
                    # Create a card for each report
                    with st.container(border=True):
                        c1, c2 = st.columns([1, 3])
                        with c1:
                            st.write("🖼️ *[Image]*")
                            # Note: We will fix the image display later when we have real URLs
                        with c2:
                            st.subheader(post['caption'])
                            st.caption(f"ID: {post['id']} | Date: {post['created_at']}")
                            st.write(f"File Name: `{post['file_name']}`")
            else:
                st.error("Failed to fetch feed.")
        except Exception as e:
            st.error(f"Connection Error: {e}")