#!/usr/bin/env python3
"""
Scraper ProfilCulture — Offres emploi secteur culture/media
Usage: python3 scraper_profilculture.py
Retourne: JSON liste d'offres
"""
import requests
from bs4 import BeautifulSoup
import json
import sys
from datetime import datetime

URL = "https://www.profilculture.com/offres-emploi"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

def scrape():
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"error": f"HTTP error: {e}", "source": "ProfilCulture", "offers": []}

    soup = BeautifulSoup(resp.text, "html.parser")
    offers = []

    # Selecteurs a adapter selon structure reelle du site
    # Le site utilise probablement des classes CSS specifiques
    for card in soup.select("article, .job-card, .offre-item, tr"):
        title_el = card.select_one("h2, h3, .job-title, .offre-title a, a[href*='offre']")
        company_el = card.select_one(".company, .employer, .entreprise")
        location_el = card.select_one(".location, .lieu, .ville")
        contract_el = card.select_one(".contract, .type-contrat, .statut")
        date_el = card.select_one(".date, .pub-date, time")
        desc_el = card.select_one(".description, .job-desc, p")

        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            continue

        link = title_el.get("href", "") if title_el and title_el.name == "a" else ""
        if link and not link.startswith("http"):
            link = "https://www.profilculture.com" + link

        offers.append({
            "title": title,
            "company": company_el.get_text(strip=True) if company_el else "ProfilCulture",
            "source": "ProfilCulture",
            "contract_type": contract_el.get_text(strip=True) if contract_el else "",
            "location": location_el.get_text(strip=True) if location_el else "",
            "link": link,
            "description": desc_el.get_text(strip=True)[:300] if desc_el else "",
            "date": date_el.get("datetime", "") if date_el and date_el.name == "time" 
                    else (date_el.get_text(strip=True) if date_el else ""),
            "scraped_at": datetime.now().isoformat(),
        })

    return {"source": "ProfilCulture", "offers_count": len(offers), "offers": offers}

if __name__ == "__main__":
    result = scrape()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("offers_count", 0) > 0:
        print(f"\n✓ {result['offers_count']} offres trouvees sur ProfilCulture", file=sys.stderr)
    else:
        print("⚠ Aucune offre trouvee. Les selecteurs CSS sont peut-etre a ajuster.", file=sys.stderr)
