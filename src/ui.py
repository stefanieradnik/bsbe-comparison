import yaml
import streamlit as st
from ui_utils import (
    get_unique_bundeslaender,
    get_unique_paragraphs,
    get_unique_absaetze,
    get_text_from_id,
)
from comparer import FuzzyComparer

st.title("BSBE Bundesländer Vergleich 😊")

st.header("Referenz 📌:")

with open("src/config.yaml", "r") as f:
    config = yaml.safe_load(f)

db_path = config["db_path"]

# st.session_state()
bundesland_options = get_unique_bundeslaender(db_path)
bundesland = st.selectbox("Wähle ein Bundesland: 🌍", options=bundesland_options)

if bundesland:
    paragraph_options = get_unique_paragraphs(db_path, bundesland)
    paragraph = st.selectbox("Wähle einen Paragraphen §:", options=paragraph_options)

if paragraph:
    absatz_options = get_unique_absaetze(db_path, bundesland, paragraph)
    absatz = st.selectbox("Wähle einen Absatz ⤵️:", options=absatz_options)

if absatz:
    ref_id = bundesland + "_" + paragraph + "_" + absatz
    text = get_text_from_id(db_path, ref_id)
    st.text("TEXT 📄:\n" + text)

st.header("Ziel 🎯:")

bundesland_options = get_unique_bundeslaender(db_path)
target_bundesland = st.selectbox("Wähle ein Ziel-Bundesland: 🎯", options=bundesland_options)

comparer = FuzzyComparer(config)
best_text, best_target_id = comparer.compare(ref_id, target_bundesland)
best_target_para = best_target_id.split("_")[1]
best_target_absatz = best_target_id.split("_")[2]
st.text("Ähnlichster Paragraph 🔎: " + best_target_para)
st.text("Ähnlichster Absatz 🔎: " + best_target_absatz)
st.text("Ähnlichster Artikel 📄:\n" + best_text)
