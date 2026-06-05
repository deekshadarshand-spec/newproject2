import pandas as pd
import streamlit as st
import os

@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    return df

# Fix: only load default if file actually exists and is non-empty
uploaded = st.file_uploader("Upload CSV dataset", type=["csv"])

if uploaded is not None:
    raw = load_data(uploaded)
elif os.path.exists(data_path) and os.path.getsize(data_path) > 0:
    raw = load_data(data_path)
else:
    st.warning("Please upload a CSV file to get started.")
    st.stop()  # Halt execution — don't try to use `raw` if it doesn't exist
