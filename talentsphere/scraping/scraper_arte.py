#!/usr/bin/env python3
"""
Scraper Arte — Offres emploi (Next.js SSR + ATS externe)
Usage: python3 scraper_arte.py
"""
import requests
from bs4 import BeautifulSoup
import json
import sys
from datetime import datetime

URLS = [
    "https://www.arte.tv/sites/corporate/emplois/",
    "https://jobs.arte.tv/",
    "https://emploi.artefrance.fr/",
]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

def scrape_url(url, source_name):
    """Tente de scraper une URL Arte"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"source": source_name, "offers": [], "error": str(e)}

    soup = BeautifulSoup(resp.text, "html.parser")
    offers = []

    # Next.js SSR: le contenu est dans le HTML initial
    # Ou structure classique selon le sous-site
    for card in soup.select("article, .job-item, .offre, tr, .card, li"):
        title_el = card.select_one("h2, h3, h4, a[href*='emploi'], a[href*='job'], .job-title")
        if not title_el:
            continue

        title = title_el.get_text(strip=True)
        if not title or len(title) < 5:
            continue

        link = title_el.get("href", "") if title_el.name == "a" else ""
        if link and not link.startswith("http"):
            link = url.rstrip("/") + "/" + link.lstrip("/")

        location_el = card.select_one(".location, .lieu, .city, .localisation")
        contract_el = card.select_one(".contract, .type, .badge")

        offers.append({
            "title": title,
            "company": "Arte",
            "source": source_name,
            "contract_type": contract_el.get_text(strip=True) if contract_el else "",
            "location": location_el.get_text(strip=True) if location_el else "",
            "link": link,
            "description": "",
            "date": "",
            "scraped_at": datetime.now().isoformat(),
        })

    return {"source": source_name, "offers_count": len(offers), "offers": offers}

def scrape():
    all_offers = []
    for url in URLS:
        src_name = url.split("//")[1].split("/")[0]
        result = scrape_url(url, src_name)
        if result.get("offers"):
            all_offers.extend(result["offers"])
        else:
            # Essayer l'URL suivante
            continue

    return {
        "source": "Arte",
        "offers_count": len(all_offers),
        "offers": all_offers,
        "note": "Les offres Arte sont reparties sur jobs.arte.tv (Strasbourg) et emploi.artefrance.fr (Paris)"
    }

if __name__ == "__main__":
    result = scrape()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\n→ {result['offers_count']} offres Arte", file=sys.stderr)
