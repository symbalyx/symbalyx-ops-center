# Projet Talentsphere

**Veille automatisee des offres d'emploi et appels d'offres dans le secteur media francais**

## Client
Jerome Chouraqui · Talentsphere  
Contact : jerome.chouraqui@talentsphere.fr  
Source : community.n8n.io

## Perimetre
Scraper 5+ sources, enrichir avec GPT, envoyer email hebdomadaire automatise.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  n8n Workflow                        │
│  Declenchement: Chaque lundi a 08:00                 │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ProfilCulture ──┬── HTTP + HTML Extract              │
│  Groupe TF1    ──┤── HTTP + HTML Extract              │
│  Arte          ──┤── HTTP + HTML Extract              │
│  France TV     ──┤── HTTP + HTML Extract              │
│  WTTJ          ──┘── HTTP + JSON Extract              │
│                                                       │
│       ┌──────────────────────┐                        │
│       │    Merge + Dedup     │                        │
│       └──────────┬───────────┘                        │
│                  │                                     │
│       ┌──────────▼───────────┐                        │
│       │  GPT Enrichissement  │                        │
│       └──────────┬───────────┘                        │
│                  │                                     │
│       ┌──────────▼───────────┐                        │
│       │  Format Email HTML   │                        │
│       └──────────┬───────────┘                        │
│                  │                                     │
│       ┌──────────▼───────────┐                        │
│       │     ENVOI EMAIL      │                        │
│       └──────────────────────┘                        │
└─────────────────────────────────────────────────────┘
```

## Fichiers fournis

```
talentsphere/
├── README.md                          # Ce fichier
├── architecture/
│   ├── architecture.md                # Documentation architecture complete
│   └── workflow-n8n.json              # Export du workflow n8n (a importer)
├── scraping/
│   ├── scraper_profilculture.py       # Scraper ProfilCulture
│   ├── scraper_tf1.py                 # Scraper Groupe TF1
│   ├── scraper_arte.py                # Scraper Arte (3 sous-domaines)
│   ├── scraper_francetv.py            # Scraper France TV
│   ├── scraper_wttj.py                # Scraper Welcome to the Jungle
│   └── orchestrator.py                # Lance tous les scrapers + agrège
├── enrichment/
│   └── gpt_enricher.py                # Pipeline GPT-4o-mini
├── email/
│   └── template.html                  # Template email responsive
└── alternatives.md                    # Solutions pour sources bloquees
```

## Budget
- **5 jours de travail** : 1 800 EUR TTC
- **Hebergement** : VPS 8€/mois (Hetzner) ou n8n Cloud 20$/mois
- **Support 1 mois** : inclus
- **Maintenance au-dela** : 150€/mois

## Pre-requis
- Compte n8n (auto-heberge sur VPS ou n8n.cloud)
- Cle API OpenAI (gpt-4o-mini)
- Serveur SMTP pour l'envoi d'email

## Pour demarrer
1. Deployer n8n sur un VPS (Hetzner CX22 à 8€/mois)
2. Importer `architecture/workflow-n8n.json` dans n8n
3. Configurer les credentials (OpenAI, SMTP)
4. Definir l'email du destinataire dans le node "ENVOYER email"
5. Activer le workflow

## Test
```bash
# Tester un scraper individuellement
python3 scraping/scraper_profilculture.py

# Tester tous les scrapers
python3 scraping/orchestrator.py

# Tester l'enrichissement GPT (cle API requise)
cat offres.json | python3 enrichment/gpt_enricher.py
```
