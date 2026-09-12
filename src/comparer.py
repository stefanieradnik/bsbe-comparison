import numpy as np
import streamlit as st
from thefuzz import fuzz


class FuzzyComparer:

    def __init__(self, config):
        self.config = config

    def compare(self, ref_text, candidates):
        ratios = [fuzz.ratio(ref_text, text) for _, text in candidates]
        best_idx = int(np.argmax(ratios))

        return candidates[best_idx][1], candidates[best_idx][0]


DEFAULT_EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


@st.cache_resource(show_spinner="Lade Embedding-Modell 🧠 ...")
def _load_embedding_model(model_name):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


@st.cache_data(show_spinner="Berechne Embeddings 🧮 ...")
def _embed_texts(_model, model_name, texts):
    return _model.encode(list(texts), normalize_embeddings=True)


class EmbeddingComparer:

    def __init__(self, config, model_name=None):
        self.config = config
        self.model_name = model_name or config.get("embedding_model", DEFAULT_EMBEDDING_MODEL)

    def compare(self, ref_text, candidates):
        candidate_ids = [c[0] for c in candidates]
        candidate_texts = tuple(c[1] for c in candidates)

        model = _load_embedding_model(self.model_name)
        candidate_embeddings = _embed_texts(model, self.model_name, candidate_texts)

        ref_embedding = model.encode(ref_text, normalize_embeddings=True)
        similarities = candidate_embeddings @ ref_embedding
        best_idx = int(np.argmax(similarities))

        return candidate_texts[best_idx], candidate_ids[best_idx]
