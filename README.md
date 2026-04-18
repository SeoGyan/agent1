# SEO Agent

This repository sets up an AI-powered SEO agent powered by [claude-seo](https://github.com/AgriciDaniel/claude-seo), running inside Claude Code.

## What is this?

This SEO agent can automatically analyze any website and tell you:
- What SEO problems it has (broken links, missing titles, slow pages, etc.)
- How to improve content so Google ranks it higher
- Whether your structured data (schema) is set up correctly
- How your site compares to competitors
- Local SEO issues (Google Business Profile, citations, etc.)

No SEO experience needed — just give it a URL and it does the work.

---

## Installation

Run this one command in your terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/AgriciDaniel/claude-seo/main/install.sh | bash
```

**Requirements:** Python 3.10+ and Git must be installed.

---

## How to Use

Start Claude Code, then type any of these commands:

| Command | What it does |
|---|---|
| `/seo audit https://yoursite.com` | Full website audit (checks up to 500 pages) |
| `/seo page https://yoursite.com/page` | Deep analysis of one specific page |
| `/seo schema https://yoursite.com` | Check structured data / rich results |
| `/seo local https://yoursite.com` | Local SEO (Google Business Profile, maps) |
| `/seo technical https://yoursite.com` | Technical issues (speed, mobile, crawling) |
| `/seo content https://yoursite.com` | Content quality and E-E-A-T analysis |
| `/seo backlinks https://yoursite.com` | Backlink profile analysis |
| `/seo competitor https://yoursite.com` | Competitor comparison pages |
| `/seo google` | Google Search Console, PageSpeed, Analytics |

### Quick Start Example

```
/seo audit https://example.com
```

This runs a full audit using 15 specialist subagents in parallel and gives you a health score with prioritized recommendations.

---

## What Gets Checked in a Full Audit

- **Technical SEO** — crawlability, indexability, mobile-friendliness, Core Web Vitals (LCP, INP, CLS)
- **On-page SEO** — title tags, meta descriptions, headings, keyword usage
- **Content Quality** — E-E-A-T signals, readability, thin content detection
- **Schema Markup** — JSON-LD validation, rich result eligibility
- **Images** — alt text, file sizes, formats, lazy loading
- **Backlinks** — referring domains, anchor text, toxic links
- **AI Search** — optimization for Google AI Overviews, ChatGPT, Perplexity

---

## Source

Built on top of [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) (v1.9.0).
