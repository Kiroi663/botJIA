from flask import Flask
import os
from scraper import run_all_scrapers  # On suppose que ton script est déplacé dans scraper.py

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot d'offres d'emploi opérationnel !"

@app.route('/run')
def run_jobs():
    run_all_scrapers()
    return "Scraping lancé !"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
