print("Running scraper test...")

from news_scraper import get_news_headlines

headlines = get_news_headlines("Tata")
for h in headlines:
    print(h)
