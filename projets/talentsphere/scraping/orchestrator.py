#!/usr/bin/env python3
"""
Orchestrateur Talentsphere — Lance tous les scrapers et agrège les resultats
Usage: python3 orchestrator.py
"""
import json
import sys
import subprocess
from datetime import datetime
from pathlib import Path

SCRAPERS_DIR = Path(__file__).parent
SCRAPERS = [
    "scraper_profilculture.py",
    "scraper_tf1.py",
    "scraper_arte.py",
    "scraper_francetv.py",
    "scraper_wttj.py",
]

def run_scraper(name):
    """Execute un script scraper et retourne ses resultats"""
    path = SCRAPERS_DIR / name
    if not path.exists():
        return {"source": name, "error": "Script non trouve", "offers": []}
    try:
        result = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return {"source": name, "error": result.stderr[:200], "offers": []}
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return {"source": name, "error": "Timeout (60s)", "offers": []}
    except json.JSONDecodeError:
        return {"source": name, "error": "JSON invalide", "offers": []}

def deduplicate(offers):
    """Deduplication par titre + source"""
    seen = set()
    unique = []
    for o in offers:
        key = f"{o.get('title','').lower().strip()}|{o.get('source','')}"
        if key not in seen and o.get('title'):
            seen.add(key)
            unique.append(o)
    return unique

def main():
    all_offers = []
    results = []

    print("=== Talentsphere — Veille emploi media ===", file=sys.stderr)
    print(f"Lancement: {datetime.now().isoformat()}", file=sys.stderr)
    print(file=sys.stderr)

    for scraper in SCRAPERS:
        print(f"  Scraping {scraper}...", file=sys.stderr, end=" ")
        result = run_scraper(scraper)
        count = len(result.get("offers", []))
        if result.get("error"):
            print(f"ERREUR: {result['error'][:60]}", file=sys.stderr)
        else:
            print(f"{count} offres", file=sys.stderr)
        results.append(result)
        all_offers.extend(result.get("offers", []))

    # Deduplication
    unique = deduplicate(all_offers)

    # Stats par source
    by_source = {}
    for o in unique:
        src = o.get("source", "Inconnu")
        by_source.setdefault(src, 0)
        by_source[src] += 1

    output = {
        "generated_at": datetime.now().isoformat(),
        "total_raw": len(all_offers),
        "total_unique": len(unique),
        "by_source": by_source,
        "offers": unique,
        "scrapers_results": [
            {
                "source": r.get("source"),
                "count": len(r.get("offers", [])),
                "error": r.get("error"),
            }
            for r in results
        ],
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))

    # Rapport console
    print(file=sys.stderr)
    print("=== RESULTATS ===", file=sys.stderr)
    print(f"  Total brut: {len(all_offers)}", file=sys.stderr)
    print(f"  Total unique: {len(unique)}", file=sys.stderr)
    for src, count in sorted(by_source.items()):
        print(f"  {src}: {count}", file=sys.stderr)

if __name__ == "__main__":
    main()
