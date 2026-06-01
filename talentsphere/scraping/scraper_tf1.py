#!/usr/bin/env python3
"""
Scraper Groupe TF1 — Offres emploi (Drupal CMS)
Usage: python3 scraper_tf1.py
"""
import requests
from bs4 import BeautifulSoup
import json
import sys
from datetime import datetime

URL = "https://www.groupe-tf1.fr/fr/talents/nous-rejoindre"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

def scrape():
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"error": f"HTTP error: {e}", "source": "Groupe TF1", "offers": []}

    soup = BeautifulSoup(resp.text, "html.parser")
    offers = []

    # Drupal structure: nodes, views, articles
    for card in soup.select("article, .node, .views-row, .job-teaser, .teaser"):
        title_el = card.select_one("h2 a, h3 a, .node__title a, .field--title a, .job-title a")
        if not title_el:
            title_el = card.select_one("h2, h3, .node__title, .field--title")
        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        link = title_el.get("href", "") if title_el.name == "a" else ""
        if link and not link.startswith("http"):
            link = "https://www.groupe-tf1.fr" + link

        desc_el = card.select_one(".field--body, .node__content, .description, p")
        contract_el = card.select_one(".field--type-contract, .job-type, .badge")

        offers.append({
            "title": title,
            "company": "Groupe TF1",
            "source": "Groupe TF1",
            "contract_type": contract_el.get_text(strip=True) if contract_el else "",
            "location": "Paris (Boulogne-Billancourt)",
            "link": link,
            "description": desc_el.get_text(strip=True)[:300] if desc_el else "",
            "date": "",
            "scraped_at": datetime.now().isoformat(),
        })

    return {"source": "Groupe TF1", "offers_count": len(offers), "offers": offers}

if __name__ == "__main__":
    result = scrape()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\n→ {result['offers_count']} offres Groupe TF1" if result['offers_count'] else "\n→ Aucune offre (verifier selecteurs)", file=sys.stderr)
