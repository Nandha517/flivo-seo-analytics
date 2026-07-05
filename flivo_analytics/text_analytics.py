"""
Flivo Backlink Opportunity Analytics — Text Analytics
========================================================
Word clouds and keyword-frequency analysis over the Benefits, Limitations,
and recommendation-rationale text fields.
"""
import os
import re
from collections import Counter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from config import CHARTS_DIR

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "is", "are",
    "this", "that", "be", "as", "at", "by", "it", "its", "not", "but", "if", "than",
    "from", "per", "via", "into", "such", "these", "those", "can", "may", "will",
    "-", "n/a", "no", "yes",
}


def _tokenize(texts: list) -> list:
    words = []
    for t in texts:
        if not isinstance(t, str):
            continue
        tokens = re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", t.lower())
        words.extend(w for w in tokens if w not in STOPWORDS)
    return words


def generate_wordcloud(texts: list, title: str, filename: str, colormap: str = "viridis") -> dict:
    """Build and save a word cloud PNG from a list of text cells, plus a
    top-keyword table for the same corpus."""
    words = _tokenize(texts)
    if not words:
        return {"path": None, "top_keywords": [], "insight": f"No usable text found for {title}."}

    text_blob = " ".join(words)
    wc = WordCloud(width=1000, height=500, background_color="white",
                    colormap=colormap, max_words=60).generate(text_blob)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(title, fontweight="bold", fontsize=13)
    path = os.path.join(CHARTS_DIR, f"{filename}.png")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)

    top_keywords = Counter(words).most_common(15)
    return {"path": path, "top_keywords": top_keywords}


def chart_keyword_frequency(top_keywords: list, title: str, filename: str, color: str = "#1F3864") -> str:
    """Bar chart of the top keywords for a given corpus."""
    if not top_keywords:
        return None
    words, counts = zip(*top_keywords)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(words[::-1], counts[::-1], color=color)
    ax.set_xlabel("Frequency")
    ax.set_title(title, fontweight="bold")
    path = os.path.join(CHARTS_DIR, f"{filename}.png")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path
