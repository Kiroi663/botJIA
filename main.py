from flask import Flask
import scraper  # Importation du module scraper

app = Flask(__name__)

@app.route('/')
def index():
    return "🚀 Le scraper fonctionne !"

@app.route('/run-scraper')
def run_scraper():
    """Route pour lancer le scraping"""
    scraper.run_all_scrapers()
    return "✅ Scraping terminé avec succès !"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
