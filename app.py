
import requests
from bs4 import BeautifulSoup
import re
from collections import defaultdict
from flask import Flask, request, jsonify

app = Flask(__name__)


class WebsiteClassifier:
    def __init__(self):
        self.category_mapping = {
            "End User": 976820002,
            "MS Partner - D365 Practice": 976820001,
            "MS Partner - Without D365 Practice": 794580001,
            "Recruitment Agency": 976820000,
            "D365 - Add On": 794580000,
            "Startup": 794580002,
        }
        self.category_keywords = {
            "End User": [
                "our company uses",
                "we use dynamics",
                "our business relies",
                "our enterprise",
                "our organization uses",
            ],
            "MS Partner - D365 Practice": [
                "microsoft partner",
                "dynamics 365",
                "d365",
                "microsoft dynamics",
                "gold partner",
                "silver partner",
                "dynamics implementation",
                "dynamics consulting",
                "erp implementation",
                "crm implementation",
                "dynamics solutions",
                "business solutions",
                "microsoft solutions",
                "certified partner",
                "dynamics expert",
                "solutions provider",
                "implementation services",
                "consulting services",
                "business central",
                "finance and operations",
                "dynamics support",
                "microsoft consulting",
            ],
            "MS Partner - Without D365 Practice": [
                "microsoft partner",
                "azure",
                "office 365",
                "microsoft 365",
                "power platform",
                "sharepoint",
                "teams",
                "cloud solutions",
                "microsoft cloud",
            ],
            "Recruitment Agency": [
                "recruitment",
                "staffing",
                "hiring",
                "job placement",
                "talent acquisition",
                "headhunting",
                "employment agency",
                "job openings",
                "careers",
                "positions available",
            ],
            "D365 - Add On": [
                "add-on",
                "plugin",
                "extension",
                "integration",
                "dynamics 365 solution",
                "dynamics marketplace",
                "integrated solution",
                "dynamics product",
            ],
            "Startup": [
                "startup",
                "start-up",
                "seed funding",
                "venture",
                "innovation",
                "disruptive",
                "early stage",
                "founding team",
                "series a",
            ],
        }

    def get_website_content(self, url):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for script in soup(["script", "style"]):
                script.decompose()
            text = " ".join(soup.get_text().lower().split())
            return text
        except Exception as e:
            return ""

    def classify_content(self, content):
        scores = defaultdict(int)
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                scores[category] += content.count(keyword)
        best_category = max(scores, key=scores.get, default=None)
        return best_category, self.category_mapping.get(best_category, None)

    def analyze_website(self, url):
        content = self.get_website_content(url)
        if not content:
            return None, None
        category, option_set_value = self.classify_content(content)
        return {"category": category, "option_set_value": option_set_value, "url": url}


classifier = WebsiteClassifier()


@app.route("/classify", methods=["POST"])
def classify_endpoint():
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "Missing 'url' in request body"}), 400
    result = classifier.analyze_website(data["url"])
    if not result["category"]:
        return jsonify({"error": "Could not classify website content"}), 500
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

