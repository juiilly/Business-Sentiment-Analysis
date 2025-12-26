from news_scraper import get_news_headlines
from sentiment_analyzer import analyze_sentiment

# Set your brand or topic here
brand_query = "Tesla"  # You can change this to any brand name

# Step 1: Get news headlines
print(f"\n🔍 Fetching news for: {brand_query}")
headlines = get_news_headlines(brand_query)

if not headlines:
    print("No headlines found or API limit reached.")
else:
    # Step 2: Analyze each headline
    print(f"\n🧠 Analyzing sentiment for {len(headlines)} headlines:\n")

    for i, headline in enumerate(headlines, start=1):
        sentiment = analyze_sentiment(headline)
        print(f"{i}. {headline}\n   → Sentiment: {sentiment}\n")
