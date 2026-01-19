# Kindle Daily Highlights

Sends you random Kindle highlights every day via email. Self-hosted on GitHub Actions. 100% free.

## Setup

### 1. Get Your Kindle Highlights

1. Connect Kindle to your computer via USB
2. Copy `My Clippings.txt` from the `documents` folder

### 2. Import Highlights

```bash
git clone https://github.com/YOUR_USERNAME/kindle-highlights.git
cd kindle-highlights

pip install -r requirements.txt

# Preview first
python src/import_clippings.py --dry-run ~/path/to/My\ Clippings.txt

# Import
python src/import_clippings.py ~/path/to/My\ Clippings.txt

git add data/highlights.json
git commit -m "Add highlights"
git push
```

### 3. Configure Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|--------|-------------|
| `RESEND_API_KEY` | API key from resend.com |
| `TO_EMAIL` | Your email address |
| `FROM_EMAIL` | Optional custom sender |

### 4. Run

Go to **Actions → Daily Kindle Highlights → Run workflow**.

The workflow runs daily at 7:00 AM UTC. Edit `.github/workflows/daily-highlights.yml` to change the schedule.

## Adding New Highlights

```bash
python src/import_clippings.py ~/path/to/My\ Clippings.txt
git add data/highlights.json
git commit -m "Add new highlights"
git push
```

Duplicates are detected automatically.

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RESEND_API_KEY` | Yes | - | Email service API key |
| `TO_EMAIL` | Yes | - | Recipient email |
| `FROM_EMAIL` | No | `onboarding@resend.dev` | Sender email |
| `HIGHLIGHTS_COUNT` | No | 5 | Highlights per email |

## License

MIT
