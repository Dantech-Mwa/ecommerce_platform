import streamlit as st
from business_app import main as business_main
from app import main as analytics_main

st.set_page_config(layout="wide")
tab1, tab2 = st.tabs(["Business Management", "Analytics Dashboard"])

with tab1:
    business_main()
with tab2:
    analytics_main()