#!/usr/bin/env python3
"""
SEO HTML Report Generator
Generates a beautiful, self-contained HTML report from SEO audit data.

Usage:
    python seo_html_report.py --data audit.json --output report.html
    python seo_html_report.py --demo --domain example.com
"""

import json
import argparse
import sys
import os
from datetime import datetime
from pathlib import Path


def score_color(s):
    if s >= 80: return "#22c55e"
    if s >= 60: return "#f59e0b"
    if s >= 40: return "#f97316"
    return "#ef4444"

def score_label(s):
    if s >= 80: return "Good"
    if s >= 60: return "Needs Work"
    if s >= 40: return "Poor"
    return "Critical"

def priority_color(p):
    return {"critical":"#ef4444","high":"#f97316","medium":"#f59e0b","low":"#3b82f6"}.get(p.lower(),"#6b7280")

def priority_bg(p):
    return {"critical":"#fef2f2","high":"#fff7ed","medium":"#fffbeb","low":"#eff6ff"}.get(p.lower(),"#f9fafb")

def priority_border(p):
    return {"critical":"#fca5a5","high":"#fdba74","medium":"#fcd34d","low":"#93c5fd"}.get(p.lower(),"#e5e7eb")

def gauge_svg(score, size=160):
    c = score_color(score)
    r = 54
    circ = 2 * 3.14159 * r
    dash = (score / 100) * circ
    gap = circ - dash
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 120 120">
  <circle cx="60" cy="60" r="{r}" fill="none" stroke="#1e293b" stroke-width="10"/>
  <circle cx="60" cy="60" r="{r}" fill="none" stroke="{c}" stroke-width="10"
    stroke-dasharray="{dash:.1f} {gap:.1f}"
    stroke-dashoffset="{circ*0.25:.1f}"
    stroke-linecap="round" transform="rotate(-90 60 60)"/>
  <text x="60" y="55" text-anchor="middle" fill="white" font-size="22" font-weight="700">{score}</text>
  <text x="60" y="72" text-anchor="middle" fill="{c}" font-size="9" font-weight="600">{score_label(score).upper()}</text>
</svg>"""

def mini_bar(score, width=120):
    c = score_color(score)
    pct = score
    return f"""<div style="width:{width}px;background:#1e293b;border-radius:4px;height:8px;margin-top:6px;">
  <div style="width:{pct}%;background:{c};height:8px;border-radius:4px;transition:width .6s;"></div>
</div>"""

def issues_html(issues_list, priority):
    if not issues_list: return ""
    color = priority_color(priority)
    bg    = priority_bg(priority)
    border= priority_border(priority)
    label = priority.upper()
    rows  = ""
    for item in issues_list:
        title  = item.get("title","Issue")
        detail = item.get("detail","")
        effort = item.get("effort","")
        effort_tag = f'<span style="font-size:11px;background:#334155;color:#94a3b8;padding:2px 8px;border-radius:10px;margin-left:8px;">{effort}</span>' if effort else ""
        rows += f"""<div style="padding:12px 16px;border-bottom:1px solid {border};last-child:border-none;">
  <div style="display:flex;align-items:center;flex-wrap:wrap;gap:4px;">
    <span style="font-weight:600;color:#f1f5f9;">{title}</span>{effort_tag}
  </div>
  {'<div style="color:#94a3b8;font-size:13px;margin-top:4px;">'+detail+'</div>' if detail else ''}
</div>"""
    return f"""<div style="margin-bottom:20px;border-radius:10px;overflow:hidden;border:1px solid {border};">
  <div style="background:{color};padding:8px 16px;display:flex;align-items:center;gap:8px;">
    <span style="color:white;font-weight:700;font-size:13px;letter-spacing:.5px;">{label}</span>
    <span style="background:rgba(255,255,255,.25);color:white;border-radius:10px;padding:1px 8px;font-size:12px;">{len(issues_list)}</span>
  </div>
  <div style="background:{bg};">{rows}</div>
