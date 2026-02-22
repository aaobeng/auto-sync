import feedparser
import json
import datetime
import os
import time
import re
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

if not os.path.exists('data'):
    os.makedirs('data')

# --- UPDATED SOURCES LIST (Added Daily Mail Sport) ---
SOURCES = [
    # --- DAILY MAIL SPORT FEEDS ---
    {"name": "Daily Mail Sport", "url": "https://www.dailymail.co.uk/sport/index.rss", "category": "Sports"},
    {"name": "Daily Mail Football", "url": "https://www.dailymail.co.uk/sport/football/index.rss", "category": "Sports"},
    {"name": "Daily Mail Boxing", "url": "https://www.dailymail.co.uk/sport/boxing/index.rss", "category": "Sports"},
    {"name": "Daily Mail Cricket", "url": "https://www.dailymail.co.uk/sport/cricket/index.rss", "category": "Sports"},
    
    # --- GENERAL & WORLD ---
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/rss.xml", "category": "General"},
    {"name": "The Guardian", "url": "https://www.theguardian.com/world/rss", "category": "General"},
    {"name": "Reuters Global", "url": "https://news.google.com/rss/search?q=world+news+when:24h", "category": "World"},
    {"name": "AP News", "url": "https://news.google.com/rss/search?q=AP+Top+News+when:24h", "category": "World"},

    # --- SPORTS ---
    {"name": "ESPN", "url": "https://www.espn.com/espn/rss/news", "category": "Sports"},
    {"name": "Yahoo Sports", "url": "https://sports.yahoo.com/rss/", "category": "Sports"},

    # --- TECH & SCIENCE ---
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "Tech"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "category": "Tech"},
    {"name": "NASA News", "url": "https://www.nasa.gov/news-release/feed/", "category": "Science"},

    # --- GAMING ---
    {"name": "IGN", "url": "https://feeds.ign.com/ign/news", "category": "Gaming"},
    {"name": "Kotaku", "url": "https://kotaku.com/rss", "category": "Gaming"},

    # --- BUSINESS ---
    {"name": "CNBC Business", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?profile=120000000&id=10001147", "category": "Business"},
    
    # --- MOVIES ---
    {"name": "Variety", "url": "https://variety.com/feed/", "category": "Movies"},
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
    link = entry.get('link', '')

    # 1. YouTube Handler (extracts medium-res thumbnail for speed)
    if 'youtube.com' in link or 'youtu.be' in link:
        video_id = None
        if 'v=' in link: video_id = link.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in link: video_id = link.split('youtu.be/')[1].split('?')[0]
        if video_id: return f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg" # mq is faster than maxres

    # 2. Check Standard RSS Image Tags
    if 'media_content' in entry and len(entry.media_content) > 0:
        url = entry.media_content[0].get('url')
    elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
        url = entry.media_thumbnail[-1].get('url')
    elif 'enclosures' in entry:
        for e in entry.enclosures:
            if 'image' in e.get('type',''):
                url = e.get('href'); break

    # 3. FAST DEEP SCRAPE (With short timeout to prevent app lag)
    if not url or "unsplash" in url:
        try:
            # Short 3s timeout so the scraper doesn't hang
            response = requests.get(link, timeout=3, headers={"User-Agent": feedparser.USER_AGENT})
            soup = BeautifulSoup(response.text, 'html.parser')
            meta_og = soup.find("meta", property="og:image") or soup.find("meta", name="twitter:image")
            if meta_og: url = meta_og.get("content")
        except: pass

    # 4. SPEED OPTIMIZATION: Shrink image dimensions
    if url and isinstance(url, str) and len(url) > 10:
        if url.startswith('//'): url = 'https:' + url
        url = url.split('?')[0] # Remove trackers
        
        # --- THE SPEED FIX: REWRITING HD URLS TO THUMBNAILS ---
        # Instead of 800x600 or original size, we force 400 width
        url = re.sub(r'/\d+x\d+/', '/400x300/', url) 
        if "espn" in url: url += "&width=400"
        if "dailymail" in url: url = url.replace("article-", "thumb-") # DailyMail specific optimization
        
        return url
    
    return "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=400&q=80"

# --- EXECUTION ---
all_articles = []
seen_links = set()

for src in SOURCES:
    print(f"Scraping {src['name']}...")
    try:
        feed = feedparser.parse(src['url'])
        # Limit to top 15 to keep news.json small and fast for Flutter
        for entry in feed.entries[:15]: 
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
        time.sleep(0.5) 
    except Exception as e:
        print(f"Error scraping {src['name']}: {e}")

with open('data/news.json', 'w', encoding='utf-8') as f:
    json.dump(all_articles, f, indent=4, ensure_ascii=False)

print(f"✅ Finished! Total: {len(all_articles)} articles.")
