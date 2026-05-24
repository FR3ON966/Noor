# -*- coding: utf-8 -*-
"""Smart AskUST Explorer - find all content pages and extract Q&A data"""
import requests
import urllib3
import sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin

sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()

BASE = "https://ustgate.ust.edu.sd"
session = requests.Session()
session.verify = False
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

visited = set()

def fetch(url):
    """Fetch a URL and return soup"""
    try:
        r = session.get(url, timeout=15)
        r.encoding = 'utf-8'
        return BeautifulSoup(r.text, 'lxml'), r.text
    except Exception as e:
        print(f"  ❌ Error fetching {url}: {e}")
        return None, ""

def extract_text(soup):
    """Extract meaningful text from a page"""
    # Remove script and style tags
    for tag in soup(['script', 'style', 'meta', 'link']):
        tag.decompose()
    text = soup.get_text(separator='\n', strip=True)
    # Filter out short/empty lines
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 5]
    return lines

def find_links(soup, base_url):
    """Find all internal links"""
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        full = urljoin(base_url, href)
        if 'ustgate.ust.edu.sd' in full or 'ust.edu.sd' in full:
            links.add(full)
    return links

# === PHASE 1: Explore main AskUST pages ===
print("=" * 70)
print("🔍 PHASE 1: Exploring AskUST site structure")
print("=" * 70)

urls_to_try = [
    f"{BASE}/askust/",
    f"{BASE}/askust/Default.aspx",
    f"{BASE}/askust/qzanswers/",
    f"{BASE}/askust/qzanswers/ans_out",
    f"{BASE}/askust/qzanswers/ans_out.aspx",
    f"{BASE}/askust/qzanswers/Default.aspx",
    f"{BASE}/askust/qzanswers/ans_in",
    f"{BASE}/askust/qzanswers/ans_in.aspx",
    f"{BASE}/askust/qzanswers/qz_out",
    f"{BASE}/askust/qzanswers/qz_out.aspx",
    f"{BASE}/askust/qzanswers/qz_in",
    f"{BASE}/askust/qzanswers/qz_in.aspx",
]

all_links = set()
for url in urls_to_try:
    print(f"\n📄 Trying: {url}")
    soup, raw = fetch(url)
    if not soup:
        continue
    
    # Get page title
    title = soup.title.string if soup.title else "No title"
    print(f"  Title: {title}")
    
    # Extract text content
    lines = extract_text(soup)
    arabic_lines = [l for l in lines if any('\u0600' <= c <= '\u06FF' for c in l)]
    
    if arabic_lines:
        print(f"  📝 Found {len(arabic_lines)} Arabic content lines:")
        for line in arabic_lines[:15]:
            print(f"    → {line[:100]}")
    
    # Find links
    links = find_links(soup, url)
    new_links = links - visited - set(urls_to_try)
    if new_links:
        print(f"  🔗 Found {len(new_links)} new links:")
        for l in list(new_links)[:10]:
            print(f"    → {l}")
    all_links.update(links)
    visited.add(url)

# === PHASE 2: Check for GridView or data content ===
print("\n\n" + "=" * 70)
print("🔍 PHASE 2: Looking for ASP.NET data controls and forms")
print("=" * 70)

soup, raw = fetch(f"{BASE}/askust/qzanswers/ans_out")
if soup:
    # Look for GridView, Repeater, DataList etc
    for tag_name in ['table', 'div', 'span']:
        tags = soup.find_all(tag_name, id=True)
        for tag in tags:
            tag_id = tag.get('id', '')
            if any(kw in tag_id.lower() for kw in ['grid', 'data', 'content', 'panel', 'label', 'gv', 'rpt', 'list']):
                inner = tag.get_text(strip=True)[:200]
                print(f"  🎯 {tag_name}#{tag_id}: {inner if inner else '(empty)'}")
    
    # Look for ViewState and form action to understand postback
    form = soup.find('form')
    if form:
        print(f"\n  Form action: {form.get('action')}")
        # Hidden fields
        hiddens = soup.find_all('input', type='hidden')
        print(f"  Hidden fields: {len(hiddens)}")
        for h in hiddens:
            name = h.get('name', '')
            val = h.get('value', '')[:50]
            print(f"    - {name}: {val}...")
    
    # Look for buttons that might load content
    buttons = soup.find_all(['input', 'button'], type=['submit', 'button'])
    for btn in buttons:
        print(f"  🔘 Button: {btn.get('name', '')} | {btn.get('value', '')}")

# === PHASE 3: Try the main UST website for FAQ content ===
print("\n\n" + "=" * 70)
print("🔍 PHASE 3: Exploring main UST website for knowledge")
print("=" * 70)

main_urls = [
    "https://www.ust.edu.sd/ar/",
    "https://www.ust.edu.sd/ar/about/",
    "https://www.ust.edu.sd/ar/faculties/",
    "https://www.ust.edu.sd/ar/admission/",
    "https://portal.ust.edu.sd/",
    "https://reg.ust.edu.sd/",
]

for url in main_urls:
    print(f"\n📄 Trying: {url}")
    soup, raw = fetch(url)
    if not soup:
        continue
    title = soup.title.string if soup.title else "No title"
    print(f"  Title: {title}")
    lines = extract_text(soup)
    arabic_lines = [l for l in lines if any('\u0600' <= c <= '\u06FF' for c in l)]
    if arabic_lines:
        print(f"  📝 {len(arabic_lines)} Arabic lines (first 10):")
        for line in arabic_lines[:10]:
            print(f"    → {line[:120]}")

print("\n\n✅ Exploration complete!")