</div>"""

def section_card(title, score, findings, icon="📋"):
    c     = score_color(score)
    label = score_label(score)
    rows  = ""
    for f in findings:
        sev = f.get("severity","info")
        sev_color = {"critical":"#ef4444","high":"#f97316","medium":"#f59e0b","low":"#3b82f6","info":"#6b7280"}.get(sev,"#6b7280")
        dot = f'<span style="width:8px;height:8px;border-radius:50%;background:{sev_color};display:inline-block;flex-shrink:0;margin-top:5px;"></span>'
        rows += f"""<div style="display:flex;gap:10px;padding:8px 0;border-bottom:1px solid #1e293b;">
  {dot}<span style="color:#cbd5e1;font-size:14px;">{f.get('text','')}</span>
</div>"""
    return f"""<div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:20px;margin-bottom:20px;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
    <span style="font-size:16px;font-weight:700;color:#f1f5f9;">{icon} {title}</span>
    <span style="background:{c}22;color:{c};border:1px solid {c}44;border-radius:20px;padding:3px 12px;font-size:13px;font-weight:600;">{score}/100 · {label}</span>
  </div>
  <div>{rows if rows else '<span style="color:#475569;font-size:13px;">No findings recorded.</span>'}</div>
</div>"""

def actions_table(actions):
    if not actions: return ""
    rows = ""
    for i, a in enumerate(actions, 1):
        p      = a.get("priority","medium")
        color  = priority_color(p)
        bg     = priority_bg(p)
        rows += f"""<tr style="border-bottom:1px solid #1e293b;">
  <td style="padding:10px 14px;color:#94a3b8;font-size:13px;">{i}</td>
  <td style="padding:10px 14px;"><span style="background:{color}22;color:{color};border:1px solid {color}44;border-radius:6px;padding:2px 8px;font-size:11px;font-weight:700;text-transform:uppercase;">{p}</span></td>
  <td style="padding:10px 14px;color:#f1f5f9;font-size:14px;">{a.get('action','')}</td>
  <td style="padding:10px 14px;color:#94a3b8;font-size:13px;">{a.get('effort','')}</td>
  <td style="padding:10px 14px;color:#94a3b8;font-size:13px;">{a.get('impact','')}</td>
</tr>"""
    return f"""<div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;overflow:hidden;margin-bottom:20px;">
  <div style="padding:16px 20px;border-bottom:1px solid #1e293b;">
    <span style="font-size:16px;font-weight:700;color:#f1f5f9;">🎯 Prioritized Action Plan</span>
  </div>
  <div style="overflow-x:auto;">
  <table style="width:100%;border-collapse:collapse;">
    <thead>
      <tr style="background:#020617;">
        <th style="padding:10px 14px;text-align:left;color:#475569;font-size:12px;letter-spacing:.5px;">#</th>
        <th style="padding:10px 14px;text-align:left;color:#475569;font-size:12px;letter-spacing:.5px;">PRIORITY</th>
        <th style="padding:10px 14px;text-align:left;color:#475569;font-size:12px;letter-spacing:.5px;">ACTION</th>
        <th style="padding:10px 14px;text-align:left;color:#475569;font-size:12px;letter-spacing:.5px;">EFFORT</th>
        <th style="padding:10px 14px;text-align:left;color:#475569;font-size:12px;letter-spacing:.5px;">IMPACT</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
  </div>
</div>"""

def score_cards_html(scores):
    icons = {"technical":"⚙️","content":"📝","on_page":"🏷️","schema":"🔗","performance":"⚡","ai_search":"🤖","images":"🖼️","local":"📍","backlinks":"🔒"}
    labels = {"technical":"Technical SEO","content":"Content Quality","on_page":"On-Page SEO","schema":"Schema Markup","performance":"Performance","ai_search":"AI Search","images":"Images","local":"Local SEO","backlinks":"Backlinks"}
    cards = ""
    for key, val in scores.items():
        c = score_color(val)
        lbl = labels.get(key, key.replace("_"," ").title())
        ico = icons.get(key,"📊")
        cards += f"""<div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:16px;text-align:center;">
  <div style="font-size:22px;margin-bottom:4px;">{ico}</div>
  <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;">{lbl}</div>
  <div style="font-size:28px;font-weight:800;color:{c};">{val}</div>
  {mini_bar(val, 80)}
  <div style="font-size:11px;color:{c};margin-top:6px;">{score_label(val)}</div>
