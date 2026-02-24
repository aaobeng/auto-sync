import feedparser
import json
import datetime
import os
import time
import re
import requests
import random
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Realistic browser pool to mimic different devices
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
]

# Cleanly organized sources with specific categories
SOURCES = [
    # ==========================================
    # FOOTBALL
    # ==========================================
    {"name": "The Sun - Football", "url": "https://www.thesun.co.uk/sport/football/feed/", "category": "Football"},
    {"name": "Mirror Football", "url": "https://www.mirror.co.uk/sport/football/rss.xml", "category": "Football"},

    # ==========================================
    # OTHER SPORTS & BOXING
    # ==========================================
    {"name": "Daily Mail Sport", "url": "https://www.dailymail.co.uk/sport/index.rss", "category": "Sports"},
    {"name": "Mirror Sport", "url": "https://www.mirror.co.uk/sport/rss.xml", "category": "Sports"},
    {"name": "ESPN", "url": "https://www.espn.com/espn/rss/news", "category": "Sports"},
    {"name": "Daily Mail Boxing", "url": "https://www.dailymail.co.uk/sport/boxing/index.rss", "category": "Boxing"},

    # ==========================================
    # GENERAL & WORLD NEWS
    # ==========================================
    {"name": "The Sun - News", "url": "https://www.thesun.co.uk/news/feed/", "category": "News"},
    {"name": "Mirror News", "url": "https://www.mirror.co.uk/news/rss.xml", "category": "News"},
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/rss.xml", "category": "News"},
    {"name": "Reuters Global", "url": "https://news.google.com/rss/search?q=world+news+when:24h", "category": "World"},

    # ==========================================
    # REGIONAL & TECH
    # ==========================================
    {"name": "Modern Ghana News", "url": "https://www.modernghana.com/rss/news", "category": "Ghana News"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "Tech"},
]

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": random.choice(["https://www.google.com/", "https://twitter.com/", "https://www.bing.com/"]),
        "Accept-Language": "en-US,en;q=0.5",
    }

def get_image(entry):
    url = None
    link = entry.get('link', '')

    # 1. RSS MEDIA TAGS
    if 'media_content' in entry and len(entry.media_content) > 0:
        url = entry.media_content[0].get('url')
    elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
        url = entry.media_thumbnail[-1].get('url')

    # 2. AT-ALL-COSTS DEEP SCRAPE
    if not url or "unsplash" in url:
        try:
            time.sleep(random.uniform(2.0, 4.0)) 
            
            resp = requests.get(link, timeout=10, headers=get_random_headers())
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                meta = soup.find("meta", property="og:image") or soup.find("meta", name="twitter:image")
                if meta:
                    url = meta.get("content")
                
                if not url:
                    hidden_images = re.findall(r'(https://a\d?\.espncdn\.com/[^"\']+\.(?:jpg|png))', resp.text)
                    if hidden_images:
                        for img in hidden_images:
                            if '16x9' in img or 'picture' in img:
                                url = img
                                break
                        if not url: url = hidden_images[0]

                if not url:
                    scripts = soup.find_all("script", type="application/ld+json")
                    for s in scripts:
                        try:
                            data = json.loads(s.string)
                            items = data if isinstance(data, list) else [data]
                            for item in items:
                                if 'image' in item:
                                    url = item['image'].get('url') if isinstance(item['image'], dict) else item['image']
                                    break
                            if url: break
                        except: continue
        except: pass

    # 3. SPEED & SPINNER FIX
    if url and isinstance(url, str) and len(url) > 10:
        url = url.split('?')[0] 
        if url.startswith('//'): url = 'https:' + url
        
        url = re.sub(r'/\d+x\d+/', '/400x300/', url)
        if "espn" in url: url += "?width=400"
        if "thesun.co.uk" in url: url = url.replace("original", "thumbnail")
        
        return url
    
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400&q=80"

# --- EXECUTION ---

# Prepare the dictionary for grouped categories
grouped_articles = {
    "Football": [],
    "News": [],
    "Boxing": [],
    "Sports": [],
    "Ghana News": [],
    "World": [],
    "Tech": []
}

seen_links = set()
total_items = 0

for src in SOURCES:
    print(f"🔄 Scrutinizing {src['name']}...")
    try:
        feedparser.USER_AGENT = random.choice(USER_AGENTS)
        feed = feedparser.parse(src['url'])
        
        for entry in feed.entries[:10]:
            link = entry.get('link', '')
            if not link or link in seen_links: continue
            
            img = get_image(entry)
            
            # --- THE TIMESTAMP FIX ---
            # Try to grab the official publish time and convert it to a clean string
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_time = datetime.datetime.fromtimestamp(time.mktime(entry.published_parsed)).strftime('%Y-%m-%d %H:%M:%S')
            else:
                # Fallback to sync time only if the RSS feed is broken
                published_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            article_data = {
                "id": link,
                "title": entry.get('title', 'No Title'),
                "imageUrl": img,
                "source": src['name'],
                "category": src['category'],
                "link": link,
                "timestamp": published_time, 
                "isSaved": 0
            }
            
            # Group by category
            cat = src['category']
            if cat not in grouped_articles:
                grouped_articles[cat] = []
                
            grouped_articles[cat].append(article_data)
            
            seen_links.add(link)
            total_items += 1
            
    except Exception as e:
        print(f"❌ Error with {src['name']}: {e}")

# Final JSON Save
with open(f'{DATA_DIR}/news.json', 'w', encoding='utf-8') as f:
    json.dump(grouped_articles, f, indent=4, ensure_ascii=False)

print(f"✅ SUCCESS! {total_items} items processed and grouped by category.")
