import csv
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
import os

def load_data(filename='sentiment_data.csv'):
    data = defaultdict(list)

    with open(filename, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            company = row['company']
            sentiment = row['sentiment']
            data[company].append(sentiment)
    return data

def save_graphs(data, output_folder='static/images'):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    image_files = []

    for company, sentiments in data.items():
        count = Counter(sentiments)
        labels = list(count.keys())
        values = list(count.values())

        plt.figure(figsize=(6, 4))
        plt.bar(labels, values, color=['green', 'red', 'gray'])
        plt.title(f'Sentiment Analysis for {company}')
        plt.xlabel('Sentiment')
        plt.ylabel('Headlines Count')
        plt.tight_layout()

        filename = f"{company.lower()}_sentiment.png"
        filepath = os.path.join(output_folder, filename)
        plt.savefig(filepath)
        plt.close()

        image_files.append(filename)

    return image_files
