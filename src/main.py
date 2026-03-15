#!/usr/bin/env python3
"""
Kindle Daily Highlights - Free Readwise Alternative
Sends 5 random Kindle highlights to your email daily via GitHub Actions + Resend

Author: Generated for Pavel
License: MIT
"""

import json
import html as html_lib
import os
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, cast

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

        metadata_line = lines[1].strip()

        page_match = re.search(r'page\s+(\d+)', metadata_line, re.IGNORECASE)
        page = page_match.group(1) if page_match else None

        # The actual highlight text (everything after the metadata line, excluding empty lines)
        highlight_text = '\n'.join(line for line in lines[3:] if line.strip())

        if highlight_text:
            highlight = {
                'title': title,
                'author': author,
                'text': highlight_text,
                'added_at': datetime.now().isoformat()
            }
            if page:
                highlight['page'] = page
            highlights.append(highlight)

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


def get_themed_highlights(highlights: list[dict], count: int = 5) -> tuple[str, list[dict]]:
    """
    Select highlights from a randomly chosen theme.

    Returns:
        Tuple of (theme_name, selected_highlights)
    """
    # Group by theme
    by_theme = {}
    for h in highlights:
        theme = h.get('theme', 'General')
        by_theme.setdefault(theme, []).append(h)

    # Pick viable themes (enough highlights, prefer non-General)
    viable = [t for t, hs in by_theme.items() if len(hs) >= count and t != 'General']

    if not viable:
        # Fallback: use any theme with enough highlights
        viable = [t for t, hs in by_theme.items() if len(hs) >= count]

    if not viable:
        # Last resort: use any theme with highlights
        viable = [t for t, hs in by_theme.items() if len(hs) > 0]

    chosen = random.choice(viable)
    selected = get_random_highlights(by_theme[chosen], count)

    return chosen, selected


