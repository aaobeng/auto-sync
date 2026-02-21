import feedparser
import json
import datetime
import os
import time
import re

# --- THE FIX FOR BLOCKED SOURCES ---
feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

if not os.path.exists('data'):
    os.makedirs('data')

# UPDATED SOURCES LIST (CNN Removed, Robust World Coverage Added)
SOURCES = [
    # --- GENERAL & WORLD ---
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/rss.xml", "category": "General"},
    {"name": "The Guardian", "url": "https://www.theguardian.com/world/rss", "category": "General"},
    {"name": "NYT Home", "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml", "category": "General"},
    {"name": "Reuters Global", "url": "https://news.google.com/rss/search?q=world+news+when:24h", "category": "World"},
    {"name": "AP News", "url": "https://news.google.com/rss/search?q=AP+Top+News+when:24h", "category": "World"},
    {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml", "category": "World"},

    # --- SPORTS ---
    {"name": "ESPN", "url": "https://www.espn.com/espn/rss/news", "category": "Sports"},
    {"name": "Sky Sports", "url": "https://www.skysports.com/rss/12040", "category": "Sports"},
    {"name": "Fox Sports", "url": "https://api.foxsports.com/v2/content/optimized-rss?partnerKey=MB0ByRq3p6W9bsY&size=30", "category": "Sports"},
    {"name": "Yahoo Sports", "url": "https://sports.yahoo.com/rss/", "category": "Sports"},

    # --- TECH & SCIENCE ---
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "Tech"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "category": "Tech"},
    {"name": "Wired", "url": "https://www.wired.com/feed/rss", "category": "Tech"},
    {"name": "NASA News", "url": "https://www.nasa.gov/news-release/feed/", "category": "Science"},
    {"name": "Space.com", "url": "https://www.space.com/feeds/all", "category": "Science"},

    # --- GAMING ---
    {"name": "IGN", "url": "https://feeds.ign.com/ign/news", "category": "Gaming"},
    {"name": "Polygon", "url": "https://www.polygon.com/rss/index.xml", "category": "Gaming"},
    {"name": "GameSpot", "url": "https://www.gamespot.com/feeds/news/", "category": "Gaming"},
    {"name": "Kotaku", "url": "https://kotaku.com/rss", "category": "Gaming"},

    # --- BUSINESS ---
    {"name": "CNBC Business", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?profile=120000000&id=10001147", "category": "Business"},
    {"name": "Fortune", "url": "https://fortune.com/feed/fortune-feeds/?id=3230629", "category": "Business"},
    {"name": "Investing.com", "url": "https://www.investing.com/rss/news.rss", "category": "Business"},

    # --- MOVIES & ENTERTAINMENT ---
    {"name": "Variety", "url": "https://variety.com/feed/", "category": "Movies"},
    {"name": "CinemaBlend", "url": "https://www.cinemablend.com/rss/news", "category": "Movies"},
    {"name": "The Hollywood Reporter", "url": "https://www.hollywoodreporter.com/feed/", "category": "Movies"},
]

def get_real_time(entry):
    try:
        ts = entry.get('published_parsed') or entry.get('updated_parsed')
        if ts: return datetime.datetime.fromtimestamp(time.mktime(ts)).strftime('%Y-%m-%d %H:%M:%S')
    except: pass
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_image(entry):
    url = None
    # 1. Media Content (highest priority)
    if 'media_content' in entry and len(entry.media_content) > 0:
        url = entry.media_content[0].get('url')
    # 2. Thumbnails
    elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
        url = entry.media_thumbnail[-1].get('url')
    # 3. Enclosures (Fix for Yahoo Sports/ESPN)
    elif 'enclosures' in entry:
        for e in entry.enclosures:
            if 'image' in e.get('type',''):
                url = e.get('href')
                break
    # 4. Regex for HTML summaries (Fix for white boxes/missing tags)
    if not url:
        txt = entry.get('summary','') + entry.get('content',[{}])[0].get('value','')
        m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', txt)
        if m: url = m.group(1)
    
    if url:
        url = url.split('?')[0] # Clean trackers
        url = re.sub(r'/\d+x\d+/', '/800x600/', url) # Fix resolution
        return url
    
    # Modernized fallback image
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=800&q=80"

all_articles = []
seen_links = set()

for src in SOURCES:
    print(f"Scraping {src['name']}...")
    try:
        feed = feedparser.parse(src['url'])
        for entry in feed.entries[:25]:
            link = entry.get('link', '')
            if not link or link in seen_links: continue
            
            article_time_str = get_real_time(entry)
            article_time = datetime.datetime.strptime(article_time_str, '%Y-%m-%d %H:%M:%S')
            
            # Keep articles from last 48 hours
            if (datetime.datetime.now() - article_time).total_seconds() <= 172800:
                all_articles.append({
                    "id": link,
                    "title": entry.get('title', 'No Title'),
                    "imageUrl": get_image(entry),
                    "source": src['name'],
                    "category": src['category'],
                    "link": link,
                    "timestamp": article_time_str,
                    "isSaved": 0
                })
                seen_links.add(link)
        time.sleep(1) # Be polite to servers
    except Exception as e:
        print(f"Error scraping {src['name']}: {e}")

with open('data/news.json', 'w', encoding='utf-8') as f:
    json.dump(all_articles, f, indent=4, ensure_ascii=False)

print(f"✅ Finished! Total Articles: {len(all_articles)}")
