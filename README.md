# Landing Page Critic

AI-powered landing page conversion analysis tool. Paste a URL, get a detailed breakdown of every mistake killing your conversions.

## Features

- **AI Vision Analysis** — Llama 4 Scout via Groq analyzes your landing page screenshot
- **10 Conversion Factors** — Hero, CTA, Trust, Colors, Typography, Copy, Layout, Mobile, Speed, Barriers
- **Score 0-100** — Overall conversion score with per-category breakdown
- **Quick Wins** — Top 3 easiest high-impact fixes
- **Download Reports** — Export as HTML or PDF
- **Analysis History** — All past analyses saved in browser
- **Bilingual UI** — Russian and English
- **Rate Limiting** — 3 free analyses per hour
- **Caching** — Same URL analyzed once per 24h

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Get free Groq API key

1. Go to [console.groq.com](https://console.groq.com)
2. Create free account
3. Generate API key

### 3. Run

```bash
set GROQ_API_KEY=your_key_here
python server.py
```

Open [http://localhost:8000](http://localhost:8000)

## Tech Stack

- **Backend**: Python + FastAPI
- **AI**: Groq (Llama 4 Scout 17B)
- **Screenshot**: Playwright (headless Chromium)
- **Frontend**: Vanilla JS + CSS
- **PDF**: html2pdf.js
- **Payments**: Google Pay (Pro tier)

## Project Structure

```
landing-page-critic/
├── server.py           # FastAPI backend
├── analyzer.py         # Groq AI analysis
├── screenshot.py       # Playwright screenshots
├── requirements.txt    # Python dependencies
├── static/
│   ├── index.html      # Main UI
│   ├── style.css       # Styles
│   └── app.js          # Frontend logic
└── history/            # Saved analyses (auto-created)
```

## API

### POST /api/analyze

```json
{
  "url": "https://example.com",
  "api_key": "gsk_..."
}
```

Response:

```json
{
  "id": "abc123",
  "url": "https://example.com",
  "timestamp": "2025-01-01T00:00:00",
  "result": {
    "overall_score": 72,
    "categories": [...],
    "quick_wins": [...],
    "summary": "..."
  }
}
```

### GET /api/history

Returns list of past analyses.

### GET /api/history/{id}

Returns single analysis by ID.

## Deployment

### Railway (recommended)

1. Push to GitHub
2. Go to [railway.app](https://railway.app)
3. New Project → Deploy from GitHub
4. Add environment variable: `GROQ_API_KEY`
5. Done

### Docker

```bash
docker build -t landing-page-critic .
docker run -p 8000:8000 -e GROQ_API_KEY=your_key landing-page-critic
```

## Pricing Model

| Tier | Price | Analyses | API Key |
|------|-------|----------|---------|
| Free | $0 | 3/hour | Your own |
| Pro | $5/mo | Unlimited | Included |

## License

MIT
