#!/usr/bin/env python3
"""
Import Kindle Clippings

Parses 'My Clippings.txt' from your Kindle device and saves highlights
to the JSON database for daily email delivery.

Usage:
    python import_clippings.py /path/to/My\ Clippings.txt
    
    Or, if your Kindle is connected:
    python import_clippings.py /Volumes/Kindle/documents/My\ Clippings.txt  # macOS
    python import_clippings.py /media/$USER/Kindle/documents/My\ Clippings.txt  # Linux
    python import_clippings.py D:\\documents\\My\ Clippings.txt  # Windows
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


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

    try:
        # Try UTF-8 with BOM first (common for Kindle files)
        with open(clippings_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Fall back to Latin-1
        with open(clippings_path, 'r', encoding='latin-1') as f:
            content = f.read()

    # Split by the separator
    entries = content.split('==========')
    skipped = {'bookmarks': 0, 'notes': 0, 'empty': 0}

    for entry in entries:
        entry = entry.strip()
        if not entry:
            skipped['empty'] += 1
            continue

        lines = entry.split('\n')
        if len(lines) < 3:
            skipped['empty'] += 1
            continue

        # First line: Book Title (Author)
        title_line = lines[0].strip()

        # Clean up title line (remove BOM and other artifacts)
        title_line = title_line.lstrip('\ufeff').strip()

        # Extract author from parentheses at the end
        author_match = re.search(r'\(([^)]+)\)\s*$', title_line)
        if author_match:
            author = author_match.group(1).strip()
            title = title_line[:author_match.start()].strip()
        else:
            author = "Unknown Author"
            title = title_line

        # Second line: metadata
        metadata_line = lines[1].strip() if len(lines) > 1 else ""

        # Skip bookmarks (no highlight text)
        if 'Your Bookmark' in metadata_line:
            skipped['bookmarks'] += 1
            continue

        # Skip notes (personal annotations, not highlights)
        if 'Your Note' in metadata_line:
            skipped['notes'] += 1
            continue

        # Parse location if present
        location_match = re.search(
            r'location\s+(\d+)(?:-(\d+))?', metadata_line, re.IGNORECASE)
        location = None
        if location_match:
            start = location_match.group(1)
            end = location_match.group(2) or start
            location = f"{start}-{end}"

        # Parse page if present
        page_match = re.search(r'page\s+(\d+)', metadata_line, re.IGNORECASE)
        page = page_match.group(1) if page_match else None

        # The actual highlight text (everything after the metadata line, excluding empty lines)
        highlight_text = '\n'.join(line.strip()
                                   for line in lines[3:] if line.strip())

        # Also check line 2 if line 3 is empty (some formats)
        if not highlight_text and len(lines) > 2:
            highlight_text = lines[2].strip()

        if highlight_text:
            highlight_data = {
                'title': title,
                'author': author,
                'text': highlight_text,
            }

            if location:
                highlight_data['location'] = location
            if page:
                highlight_data['page'] = page

            highlights.append(highlight_data)

    return highlights, skipped


def deduplicate_highlights(existing: list[dict], new: list[dict]) -> tuple[list[dict], int]:
    """
    Merge new highlights with existing ones, avoiding duplicates.
    Returns merged list and count of new highlights added.
    """
    # Create a set of existing highlight signatures
    existing_signatures = set()
    for h in existing:
        sig = (h['title'], h['text'][:100])  # Use first 100 chars of text
        existing_signatures.add(sig)

    merged = existing.copy()
    added = 0

    for h in new:
        sig = (h['title'], h['text'][:100])
        if sig not in existing_signatures:
            h['added_at'] = datetime.now().isoformat()
            merged.append(h)
            existing_signatures.add(sig)
            added += 1

    return merged, added


def main():
    parser = argparse.ArgumentParser(
        description='Import Kindle highlights from My Clippings.txt',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import from a file
  python import_clippings.py ~/Downloads/My\\ Clippings.txt
  
  # Import from connected Kindle (macOS)
  python import_clippings.py /Volumes/Kindle/documents/My\\ Clippings.txt
  
  # Show statistics only (dry run)
  python import_clippings.py --dry-run ~/Downloads/My\\ Clippings.txt
        """
    )
    parser.add_argument('clippings_file', help='Path to My Clippings.txt file')
    parser.add_argument('--output', '-o', default='data/highlights.json',
                        help='Output JSON file (default: data/highlights.json)')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Parse and show statistics without saving')

    args = parser.parse_args()

    # Check if input file exists
    if not os.path.exists(args.clippings_file):
        print(f"Error: File not found: {args.clippings_file}")
        sys.exit(1)

    print(f"📖 Parsing: {args.clippings_file}")

    # Parse clippings
    highlights, skipped = parse_clippings(args.clippings_file)

    print(f"\n📊 Parsing Results:")
    print(f"   ✅ Highlights found: {len(highlights)}")
    print(f"   ⏭️  Bookmarks skipped: {skipped['bookmarks']}")
    print(f"   ⏭️  Notes skipped: {skipped['notes']}")
    print(f"   ⏭️  Empty entries: {skipped['empty']}")

    if not highlights:
        print("\n⚠️  No highlights found. Check your file format.")
        sys.exit(1)

    # Group by book for statistics
    books = {}
    for h in highlights:
        key = f"{h['title']} by {h['author']}"
        if key not in books:
            books[key] = 0
        books[key] += 1

    print(f"\n📚 Books found ({len(books)}):")
    for book, count in sorted(books.items(), key=lambda x: -x[1])[:10]:
        print(f"   • {book}: {count} highlights")
    if len(books) > 10:
        print(f"   ... and {len(books) - 10} more books")

    if args.dry_run:
        print("\n🔍 Dry run - no changes made.")
        return

    # Load existing highlights
    script_dir = Path(__file__).parent.parent
    output_path = script_dir / args.output

    existing = []
    if output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        print(f"\n📂 Existing database: {len(existing)} highlights")

    # Merge and deduplicate
    merged, added = deduplicate_highlights(existing, highlights)

    # Save
    os.makedirs(output_path.parent, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    print(f"\n✨ Import complete!")
    print(f"   📥 New highlights added: {added}")
    print(f"   📊 Total highlights: {len(merged)}")
    print(f"   💾 Saved to: {output_path}")


if __name__ == '__main__':
    main()
