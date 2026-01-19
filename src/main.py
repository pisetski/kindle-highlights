#!/usr/bin/env python3
"""
Kindle Daily Highlights - Free Readwise Alternative
Sends 5 random Kindle highlights to your email daily via GitHub Actions + Resend

Author: Generated for Pavel
License: MIT
"""

import json
import os
import random
import re
from datetime import datetime
from pathlib import Path

import resend


def parse_clippings(clippings_path: str) -> list[dict]:
    """
    Parse Kindle's 'My Clippings.txt' file into structured highlights.

    The file format is:
    Book Title (Author)
    - Your Highlight on page X | location Y-Z | Added on Day, Month Date, Year Time

    Highlight text here
    ==========
    """
    highlights = []

    with open(clippings_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()

    # Split by the separator
    entries = content.split('==========')

    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue

        lines = entry.split('\n')
        if len(lines) < 3:
            continue

        # First line: Book Title (Author)
        title_line = lines[0].strip()

        # Extract author from parentheses at the end
        author_match = re.search(r'\(([^)]+)\)\s*$', title_line)
        if author_match:
            author = author_match.group(1)
            title = title_line[:author_match.start()].strip()
        else:
            author = "Unknown"
            title = title_line

        # Second line: metadata (page, location, date)
        # Skip if it's a bookmark (no highlight text)
        if 'Your Bookmark' in lines[1]:
            continue

        # The actual highlight text (everything after the metadata line, excluding empty lines)
        highlight_text = '\n'.join(line for line in lines[3:] if line.strip())

        if highlight_text:
            highlights.append({
                'title': title,
                'author': author,
                'text': highlight_text,
                'added_at': datetime.now().isoformat()
            })

    return highlights


def load_highlights(data_path: str) -> list[dict]:
    """Load highlights from JSON storage."""
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_highlights(highlights: list[dict], data_path: str):
    """Save highlights to JSON storage."""
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(highlights, f, indent=2, ensure_ascii=False)


def get_random_highlights(highlights: list[dict], count: int = 5) -> list[dict]:
    """Select random highlights, ensuring variety in books if possible."""
    if len(highlights) <= count:
        return highlights

    # Try to get highlights from different books
    books = {}
    for h in highlights:
        key = h['title']
        if key not in books:
            books[key] = []
        books[key].append(h)

    selected = []
    book_keys = list(books.keys())
    random.shuffle(book_keys)

    # First pass: one from each book
    for key in book_keys:
        if len(selected) >= count:
            break
        selected.append(random.choice(books[key]))

    # If we need more, pick randomly from remaining
    if len(selected) < count:
        remaining = [h for h in highlights if h not in selected]
        needed = count - len(selected)
        selected.extend(random.sample(remaining, min(needed, len(remaining))))

    random.shuffle(selected)
    return selected


def format_email_html(highlights: list[dict]) -> str:
    """Format highlights as a beautiful HTML email."""
    date_str = datetime.now().strftime('%B %d, %Y')

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Georgia, 'Times New Roman', serif;
            line-height: 1.6;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fafafa;
            color: #333;
        }}
        .header {{
            text-align: center;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 24px;
            color: #2c3e50;
            margin: 0;
        }}
        .header p {{
            color: #7f8c8d;
            margin: 5px 0 0 0;
            font-size: 14px;
        }}
        .highlight {{
            background: white;
            border-left: 4px solid #3498db;
            padding: 20px;
            margin-bottom: 25px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .highlight-text {{
            font-size: 16px;
            font-style: italic;
            color: #2c3e50;
            margin: 0 0 15px 0;
        }}
        .highlight-source {{
            font-size: 13px;
            color: #7f8c8d;
            margin: 0;
        }}
        .highlight-source strong {{
            color: #34495e;
        }}
        .footer {{
            text-align: center;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            font-size: 12px;
            color: #95a5a6;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 Your Daily Highlights</h1>
        <p>{date_str}</p>
    </div>
"""

    for h in highlights:
        html += f"""
    <div class="highlight">
        <p class="highlight-text">"{h['text']}"</p>
        <p class="highlight-source">— <strong>{h['title']}</strong> by {h['author']}</p>
    </div>
"""

    html += """
    <div class="footer">
        <p>Powered by your personal Kindle Highlights system</p>
    </div>
</body>
</html>
"""
    return html


def send_email(to_email: str, highlights: list[dict], from_email: str = None):
    """Send highlights email via Resend."""
    resend.api_key = os.environ.get('RESEND_API_KEY')

    if not resend.api_key:
        raise ValueError("RESEND_API_KEY environment variable is required")

    # Use Resend's default sender if no custom domain
    if not from_email:
        from_email = "Kindle Highlights <onboarding@resend.dev>"

    html_content = format_email_html(highlights)
    date_str = datetime.now().strftime('%B %d')

    params = {
        "from": from_email,
        "to": [to_email],
        "subject": f"📚 Your Daily Kindle Highlights - {date_str}",
        "html": html_content,
    }

    response = resend.Emails.send(params)
    return response


def main():
    """Main entry point for the daily highlights job."""
    # Configuration from environment
    to_email = os.environ.get('TO_EMAIL')
    from_email = os.environ.get('FROM_EMAIL')  # Optional
    highlights_count = int(os.environ.get('HIGHLIGHTS_COUNT', '5'))

    if not to_email:
        raise ValueError("TO_EMAIL environment variable is required")

    # Paths
    script_dir = Path(__file__).parent.parent
    data_path = script_dir / 'data' / 'highlights.json'

    # Load highlights
    highlights = load_highlights(str(data_path))

    if not highlights:
        print("No highlights found. Please run 'import_clippings.py' first.")
        return

    print(
        f"Loaded {len(highlights)} highlights from {len(set(h['title'] for h in highlights))} books")

    # Select random highlights
    selected = get_random_highlights(highlights, highlights_count)
    print(f"Selected {len(selected)} random highlights")

    # Send email
    response = send_email(to_email, selected, from_email)
    print(f"Email sent successfully! ID: {response.get('id', 'unknown')}")


if __name__ == '__main__':
    main()
