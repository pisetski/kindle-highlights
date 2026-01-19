#!/usr/bin/env python3
"""
Migration Script: Add themes to existing highlights.

Run this script once to classify existing highlights in your database.
After running, all highlights will have a 'theme' field.

Usage:
    python src/migrate_themes.py
"""
import json
from pathlib import Path

from classifier import classify_book


def main():
    data_path = Path(__file__).parent.parent / "data" / "highlights.json"

    if not data_path.exists():
        print(f"No highlights file found at {data_path}")
        print("Run import_clippings.py first to import your highlights.")
        return

    with open(data_path) as f:
        highlights = json.load(f)

    if not highlights:
        print("No highlights found in database.")
        return

    # Find unique books without themes
    books = {}
    for h in highlights:
        if 'theme' not in h:
            books[(h['title'], h['author'])] = None

    if not books:
        print("All highlights already have themes!")
        return

    print(f"🤖 Classifying {len(books)} books...")
    for (title, author) in books:
        theme = classify_book(title, author)
        books[(title, author)] = theme
        print(f"   • {title}: {theme}")

    # Apply themes
    for h in highlights:
        if 'theme' not in h:
            h['theme'] = books[(h['title'], h['author'])]

    with open(data_path, 'w') as f:
        json.dump(highlights, f, indent=2, ensure_ascii=False)

    print(f"\n✨ Done! Updated {len(highlights)} highlights.")
    print(f"💾 Saved to: {data_path}")


if __name__ == '__main__':
    main()