</div>"""
    count = len(scores)
    cols = min(count, 4)
    return f'<div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:14px;margin-bottom:24px;">{cards}</div>'

def radar_chart_js(scores):
    labels = [k.replace("_"," ").title() for k in scores.keys()]
    values = list(scores.values())
    labels_js = json.dumps(labels)
    values_js = json.dumps(values)
    return f"""<canvas id="radarChart" style="max-height:300px;"></canvas>
<script>
new Chart(document.getElementById('radarChart'),{{
  type:'radar',
  data:{{
    labels:{labels_js},
    datasets:[{{
      label:'SEO Score',
      data:{values_js},
      backgroundColor:'rgba(59,130,246,.15)',
      borderColor:'#3b82f6',
      pointBackgroundColor:'#3b82f6',
      pointRadius:4,
      borderWidth:2
    }}]
  }},
  options:{{
    responsive:true,
    scales:{{r:{{
      min:0,max:100,
      ticks:{{color:'#475569',font:{{size:10}},backdropColor:'transparent',stepSize:25}},
      grid:{{color:'#1e293b'}},
      pointLabels:{{color:'#94a3b8',font:{{size:11}}}}
    }}}},
    plugins:{{legend:{{display:false}}}}
  }}
}});
</script>"""

def generate_html(data: dict) -> str:
    domain      = data.get("domain","example.com")
    audit_date  = data.get("audit_date", datetime.now().strftime("%B %d, %Y"))
    overall     = data.get("overall_score", 0)
    scores      = data.get("scores", {})
    issues      = data.get("issues", {})
    quick_wins  = data.get("quick_wins", [])
    actions     = data.get("actions", [])
    sections    = data.get("sections", [])
    business    = data.get("business_type","Unknown")
    summary     = data.get("summary","")

    all_issues_count = sum(len(v) for v in issues.values() if isinstance(v, list))
    critical_count   = len(issues.get("critical",[]))

    gauge   = gauge_svg(overall, 180)
    s_cards = score_cards_html(scores)
    radar   = radar_chart_js(scores) if scores else ""

    issues_sec = ""
    for prio in ["critical","high","medium","low"]:
        lst = issues.get(prio,[])
        if lst:
            issues_sec += issues_html(lst, prio)

    sections_html = ""
    for sec in sections:
        sections_html += section_card(
            sec.get("title","Section"),
            sec.get("score", 50),
            sec.get("findings",[]),
            sec.get("icon","📋")
        )

    actions_sec = actions_table(actions)

    quick_wins_html = ""
    if quick_wins:
        items = "".join(f'<li style="padding:6px 0;border-bottom:1px solid #1e293b;color:#cbd5e1;font-size:14px;">⚡ {w}</li>' for w in quick_wins)
        quick_wins_html = f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:20px;margin-bottom:20px;"><div style="font-size:16px;font-weight:700;color:#f1f5f9;margin-bottom:12px;">⚡ Quick Wins</div><ul style="list-style:none;padding:0;margin:0;">{items}</ul></div>'

    oc = score_color(overall)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>SEO Audit Report — {domain}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#020617;color:#e2e8f0;min-height:100vh;}}
  .topbar{{background:#0f172a;border-bottom:1px solid #1e293b;padding:14px 32px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:100;}}
  .logo{{font-size:18px;font-weight:800;color:#f1f5f9;letter-spacing:-.3px;}}
  .logo span{{color:#3b82f6;}}
  .btn{{display:inline-flex;align-items:center;gap:6px;padding:8px 18px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;border:none;text-decoration:none;transition:opacity .2s;}}
  .btn:hover{{opacity:.85;}}
  .btn-primary{{background:#3b82f6;color:white;}}
  .btn-secondary{{background:#1e293b;color:#cbd5e1;border:1px solid #334155;}}
  .btn-group{{display:flex;gap:8px;}}
  .hero{{background:linear-gradient(135deg,#0f172a 0%,#0c1220 100%);border-bottom:1px solid #1e293b;padding:48px 32px;}}
  .hero-inner{{max-width:1100px;margin:0 auto;display:flex;gap:48px;align-items:center;flex-wrap:wrap;}}
  .hero-gauge{{text-align:center;flex-shrink:0;}}
  .hero-info{{flex:1;min-width:280px;}}
  .hero-domain{{font-size:28px;font-weight:800;color:#f1f5f9;margin-bottom:6px;}}
  .hero-meta{{color:#64748b;font-size:14px;margin-bottom:16px;}}
  .hero-summary{{color:#94a3b8;font-size:15px;line-height:1.6;max-width:600px;}}
  .stat-pills{{display:flex;gap:12px;flex-wrap:wrap;margin-top:20px;}}
  .pill{{background:#1e293b;border:1px solid #334155;border-radius:20px;padding:6px 14px;font-size:13px;color:#94a3b8;}}
  .pill strong{{color:#f1f5f9;}}
  .main{{max-width:1100px;margin:0 auto;padding:32px;}}
  .section-title{{font-size:20px;font-weight:700;color:#f1f5f9;margin:32px 0 16px;padding-bottom:10px;border-bottom:1px solid #1e293b;}}
  .grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:20px;}}
  .radar-wrap{{background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:20px;}}
  @media print{{
    .topbar .btn-group{{display:none;}}
    body{{background:white;color:#1e293b;}}
    .topbar,.hero{{background:white!important;border-color:#e2e8f0!important;}}
    .hero-domain,.section-title{{color:#1e293b!important;}}
  }}
  @media(max-width:700px){{
    .hero-inner{{flex-direction:column;}}
    .grid-2{{grid-template-columns:1fr;}}
    .topbar{{flex-direction:column;gap:12px;}}
  }}
</style>
</head>
<body>

<div class="topbar">
  <div class="logo">SEO<span>.</span>Report</div>
  <div class="btn-group">
    <button class="btn btn-secondary" onclick="downloadHTML()">⬇ Download HTML</button>
    <button class="btn btn-primary" onclick="window.print()">🖨 Save as PDF</button>
  </div>
</div>

<div class="hero">
  <div class="hero-inner">
    <div class="hero-gauge">
      {gauge}
      <div style="color:#64748b;font-size:12px;margin-top:4px;">Overall SEO Score</div>
    </div>
    <div class="hero-info">
      <div class="hero-domain">{domain}</div>
      <div class="hero-meta">Audit Date: {audit_date} &nbsp;·&nbsp; Business Type: {business}</div>
      <div class="hero-summary">{summary}</div>
      <div class="stat-pills">
        <div class="pill">Issues: <strong style="color:#ef4444;">{all_issues_count}</strong></div>
        <div class="pill">Critical: <strong style="color:#ef4444;">{critical_count}</strong></div>
        <div class="pill">Actions: <strong style="color:#3b82f6;">{len(actions)}</strong></div>
      </div>
    </div>
  </div>
</div>

<div class="main">

  <div class="section-title">📊 Score Breakdown</div>
  {s_cards}

  <div class="grid-2">
    <div class="radar-wrap">
      <div style="font-size:15px;font-weight:700;color:#f1f5f9;margin-bottom:16px;">Radar Overview</div>
      {radar}
    </div>
    <div>
      {quick_wins_html}
    </div>
  </div>

  <div class="section-title">🚨 Issues Found</div>
  {issues_sec if issues_sec else '<p style="color:#475569;">No issues recorded.</p>'}

  {'<div class="section-title">📋 Detailed Analysis</div>' + sections_html if sections_html else ''}

  <div class="section-title">🎯 Action Plan</div>
  {actions_sec if actions_sec else '<p style="color:#475569;">No actions recorded.</p>'}

  <div style="text-align:center;padding:32px 0;color:#334155;font-size:13px;">
    Generated by claude-seo v1.9.0 &nbsp;·&nbsp; {audit_date}
  </div>

</div>

<script>
function downloadHTML(){{
  const blob = new Blob([document.documentElement.outerHTML],{{type:'text/html'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'seo-report-{domain.replace(".", "-")}.html';
  a.click();
}}
</script>

</body>
</html>"""


