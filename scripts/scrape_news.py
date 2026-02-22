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

SOURCES = [
    # --- DAILY MAIL ---
    {"name": "Daily Mail Sport", "url": "https://www.dailymail.co.uk/sport/index.rss", "category": "Sports"},
    {"name": "Daily Mail Boxing", "url": "https://www.dailymail.co.uk/sport/boxing/index.rss", "category": "Sports"},
    
    # --- THE SUN ---
    {"name": "The Sun - Sport", "url": "https://www.thesun.co.uk/sport/feed/", "category": "Sports"},
    {"name": "The Sun - Football", "url": "https://www.thesun.co.uk/sport/football/feed/", "category": "Sports"},
    {"name": "The Sun - News", "url": "https://www.thesun.co.uk/news/feed/", "category": "General"},

    # --- THE MIRROR ---
    {"name": "Mirror Sport", "url": "https://www.mirror.co.uk/sport/rss.xml", "category": "Sports"},
    {"name": "Mirror Football", "url": "https://www.mirror.co.uk/sport/football/rss.xml", "category": "Sports"},
    {"name": "Mirror News", "url": "https://www.mirror.co.uk/news/rss.xml", "category": "General"},

    # --- GLOBAL & TECH ---
    {"name": "ESPN", "url": "https://www.espn.com/espn/rss/news", "category": "Sports"},
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/rss.xml", "category": "General"},
    {"name": "Reuters Global", "url": "https://news.google.com/rss/search?q=world+news+when:24h", "category": "World"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "Tech"},
]

def get_random_headers():
    """Generates fresh headers and random referers for every request."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": random.choice(["https://www.google.com/", "https://twitter.com/", "https://www.bing.com/"]),
        "Accept-Language": "en-US,en;q=0.5",
    }

def get_image(entry):
    url = None
    link = entry.get('link', '')

    # 1. RSS MEDIA TAGS (Fastest)
    if 'media_content' in entry and len(entry.media_content) > 0:
        url = entry.media_content[0].get('url')
    elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
        url = entry.media_thumbnail[-1].get('url')

    # 2. AT-ALL-COSTS DEEP SCRAPE (For Mirror, Sun, and ESPN Video)
    if not url or "unsplash" in url:
        try:
            # Human Delay: Mimics a user 'clicking' and 'scrolling'
            time.sleep(random.uniform(2.0, 4.0)) 
            
            resp = requests.get(link, timeout=10, headers=get_random_headers())
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Check Meta (OG) tags
                meta = soup.find("meta", property="og:image") or soup.find("meta", name="twitter:image")
                if meta:
                    url = meta.get("content")
                
                # Check JSON-LD (Common in Mirror/Daily Mail for video/top stories)
                if not url:
                    scripts = soup.find_all("script", type="application/ld+json")
                    for s in scripts:
                        try:
                            data = json.loads(s.string)
                            if 'image' in data:
                                if isinstance(data['image'], dict): url = data['image'].get('url')
                                else: url = data['image']
                                break
                        except: continue
        except: pass

    # 3. SPEED & SPINNER FIX: Image Resizing
    if url and isinstance(url, str) and len(url) > 10:
        # Clean the URL
        url = url.split('?')[0]
        if url.startswith('//'): url = 'https:' + url
        
        # Mirror/Sun often use massive URLs. We shrink them for Flutter.
        url = re.sub(r'/\d+x\d+/', '/600x450/', url)
        if "espn" in url: url += "?width=600"
        if "thesun.co.uk" in url: url = url.replace("original", "thumbnail")
        
        return url
    
    # Solid default if nothing works
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600&q=80"

# --- EXECUTION ---
all_articles = []
seen_links = set()

for src in SOURCES:
    print(f"🔄 Scrutinizing {src['name']}...")
    try:
        # Rotate user identity for the RSS fetch
        feedparser.USER_AGENT = random.choice(USER_AGENTS)
        feed = feedparser.parse(src['url'])
        
        # Take top 10 to keep the Flutter JSON fast
        for entry in feed.entries[:10]:
            link = entry.get('link', '')
            if not link or link in seen_links: continue
            
            # Deep Scrape occurs here with human delays
            img = get_image(entry)
            
            all_articles.append({
                "id": link,
                "title": entry.get('title', 'No Title'),
                "imageUrl": img,
                "source": src['name'],
                "category": src['category'],
                "link": link,
                "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "isSaved": 0
            })
            seen_links.add(link)
            
    except Exception as e:
        print(f"❌ Error with {src['name']}: {e}")

# Save results for your Flutter App
with open(f'{DATA_DIR}/news.json', 'w', encoding='utf-8') as f:
    json.dump(all_articles, f, indent=4, ensure_ascii=False)

print(f"✅ SUCCESS! {len(all_articles)} items ready for Flutter.")
