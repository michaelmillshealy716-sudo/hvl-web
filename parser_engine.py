import requests
import re

class SECSentinel:
    def __init__(self, ticker):
        self.ticker = ticker
        self.headers = {'User-Agent': 'Healy Vector Labs michael@healyvectorlabs.com'}

    def get_cik(self):
        return {"GPRO": "0001500435", "TSLA": "0001318605", "NN": "0001822036"}.get(self.ticker)

    def resolve_8k_url(self):
        cik = self.get_cik()
        api_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        
        r = requests.get(api_url, headers=self.headers)
        recent = r.json()['filings']['recent']
        
        # Find the index of the first 8-K form
        idx = recent['form'].index('8-K')
        acc_no = recent['accessionNumber'][idx].replace('-', '')
        primary_doc = recent['primaryDocument'][idx]
        
        # Build the Archives URL
        cik_clean = cik.lstrip('0')
        return f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{acc_no}/{primary_doc}"

    def audit_defense_pivot(self, url):
        # The 'Defense' weighting logic
        text = requests.get(url, headers=self.headers).text.upper()
        keywords = {
            "DEFENSE": 10.0, "AEROSPACE": 8.0, "ARTEMIS": 15.0, 
            "OLIVER WYMAN": 12.0, "RESTRUCTURING": 5.0
        }
        
        score = 0
        for word, weight in keywords.items():
            count = len(re.findall(word, text))
            score += (count * weight)
            
        return score

# --- HEALY VECTOR LABS: STRIKE TEST ---
agent = SECSentinel("GPRO")
doc_url = agent.resolve_8k_url()
sentiment_score = agent.audit_defense_pivot(doc_url)

print(f"--- PARSER AUDIT COMPLETE ---")
print(f"Latest 8-K URL: {doc_url}")
print(f"Defense Pivot Sentiment Score: {sentiment_score}")