def format_email_html(highlights: list[dict], theme: Optional[str] = None) -> str:
    """Format highlights as a polished HTML email."""
    date_str = datetime.now().strftime('%B %d, %Y')
    title = f"📚 {theme} Highlights" if theme else "📚 Your Daily Highlights"
    intro = (
        f"A focused set of ideas from your {html_lib.escape(theme)} shelf, ready to skim and revisit."
        if theme else
        "A focused set of ideas from your library, ready to skim and revisit."
    )

    markup = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: Georgia, 'Times New Roman', serif;
            margin: 0 auto;
            padding: 24px 12px;
            background-color: #f4efe6;
            color: #1f2933;
        }}
        .container {{
            max-width: 680px;
            margin: 0 auto;
            background: #fffdf8;
            border: 1px solid #eadfce;
            border-radius: 24px;
            overflow: hidden;
        }}
        .header {{
            padding: 36px 32px 28px;
            background: #fcf8f1;
            border-bottom: 1px solid #eadfce;
        }}
        .eyebrow {{
            display: inline-block;
            margin-bottom: 14px;
            padding: 7px 12px;
            border-radius: 999px;
            background: #f1dfcb;
            color: #8b4e1f;
            font-family: Arial, Helvetica, sans-serif;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}
        .header h1 {{
            font-size: 32px;
            line-height: 1.15;
            color: #1d2a35;
            margin: 0;
        }}
        .header p {{
            color: #4b5563;
            margin: 12px 0 0 0;
            font-size: 17px;
            line-height: 1.7;
        }}
        .stats {{
            margin-top: 22px;
            font-family: Arial, Helvetica, sans-serif;
            font-size: 13px;
            font-weight: 600;
            color: #5f6772;
        }}
        .stat {{
            display: inline-block;
            margin: 0 10px 8px 0;
            padding: 8px 12px;
            border: 1px solid #eadfce;
            border-radius: 999px;
            background: #ffffff;
        }}
        .content {{
            padding: 28px 24px 12px;
        }}
        .highlight {{
            background: #ffffff;
            border: 1px solid #eadfce;
            border-radius: 20px;
            padding: 22px 22px 18px;
            margin-bottom: 18px;
        }}
        .highlight-index {{
            margin: 0 0 14px 0;
            font-family: Arial, Helvetica, sans-serif;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #a15d25;
        }}
        .highlight-text {{
            font-size: 22px;
            line-height: 1.65;
            color: #24303a;
            margin: 0;
        }}
        .highlight-source {{
            font-family: Arial, Helvetica, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: #6b7280;
            margin: 18px 0 0 0;
            padding-top: 16px;
            border-top: 1px solid #eee4d3;
        }}
        .highlight-source strong {{
            color: #26333d;
        }}
        .footer {{
            text-align: center;
            padding: 20px 32px 30px;
            border-top: 1px solid #eadfce;
            font-family: Arial, Helvetica, sans-serif;
            font-size: 13px;
            line-height: 1.7;
            color: #7b8088;
            background: #fcf8f1;
        }}
        @media only screen and (max-width: 640px) {{
            body {{
                padding: 12px 8px;
            }}
            .header, .content, .footer {{
                padding-left: 18px;
                padding-right: 18px;
            }}
            .header h1 {{
                font-size: 28px;
            }}
            .header p {{
                font-size: 16px;
            }}
            .highlight {{
                padding: 18px;
                border-radius: 16px;
            }}
            .highlight-text {{
                font-size: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="eyebrow">{html_lib.escape(theme) if theme else 'Daily Highlights'}</div>
            <h1>{html_lib.escape(title)}</h1>
            <p>{intro}</p>
            <div class="stats">
                <span class="stat">{date_str}</span>
                <span class="stat">{len(highlights)} highlights</span>
                <span class="stat">{len(set(h.get('title', 'Unknown') for h in highlights))} books</span>
            </div>
        </div>
        <div class="content">
"""

    for index, h in enumerate(highlights, start=1):
        title_text = html_lib.escape(str(h.get('title', 'Unknown Title')))
        author_text = html_lib.escape(str(h.get('author', 'Unknown Author')))
        highlight_text = html_lib.escape(str(h.get('text', '')))
        source_parts = [f"<strong>{title_text}</strong>", f"by {author_text}"]
        if h.get('page'):
            source_parts.append(f"Page {html_lib.escape(str(h['page']))}")

        markup += f"""
    <div class="highlight">
        <p class="highlight-index">Highlight {index:02d}</p>
        <p class="highlight-text">&ldquo;{highlight_text}&rdquo;</p>
        <p class="highlight-source">{' &middot; '.join(source_parts)}</p>
    </div>
"""

    markup += """
        </div>
    <div class="footer">
        <p>Sent from your personal Kindle Highlights system.</p>
    </div>
    </div>
</body>
</html>
"""
    return markup


def send_email(to_email: str, highlights: list[dict], theme: Optional[str] = None, from_email: Optional[str] = None):
    """Send highlights email via Resend."""
    resend.api_key = os.environ.get('RESEND_API_KEY')

    if not resend.api_key:
        raise ValueError("RESEND_API_KEY environment variable is required")

    # Use Resend's default sender if no custom domain
    if not from_email:
        from_email = "Kindle Highlights <onboarding@resend.dev>"

    html_content = format_email_html(highlights, theme)
    date_str = datetime.now().strftime('%B %d')

    if theme:
        subject = f"📚 {theme} Highlights - {date_str}"
    else:
        subject = f"📚 Your Daily Kindle Highlights - {date_str}"

    params = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html_content,
    }

    response = resend.Emails.send(cast(Any, params))
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

    # Select themed highlights
    theme, selected = get_themed_highlights(highlights, highlights_count)
    print(f"Selected theme: {theme}")
    print(f"Selected {len(selected)} highlights from {len(set(h['title'] for h in selected))} books")

    # Send email
    response = send_email(to_email, selected, theme, from_email)
    print(f"Email sent successfully! ID: {response.get('id', 'unknown')}")


if __name__ == '__main__':
    main()
