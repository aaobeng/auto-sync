import feedparser
import json
import datetime
import os
import time
import re

# --- THE FIX FOR BLOCKED SOURCES ---
# This makes your bot look like a real Google Chrome browser
feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# Ensure data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

# MEGA SOURCES LIST (Specifics + Search Engines)
SOURCES = [
    # --- GENERAL ---
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/rss.xml", "category": "General"},
    {"name": "The Guardian", "url": "https://www.theguardian.com/world/rss", "category": "General"},
    {"name": "NYT Home", "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml", "category": "General"},
    {"name": "Associated Press", "url": "https://news.google.com/rss/search?q=when:24h+allinurl:apnews.com", "category": "General"},
    {"name": "ABC News", "url": "https://abcnews.go.com/abcnews/topstories", "category": "General"},

    # --- SPORTS (The Mega Section) ---
    {"name": "ESPN", "url": "https://www.espn.com/espn/rss/news", "category": "Sports"},
    {"name": "Sky Sports", "url": "https://www.skysports.com/rss/12040", "category": "Sports"},
    {"name": "CBS Sports", "url": "https://www.cbssports.com/rss/headlines/", "category": "Sports"},
    {"name": "Fox Sports", "url": "https://api.foxsports.com/v2/content/optimized-rss?partnerKey=MB0ByRq3p6W9bsY&size=30", "category": "Sports"},
    {"name": "Yahoo Sports", "url": "https://sports.yahoo.com/rss/", "category": "Sports"},
    {"name": "Global Sports Hub", "url": "https://news.google.com/rss/search?q=sports+news+when:24h", "category": "Sports"},
    {"name": "Transfer Market", "url": "https://news.google.com/rss/search?q=football+transfers+when:24h", "category": "Sports"},

    # --- TECH ---
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "Tech"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "category": "Tech"},
    {"name": "Wired", "url": "https://www.wired.com/feed/rss", "category": "Tech"},
    {"name": "Global Tech Hub", "url": "https://news.google.com/rss/search?q=technology+when:24h", "category": "Tech"},

    # --- WORLD & MOVIES ---
    {"name": "CNN World", "url": "http://rss.cnn.com/rss/edition_world.rss", "category": "World"},
    {"name": "Reuters Global", "url": "https://news.google.com/rss/search?q=world+news+when:24h", "category": "World"},
    {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml", "category": "World"},
    {"name": "CinemaBlend", "url": "https://www.cinemablend.com/rss/news", "category": "Movies"},
    {"name": "Variety", "url": "https://variety.com/feed/", "category": "Movies"},
]

def get_real_time(entry):
    try:
        ts = entry.get('published_parsed') or entry.get('updated_parsed')
        if ts: return datetime.datetime.fromtimestamp(time.mktime(ts)).strftime('%Y-%m-%d %H:%M:%S')
    except: pass
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_image(entry):
    url = None
    if 'media_content' in entry: url = entry.media_content[0]['url']
    elif 'media_thumbnail' in entry: url = entry.media_thumbnail[-1]['url']
    elif 'enclosures' in entry:
        for e in entry.enclosures:
            if 'image' in e.get('type',''): url = e.get('href'); break
    if not url:
        txt = entry.get('summary','') + entry.get('content',[{}])[0].get('value','')
        m = re.search(r'img.*?src="([^"]+)"', txt)
        if m: url = m.group(1)
    if url:
        url = url.split('?')[0] # Strips tiny thumbnail limits
        url = re.sub(r'/\d+/', '/800/', url) # Forces BBC HD
        return url
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1000"

all_articles = []
seen_links = set()

for src in SOURCES:
    print(f"Scraping {src['name']}...")
    try:
        feed = feedparser.parse(src['url'])
        if not feed.entries: print(f"⚠️ Feed empty: {src['name']}")
        
        for entry in feed.entries[:30]: # Limit set to 30
            if entry.link in seen_links: continue
            
            # STRICT AGE FILTER: Only Today & Yesterday
            article_time_str = get_real_time(entry)
            article_time = datetime.datetime.strptime(article_time_str, '%Y-%m-%d %H:%M:%S')
            
            if (datetime.datetime.now() - article_time).days <= 1:
                all_articles.append({
                    "id": entry.link,
                    "title": entry.title,
                    "imageUrl": get_image(entry),
                    "source": src['name'],
                    "category": src['category'],
                    "link": entry.link,
                    "timestamp": article_time_str,
                    "isSaved": 0
                })
                seen_links.add(entry.link)
        time.sleep(1) # Be polite to servers
    except Exception as e:
        print(f"Error scraping {src['name']}: {e}")

# Save the final JSON
with open('data/news.json', 'w') as f:
    json.dump(all_articles, f, indent=4)

print(f"✅ Finished! Found {len(all_articles)} fresh articles.")
