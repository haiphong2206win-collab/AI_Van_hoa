import streamlit as st

def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_image" not in st.session_state:
        st.session_state.current_image = None

def new_chat():
    st.session_state.messages = []
    st.session_state.current_image = None

def clear_image():
    st.session_state.current_image = None
