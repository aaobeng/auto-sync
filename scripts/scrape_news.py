import feedparser
import json
import datetime
import os
import time
import re
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
# Spoofing a real browser to prevent being blocked by news sites
feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

if not os.path.exists('data'):
    os.makedirs('data')

# --- THE SOURCES LIST YOU PROVIDED ---
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

def refine_category(entry, current_category):
    """OPERA NEWS STYLE: Categorizes based on keywords found in the text."""
    text = (entry.get('title', '') + " " + entry.get('summary', '')).lower()
    rules = {
        "Sports": ["football", "soccer", "nba", "real madrid", "barcelona", "premier league", "match", "goal"],
        "Tech": ["apple", "iphone", "google", "ai", "artificial intelligence", "crypto", "bitcoin", "tech"],
        "Science": ["nasa", "space", "climate", "health", "research", "scientific"],
        "Gaming": ["ps5", "xbox", "nintendo", "gta", "fortnite", "gaming", "esports"],
        "Business": ["market", "stocks", "economy", "finance", "trade", "investment"],
        "Movies": ["film", "netflix", "hollywood", "actor", "oscars", "trailer"]
    }
    for cat, keywords in rules.items():
        if any(kw in text for kw in keywords):
            return cat
    return current_category

def get_image(entry):
    url = None
    link = entry.get('link', '')

    # 1. YouTube Handler (extracts high-res thumbnail)
    if 'youtube.com' in link or 'youtu.be' in link:
        video_id = None
        if 'v=' in link: video_id = link.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in link: video_id = link.split('youtu.be/')[1].split('?')[0]
        if video_id: return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

    # 2. Check Standard RSS Image Tags
    if 'media_content' in entry and len(entry.media_content) > 0:
        url = entry.media_content[0].get('url')
    elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
        url = entry.media_thumbnail[-1].get('url')
    elif 'enclosures' in entry:
        for e in entry.enclosures:
            if 'image' in e.get('type',''):
                url = e.get('href')
                break

    # 3. DEEP SCRAPE (Fixes the Yahoo Sports / ESPN blank images)
    if not url or "unsplash" in url:
        try:
            response = requests.get(link, timeout=10, headers={"User-Agent": feedparser.USER_AGENT})
            soup = BeautifulSoup(response.text, 'html.parser')
            # Look for Open Graph image metadata
            meta_og = soup.find("meta", property="og:image") or \
                      soup.find("meta", property="og:image:secure_url") or \
                      soup.find("meta", name="twitter:image")
            if meta_og:
                url = meta_og.get("content")
        except:
            pass

    # 4. Cleanup and Resolution Formatting
    if url and isinstance(url, str) and len(url) > 10:
        if url.startswith('//'): url = 'https:' + url
        url = url.split('?')[0] # Remove trackers
        url = re.sub(r'/\d+x\d+/', '/800x600/', url) # Force high-res
        url = re.sub(r'--/.*', '', url) # Fixes Yahoo specific URL bugs
        return url
    
    # Modern Fallback (Instead of the old newspaper image)
    return "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=800&q=80"

# --- EXECUTION ---
all_articles = []
seen_links = set()

for src in SOURCES:
    print(f"Scraping {src['name']}...")
    try:
        feed = feedparser.parse(src['url'])
        for entry in feed.entries[:20]: # Fetch top 20 per source
            link = entry.get('link', '')
            if not link or link in seen_links: continue
            
            # Smart category refinement
            final_category = refine_category(entry, src['category'])
            
            article_time_str = get_real_time(entry)
            article_time = datetime.datetime.strptime(article_time_str, '%Y-%m-%d %H:%M:%S')
            
            # Keep articles from last 48 hours
            if (datetime.datetime.now() - article_time).total_seconds() <= 172800:
                all_articles.append({
                    "id": link,
                    "title": entry.get('title', 'No Title'),
                    "imageUrl": get_image(entry),
                    "source": src['name'],
                    "category": final_category,
                    "link": link,
                    "timestamp": article_time_str,
                    "isSaved": 0
                })
                seen_links.add(link)
        time.sleep(1) # Be nice to servers
    except Exception as e:
        print(f"Error scraping {src['name']}: {e}")

# Save the final results to JSON for your Flutter app
with open('data/news.json', 'w', encoding='utf-8') as f:
    json.dump(all_articles, f, indent=4, ensure_ascii=False)

print(f"✅ Scraping Finished! Total Articles: {len(all_articles)}")
