import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import csv
import os

def fetch_headlines_with_sentiment(companies=['Apple']):
    all_headlines = []

    for company in companies:
        url = f'https://news.google.com/rss/search?q={company}&hl=en-IN&gl=IN&ceid=IN:en'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.findAll('item')

        for item in items:
            title = item.title.text
            sentiment = TextBlob(title).sentiment.polarity

            if sentiment > 0:
                sentiment_label = 'Positive'
            elif sentiment < 0:
                sentiment_label = 'Negative'
            else:
                sentiment_label = 'Neutral'

            all_headlines.append({
                'company': company,
                'title': title,
                'sentiment': sentiment_label
            })

    return all_headlines

def save_to_csv(data, filename='sentiment_data.csv'):
    file_exists = os.path.isfile(filename)

    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['company', 'title', 'sentiment'])

        if not file_exists:
            writer.writeheader()

        writer.writerows(data)

# For testing
if __name__ == "__main__":
    headlines = fetch_headlines_with_sentiment(['Apple', 'Amazon', 'Infosys'])
    save_to_csv(headlines)
    print("Saved to sentiment_data.csv")
