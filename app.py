from flask import Flask
from job_scraper import run_all_scrapers  # Importation directe de la fonction

app = Flask(__name__)

@app.route('/')
def index():
    return "🚀 Le scraper est actif sur Render !"

@app.route('/run-scraper')
def run_scraper():
    """Route pour lancer le scraping"""
    result = run_all_scrapers()
    return f"✅ Scraping terminé : {result} nouvelles offres ajoutées."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
