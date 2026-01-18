import feedparser
from google import genai
from google.genai import types
import os
import datetime
import traceback

# 1. SETUP
API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

rss_feeds = [
    "https://feeds.ign.com/ign/news",
    "https://www.gamespot.com/feeds/news/",
]

# 2. HTML TEMPLATE WITH ERROR BOX SUPPORT
html_template = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Game News - Diagnostics</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {{ background-color: #121212; color: #ffffff; font-family: 'Tajawal', sans-serif; margin: 0; padding: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .error-box {{ background: #cf6679; color: #000; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: left; direction: ltr; font-family: monospace; }}
        .card {{ background: #1e1e1e; border-radius: 12px; margin-bottom: 20px; padding: 20px; border: 1px solid #333; }}
        h1 {{ text-align: center; color: #bb86fc; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Game News Diagnostics</h1>
        <div style="text-align: center; color: #888;">Updated: {date}</div>
        
        {error_section}

        {articles}
    </div>
</body>
</html>
"""

def main():
    error_html = ""
    articles_html = ""
    
    # TEST 1: Check API Key
    if not API_KEY:
        error_html += "<div class='error-box'>❌ FATAL: GEMINI_API_KEY is missing from GitHub Secrets.</div>"
    
    # TEST 2: Check AI Connection (The likely failure point)
    try:
        print("Testing AI Connection...")
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents="Say 'Hello' in Arabic.",
        )
        print("✅ AI Connection Success!")
    except Exception as e:
        print(f"❌ AI Failed: {e}")
        # Add the actual error to the website so we can see it
        error_html += f"<div class='error-box'><strong>⚠️ AI Error:</strong><br>{str(e)}</div>"

    # FETCH NEWS (Even if AI fails, show the English news so the site isn't empty)
    for feed_url in rss_feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:3]: # Limit to 3 for speed
                articles_html += f"""
                <div class="card">
                    <h3>{entry.title}</h3>
                    <p>{getattr(entry, 'summary', '')[:150]}...</p>
                    <small>Raw English Content (AI Translation Skipped)</small>
                </div>
                """
        except Exception as e:
            error_html += f"<div class='error-box'>Feed Error: {e}</div>"

    # Generate HTML
    now = datetime.datetime.now().strftime("%H:%M:%S UTC")
    final_html = html_template.format(
        date=now, 
        error_section=error_html, 
        articles=articles_html
    )
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)

if __name__ == "__main__":
    main()
