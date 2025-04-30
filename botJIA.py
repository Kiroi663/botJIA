import requests
import json
from pymongo import MongoClient
from datetime import datetime
import offreBot  # Contient MONGO_URI et SCRIPT
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse

class JobScraper:
    """Scraper pour récupérer les offres d'emploi LinkedIn et les stocker dans MongoDB."""

    def __init__(self, url, mongo_uri, db_name, collection_name, force_category=None):
        self.url = url
        self.force_category = force_category
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0.0.0 Safari/537.36"
        }
        self.client = MongoClient(mongo_uri, tls=True, tlsAllowInvalidCertificates=True)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

        try:
            self.client.server_info()
            print("✅ Connexion réussie à MongoDB")
        except Exception as e:
            print(f"❌ Erreur de connexion à MongoDB : {e}")
            exit(1)

    @staticmethod
    def categorize_job(title):
        title_lower = title.lower()
        categories = {
            "Informatique / IT": ["développeur", "it", "digital", "logiciel", "technicien"],
            "Finance / Comptabilité": ["finance", "comptable", "audit", "gestion des risques"],
            "Communication / Marketing": ["communication", "marketing", "publicité"],
            "Conseil / Stratégie": ["consultant", "analyse", "conseil", "business"],
            "Transport / Logistique": ["transport", "logistique", "mobilité"],
            "Ingénierie / BTP": ["ingénieur", "technicien", "construction", "chantier"],
            "Santé / Médical": ["santé", "hôpital", "médecin", "infirmier", "pharmacie"],
            "Éducation / Formation": ["éducation", "professeur", "enseignant", "formation"],
            "Ressources humaines / Recrutement": ["recrutement", "ressources humaines", "rh"],
            "Droit / Légal / Juridique": ["juridique", "avocat", "droit"],
            "Environnement / Développement durable": ["environnement", "développement durable", "écologie"],
            "Sécurité / Défense / Surveillance": ["sécurité", "défense", "surveillance"],
            "Humanitaire / ONG / Social": ["humanitaire", "ong", "social"],
            "Tourisme / Hôtellerie / Restauration": ["hôtellerie", "restauration", "tourisme"],
            "Art / Culture / Design": ["art", "culture", "design"],
            "Industrie / Production / Maintenance": ["industrie", "production", "maintenance"],
            "Commerce / Vente / Distribution": ["commerce", "vente", "distribution"],
            "Immobilier / Construction": ["immobilier", "construction"],
            "Agriculture / Agroalimentaire": ["agriculture", "agroalimentaire"],
            "Sciences / Recherche": ["sciences", "recherche"],
            "Transport / Mécanique / Automobile": ["automobile", "mécanique", "transport"],
            "Alternance / Stage": ["alternance", "stage"],
            "Remote": ["remote", "à distance"]
        }
        for category, keywords in categories.items():
            if any(word in title_lower for word in keywords):
                return category
        return "Autre"

    def normalize_url(self, url):
        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

    def fetch_html(self):
        try:
            response = requests.get(self.url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"❌ Erreur lors de la récupération de la page : {e}")
            return None

    def extract_jobs_from_html(self, html):
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        job_listings = soup.select('ul.jobs-search__results-list > li')

        for job in job_listings:
            title_tag = job.select_one('h3.base-search-card__title')
            company_tag = job.select_one('h4.base-search-card__subtitle')
            location_tag = job.select_one('span.job-search-card__location')
            link_tag = job.select_one('a.base-card__full-link')

            title = title_tag.get_text(strip=True) if title_tag else "N/A"
            company = company_tag.get_text(strip=True) if company_tag else "N/A"
            location = location_tag.get_text(strip=True) if location_tag else "N/A"
            job_url = link_tag['href'] if link_tag and 'href' in link_tag.attrs else "N/A"

            jobs.append({
                "title": title,
                "company": company,
                "location": location,
                "url": job_url
            })

        return jobs

    def run_scraper(self):
        html_content = self.fetch_html()
        if not html_content:
            print("❌ Échec de la récupération du contenu HTML.")
            return

        job_list = self.extract_jobs_from_html(html_content)
        if not job_list:
            print("❌ Aucune offre trouvée.")
            return

        results = []

        for job in job_list:
            job_url = self.normalize_url(job['url'])
            print(f"📌 Vérification de l'offre : {job_url}")

            if self.collection.find_one({"url": job_url}):
                print("⚠️ Offre déjà existante. Ignorée.\n")
                continue

            category = self.force_category or self.categorize_job(job["title"])
            print(f"🗂️ Catégorie attribuée : {category}")

            job_entry = {
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "url": job_url,
                "resume": "Plus de données via le lien ci-dessous",
                "category": category,
                "is_notified": False,
                "created_at": datetime.utcnow().isoformat()
            }
            results.append(job_entry)

        if results:
            try:
                self.collection.insert_many(results)
                print(f"✅ {len(results)} offres insérées dans MongoDB.")
            except Exception as e:
                print(f"❌ Erreur lors de l'insertion : {e}")

if __name__ == "__main__":
    url_categories = [
        ("https://www.linkedin.com/jobs/search/?currentJobId=4214526336&f_WT=2%2C3&geoId=101271829&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true&sortBy=DD", "Remote"),
        ("https://cd.linkedin.com/jobs/kinshasa-jobs", None),
        ("https://www.linkedin.com/jobs/search/?currentJobId=4070767276&f_E=1&geoId=101271829&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true", "Alternance / Stage")
    ]

    for url, forced_cat in url_categories:
        print(f"\n🚀 Scraping de : {url}")
        scraper = JobScraper(
            url=url,
            mongo_uri=offreBot.MONGO_URI,
            db_name="job_database",
            collection_name="christ",
            force_category=forced_cat
        )
        scraper.run_scraper()
