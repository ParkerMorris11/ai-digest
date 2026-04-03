# AI Digest

A self-hosted Python agent that reads four AI newsletters every morning, filters and ranks stories by relevance to your professional focus, and emails you a curated briefing before your day starts.

Runs on your Mac with a single cron job. No subscriptions, no SaaS dependencies — just a Python script, an API key, and your Gmail account.

![Email preview](docs/email-preview.png)

---

## How It Works

```
┌──────────────────────────────────────────────────────────────┐
│                        8:00 AM                               │
│                   macOS triggers                             │
│                   launchd job                                │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                    FETCH                                     │
│                                                              │
│   The Rundown AI ──┐                                         │
│   Superhuman AI  ──┤                                         │
│   TLDR AI ─────────┼──▶  Raw newsletter text (4 sources)     │
│   The Neuron ──────┘                                         │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                   ANALYZE                                    │
│                                                              │
│   Claude receives:                                           │
│   • Combined newsletter content (token-trimmed)              │
│   • Your consulting niche description                        │
│   • Model auto-selected: Sonnet (Mon) / Haiku (Tue–Fri)     │
│                                                              │
│   Claude returns structured JSON:                            │
│   • Deduplicated stories across sources                      │
│   • Relevance score (1–5) per story                          │
│   • Category tags (tools, research, enterprise, etc.)        │
│   • "Why it matters" for your niche                          │
│   • 2–3 specific action items                                │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                   DELIVER                                    │
│                                                              │
│   • HTML email with TOC, tag pills, score badges             │
│   • Plain text fallback for any email client                 │
│   • Local archive saved to ~/.ai-digest/digests/             │
└──────────────────────────────────────────────────────────────┘
```

The entire process takes about 30 seconds per run.

---

## Cost Analysis

AI Digest uses the Anthropic API. Here's what a typical run costs:

### Per Run

| Component | Tokens | Rate | Cost |
|-----------|--------|------|------|
| Input (system prompt + newsletter text) | ~8,500 | $3.00 / MTok | $0.026 |
| Output (structured JSON digest) | ~2,500 | $15.00 / MTok | $0.038 |
| **Total per run** | | | **$0.063** |

### Projected Annual Cost

| Frequency | Model | Annual Cost |
|-----------|-------|-------------|
| Weekdays (260 runs/yr) | Claude Sonnet 4.6 (`claude-sonnet-4-6`) | **~$16.38** |
| Weekdays (260 runs/yr) | Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) | **~$5.46** |
| Weekdays (260 runs/yr) | Two-tier (Sonnet Mon + Haiku Tue–Fri) | **~$7.64** |

The default configuration uses a **two-tier model strategy**: Sonnet on Mondays for a deep-dive start to the week, Haiku the rest of the week for cost efficiency. Configure this in `config.json`.

### What Else You Need

| Resource | Cost |
|----------|------|
| Gmail (SMTP sending) | Free |
| Python 3.9+ | Pre-installed on macOS |
| `certifi` package | Free |

**Total cost of ownership: approximately $6–$17 per year** depending on your model choice.

---

## Setup

### Prerequisites

