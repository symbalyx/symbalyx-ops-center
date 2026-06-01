#!/usr/bin/env python3
"""
Scraper France TV — Recrutement
Usage: python3 scraper_francetv.py
"""
import requests
from bs4 import BeautifulSoup
import json
import sys
from datetime import datetime

URL = "https://recrutement.francetelevisions.fr/"
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
        return {"error": f"HTTP error: {e}", "source": "France TV", "offers": []}

    soup = BeautifulSoup(resp.text, "html.parser")
    offers = []

    # Structure depend de l'ATS utilise (Taleo, Workday, ou custom)
    # Plusieurs formats possibles
    for card in soup.select("article, .job, .offre, .requisition, .posting, tr, .card, li.job-listing"):
        title_el = card.select_one("h2, h3, .job-title, .requisition-title, a[href*='job'], a[href*='posting']")
        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        if not title or len(title) < 3:
            continue

        link = title_el.get("href", "") if title_el.name == "a" else ""
        if link and not link.startswith("http"):
            link = URL.rstrip("/") + "/" + link.lstrip("/")

        location_el = card.select_one(".location, .lieu, .city")
        contract_el = card.select_one(".type, .contract, .badge, .field--type")

        offers.append({
            "title": title,
            "company": "France Televisions",
            "source": "France TV",
            "contract_type": contract_el.get_text(strip=True) if contract_el else "",
            "location": location_el.get_text(strip=True) if location_el else "Paris",
            "link": link,
            "description": "",
            "date": "",
            "scraped_at": datetime.now().isoformat(),
        })

    return {"source": "France TV", "offers_count": len(offers), "offers": offers}

if __name__ == "__main__":
    result = scrape()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["offers_count"]:
        print(f"\n→ {result['offers_count']} offres France TV", file=sys.stderr)
    else:
        print("\n→ Aucune offre. Le portail recrutement utilise peut-etre un ATS (Taleo/Workday) avec chargement JS.", file=sys.stderr)
