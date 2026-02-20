import feedparser
import json
import datetime
import os
import time

# Create data directory if it doesn't exist
if not os.path.exists('data'):
    os.makedirs('data')

SOURCES = [
    {"name": "BBC News", "url": "http://feeds.bbci.co.uk/news/rss.xml", "category": "General"},
    {"name": "ESPN", "url": "https://www.espn.com/espn/rss/news", "category": "Sports"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "Tech"}
]

def get_image(entry):
    # 1. Check for 'media_content' (The Verge uses this)
    if 'media_content' in entry and len(entry.media_content) > 0:
        return entry.media_content[0]['url']
        
    # 2. Check for 'media_thumbnail' (BBC News uses this!)
    if 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
        return entry.media_thumbnail[0]['url']
        
    # 3. Check for 'enclosures' (ESPN uses this!)
    if 'enclosures' in entry:
        for enc in entry.enclosures:
            if 'image' in enc.get('type', ''):
                return enc.get('href')
                
    # 4. Check for 'links' (Standard Atom feeds)
    if 'links' in entry:
        for link in entry.links:
            if 'image' in link.get('type', ''):
                return link.get('href')

    # 5. Fallback image if the news site completely forgot to include an image
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1000"

all_articles = []

for src in SOURCES:
    print(f"Fetching {src['name']}...")
    try:
        feed = feedparser.parse(src['url'])
        for entry in feed.entries[:15]: 
            all_articles.append({
                "id": entry.link,
                "title": entry.title,
                "imageUrl": get_image(entry),
                "source": src['name'],
                "category": src['category'],
                "link": entry.link,
                "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "isSaved": 0
            })
        time.sleep(2) 
    except Exception as e:
        print(f"Failed to fetch {src['name']}: {e}")

# Save to JSON
with open('data/news.json', 'w') as f:
    json.dump(all_articles, f, indent=4)
    
print("News successfully scraped and saved!")
