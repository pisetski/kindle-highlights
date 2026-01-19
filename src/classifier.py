#!/usr/bin/env python3
"""
Book Theme Classifier

Uses Hugging Face zero-shot classification to categorize books into themes.
The model is loaded lazily to save memory and downloaded on first use (~180MB).
"""

from transformers import pipeline

# Define your themes (customize as needed)
THEMES = [
    "Philosophy",
    "Psychology",
    "Finance & Investing",
    "Software Engineering",
    "Productivity",
    "History",
    "Science",
    "Business",
    "Fiction",
    "Biography",
]

_classifier = None


def get_classifier():
    """Lazy load classifier to save memory."""
    global _classifier
    if _classifier is None:
        _classifier = pipeline(
            "zero-shot-classification",
            model="MoritzLaurer/deberta-v3-base-mnli-fever-anli"
        )
    return _classifier


def classify_book(title: str, author: str) -> str:
    """
    Classify a book into a theme using zero-shot classification.

    Args:
        title: Book title
        author: Book author

    Returns:
        Theme string (one of THEMES or "General" if confidence is low)
    """
    classifier = get_classifier()

    # Create descriptive text for classification
    text = f"{title} by {author}"

    result = classifier(text, THEMES, multi_label=False)

    # Return top theme if confidence > 0.3, else "General"
    if result["scores"][0] > 0.3:
        return result["labels"][0]
    return "General"
