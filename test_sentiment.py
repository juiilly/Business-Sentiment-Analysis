from sentiment_analyzer import analyze_sentiment

sample_texts = [
    "The company reported record profits this quarter.",
    "Shares fell sharply due to poor performance.",
    "The CEO made an announcement.",
]

for text in sample_texts:
    sentiment = analyze_sentiment(text)
    print(f"'{text}' → Sentiment: {sentiment}")
