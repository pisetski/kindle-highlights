# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A free, self-hosted alternative to Readwise that sends random Kindle highlights to your email daily via GitHub Actions. Imports highlights from Kindle's native "My Clippings.txt" file, stores them in JSON, and emails 5 random highlights daily using the Resend API.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Import highlights from Kindle (one-time)
python src/import_clippings.py /path/to/My\ Clippings.txt

# Preview import without saving
python src/import_clippings.py --dry-run /path/to/My\ Clippings.txt

# Send test email manually (requires environment variables)
RESEND_API_KEY=xxx TO_EMAIL=you@example.com python src/main.py
```

## Architecture

```
My Clippings.txt (Kindle)
    ↓
import_clippings.py (parse + deduplicate)
    ↓
data/highlights.json (storage)
    ↓
[GitHub Actions cron: 7 AM UTC daily]
    ↓
main.py (select random, format HTML, send via Resend API)
    ↓
Email
```

**Key files:**
- `src/main.py` - Daily email sending: loads highlights, selects 5 random with book diversity, formats HTML email, sends via Resend
- `src/import_clippings.py` - Parses Kindle's clippings format, deduplicates using (title, first 100 chars of text) signature
- `data/highlights.json` - JSON array of highlight objects with title, author, text, location, page, added_at
- `.github/workflows/daily-highlights.yml` - GitHub Actions automation (Python 3.11, ubuntu-latest)

## Environment Variables

- `RESEND_API_KEY` - Resend API key (required)
- `TO_EMAIL` - Recipient email (required)
- `FROM_EMAIL` - Sender email (optional, defaults to onboarding@resend.dev)
- `HIGHLIGHTS_COUNT` - Number of highlights per email (optional, defaults to 5)
