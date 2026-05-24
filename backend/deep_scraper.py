# -*- coding: utf-8 -*-
"""
Deep AskUST Scraper - Extract ALL knowledge from UST inquiry system
Strategy:
1. Scrape ustanswers.aspx (likely has all Q&A)
2. Scrape ustanser_stud.aspx (student-specific answers)
3. Try ASP.NET postbacks on main page to load category content
4. Scrape portal.ust.edu.sd for services info
5. Save everything as clean knowledge base
"""
import requests, urllib3, sys, re, json, time
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

all_knowledge = []

def fetch(url, method='GET', data=None):
    try:
        if method == 'POST':
            r = session.post(url, data=data, timeout=20)
        else:
            r = session.get(url, timeout=20)
        r.encoding = 'utf-8'
        return BeautifulSoup(r.text, 'lxml'), r.text
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None, ""

def clean_text(text):
    """Clean extracted text"""
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_qa_content(soup, source_name):
    """Extract Q&A pairs or general content from a page"""
    items = []
    
    # Method 1: Look for Q&A pairs in tables
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            text_parts = []
            for cell in cells:
                t = clean_text(cell.get_text())
                if t and len(t) > 3 and any('\u0600' <= c <= '\u06FF' for c in t):
                    text_parts.append(t)
            if text_parts:
                combined = ' | '.join(text_parts)
                if combined not in [item['content'] for item in items]:
                    items.append({'content': combined, 'source': source_name})
    
    # Method 2: Look for divs with class containing 'answer', 'content', 'panel'
    for div in soup.find_all(['div', 'span', 'p', 'label']):
        text = clean_text(div.get_text())
        if text and len(text) > 10 and any('\u0600' <= c <= '\u06FF' for c in text):
            # Skip if it's just a container with children we've already processed
            if len(div.find_all(['div', 'span', 'p'])) > 3:
                continue
            if text not in [item['content'] for item in items]:
                items.append({'content': text, 'source': source_name})
    
    # Method 3: Look for input fields with Arabic values (ASP.NET pattern)
    for inp in soup.find_all('input', type='text'):
        val = inp.get('value', '')
        if val and len(val) > 5 and any('\u0600' <= c <= '\u06FF' for c in val):
            items.append({'content': val, 'source': source_name})
    
    # Method 4: Look for links with content
    for a in soup.find_all('a'):
        text = clean_text(a.get_text())
        href = a.get('href', '')
        if text and len(text) > 5 and any('\u0600' <= c <= '\u06FF' for c in text):
            entry = text
            if href and href.startswith('http'):
                entry = f"{text} (رابط: {href})"
            if entry not in [item['content'] for item in items]:
                items.append({'content': entry, 'source': source_name})
    
    return items

def try_aspnet_postback(url, soup, event_target):
    """Try to simulate an ASP.NET postback to load content"""
    form = soup.find('form')
    if not form:
        return None, ""
    
    data = {}
    for inp in soup.find_all('input', type='hidden'):
        name = inp.get('name', '')
        val = inp.get('value', '')
        if name:
            data[name] = val
    
    data['__EVENTTARGET'] = event_target
    data['__EVENTARGUMENT'] = ''
    
    action = form.get('action', url)
    full_url = urljoin(url, action)
    
    return fetch(full_url, method='POST', data=data)

# ══════════════════════════════════════════
# PHASE 1: Scrape the main AskUST page
# ══════════════════════════════════════════
print("=" * 70)
print("📚 PHASE 1: Main AskUST Page")
print("=" * 70)

soup, raw = fetch(f"{BASE}/askust/")
if soup:
    items = extract_qa_content(soup, "askust_main")
    print(f"  Found {len(items)} content items")
    all_knowledge.extend(items)
    
    # Find all clickable elements (buttons, links) that might load content
    buttons = soup.find_all(['a', 'input', 'button'])
    clickable_targets = []
    for btn in buttons:
        href = btn.get('href', '')
        if 'javascript:__doPostBack' in href:
            # Extract event target from __doPostBack('target','arg')
            match = re.search(r"__doPostBack\('([^']+)'", href)
            if match:
                target = match.group(1)
                text = clean_text(btn.get_text())
                clickable_targets.append((target, text))
                print(f"  🔘 PostBack: {target} → {text}")

    # Try clicking each category via postback
    print(f"\n  🔄 Trying {len(clickable_targets)} postback targets...")
    for target, label in clickable_targets:
        print(f"\n  📂 Loading category: {label}")
        cat_soup, cat_raw = try_aspnet_postback(f"{BASE}/askust/Default.aspx", soup, target)
        if cat_soup:
            cat_items = extract_qa_content(cat_soup, f"askust_{label}")
            new_items = [i for i in cat_items if i['content'] not in [k['content'] for k in all_knowledge]]
            print(f"    Found {len(new_items)} new items")
            all_knowledge.extend(new_items)
            # Save the soup for further postbacks within this category
            
            # Look for sub-category postbacks
            sub_buttons = cat_soup.find_all(['a', 'input', 'button'])
            for sub_btn in sub_buttons:
                sub_href = sub_btn.get('href', '')
                if 'javascript:__doPostBack' in sub_href:
                    sub_match = re.search(r"__doPostBack\('([^']+)'", sub_href)
                    if sub_match:
                        sub_target = sub_match.group(1)
                        sub_text = clean_text(sub_btn.get_text())
                        if sub_target != target and sub_text and len(sub_text) > 3:
                            print(f"    📄 Sub-category: {sub_text}")
                            sub_soup, _ = try_aspnet_postback(f"{BASE}/askust/Default.aspx", cat_soup, sub_target)
                            if sub_soup:
                                sub_items = extract_qa_content(sub_soup, f"askust_{label}_{sub_text}")
                                new_sub = [i for i in sub_items if i['content'] not in [k['content'] for k in all_knowledge]]
                                print(f"      Found {len(new_sub)} new items")
                                all_knowledge.extend(new_sub)
                            time.sleep(0.3)
        time.sleep(0.5)

