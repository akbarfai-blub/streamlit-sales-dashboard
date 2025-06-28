import pickle
import streamlit as st

@st.cache_data
def load_model():
    with open("models/model_sales.pkl", "rb") as f:
        return pickle.load(f)