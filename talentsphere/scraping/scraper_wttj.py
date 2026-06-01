#!/usr/bin/env python3
"""
Scraper Welcome to the Jungle — Offres secteur media (Next.js SSR)
Usage: python3 scraper_wttj.py
Extrait les donnees JSON embarquees dans le rendu Next.js
"""
import requests
import json
import re
import sys
from datetime import datetime

URL = "https://www.welcometothejungle.com/fr/jobs"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

def extract_nextjs_json(html):
    """Extrait les donnees JSON des chunks Next.js"""
    offers = []

    # Pattern 1: self.__next_f.push() avec JSON
    next_f_matches = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.DOTALL)
    for chunk in next_f_matches:
        # Decoder les escape sequences
        chunk = chunk.encode().decode('unicode_escape', errors='ignore')
        # Chercher des donnees JSON d'offres
        for match in re.finditer(r'({"offers":\[.*?\]}|\{"jobs":\[.*?\]})', chunk):
            try:
                data = json.loads(match.group(1))
                if "offers" in data:
                    offers.extend(data["offers"])
                elif "jobs" in data:
                    offers.extend(data["jobs"])
            except json.JSONDecodeError:
                continue

    # Pattern 2: JSON-LD structuré
    jsonld_matches = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>',
        html, re.DOTALL
    )
    for j in jsonld_matches:
        try:
            data = json.loads(j)
            if isinstance(data, dict):
                if data.get("@type") == "ItemList" and "itemListElement" in data:
                    for item in data["itemListElement"]:
                        if isinstance(item, dict) and "item" in item:
                            offers.append(item["item"])
        except json.JSONDecodeError:
            continue

    return offers

def scrape():
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"error": f"HTTP error: {e}", "source": "WTTJ", "offers": []}

    offers = extract_nextjs_json(resp.text)

    # Fallback: parser HTML si aucun JSON trouve
    if not offers:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.select("article, [data-testid='job-card'], a[href*='/fr/jobs/']"):
            title_el = card.select_one("h2, h3, [data-testid='job-title']")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            company_el = card.select_one("[data-testid='company-name'], .company")
            link = card.get("href", "") if card.name == "a" else ""
            if not link:
                link_el = card.select_one("a[href*='/fr/jobs/']")
                if link_el:
                    link = link_el.get("href", "")
            if link and not link.startswith("http"):
                link = "https://welcometothejungle.com" + link

            offers.append({
                "title": title,
                "company": company_el.get_text(strip=True) if company_el else "",
                "source": "WTTJ",
                "contract_type": "",
                "location": "",
                "link": link,
                "description": "",
                "date": "",
                "scraped_at": datetime.now().isoformat(),
            })

    # Normaliser le format
    normalized = []
    for o in offers:
        normalized.append({
            "title": o.get("title") or o.get("name") or "",
            "company": o.get("company") or o.get("organization_name") or o.get("employer") or "",
            "source": "WTTJ",
            "contract_type": o.get("contract_type") or o.get("contract") or "",
            "location": o.get("location") or o.get("office") or "",
            "link": o.get("link") or o.get("url") or o.get("@id") or "",
            "description": o.get("description") or "",
            "date": o.get("date") or o.get("published_at") or "",
            "scraped_at": datetime.now().isoformat(),
        })

    return {"source": "WTTJ", "offers_count": len(normalized), "offers": normalized}

if __name__ == "__main__":
    result = scrape()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\n→ {result['offers_count']} offres WTTJ", file=sys.stderr)
