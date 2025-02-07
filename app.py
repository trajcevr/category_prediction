
import requests
from bs4 import BeautifulSoup
import re
from collections import defaultdict
from flask import Flask, request, jsonify


from pyngrok import ngrok

app = Flask(__name__)

class WebsiteClassifier:
    def __init__(self):
        self.category_mapping = {
            "End User": 976820002,
            "MS Partner - D365 Practice": 976820001,
            "MS Partner - Without D365 Practice": 794580001,
            "Recruitment Agency": 976820000,
            "D365 - Add On": 794580000,
            "Startup": 794580002
        }

        self.category_keywords = {
            "End User": [
                'our company uses', 'we use dynamics', 'our business relies',
                'our enterprise', 'our organization uses'
            ],
            "MS Partner - D365 Practice": [
                'microsoft partner', 'dynamics 365', 'd365',
                'microsoft dynamics', 'gold partner', 'silver partner',
                'dynamics implementation', 'dynamics consulting',
                'erp implementation', 'crm implementation',
                'dynamics solutions', 'business solutions',
                'microsoft solutions', 'certified partner',
                'dynamics expert', 'solutions provider',
                'implementation services', 'consulting services',
                'business central', 'finance and operations',
                'dynamics support', 'microsoft consulting'
            ],
            "MS Partner - Without D365 Practice": [
                'microsoft partner', 'azure', 'office 365', 'microsoft 365',
                'power platform', 'sharepoint', 'teams',
                'cloud solutions', 'microsoft cloud'
            ],
            "Recruitment Agency": [
                'recruitment', 'staffing', 'hiring', 'job placement',
                'talent acquisition', 'headhunting', 'employment agency',
                'job openings', 'careers', 'positions available'
            ],
            "D365 - Add On": [
                'add-on', 'plugin', 'extension', 'integration',
                'dynamics 365 solution', 'dynamics marketplace',
                'integrated solution', 'dynamics product'
            ],
            "Startup": [
                'startup', 'start-up', 'seed funding', 'venture',
                'innovation', 'disruptive', 'early stage',
                'founding team', 'series a'
            ]
        }

        self.keyword_weights = {
            "microsoft partner": 3,
            "dynamics 365": 3,
            "d365": 3,
            "implementation": 2,
            "consulting": 2,
            "solutions provider": 2
        }

    def get_website_content(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text()

            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return text.lower()

        except Exception as e:
            print(f"Error fetching website content: {str(e)}")
            return ""

    def classify_content(self, content):
        scores = defaultdict(float)  

        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                count = len(re.findall(r'' + re.escape(keyword) + r'', content))

                weight = self.keyword_weights.get(keyword, 1)
                scores[category] += count * weight

        if ('dynamics' in content or 'd365' in content) and            ('implementation' in content or 'consulting' in content or 'solutions' in content):
            scores["MS Partner - D365 Practice"] *= 1.5

        if not any(scores.values()):
            return None, None

        best_category = max(scores.items(), key=lambda x: x[1])[0]
        confidence_score = scores[best_category] / sum(scores.values())

        return best_category, self.category_mapping[best_category]

    def analyze_website(self, url):
        content = self.get_website_content(url)
        if not content:
            return None, None

        category, option_set_value = self.classify_content(content)

        return {
            'category': category,
            'option_set_value': option_set_value,
            'url': url
        }

classifier = WebsiteClassifier()

@app.route('/classify', methods=['POST'])
def classify_endpoint():
 
    data = request.get_json()

    if not data or 'url' not in data:
        return jsonify({"error": "Missing 'url' in request body"}), 400

    url = data['url']
    result = classifier.analyze_website(url)

    if not result['category']:
        return jsonify({"error": "Could not classify website content"}), 500

    return jsonify(result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
