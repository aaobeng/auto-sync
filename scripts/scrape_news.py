import feedparser
import json
import datetime
import os
import time
import re
import math
import requests
import random
from bs4 import BeautifulSoup
from newspaper import Article

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

# --- THE COOKIE SESSION (The Fix) ---
session = requests.Session()
session.cookies.update({
    "CONSENT": "YES+cb.20230101-08-p0.en+FX+000",
    "euconsent-v2": "true",
    "cookie_notice_accepted": "true",
    "OptanonAlertBoxClosed": "2026-03-04T00:00:00.000Z"
})

SOURCES = [
    # =========================================================
    # SPORTS (Football, Sports, Boxing combined)
    # =========================================================
    {"name": "The Sun - Football",      "url": "https://www.thesun.co.uk/sport/football/feed/",                    "category": "Sports"},
    {"name": "Mirror Football",         "url": "https://www.mirror.co.uk/sport/football/rss.xml",                  "category": "Sports"},
    {"name": "Sky Sports Football",     "url": "https://www.skysports.com/rss/12040",                              "category": "Sports"},
    {"name": "The Guardian Football",   "url": "https://www.theguardian.com/football/rss",                         "category": "Sports"},
    {"name": "TalkSport Football",      "url": "https://talksport.com/football/feed/",                             "category": "Sports"},
    {"name": "Daily Mail Sport",        "url": "https://www.dailymail.co.uk/sport/index.rss",                      "category": "Sports"},
    {"name": "Mirror Sport",            "url": "https://www.mirror.co.uk/sport/rss.xml",                           "category": "Sports"},
    {"name": "ESPN",                    "url": "https://www.espn.com/espn/rss/news",                               "category": "Sports"},
    {"name": "Sky Sports General",      "url": "https://www.skysports.com/rss/12020",                              "category": "Sports"},
    {"name": "Daily Mail Boxing",       "url": "https://www.dailymail.co.uk/sport/boxing/index.rss",               "category": "Sports"},
    {"name": "TalkSport Boxing",        "url": "https://talksport.com/sport/boxing/feed/",                         "category": "Sports"},
    # NEW: Sports expanded
    {"name": "ESPN Cricinfo",           "url": "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",       "category": "Sports"},
    {"name": "RugbyPass",               "url": "https://www.rugbypass.com/feed/",                                  "category": "Sports"},
    {"name": "Planet Rugby",            "url": "https://www.planetrugby.com/feed/",                                "category": "Sports"},
    {"name": "Autosport F1",            "url": "https://www.autosport.com/rss/feed/f1",                            "category": "Sports"},
    {"name": "RaceFans F1",             "url": "https://www.racefans.net/feed/",                                   "category": "Sports"},
    {"name": "BoxingNews24",            "url": "https://www.boxingnews24.com/feed/",                               "category": "Sports"},
    {"name": "Bad Left Hook Boxing",    "url": "https://www.badlefthook.com/rss/current",                          "category": "Sports"},
    {"name": "Golf Digest",             "url": "https://www.golfdigest.com/rss/all",                               "category": "Sports"},
    {"name": "Tennis World USA",        "url": "https://www.tennisworldusa.org/rss/",                              "category": "Sports"},
    {"name": "World Athletics",         "url": "https://worldathletics.org/rss/news",                              "category": "Sports"},
    {"name": "NBA.com News",            "url": "https://www.nba.com/news/rss.xml",                                 "category": "Sports"},
    {"name": "Bleacher Report",         "url": "https://bleacherreport.com/articles/feed",                         "category": "Sports"},

    # =========================================================
    # TECH
    # =========================================================
    {"name": "The Verge",               "url": "https://www.theverge.com/rss/index.xml",                          "category": "Tech"},
    {"name": "TechCrunch",              "url": "https://techcrunch.com/feed/",                                     "category": "Tech"},
    {"name": "Wired",                   "url": "https://www.wired.com/feed/rss",                                   "category": "Tech"},
    {"name": "CNET",                    "url": "https://www.cnet.com/rss/news/",                                   "category": "Tech"},

    # =========================================================
    # WORLD — Global / International
    # =========================================================
    # Tier-1 International
    {"name": "CNN Top Stories",         "url": "http://rss.cnn.com/rss/edition.rss",                              "category": "World"},
    {"name": "Al Jazeera World",        "url": "https://www.aljazeera.com/xml/rss/all.xml",                       "category": "World"},
    {"name": "NYT World",               "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",          "category": "World"},
    {"name": "Reuters",                 "url": "https://feeds.reuters.com/reuters/topNews",                        "category": "World"},
    {"name": "AP News",                 "url": "https://rsshub.app/apnews/topics/apf-topnews",                     "category": "World"},
    {"name": "BBC World",               "url": "https://feeds.bbci.co.uk/news/world/rss.xml",                     "category": "World"},

    # --- AFRICA ---
    # Nigeria
    {"name": "Premium Times Nigeria",   "url": "https://www.premiumtimesng.com/feed/",                            "category": "World"},
    {"name": "Vanguard Nigeria",        "url": "https://www.vanguardngr.com/feed/",                               "category": "World"},
    {"name": "Pulse Nigeria",           "url": "https://www.pulse.ng/rss",                                        "category": "World"},
    {"name": "The Guardian Nigeria",    "url": "https://guardian.ng/feed/",                                       "category": "World"},
    {"name": "This Day Live",           "url": "https://www.thisdaylive.com/index.php/feed/",                     "category": "World"},
    # South Africa
    {"name": "News24",                  "url": "https://www.news24.com/feeds",                                    "category": "World"},
    {"name": "Mail & Guardian",         "url": "https://mg.co.za/feed/",                                          "category": "World"},
    {"name": "IOL South Africa",        "url": "https://www.iol.co.za/cmlink/rss/1.640",                          "category": "World"},
    {"name": "The South African",       "url": "https://www.thesouthafrican.com/feed/",                           "category": "World"},
    {"name": "eNCA",                    "url": "https://www.enca.com/rss.xml",                                    "category": "World"},
    # Kenya
    {"name": "Daily Nation",            "url": "https://www.nation.co.ke/rss",                                    "category": "World"},
    {"name": "The Star Kenya",          "url": "https://www.the-star.co.ke/rss.xml",                              "category": "World"},
    {"name": "The Standard Kenya",      "url": "https://www.standardmedia.co.ke/rss/headlines.php",               "category": "World"},
    {"name": "Citizen Digital Kenya",   "url": "https://citizentv.co.ke/feed/",                                   "category": "World"},
    # Egypt / North Africa
    {"name": "Ahram Online",            "url": "https://english.ahram.org.eg/Rss.aspx",                           "category": "World"},
    {"name": "Egypt Independent",       "url": "https://www.egyptindependent.com/feed/",                          "category": "World"},
    {"name": "Morocco World News",      "url": "https://www.moroccoworldnews.com/feed/",                          "category": "World"},
    # NEW: East & Central Africa
    {"name": "The East African",        "url": "https://www.theeastafrican.co.ke/rss",                            "category": "World"},
    {"name": "Daily Monitor Uganda",    "url": "https://www.monitor.co.ug/rss",                                   "category": "World"},
    {"name": "The New Times Rwanda",    "url": "https://www.newtimes.co.rw/rss.xml",                              "category": "World"},
    {"name": "The Citizen Tanzania",    "url": "https://www.thecitizen.co.tz/rss",                                "category": "World"},
    {"name": "Addis Standard Ethiopia", "url": "https://addisstandard.com/feed/",                                 "category": "World"},
    # NEW: West & Southern Africa
    {"name": "Front Page Africa (LBR)", "url": "https://frontpageafricaonline.com/feed/",                         "category": "World"},
    {"name": "The Namibian",            "url": "https://www.namibian.com.na/rss.xml",                             "category": "World"},
    {"name": "Lusaka Times Zambia",     "url": "https://www.lusakatimes.com/feed/",                               "category": "World"},
    {"name": "NewsDay Zimbabwe",        "url": "https://www.newsday.co.zw/feed/",                                 "category": "World"},
    {"name": "AllAfrica",               "url": "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf",  "category": "World"},

    # --- AMERICAS ---
    # USA
    {"name": "Fox News",                "url": "https://moxie.foxnews.com/google-publisher/latest.xml",           "category": "World"},
    {"name": "NBC News",                "url": "https://feeds.nbcnews.com/nbcnews/public/news",                   "category": "World"},
    {"name": "ABC News US",             "url": "https://abcnews.go.com/abcnews/usnews",                           "category": "World"},
    {"name": "CBS News",                "url": "https://www.cbsnews.com/latest/rss/main",                         "category": "World"},
    {"name": "USA Today",               "url": "https://www.usatoday.com/rss",                                    "category": "World"},
    {"name": "NPR News",                "url": "https://feeds.npr.org/1001/rss.xml",                              "category": "World"},
    # Canada
    {"name": "CBC News",                "url": "https://www.cbc.ca/cmlink/rss-topstories",                        "category": "World"},
    {"name": "The Globe and Mail",      "url": "https://www.theglobeandmail.com/feed/?rss",                       "category": "World"},
    {"name": "Toronto Star",            "url": "https://www.thestar.com/content/thestar/feed.RSS",                "category": "World"},
    {"name": "National Post",           "url": "https://nationalpost.com/feed",                                   "category": "World"},
    # NEW: Latin America
    {"name": "Colombia Reports",        "url": "https://colombiareports.com/feed/",                               "category": "World"},
    {"name": "Santiago Times Chile",    "url": "https://santiagotimes.cl/feed/",                                  "category": "World"},
    {"name": "Havana Times Cuba",       "url": "https://havanatimes.org/feed/",                                   "category": "World"},
    {"name": "Venezuela Analysis",      "url": "https://venezuelaanalysis.com/feed",                              "category": "World"},
    {"name": "MercoPress (S.America)",  "url": "https://en.mercopress.com/rss",                                   "category": "World"},
    {"name": "Buenos Aires Times",      "url": "https://batimes.com.ar/rss/",                                     "category": "World"},
    {"name": "Mexico News Daily",       "url": "https://mexiconewsdaily.com/feed/",                               "category": "World"},
    {"name": "The Rio Times Brazil",    "url": "https://riotimesonline.com/feed/",                                "category": "World"},
    {"name": "Tico Times Costa Rica",   "url": "https://ticotimes.net/feed",                                      "category": "World"},
    {"name": "The Panama News",         "url": "https://www.thepanamanews.com/feed/",                             "category": "World"},
    {"name": "Belize Breaking News",    "url": "https://www.breakingbelizenews.com/feed/",                        "category": "World"},
    # Caribbean
    {"name": "Jamaica Observer",        "url": "https://www.jamaicaobserver.com/feed/",                           "category": "World"},
    {"name": "Caribbean News Now",      "url": "https://www.caribbeannewsnow.com/feed/",                          "category": "World"},
    {"name": "Trinidad Guardian",       "url": "https://www.guardian.co.tt/rss",                                  "category": "World"},

    # --- EUROPE ---
    # Pan-European
    {"name": "Politico Europe",         "url": "https://www.politico.eu/feed/",                                   "category": "World"},
    {"name": "Euronews",                "url": "https://www.euronews.com/rss",                                    "category": "World"},
    # France
    {"name": "France24 English",        "url": "https://www.france24.com/en/rss",                                 "category": "World"},
    {"name": "RFI English",             "url": "https://www.rfi.fr/en/rss",                                       "category": "World"},
    {"name": "The Local France",        "url": "https://www.thelocal.fr/rss.xml",                                 "category": "World"},
    # Germany
    {"name": "Deutsche Welle (DW)",     "url": "https://rss.dw.com/rdf/rss-en-all",                              "category": "World"},
    {"name": "The Local Germany",       "url": "https://www.thelocal.de/rss.xml",                                 "category": "World"},
    # Italy / Spain
    {"name": "The Local Italy",         "url": "https://www.thelocal.it/rss.xml",                                 "category": "World"},
    {"name": "El País English",         "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada","category": "World"},
    {"name": "The Local Spain",         "url": "https://www.thelocal.es/rss.xml",                                 "category": "World"},
    # Nordic / Benelux
    {"name": "DutchNews.nl",            "url": "https://www.dutchnews.nl/feed/",                                  "category": "World"},
    {"name": "The Local Sweden",        "url": "https://www.thelocal.se/rss.xml",                                 "category": "World"},
    {"name": "The Local Norway",        "url": "https://www.thelocal.no/rss.xml",                                 "category": "World"},
    {"name": "The Local Denmark",       "url": "https://www.thelocal.dk/rss.xml",                                 "category": "World"},
    # NEW: Eastern Europe
    {"name": "Notes from Poland",       "url": "https://notesfrompoland.com/feed/",                               "category": "World"},
    {"name": "Prague Morning (CZ)",     "url": "https://www.praguemorning.cz/feed/",                              "category": "World"},
    {"name": "Daily News Hungary",      "url": "https://dailynewshungary.com/feed/",                              "category": "World"},
    {"name": "Romania Insider",         "url": "https://www.romania-insider.com/feed",                            "category": "World"},
    {"name": "Kyiv Post (Ukraine)",     "url": "https://www.kyivpost.com/rss",                                    "category": "World"},
    {"name": "Balkan Insight",          "url": "https://balkaninsight.com/feed/",                                 "category": "World"},
    {"name": "Sofia Globe Bulgaria",    "url": "https://sofiaglobe.com/feed/",                                    "category": "World"},
    {"name": "Total Croatia News",      "url": "https://www.total-croatia-news.com/feed",                         "category": "World"},
    {"name": "LRT English Lithuania",   "url": "https://www.lrt.lt/en/rss",                                       "category": "World"},
    {"name": "ERR News Estonia",        "url": "https://news.err.ee/rss",                                         "category": "World"},
    {"name": "LSM Latvia English",      "url": "https://eng.lsm.lv/rss.a4d",                                     "category": "World"},

    # --- MIDDLE EAST ---
    {"name": "The National (UAE)",      "url": "https://www.thenationalnews.com/rss",                             "category": "World"},
    {"name": "Arab News",               "url": "https://www.arabnews.com/rss.xml",                                "category": "World"},
    {"name": "Gulf News",               "url": "https://gulfnews.com/rss",                                        "category": "World"},
    {"name": "Haaretz",                 "url": "https://www.haaretz.com/rss",                                     "category": "World"},
    {"name": "The Times of Israel",     "url": "https://www.timesofisrael.com/feed/",                             "category": "World"},
    {"name": "Daily Sabah Turkey",      "url": "https://www.dailysabah.com/rss",                                  "category": "World"},
    {"name": "Hürriyet Daily News",     "url": "https://www.hurriyetdailynews.com/rss",                           "category": "World"},
    # NEW: Middle East expanded
    {"name": "Naharnet Lebanon",        "url": "https://www.naharnet.com/rss",                                    "category": "World"},
    {"name": "Jordan Times",            "url": "https://jordantimes.com/rss.xml",                                  "category": "World"},
    {"name": "Iraq News (iraqinews)",   "url": "https://www.iraqinews.com/feed/",                                 "category": "World"},
    {"name": "Iran International",      "url": "https://www.iranintl.com/en/rss",                                 "category": "World"},
    {"name": "Kuwait Times",            "url": "https://www.kuwaittimes.com/feed/",                               "category": "World"},
    {"name": "Gulf Daily News Bahrain", "url": "https://www.gdnonline.com/rss",                                   "category": "World"},
    {"name": "Times of Oman",           "url": "https://www.timesofoman.com/rss",                                 "category": "World"},

    # --- ASIA ---
    # South Asia
    {"name": "Times of India",          "url": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",    "category": "World"},
    {"name": "The Hindu",               "url": "https://www.thehindu.com/news/feeder/default.rss",               "category": "World"},
    {"name": "Indian Express",          "url": "https://indianexpress.com/feed/",                                 "category": "World"},
    {"name": "NDTV",                    "url": "https://feeds.feedburner.com/NDTV-LatestNews",                   "category": "World"},
    {"name": "Hindustan Times",         "url": "https://www.hindustantimes.com/rss/topnews/rssfeed.xml",          "category": "World"},
    {"name": "Dawn Pakistan",           "url": "https://www.dawn.com/feeds/home",                                 "category": "World"},
    {"name": "The Express Tribune PK",  "url": "https://tribune.com.pk/feed/",                                   "category": "World"},
    {"name": "Geo News Pakistan",       "url": "https://www.geo.tv/rss",                                          "category": "World"},
    {"name": "The Daily Star BD",       "url": "https://www.thedailystar.net/rss.xml",                           "category": "World"},
    {"name": "Dhaka Tribune",           "url": "https://www.dhakatribune.com/feed",                              "category": "World"},
    # NEW: South Asia expanded
    {"name": "Kathmandu Post Nepal",    "url": "https://kathmandupost.com/rss",                                   "category": "World"},
    {"name": "Daily Mirror Sri Lanka",  "url": "https://www.dailymirror.lk/rss/",                                "category": "World"},
    # East Asia
    {"name": "NHK World Japan",         "url": "https://www3.nhk.or.jp/nhkworld/rss/news/",                      "category": "World"},
    {"name": "The Japan Times",         "url": "https://www.japantimes.co.jp/feed/",                              "category": "World"},
    {"name": "Kyodo News Japan",        "url": "https://english.kyodonews.net/rss",                               "category": "World"},
    {"name": "Yonhap News Korea",       "url": "https://en.yna.co.kr/rss/",                                      "category": "World"},
    {"name": "The Korea Herald",        "url": "https://www.koreaherald.com/rss/",                                "category": "World"},
    {"name": "South China Morning Post","url": "https://www.scmp.com/rss/2/feed",                                 "category": "World"},
    {"name": "China Daily",             "url": "https://www.chinadaily.com.cn/rss/china_rss.xml",                "category": "World"},
    {"name": "Sixth Tone China",        "url": "https://www.sixthtone.com/rss/",                                  "category": "World"},
    # Southeast Asia
    {"name": "The Straits Times (SG)",  "url": "https://www.straitstimes.com/rss.xml",                           "category": "World"},
    {"name": "Channel NewsAsia",        "url": "https://www.channelnewsasia.com/rss",                            "category": "World"},
    {"name": "The Star Malaysia",       "url": "https://www.thestar.com.my/rss",                                  "category": "World"},
    {"name": "Malay Mail",              "url": "https://www.malaymail.com/rss",                                   "category": "World"},
    {"name": "The Jakarta Post",        "url": "https://www.thejakartapost.com/rss",                              "category": "World"},
    {"name": "Rappler Philippines",     "url": "https://www.rappler.com/rss/",                                    "category": "World"},
    {"name": "Philippine Daily Inquirer","url": "https://newsinfo.inquirer.net/feed",                             "category": "World"},
    {"name": "VnExpress International", "url": "https://e.vnexpress.net/rss",                                     "category": "World"},
    {"name": "Bangkok Post Thailand",   "url": "https://www.bangkokpost.com/rss",                                 "category": "World"},
    {"name": "The Nation Thailand",     "url": "https://www.nationthailand.com/rss",                              "category": "World"},
    # NEW: Southeast Asia expanded
    {"name": "Irrawaddy Myanmar",       "url": "https://www.irrawaddy.com/feed",                                  "category": "World"},
    {"name": "Phnom Penh Post Cambodia","url": "https://www.phnompenhpost.com/rss.xml",                           "category": "World"},
    # NEW: Central Asia
    {"name": "Astana Times Kazakhstan", "url": "https://astanatimes.com/feed/",                                   "category": "World"},
    {"name": "Kun.uz Uzbekistan",       "url": "https://kun.uz/en/rss",                                           "category": "World"},
    {"name": "JAM News Georgia",        "url": "https://jam-news.net/feed/",                                      "category": "World"},
    {"name": "Armenpress Armenia",      "url": "https://armenpress.am/eng/rss/news/",                             "category": "World"},
    {"name": "Trend News Azerbaijan",   "url": "https://en.trend.az/rss",                                         "category": "World"},

    # --- OCEANIA ---
    {"name": "ABC News Australia",      "url": "https://www.abc.net.au/news/feed/51120/rss.xml",                  "category": "World"},
    {"name": "Sydney Morning Herald",   "url": "https://www.smh.com.au/rss/feed.xml",                             "category": "World"},
    {"name": "The Age Australia",       "url": "https://www.theage.com.au/rss/feed.xml",                          "category": "World"},
    {"name": "News.com.au",             "url": "https://www.news.com.au/content-feeds/latest-news/",              "category": "World"},
    {"name": "NZ Herald",               "url": "https://www.nzherald.co.nz/rss/",                                 "category": "World"},
    {"name": "Stuff.co.nz",             "url": "https://www.stuff.co.nz/rss",                                     "category": "World"},
    {"name": "RNZ News",                "url": "https://www.rnz.co.nz/rss/news.xml",                              "category": "World"},
    # NEW: Pacific Islands
    {"name": "RNZ Pacific",             "url": "https://www.rnz.co.nz/international/pacific-news/rss.xml",        "category": "World"},
    {"name": "Fiji Times",              "url": "https://www.fijitimes.com/feed/",                                  "category": "World"},
    {"name": "Samoa Observer",          "url": "https://www.samoaobserver.ws/feed/",                              "category": "World"},
    {"name": "ABC Pacific Beat",        "url": "https://www.abc.net.au/news/feed/2942460/rss.xml",                "category": "World"},

    # =========================================================
    # NEWS (UK domestic general news)
    # =========================================================
    {"name": "The Sun - News",          "url": "https://www.thesun.co.uk/news/feed/",                             "category": "News"},
    {"name": "Mirror News",             "url": "https://www.mirror.co.uk/news/rss.xml",                           "category": "News"},
    {"name": "BBC News",                "url": "https://feeds.bbci.co.uk/news/rss.xml",                           "category": "News"},
    {"name": "BBC News UK",             "url": "https://feeds.bbci.co.uk/news/uk/rss.xml",                        "category": "News"},
    {"name": "The Independent",         "url": "https://www.independent.co.uk/rss",                               "category": "News"},
    {"name": "The Telegraph",           "url": "https://www.telegraph.co.uk/rss.xml",                             "category": "News"},
    {"name": "Daily Express",           "url": "https://www.express.co.uk/rss",                                   "category": "News"},

    # =========================================================
    # GHANA NEWS
    # =========================================================
    {"name": "MyJoyOnline",             "url": "https://www.myjoyonline.com/feed/",                               "category": "Ghana News"},
    {"name": "Citi Newsroom",           "url": "https://citinewsroom.com/feed/",                                  "category": "Ghana News"},
    {"name": "Pulse Ghana",             "url": "https://www.pulse.com.gh/rss",                                    "category": "Ghana News"},
    {"name": "GhanaWeb General",        "url": "https://cdn.ghanaweb.com/feed/newsfeed.xml",                      "category": "Ghana News"},
    {"name": "Graphic Online",          "url": "https://www.graphic.com.gh/rss",                                  "category": "Ghana News"},
]

# =========================================================
# SOURCE SUMMARY (printed at startup)
# =========================================================
def print_source_summary():
    from collections import Counter
    counts = Counter(s["category"] for s in SOURCES)
    print("\n📡 SOURCE SUMMARY")
    print("=" * 40)
    for cat, n in sorted(counts.items()):
        print(f"  {cat:<20} {n:>3} sources")
    print(f"  {'TOTAL':<20} {len(SOURCES):>3} sources")
    print("=" * 40 + "\n")

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": random.choice(["https://www.google.com/", "https://twitter.com/", "https://www.bing.com/"]),
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

def get_full_article_data(url):
    """Deep scrapes using the cookie session to bypass GDPR walls."""
    try:
        resp = session.get(url, headers=get_random_headers(), timeout=15)
        if resp.status_code != 200:
            return None

        article = Article(url)
        article.set_html(resp.text)
        article.parse()

        full_text = article.text

        junk_patterns = [
            r"Follow us on.*", r"Sign up for.*", r"Advertisement",
            r"Read more:.*", r"Share this:.*", r"Story continues below.*"
        ]
        for pattern in junk_patterns:
            full_text = re.sub(pattern, "", full_text, flags=re.IGNORECASE)

        full_text = full_text.strip()
        word_count = len(full_text.split())

        if word_count < 30:
            return None

        read_time_mins = max(1, math.ceil(word_count / 200))
        return {
            "content": full_text,
            "readTime": f"{read_time_mins} min read"
        }

    except Exception:
        return None

def get_image(entry, link):
    url = None

    # 1. RSS MEDIA TAGS
    if 'media_content' in entry and len(entry.media_content) > 0:
        url = entry.media_content[0].get('url')
    elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
        url = entry.media_thumbnail[-1].get('url')

    # 2. DEEP SCRAPE fallback
    if not url or "unsplash" in url:
        try:
            time.sleep(random.uniform(0.5, 1.5))
            resp = session.get(link, timeout=10, headers=get_random_headers())
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                meta = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
                if meta:
                    url = meta.get("content")

                if not url:
                    hidden_images = re.findall(r'(https://a\d?\.espncdn\.com/[^"\']+\.(?:jpg|png))', resp.text)
                    if hidden_images:
                        for img in hidden_images:
                            if '16x9' in img or 'picture' in img:
                                url = img
                                break
                        if not url:
                            url = hidden_images[0]

                if not url:
                    scripts = soup.find_all("script", type="application/ld+json")
                    for s in scripts:
                        if not s.string:
                            continue
                        try:
                            data = json.loads(s.string)
                            items = data if isinstance(data, list) else [data]
                            for item in items:
                                if isinstance(item, dict) and 'image' in item:
                                    img_data = item['image']
                                    url = img_data.get('url') if isinstance(img_data, dict) else img_data
                                    break
                            if url:
                                break
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass

    # 3. CLEAN & NORMALISE
    if url and isinstance(url, str) and len(url) > 10:
        if "espn" not in url:
            url = url.split('?')[0]
        if url.startswith('//'):
            url = 'https:' + url
        url = re.sub(r'/\d+x\d+/', '/400x300/', url)
        if "espn" in url and "?width=" not in url:
            url += "?width=400"
        if "thesun.co.uk" in url:
            url = url.replace("original", "thumbnail")
        return url

    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400&q=80"

# =========================================================
# EXECUTION
# =========================================================
print_source_summary()

grouped_articles = {
    "Football": [], "News": [], "Boxing": [],
    "Sports": [], "Ghana News": [], "World": [], "Tech": []
}

seen_links = set()
total_items = 0

for src in SOURCES:
    print(f"🔄 Fetching {src['name']}...")
    try:
        feed_response = session.get(src['url'], headers=get_random_headers(), timeout=15)
        feed = feedparser.parse(feed_response.content)

        valid_count = 0

        for entry in feed.entries:
            if valid_count >= 8:
                break

            link = entry.get('link', '')
            title = entry.get('title', 'No Title')

            if not link or link in seen_links:
                continue

            time.sleep(random.uniform(0.5, 1.5))
            article_info = get_full_article_data(link)

            if not article_info:
                print(f"   ⏩ Skipped (Under 30 words / Blocked): {title}")
                continue

            img = get_image(entry, link)

            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_time = datetime.datetime.fromtimestamp(
                    time.mktime(entry.published_parsed)
                ).strftime('%Y-%m-%d %H:%M:%S')
            else:
                published_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            article_data = {
                "id": link,
                "title": title,
                "imageUrl": img,
                "source": src['name'],
                "category": src['category'],
                "link": link,
                "timestamp": published_time,
                "isSaved": 0,
                "readTime": article_info["readTime"],
                "content": article_info["content"]
            }

            cat = src['category']
            if cat not in grouped_articles:
                grouped_articles[cat] = []

            grouped_articles[cat].append(article_data)
            seen_links.add(link)
            total_items += 1
            valid_count += 1

        time.sleep(random.uniform(0.5, 2.0))

    except Exception as e:
        print(f"❌ Error with {src['name']}: {e}")

filepath = os.path.join(DATA_DIR, 'news.json')
with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(grouped_articles, f, indent=4, ensure_ascii=False)

print(f"\n✅ SUCCESS! {total_items} text-rich articles saved to {filepath}")
