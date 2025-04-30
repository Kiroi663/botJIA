import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse
from pymongo import MongoClient
from datetime import datetime
import offreBot  # contient MONGO_URI et SCRIPT

class JobScraper:
    def __init__(self, url, mongo_uri, db_name, collection_name, force_category=None):
        self.url = url
        self.force_category = force_category
        self.headers = {
            "User-Agent": "Mozilla/5.0"
        }
        self.client = MongoClient(mongo_uri, tls=True, tlsAllowInvalidCertificates=True)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.client.server_info()

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
        except requests.RequestException:
            return None

    def extract_jobs_from_html(self, html):
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        job_listings = soup.select('ul.jobs-search__results-list > li')
        for job in job_listings:
            title = job.select_one('h3.base-search-card__title')
            company = job.select_one('h4.base-search-card__subtitle')
            location = job.select_one('span.job-search-card__location')
            link = job.select_one('a.base-card__full-link')
            jobs.append({
                "title": title.get_text(strip=True) if title else "N/A",
                "company": company.get_text(strip=True) if company else "N/A",
                "location": location.get_text(strip=True) if location else "N/A",
                "url": link["href"] if link else "N/A"
            })
        return jobs

    def run(self):
        html = self.fetch_html()
        if not html:
            return []

        jobs = self.extract_jobs_from_html(html)
        new_jobs = []

        for job in jobs:
            job_url = self.normalize_url(job["url"])
            if self.collection.find_one({"url": job_url}):
                continue

            category = self.force_category or self.categorize_job(job["title"])
            new_jobs.append({
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "url": job_url,
                "resume": "Plus de données via le lien ci-dessous",
                "category": category,
                "is_notified": False,
                "created_at": datetime.utcnow().isoformat()
            })

        if new_jobs:
            self.collection.insert_many(new_jobs)

        return len(new_jobs)

def run_all_scrapers():
    url_categories = [
        ("https://www.linkedin.com/jobs/search/?currentJobId=4214526336&f_WT=2%2C3&geoId=101271829", "Remote"),
        ("https://cd.linkedin.com/jobs/kinshasa-jobs", None),
        ("https://www.linkedin.com/jobs/search/?currentJobId=4070767276&f_E=1&geoId=101271829", "Alternance / Stage")
    ]
    total_inserted = 0
    for url, cat in url_categories:
        scraper = JobScraper(url, offreBot.MONGO_URI, "job_database", "christ", cat)
        total_inserted += scraper.run()
    return total_inserted