# ══════════════════════════════════════════
# PHASE 2: Scrape ustanswers.aspx
# ══════════════════════════════════════════
print("\n\n" + "=" * 70)
print("📚 PHASE 2: ustanswers.aspx")
print("=" * 70)

soup2, raw2 = fetch(f"{BASE}/askust/ustanswers.aspx")
if soup2:
    items2 = extract_qa_content(soup2, "ustanswers")
    new2 = [i for i in items2 if i['content'] not in [k['content'] for k in all_knowledge]]
    print(f"  Found {len(new2)} new items")
    all_knowledge.extend(new2)

# ══════════════════════════════════════════
# PHASE 3: Scrape ustanser_stud.aspx
# ══════════════════════════════════════════
print("\n\n" + "=" * 70)
print("📚 PHASE 3: ustanser_stud.aspx")
print("=" * 70)

soup3, raw3 = fetch(f"{BASE}/askust/ustanser_stud.aspx")
if soup3:
    items3 = extract_qa_content(soup3, "ustanser_stud")
    new3 = [i for i in items3 if i['content'] not in [k['content'] for k in all_knowledge]]
    print(f"  Found {len(new3)} new items")
    all_knowledge.extend(new3)

# ══════════════════════════════════════════
# PHASE 4: Scrape qzanswers/ans_out with postbacks
# ══════════════════════════════════════════
print("\n\n" + "=" * 70)
print("📚 PHASE 4: qzanswers/ans_out")
print("=" * 70)

soup4, raw4 = fetch(f"{BASE}/askust/qzanswers/ans_out")
if soup4:
    items4 = extract_qa_content(soup4, "qzanswers_ans_out")
    new4 = [i for i in items4 if i['content'] not in [k['content'] for k in all_knowledge]]
    print(f"  Found {len(new4)} new items")
    all_knowledge.extend(new4)
    
    # Try postbacks here too
    for btn in soup4.find_all(['a', 'input', 'button']):
        href = btn.get('href', '')
        if 'javascript:__doPostBack' in href:
            match = re.search(r"__doPostBack\('([^']+)'", href)
            if match:
                target = match.group(1)
                text = clean_text(btn.get_text())
                print(f"  🔘 PostBack: {text}")
                pb_soup, _ = try_aspnet_postback(f"{BASE}/askust/qzanswers/ans_out", soup4, target)
                if pb_soup:
                    pb_items = extract_qa_content(pb_soup, f"qzanswers_{text}")
                    new_pb = [i for i in pb_items if i['content'] not in [k['content'] for k in all_knowledge]]
                    print(f"    Found {len(new_pb)} new items")
                    all_knowledge.extend(new_pb)
                time.sleep(0.3)

# ══════════════════════════════════════════
# PHASE 5: Scrape portal.ust.edu.sd
# ══════════════════════════════════════════
print("\n\n" + "=" * 70)
print("📚 PHASE 5: portal.ust.edu.sd")
print("=" * 70)

soup5, raw5 = fetch("https://portal.ust.edu.sd/")
if soup5:
    items5 = extract_qa_content(soup5, "portal_ust")
    new5 = [i for i in items5 if i['content'] not in [k['content'] for k in all_knowledge]]
    print(f"  Found {len(new5)} new items")
    all_knowledge.extend(new5)

# ══════════════════════════════════════════
# SAVE RESULTS
# ══════════════════════════════════════════
print("\n\n" + "=" * 70)
print("💾 SAVING KNOWLEDGE BASE")
print("=" * 70)

# Filter out short/useless items
useful = [k for k in all_knowledge if len(k['content']) > 15]

# Remove duplicates
seen = set()
unique = []
for k in useful:
    if k['content'] not in seen:
        seen.add(k['content'])
        unique.append(k)

print(f"  Total unique items: {len(unique)}")

# Save as JSON
with open('../data/askust_knowledge.json', 'w', encoding='utf-8') as f:
    json.dump(unique, f, ensure_ascii=False, indent=2)
print("  ✅ Saved to data/askust_knowledge.json")

# Save as plain text for knowledge base
with open('../data/askust_knowledge.txt', 'w', encoding='utf-8') as f:
    current_source = ""
    for item in unique:
        if item['source'] != current_source:
            current_source = item['source']
            f.write(f"\n{'='*60}\n")
            f.write(f"المصدر: {current_source}\n")
            f.write(f"{'='*60}\n\n")
        f.write(f"• {item['content']}\n\n")
print("  ✅ Saved to data/askust_knowledge.txt")

# Print sample
print(f"\n📋 Sample of extracted knowledge:")
for item in unique[:20]:
    print(f"  [{item['source']}] {item['content'][:120]}")

print(f"\n🎉 DONE! Total knowledge items: {len(unique)}")
