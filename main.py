from flask import Flask, jsonify
from job_scraper import run_all_scrapers

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Job Scraper API est en ligne !"

@app.route("/run-scraper", methods=["GET"])
def run_scraper():
    try:
        inserted = run_all_scrapers()
        return jsonify({"status": "success", "inserted": inserted})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
