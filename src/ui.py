import yaml
import streamlit as st

from comparer import EmbeddingComparer, FuzzyComparer
from ui_utils import (
    get_absatz_candidates,
    get_full_paragraph_text,
    get_paragraph_candidates,
    get_text_from_id,
    get_unique_absaetze,
    get_unique_bundeslaender,
    get_unique_paragraphs,
)

FULL_PARAGRAPH_OPTION = "Gesamter Paragraph (alle Absätze)"

st.title("BSBE Bundesländer Vergleich 😊")

similarity_mode = st.segmented_control(
    "Ähnlichkeitsmodus 🔀:",
    options=["Fuzzy", "Embedding"],
    default="Fuzzy",
)
if similarity_mode is None:
    similarity_mode = "Fuzzy"

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
    absatz_options = get_unique_absaetze(db_path, bundesland, paragraph) + [FULL_PARAGRAPH_OPTION]
    absatz = st.selectbox("Wähle einen Absatz ⤵️:", options=absatz_options)

if absatz:
    compare_full_paragraph = absatz == FULL_PARAGRAPH_OPTION
    if compare_full_paragraph:
        ref_text = get_full_paragraph_text(db_path, bundesland, paragraph)
    else:
        ref_id = bundesland + "_" + paragraph + "_" + absatz
        ref_text = get_text_from_id(db_path, ref_id)
    st.text("TEXT 📄:\n" + ref_text)

st.header("Ziel 🎯:")

bundesland_options = get_unique_bundeslaender(db_path)
target_bundesland = st.selectbox("Wähle ein Ziel-Bundesland: 🎯", options=bundesland_options)

if similarity_mode == "Embedding":
    comparer = EmbeddingComparer(config)
else:
    comparer = FuzzyComparer(config)

if compare_full_paragraph:
    candidates = get_paragraph_candidates(db_path, target_bundesland)
    best_text, best_target_paragraph = comparer.compare(ref_text, candidates)
    st.text("Ähnlichster Paragraph 🔎: " + best_target_paragraph)
    st.text("Ähnlichster Artikel 📄:\n" + best_text)
else:
    candidates = get_absatz_candidates(db_path, target_bundesland)
    best_text, best_target_id = comparer.compare(ref_text, candidates)
    best_target_para = best_target_id.split("_")[1]
    best_target_absatz = best_target_id.split("_")[2]
    st.text("Ähnlichster Paragraph 🔎: " + best_target_para)
    st.text("Ähnlichster Absatz 🔎: " + best_target_absatz)
    st.text("Ähnlichster Artikel 📄:\n" + best_text)
