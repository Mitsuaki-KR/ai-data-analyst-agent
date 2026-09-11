import base64
import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="AI Data Analyst Agent", page_icon="📊")
st.title("📊 AI Data Analyst Agent")
st.caption("Pose une question sur les ventes e-commerce (dataset Olist) en langage naturel.")

if "history" not in st.session_state:
    st.session_state.history = []

for entry in st.session_state.history:
    with st.chat_message("user"):
        st.write(entry["question"])
    with st.chat_message("assistant"):
        st.write(entry["answer"])
        if entry.get("chart_base64"):
            st.image(base64.b64decode(entry["chart_base64"]))
        with st.expander("Voir la requête SQL"):
            st.code(entry["sql"], language="sql")

question = st.chat_input("Pose ta question ici...")

if question:
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Analyse en cours..."):
            try:
                response = requests.post(f"{API_URL}/ask", json={"question": question}, timeout=30)
                response.raise_for_status()
                data = response.json()

                st.write(data["answer"])
                if data.get("chart_base64"):
                    st.image(base64.b64decode(data["chart_base64"]))
                with st.expander("Voir la requête SQL"):
                    st.code(data["sql"], language="sql")

                st.session_state.history.append({
                    "question": question,
                    "answer": data["answer"],
                    "sql": data["sql"],
                    "chart_base64": data.get("chart_base64"),
                })
            except requests.exceptions.HTTPError as e:
                st.error(f"L'agent n'a pas pu répondre à cette question : {e.response.json().get('detail', str(e))}")
            except requests.exceptions.RequestException as e:
                st.error(f"Impossible de contacter l'API : {e}")