def demo_data(domain="example.com"):
    return {
        "domain": domain,
        "audit_date": datetime.now().strftime("%B %d, %Y"),
        "overall_score": 56,
        "business_type": "EdTech / FinTech",
        "summary": "The site has strong content and brand signals but is blocked to all crawlers including Googlebot. Fixing bot-protection, adding schema markup, and creating an llms.txt will unlock the largest ranking gains.",
        "scores": {
            "technical": 55,
            "content": 70,
            "on_page": 62,
            "schema": 28,
            "performance": 50,
            "ai_search": 46,
            "images": 50
        },
        "issues": {
            "critical": [
                {"title": "All crawlers blocked (HTTP 403)", "detail": "Googlebot, GPTBot, and Bingbot all receive 403. Whitelist verified bots in Cloudflare WAF.", "effort": "2 hrs"},
                {"title": "robots.txt returns 403", "detail": "Google requires robots.txt to be publicly readable.", "effort": "30 min"},
                {"title": "No schema markup on any page", "detail": "Zero JSON-LD detected. No rich result eligibility.", "effort": "2 hrs"},
            ],
            "high": [
                {"title": "/loaneligs — non-keyword URL", "detail": "Main CTA page has a zero-keyword URL slug. 301 redirect to /apply-education-loan-abroad.", "effort": "3 hrs"},
                {"title": "No AggregateRating schema", "detail": "JustDial 4.7★ 1,583 reviews not surfaced in SERP.", "effort": "1 hr"},
                {"title": "No llms.txt file", "detail": "ChatGPT, Perplexity, and Claude cannot prioritize your pages.", "effort": "1 hr"},
                {"title": "No Wikipedia article", "detail": "ChatGPT cites Wikipedia in 47.9% of responses. GyanDhan meets notability threshold.", "effort": "1 week"},
            ],
            "medium": [
                {"title": "No publication dates on blog articles", "detail": "Financial content (YMYL) needs visible 'Last updated' dates.", "effort": "2 hrs"},
                {"title": "discussions subdomain splits authority", "detail": "Move to /community or add canonical to consolidate link equity.", "effort": "2 days"},
                {"title": "City pages — doorway page risk", "detail": "30+ city pages may have swappable content. Enforce 60% unique content per city.", "effort": "1 week"},
            ],
            "low": [
                {"title": "No hreflang tags", "detail": "If Hindi or regional content is planned, add hreflang.", "effort": "Planning"},
                {"title": "No IndexNow implementation", "detail": "Instant indexing signal for Bing/Yandex.", "effort": "1 hr"},
            ]
        },
        "quick_wins": [
            "Whitelist Googlebot & GPTBot in Cloudflare (2 hrs → unblocks everything)",
            "Add Organization + FinancialService JSON-LD to homepage (2 hrs)",
            "Create llms.txt at root domain (1 hr)",
            "Add AggregateRating schema using JustDial 4.7★ data (1 hr)",
            "Claim Bing Places — powers ChatGPT, Copilot, Alexa (30 min)",
            "Claim Apple Business Connect — 27% consumer usage in 2026 (30 min)",
        ],
        "sections": [
            {
                "title": "Technical SEO", "score": 55, "icon": "⚙️",
                "findings": [
                    {"severity":"critical","text":"robots.txt and sitemap.xml both return 403"},
                    {"severity":"critical","text":"Cloudflare blocks Googlebot, GPTBot, PerplexityBot, ClaudeBot"},
                    {"severity":"high","text":"www vs non-www redirect not verified"},
                    {"severity":"high","text":"/loaneligs — non-descriptive, zero-keyword URL"},
                    {"severity":"medium","text":"discussions.gyandhan.com subdomain dilutes domain authority"},
                ]
            },
            {
                "title": "Content Quality", "score": 70, "icon": "📝",
                "findings": [
                    {"severity":"high","text":"No author bylines or credentials on blog posts (YMYL content)"},
                    {"severity":"high","text":"No 'Last updated' dates on financial articles"},
                    {"severity":"medium","text":"Blog URL structure inconsistent — mix of flat and subdirectory"},
                    {"severity":"info","text":"Good lender-specific pages with current year dates"},
                    {"severity":"info","text":"Active blog covering study abroad, loans, and exam prep"},
                ]
            },
            {
                "title": "Schema Markup", "score": 28, "icon": "🔗",
                "findings": [
                    {"severity":"critical","text":"No Organization or FinancialService schema on homepage"},
                    {"severity":"critical","text":"No AggregateRating schema — 4.7★ JustDial rating invisible to Google"},
                    {"severity":"critical","text":"No Article schema on any blog post"},
                    {"severity":"high","text":"No LoanOrCredit schema on lender pages"},
                    {"severity":"high","text":"No BreadcrumbList schema on any page"},
                ]
            },
            {
                "title": "AI Search (GEO)", "score": 46, "icon": "🤖",
                "findings": [
                    {"severity":"critical","text":"All AI crawlers likely blocked (GPTBot, ClaudeBot, PerplexityBot)"},
                    {"severity":"critical","text":"No llms.txt — AI crawlers have no content guidance"},
                    {"severity":"high","text":"No Wikipedia article — ChatGPT cites Wikipedia in 47.9% of answers"},
                    {"severity":"high","text":"No Reddit presence — Perplexity cites Reddit in 46.7% of results"},
                    {"severity":"medium","text":"Bing Places not confirmed — powers ChatGPT, Copilot, Alexa"},
                ]
            },
        ],
        "actions": [
            {"priority":"critical","action":"Whitelist Googlebot, GPTBot, PerplexityBot, Bingbot in Cloudflare WAF","effort":"2 hrs","impact":"Unblocks all indexing & AI crawling"},
            {"priority":"critical","action":"Make robots.txt publicly accessible (remove 403)","effort":"30 min","impact":"Required by Google guidelines"},
            {"priority":"critical","action":"Add Organization + FinancialService JSON-LD to homepage","effort":"2 hrs","impact":"Rich results eligibility"},
            {"priority":"critical","action":"Submit XML sitemap directly in Google Search Console","effort":"30 min","impact":"Accelerates URL discovery"},
            {"priority":"high","action":"301 redirect /loaneligs → /apply-education-loan-abroad","effort":"3 hrs","impact":"Keyword relevance + CTR lift"},
            {"priority":"high","action":"Create llms.txt at root domain","effort":"1 hr","impact":"AI search visibility across ChatGPT, Perplexity, Claude"},
            {"priority":"high","action":"Add AggregateRating schema (4.7★, 1583 reviews from JustDial)","effort":"1 hr","impact":"Star ratings in SERP"},
            {"priority":"high","action":"Claim Bing Places listing","effort":"30 min","impact":"ChatGPT + Copilot + Alexa data feed"},
            {"priority":"high","action":"Claim Apple Business Connect","effort":"30 min","impact":"27% consumer usage in 2026"},
            {"priority":"high","action":"Add Article + author schema to all blog posts","effort":"4 hrs","impact":"E-E-A-T for YMYL content"},
            {"priority":"medium","action":"Add Last Updated dates to all financial articles","effort":"2 hrs","impact":"Freshness + trust signals"},
            {"priority":"medium","action":"Audit 30+ city pages for doorway page risk","effort":"1 day","impact":"Prevents core update penalty"},
            {"priority":"medium","action":"Standardize blog URL structure (flat vs subdirectory)","effort":"1 week","impact":"Crawl efficiency"},
            {"priority":"low","action":"Create Wikipedia article via AfC process","effort":"1 week","impact":"ChatGPT citation in 47.9% of responses"},
            {"priority":"low","action":"Build Reddit presence in r/Indian_Academia, r/GRE","effort":"Ongoing","impact":"Perplexity citation signals"},
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="Generate SEO HTML Report")
    parser.add_argument("--data",   help="Path to audit JSON data file")
    parser.add_argument("--output", default="seo-report.html", help="Output HTML file path")
    parser.add_argument("--domain", default="example.com",     help="Domain name (used with --demo)")
    parser.add_argument("--demo",   action="store_true",        help="Generate demo report")
    args = parser.parse_args()

    if args.demo:
        data = demo_data(args.domain)
    elif args.data:
        with open(args.data) as f:
            data = json.load(f)
    else:
        data = demo_data(args.domain)

    html = generate_html(data)

    out = Path(args.output)
    out.write_text(html, encoding="utf-8")
    print(f"✓ Report saved → {out.resolve()}")
    print(f"  Open in browser: file://{out.resolve()}")


if __name__ == "__main__":
    main()
