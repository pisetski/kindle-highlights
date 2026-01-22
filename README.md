# Kindle Daily Highlights

Sends you theme-based Kindle highlights every day via email. Each email focuses on a single theme (Philosophy, Psychology, Software Engineering, etc.) so you receive cohesive, related insights. Self-hosted on GitHub Actions. 100% free.

## Setup

### 1. Connect Kindle to your computer

### 2. Import Highlights

```bash
pip install -r requirements.txt

# Preview first
python src/import_clippings.py --dry-run /Volumes/Kindle/documents/My\ Clippings.txt

# Import (first run downloads ~180MB AI model for classification)
python src/import_clippings.py /Volumes/Kindle/documents/My\ Clippings.txt

# Encrypt highlights
gpg --symmetric --cipher-algo AES256 data/highlights.json
# Enter your passphrase when prompted

git add data/highlights.json.gpg
git commit -m "Add highlights"
git push
```

Books are automatically classified into themes during import using a local AI model (`MoritzLaurer/deberta-v3-base-mnli-fever-anli`). For more accurate classification, consider using a cloud LLM.

### 3. Configure Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|--------|-------------|
| `RESEND_API_KEY` | API key from resend.com |
| `TO_EMAIL` | Your email address |
| `FROM_EMAIL` | Optional custom sender |
| `GPG_PASSPHRASE` | Passphrase used to encrypt highlights.json |

### 4. Run

Go to **Actions → Daily Kindle Highlights → Run workflow**.

The workflow runs daily at 7:00 AM UTC. Edit `.github/workflows/daily-highlights.yml` to change the schedule.

## Adding New Highlights

```bash
python src/import_clippings.py /Volumes/Kindle/documents/My\ Clippings.txt
gpg --symmetric --cipher-algo AES256 data/highlights.json
# Enter your passphrase when prompted

git add data/highlights.json.gpg

git commit -m "Add new highlights"
git push
```

Duplicates are detected automatically. New books are classified into themes.

## Customizing Themes

Edit `src/classifier.py` to modify the theme list:

```python
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
    # Add your own:
    "Spirituality",
    "Health & Fitness",
]
```

After changing themes, re-run the migration to reclassify all books:

```bash
# Remove existing themes first
python -c "import json; d=json.load(open('data/highlights.json')); [h.pop('theme',None) for h in d]; json.dump(d,open('data/highlights.json','w'),indent=2)"

# Reclassify
python src/migrate_themes.py
```

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RESEND_API_KEY` | Yes | - | Email service API key |
| `TO_EMAIL` | Yes | - | Recipient email |
| `FROM_EMAIL` | No | `onboarding@resend.dev` | Sender email |
| `HIGHLIGHTS_COUNT` | No | 5 | Highlights per email |
| `GPG_PASSPHRASE` | Yes | - | Passphrase to decrypt highlights |

## License

GPL-3.0 - See [LICENSE](LICENSE) for details.
