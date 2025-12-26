from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests, os
from textblob import TextBlob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import tweepy, praw
from datetime import datetime

# App configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    watchlist = db.Column(db.Text)

    def is_authenticated(self): return True
    def is_active(self): return True
    def is_anonymous(self): return False
    def get_id(self): return str(self.id)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# API setup
NEWS_API_KEY = "2f49168339f34f4b8a819636779e09f3"
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAANAt0gEAAAAA3IU4G3dB%2FLVTrBAEyyLo2enZHWo%3DIiHtHNjUUSMtDfj6f6wXAtqYqHtkMeuCSgzdGemEHW6WwhOrXp"
client = tweepy.Client(bearer_token=BEARER_TOKEN)
reddit = praw.Reddit(client_id="AxjrJOyQppjQGVbI8nspnw", client_secret="4p1v-LWfGLAQ75U0qblXQQaw-0yzbQ", user_agent="SentimentTracker by /u/BeginningKitchen2973")
NEWS_API_URL = "https://newsapi.org/v2/everything"
GRAPH_DIR = "static/graphs"
os.makedirs(GRAPH_DIR, exist_ok=True)

# Data fetching and sentiment analysis
def fetch_news(company, page_size=20, from_param=None, to_param=None):
    params = {
        "q": company,
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY,
        "language": "en",
        "pageSize": page_size
    }
    if from_param:
        params["from"] = from_param
    if to_param:
        params["to"] = to_param
    response = requests.get(NEWS_API_URL, params=params)
    articles = response.json().get("articles", [])
    return [{"title": a["title"], "description": a.get("description", ""), "url": a.get("url", "")} for a in articles]


def fetch_tweets(company, max_results=5):
    try:
        query = f"{company} lang:en -is:retweet"
        tweets = client.search_recent_tweets(query=query, tweet_fields=["text"], max_results=max_results)
        return [t.text for t in tweets.data] if tweets.data else ["No tweets"]
    except Exception as e:
        print(f"Error fetching tweets: {e}")
        return [f"Twitter error: {str(e)}"]

def fetch_reddit_posts(company, limit=20):
    try:
      return [{"title": sub.title, "url": f"https://reddit.com{sub.permalink}"} for sub in reddit.subreddit("all").search(company, limit=limit)]
    except Exception as e:
        return [f"Reddit error: {e}"]

def analyze_sentiment(text):
    polarity = TextBlob(text).sentiment.polarity
    return "Positive" if polarity > 0.1 else "Negative" if polarity < -0.1 else "Neutral"

import seaborn as sns
sns.set_theme(style="darkgrid")

import seaborn as sns
import matplotlib.pyplot as plt

sns.set_style("whitegrid")

def plot_sentiment(source, company, sentiment_counts):
    fig, ax = plt.subplots(figsize=(7, 5))
    
    # Custom colors with soft gradient tones
    color_map = {
        "Positive": "#10B981",  # Emerald
        "Negative": "#EF4444",  # Rose
        "Neutral": "#64748B"    # Slate
    }

    categories = list(sentiment_counts.keys())
    values = list(sentiment_counts.values())
    colors = [color_map[cat] for cat in categories]

    bars = ax.bar(categories, values, color=colors, edgecolor='white', linewidth=1.5)

    # Add number labels on top of bars
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.3, f"{int(yval)}", ha='center',
                va='bottom', fontsize=13, fontweight='bold', color='white', bbox=dict(boxstyle="round,pad=0.3", fc="#0f172a", ec="none"))

    # Title and axis settings
    ax.set_title(f"{source} Sentiment Analysis", fontsize=16, weight='bold', color='white', pad=15)
    ax.set_facecolor("#1e293b")  # dark background for axes
    fig.patch.set_facecolor("#0f172a")  # full figure dark background
    ax.tick_params(colors='white', labelsize=12)

    # Remove grid lines and spines for a modern look
    sns.despine(left=True, bottom=True)
    ax.grid(False)
    ax.set_ylabel("Count", fontsize=12, color='white')

    filename = f"{source}_{company}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    path = os.path.join(GRAPH_DIR, filename)
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    return filename