- macOS with Python 3.9+
- An [Anthropic API key](https://console.anthropic.com/settings/keys)
- A [Gmail App Password](https://myaccount.google.com/apppasswords) (requires 2FA enabled)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/ai-digest.git
cd ai-digest

# Install the one dependency
pip3 install certifi

# Run interactive setup (saves to ~/.ai-digest/config.json)
python3 setup_config.py

# Test it (dry run — no email sent)
python3 main.py --dry-run

# Full run (fetches, analyzes, emails)
python3 main.py

# Schedule it (weekdays at 8 AM)
python3 install_schedule.py
```

The setup script will prompt you for:
1. **Anthropic API key** — for Claude to analyze and rank stories
2. **Gmail address** — sender address for the digest email
3. **Gmail App Password** — a 16-character app-specific password (not your regular password)
4. **Recipient email** — where to send the digest (defaults to your Gmail)
5. **Consulting niche** — a short description of your focus area for relevance scoring

### Gmail App Password

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Two-factor authentication must be enabled first
3. Enter a name (e.g., "AI Digest") and click Create
4. Copy the 16-character password

---

## Project Structure

```
ai-digest/
├── main.py                 # Entry point
├── setup_config.py         # Interactive configuration
├── install_schedule.py     # macOS launchd scheduler
├── requirements.txt        # Dependencies (certifi only)
├── src/
│   ├── config.py           # Config loading and validation
│   ├── fetchers.py         # Newsletter content fetching
│   ├── digest.py           # Claude API integration and scoring
│   ├── email_template.py   # HTML email rendering
│   └── mailer.py           # Gmail SMTP delivery
└── docs/
    └── email-preview.png   # Sample email screenshot
```

### Relevance Scoring

Each story is scored 1–5 based on your configured niche:

| Score | Meaning | Example |
|-------|---------|---------|
| **5** | Directly actionable | New AI tool your clients could deploy this week |
| **4** | Highly relevant | Major platform update, enterprise AI trend |
| **3** | Moderately relevant | Research with business implications, funding signals |
| **2** | Tangentially relevant | General AI news, consumer products |
| **1** | Low relevance | Entertainment AI, niche academic research |

Stories scored 3–5 appear in the **Top Stories** section with full summaries. Stories scored 1–2 appear in **Quick Scan** as one-liners.

### Story Tags

Each story is tagged with 1–2 categories for visual scanning:

`tools` · `research` · `infrastructure` · `funding` · `policy` · `product` · `strategy` · `automation` · `open-source` · `enterprise`

Tags appear as colored pills next to the relevance badge in the email.

---

## Configuration

All configuration is stored in `~/.ai-digest/config.json`:

```json
{
  "anthropic_api_key": "sk-ant-...",
  "gmail_address": "you@gmail.com",
  "gmail_app_password": "abcd efgh ijkl mnop",
  "recipient_email": "you@gmail.com",
  "consulting_niche": "AI consulting firm helping businesses implement AI tools...",
  "default_model": "claude-haiku-4-5-20251001",
  "sonnet_days": [0]
}
```

### Model Strategy

| Key | Default | Description |
|-----|---------|-------------|
| `default_model` | `claude-haiku-4-5-20251001` | Model used on most days |
| `sonnet_days` | `[0]` (Monday) | Days to use Sonnet instead (0=Mon, 1=Tue, … 6=Sun) |

Set `sonnet_days` to `[]` for Haiku every day, or `[0, 1, 2, 3, 4]` for Sonnet every weekday.

You can also set values via environment variables: `ANTHROPIC_API_KEY`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `DIGEST_RECIPIENT`, `DIGEST_NICHE`, `DIGEST_MODEL`.

To re-run setup: `python3 setup_config.py`

---

## Useful Commands

| Action | Command |
|--------|---------|
| Run manually | `python3 main.py` |
| Dry run (no email) | `python3 main.py --dry-run` |
| View logs | `cat ~/.ai-digest/logs/digest.log` |
| Browse past digests | `ls ~/.ai-digest/digests/` |
| Open today's digest in browser | `open ~/.ai-digest/digests/$(date +%Y-%m-%d).html` |
| Update configuration | `python3 setup_config.py` |
| Change schedule time | Edit `Hour` in `~/Library/LaunchAgents/com.ai-digest.daily.plist` |
| Stop the schedule | `python3 install_schedule.py --uninstall` |
| Restart the schedule | `python3 install_schedule.py` |

---

## Newsletter Sources

| Newsletter | Subscribers | What It Covers |
|-----------|-------------|----------------|
| [The Rundown AI](https://www.therundown.ai) | 2M+ | Daily AI news, tools, and industry developments |
| [Superhuman AI](https://www.superhuman.ai) | 1.5M+ | AI tools, tutorials, and productivity workflows |
| [TLDR AI](https://tldr.tech/ai) | 500K+ | AI research, tools, and machine learning news |
| [The Neuron](https://www.theneurondaily.com) | 600K+ | AI trends, tools, and business applications |

The agent fetches the latest issue from each source's public archive. If a source is unavailable on a given day, the digest proceeds with the remaining sources (minimum 2 of 4 required).

---

## Customization

**Change your niche** — Edit `consulting_niche` in `~/.ai-digest/config.json`. This is the context Claude uses to score relevance, so updating it will shift which stories rank highest.

**Add newsletter sources** — Add a new fetch function in `src/fetchers.py` and include it in the `newsletters` dict in `main.py`.

**Swap the model** — Change `default_model` in `~/.ai-digest/config.json`. Use `claude-haiku-4-5-20251001` for lower cost or `claude-sonnet-4-6` for highest quality. Use `sonnet_days` to control which days get the premium model.

**Change the schedule** — Edit the `Hour` and `Minute` values in the launchd plist at `~/Library/LaunchAgents/com.ai-digest.daily.plist`, then run:

```bash
launchctl unload ~/Library/LaunchAgents/com.ai-digest.daily.plist
launchctl load ~/Library/LaunchAgents/com.ai-digest.daily.plist
```

---

## Troubleshooting

**SSL certificate errors** — The script uses `certifi` to handle macOS SSL certificates. If you still see errors, run `pip3 install --upgrade certifi`.

**Email not sending** — Check `~/.ai-digest/logs/digest-error.log`. The most common fix is regenerating your Gmail App Password.

**"Application-specific password required"** — You're using your regular Gmail password instead of an App Password. Create one at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).

**Script not running on schedule** — Your Mac needs to be awake at the scheduled time. macOS will run missed jobs when the Mac next wakes up.

**Claude API errors** — Verify your API key and check your balance at [console.anthropic.com](https://console.anthropic.com/settings/billing).

---

## License

MIT License. See [LICENSE](LICENSE) for details.
