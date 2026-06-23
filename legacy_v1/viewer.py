"""
viewer.py — CloudMatchAI Job Viewer
Run this any time after main.py to get:
  1. jobs_export.csv   — open in Excel
  2. jobs_viewer.html  — open in any browser
"""

import csv
import sqlite3
import webbrowser
import os
from datetime import datetime

DB_FILE = "jobs.db"
CSV_FILE = "jobs_export.csv"
HTML_FILE = "jobs_viewer.html"


def fetch_jobs():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT title, company, location, url, score, description, scraped_at
        FROM jobs
        ORDER BY score DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def export_csv(rows):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Company", "Location", "URL", "Score", "Description", "Scraped At"])
        writer.writerows(rows)
    print(f"[+] CSV saved: {CSV_FILE}")


def export_html(rows):
    rows_html = ""
    for title, company, location, url, score, description, scraped_at in rows:
        badge_color = "#22c55e" if score >= 60 else "#f59e0b" if score >= 30 else "#6b7280"
        desc_safe = (description or "").replace("<", "&lt;").replace(">", "&gt;")
        url_safe = url or "#"
        rows_html += f"""
        <tr>
          <td><a href="{url_safe}" target="_blank">{title}</a></td>
          <td>{company}</td>
          <td>{location}</td>
          <td><span class="badge" style="background:{badge_color}">{score}</span></td>
          <td class="desc">{desc_safe}</td>
          <td class="ts">{scraped_at[:10] if scraped_at else ""}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CloudMatchAI — Job Viewer</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; padding: 24px; }}
  h1 {{ font-size: 1.5rem; margin-bottom: 4px; color: #38bdf8; }}
  p.sub {{ color: #94a3b8; font-size: 0.85rem; margin-bottom: 16px; }}
  .toolbar {{ display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }}
  input, select {{ background: #1e293b; border: 1px solid #334155; color: #e2e8f0;
                   padding: 8px 12px; border-radius: 6px; font-size: 0.9rem; }}
  input {{ width: 280px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
  thead th {{ background: #1e293b; padding: 10px 12px; text-align: left;
              color: #94a3b8; font-weight: 600; cursor: pointer; user-select: none; }}
  thead th:hover {{ color: #38bdf8; }}
  tbody tr {{ border-bottom: 1px solid #1e293b; }}
  tbody tr:hover {{ background: #1e293b; }}
  td {{ padding: 10px 12px; vertical-align: top; }}
  td a {{ color: #38bdf8; text-decoration: none; }}
  td a:hover {{ text-decoration: underline; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px;
            font-size: 0.75rem; font-weight: 700; color: white; }}
  .desc {{ color: #94a3b8; font-size: 0.8rem; max-width: 340px; }}
  .ts {{ color: #64748b; font-size: 0.8rem; white-space: nowrap; }}
  #count {{ color: #94a3b8; font-size: 0.85rem; margin-bottom: 10px; }}
</style>
</head>
<body>
<h1>☁️ CloudMatchAI</h1>
<p class="sub">Generated {datetime.utcnow().strftime("%Y-%m-%d %H:%M")} UTC &nbsp;|&nbsp; {len(rows)} total jobs</p>

<div class="toolbar">
  <input type="text" id="search" placeholder="Search title, company, location..." oninput="filterTable()">
  <select id="minScore" onchange="filterTable()">
    <option value="0">All scores</option>
    <option value="30">Score ≥ 30</option>
    <option value="50">Score ≥ 50</option>
    <option value="70">Score ≥ 70</option>
  </select>
  <select id="remoteOnly" onchange="filterTable()">
    <option value="0">All locations</option>
    <option value="1">Remote only</option>
  </select>
</div>

<div id="count"></div>

<table id="jobTable">
  <thead>
    <tr>
      <th onclick="sortTable(0)">Title ↕</th>
      <th onclick="sortTable(1)">Company ↕</th>
      <th onclick="sortTable(2)">Location ↕</th>
      <th onclick="sortTable(3)">Score ↕</th>
      <th>Snippet</th>
      <th onclick="sortTable(5)">Date ↕</th>
    </tr>
  </thead>
  <tbody id="tbody">
    {rows_html}
  </tbody>
</table>

<script>
let sortDir = {{}};

function filterTable() {{
  const q = document.getElementById('search').value.toLowerCase();
  const minScore = parseInt(document.getElementById('minScore').value);
  const remoteOnly = document.getElementById('remoteOnly').value === '1';
  const rows = document.querySelectorAll('#tbody tr');
  let visible = 0;
  rows.forEach(row => {{
    const text = row.innerText.toLowerCase();
    const score = parseInt(row.cells[3].innerText) || 0;
    const isRemote = text.includes('remote');
    const show = text.includes(q) && score >= minScore && (!remoteOnly || isRemote);
    row.style.display = show ? '' : 'none';
    if (show) visible++;
  }});
  document.getElementById('count').textContent = visible + ' jobs shown';
}}

function sortTable(col) {{
  const tbody = document.getElementById('tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  sortDir[col] = !sortDir[col];
  rows.sort((a, b) => {{
    let av = a.cells[col].innerText.trim();
    let bv = b.cells[col].innerText.trim();
    const an = parseFloat(av), bn = parseFloat(bv);
    if (!isNaN(an) && !isNaN(bn)) return sortDir[col] ? an - bn : bn - an;
    return sortDir[col] ? av.localeCompare(bv) : bv.localeCompare(av);
  }});
  rows.forEach(r => tbody.appendChild(r));
  filterTable();
}}

filterTable();
</script>
</body>
</html>"""

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[+] HTML viewer saved: {HTML_FILE}")


def main():
    rows = fetch_jobs()
    if not rows:
        print("[!] No jobs in database yet. Run main.py first.")
        return
    print(f"[*] Exporting {len(rows)} jobs...")
    export_csv(rows)
    export_html(rows)
    webbrowser.open(f"file:///{os.path.abspath(HTML_FILE).replace(chr(92), '/')}")
    print("[*] Opened viewer in browser!")


if __name__ == "__main__":
    main()