def generate_sentiment_data(company, from_date=None, to_date=None):
    sources = {
        "News": fetch_news(company, from_param=from_date, to_param=to_date),
        "Twitter": fetch_tweets(company, max_results=20),
        "Reddit": fetch_reddit_posts(company, limit=20)
    }

    sentiment_summary = {}
    all_headlines = {}
    combined = {"Positive": 0, "Negative": 0, "Neutral": 0}

    for source, texts in sources.items():
        if source == "News":
            sentiments = [analyze_sentiment(f"{t['title']} {t.get('description', '')}") for t in texts]
            headlines = [(t["title"], t.get("description", ""), t.get("url", "#"), s) for t, s in zip(texts, sentiments)]
        elif source == "Reddit":
            sentiments = [analyze_sentiment(t["title"]) for t in texts]
            headlines = [(t["title"], "", t["url"], s) for t, s in zip(texts, sentiments)]
        else:  # Twitter
            sentiments = [analyze_sentiment(t) for t in texts]
            headlines = [(t, "", "#", s) for t, s in zip(texts, sentiments)]

        counts = {s: sentiments.count(s) for s in ["Positive", "Negative", "Neutral"]}
        for k in combined:
            combined[k] += counts[k]

        sentiment_summary[source] = counts
        sentiment_summary[source]["graph"] = plot_sentiment(source, company, counts)
        all_headlines[source] = headlines

    sentiment_summary["Combined"] = combined
    sentiment_summary["Combined"]["graph"] = plot_sentiment("Combined", company, combined)
    return sentiment_summary, all_headlines

# Routes
@app.route("/filter", methods=["GET", "POST"])
def home():
    company = "Apple"
    from_date = to_date = None
    if request.method == "POST":
        company = request.form.get("company", "Apple").strip()
        from_date = request.form.get("from_date") or None
        to_date = request.form.get("to_date") or None
    summary, headlines = generate_sentiment_data(company, from_date, to_date)
    graphs = {k: f"{GRAPH_DIR}/{v['graph']}" for k, v in summary.items() if v.get("graph")}
    return render_template("index.html", company=company, sentiment_summary=summary, headlines=headlines, graphs=graphs, from_date=from_date, to_date=to_date)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            flash("Username already exists!")
            return redirect(url_for('register'))
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!")
            return redirect(url_for('dashboard'))  # assuming you have a dashboard route
        else:
            flash("Invalid username or password.")
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

import calendar

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    companies = (current_user.watchlist or "").split(",")
    companies = list(filter(None, companies))

    if request.method == 'POST':
        company = request.form.get("company", "Apple").strip()
        year = request.form.get("year")
        month = request.form.get("month")
        date = request.form.get("date")

        # Clean inputs
        year = None if year in [None, "", "-1"] else year
        month = None if month in [None, "", "-1"] else month
        date = None if date in [None, ""] else date

        # Build from_date and to_date
        from_date = to_date = None
        if date:
            from_date = to_date = date
        elif year and month:
            last_day = calendar.monthrange(int(year), int(month))[1]
            from_date = f"{year}-{int(month):02d}-01"
            to_date = f"{year}-{int(month):02d}-{last_day}"

        # Save to watchlist if new
        if company and company not in companies:
            current_user.watchlist = (current_user.watchlist or "") + f",{company}"
            db.session.commit()
            companies.append(company)

        # Generate filtered sentiment data
        summary, headlines = generate_sentiment_data(company, from_date, to_date)
        graphs = {k: f"{GRAPH_DIR}/{v['graph']}" for k, v in summary.items() if v.get("graph")}

        return render_template("index.html", company=company, sentiment_summary=summary,
                               headlines=headlines, graphs=graphs, from_date=from_date, to_date=to_date)

    # GET request: render dashboard
    return render_template("dashboard.html", username=current_user.username, watchlist=companies)


@app.route("/")
def index():
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)


