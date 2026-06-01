#!/usr/bin/env python3
"""
Pipeline d'enrichissement GPT pour les offres d'emploi media
Utilise l'API OpenAI pour resumer, categoriser et prioriser chaque offre.

Usage: 
  python3 gpt_enricher.py < fichier_offres.json
  cat offres.json | python3 gpt_enricher.py

Input: JSON avec champ "offers" (tableau d'objets avec title, company, etc.)
Output: JSON avec les offres enrichies (summary, tags, urgency)
"""
import json
import sys
import os
import re

def build_prompt(offers):
    """Construit le prompt systeme + utilisateur pour GPT"""
    system_prompt = """Tu es un assistant specialise dans le secteur media francais (television, cinema, production, audiovisuel, radio, presse). Pour chaque offre d'emploi, tu extrais et enrichis les informations.

Reponds UNIQUEMENT avec un tableau JSON valide. Chaque element doit contenir :
- title: titre du poste
- company: entreprise / media
- contract_type: type de contrat (CDI, CDD, Freelance, Stage, Alternance, Interim)
- location: localisation
- summary: resume en 1 phrase (20 mots max)
- tags: tableau de 3 mots-cles parmi : ['Production','Journalisme','Technique','Marketing','Commercial','Direction','RH','Design','Communication','Digital','Administratif','Juridique','Alternance']
- urgency: niveau d'urgence de 1 a 3 (1=faible, 2=moyen, 3=eleve)
- source: source originale de l'offre"""

    # Limiter a 30 offres par appel pour eviter les depassements de tokens
    batch = offers[:30]
    user_prompt = "Voici les offres d'emploi media a analyser :\n\n"
    user_prompt += json.dumps(batch, ensure_ascii=False, indent=2)
    user_prompt += "\n\nRetourne UNIQUEMENT le tableau JSON, sans commentaires ni markdown."

    return system_prompt, user_prompt

def call_openai(system_prompt, user_prompt):
    """Appelle l'API OpenAI via curl (pas de dependance openai pip)"""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return {"error": "OPENAI_API_KEY non definie dans l'environnement"}

    payload = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 3000,
    })

    import subprocess
    try:
        result = subprocess.run(
            ["curl", "-s", "https://api.openai.com/v1/chat/completions",
             "-H", f"Authorization: Bearer {api_key}",
             "-H", "Content-Type: application/json",
             "-d", payload],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return {"error": f"curl error: {result.stderr[:200]}"}

        data = json.loads(result.stdout)
        if "error" in data:
            return {"error": data["error"].get("message", str(data["error"]))}

        content = data["choices"][0]["message"]["content"]

        # Extraire le JSON de la reponse
        json_match = re.search(r'(\[.*\])', content, re.DOTALL)
        if json_match:
            enriched = json.loads(json_match.group(1))
            return {"enriched": enriched}
        else:
            return {"error": "Pas de JSON trouve dans la reponse GPT", "raw": content[:200]}

    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        return {"error": str(e)}

def enrich(offers, api_key=None):
    """Point d'entree principal : enrichit une liste d'offres"""
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    if not offers:
        return {"enriched": [], "error": "Aucune offre a enrichir"}

    system_prompt, user_prompt = build_prompt(offers)
    result = call_openai(system_prompt, user_prompt)

    if "error" in result:
        # Fallback: enrichissement basique sans IA
        return {
            "enriched": [
                {
                    "title": o.get("title", ""),
                    "company": o.get("company", ""),
                    "source": o.get("source", ""),
                    "contract_type": o.get("contract_type", ""),
                    "location": o.get("location", ""),
                    "summary": "",
                    "tags": ["Media"],
                    "urgency": 2,
                }
                for o in offers
            ],
            "error": result["error"],
            "fallback": True
        }

    return result

if __name__ == "__main__":
    # Lecture depuis stdin ou fichier
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    offers = data.get("offers", data if isinstance(data, list) else [])
    if isinstance(data, dict) and "offers" not in data:
        offers = [data]

    result = enrich(offers)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result.get("enriched"):
        print(f"\n✓ {len(result['enriched'])} offres enrichies", file=sys.stderr)
    if result.get("error"):
        print(f"⚠ {result['error']}", file=sys.stderr)
    if result.get("fallback"):
        print("⚠ Enrichissement basique (sans IA) utilise", file=sys.stderr)
