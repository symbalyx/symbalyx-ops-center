# Projet Talentsphere — Veille emploi media automatisee

## Architecture du workflow (n8n)

### Schema general

```
[Schedule: Lundi 8h]
         |
    +----+----+----+----+----+
    |    |    |    |    |    |
Profil  TF1  Arte France  WTTJ
Culture          TV
    |    |    |    |    |    |
 [Parser HTML / Extract JSON]
    |    |    |    |    |    |
    +----+----+----+----+----+
              |
          [Merge]
              |
      [Deduplication]
              |
      [GPT Enrichissement]
              |
      [Format email HTML]
              |
       [ENVOI EMAIL]
```

### Sources scrapees

| # | Source | URL | Methode | Status |
|---|--------|-----|---------|--------|
| 1 | ProfilCulture | profilculture.com | HTTP + HTML Parser | OK |
| 2 | Groupe TF1 | groupe-tf1.fr | HTTP + HTML Parser | OK |
| 3 | Arte | arte.tv/corporate/emplois | HTTP + HTML Parser | OK |
| 4 | France TV | recrutement.francetelevisions.fr | HTTP + HTML Parser | OK |
| 5 | WTTJ | welcometothejungle.com | HTTP + Next.js JSON extract | OK |
| 6 | Ecran Total | ecran-total.fr | ScrapingBee / alternative | Bloque Cloudflare |
| 7 | Groupe M6 | A identifier | A definir | Page emploi introuvable |

### Etapes du workflow

#### 1. Declenchement
- Cron n8n : chaque lundi a 08:00
- Possible de declencher manuellement pour un test

#### 2. Scraping parallele (5 branches simultanees)
Chaque branche :
1. HTTP Request vers la source
2. Parsing HTML (n8n HTML Extract) ou extraction JSON (Code node)
3. Normalisation au format commun

**Format commun de sortie :**
```json
{
  "title": "Charge de production",
  "company": "TF1",
  "source": "Groupe TF1",
  "contract_type": "CDI",
  "location": "Paris",
  "link": "https://...",
  "description": "...",
  "date": "2026-06-01",
  "scraped_at": "2026-06-01T08:01:00Z"
}
```

#### 3. Merge + Deduplication
- Fusion de toutes les branches (n8n Merge node)
- Deduplication par titre + entreprise (Code node)
- Filtrage : uniquement les offres publiees dans les 7 derniers jours

#### 4. Enrichissement GPT (gpt-4o-mini)
Appel OpenAI avec le prompt suivant :

```
System: Tu es assistant specialise secteur media francais.
Pour chaque offre, extrais : titre, entreprise, type contrat,
localisation, resume (20 mots), 3 tags, urgence (1-3).
Reponds UNIQUEMENT en JSON.
```

#### 5. Generation email
- Template HTML responsive
- Regroupe par source (sous-titres colores)
- Tags de categorie (pastilles)
- Lien direct vers chaque offre

#### 6. Envoi
- Email depuis arsene@symbalyx.com
- Destinataire : jerome.chouraqui@talentsphere.fr
- Objet : "Veille Emploi Media — Lundi 1 juin 2026"
- Tracking pixel ouvertures

### Alternatives pour sources bloquees

**Ecran Total (Cloudflare)**
- Option 1 : Remplacement par LinkedIn Jobs (scraping Google Cache)
- Option 2 : API Pole Emploi (offres media/culture)
- Option 3 : ScrapingBee (service payant ~0.01$/appel)
- Option 4 : Scraper via Playwright + proxy (maintenance lourde)
- Recommande : ScrapingBee + URL ecran-total.fr

**Groupe M6**
- Option 1 : LinkedIn scraping (offres Groupe M6)
- Option 2 : Welcome to the Jungle recherche "M6"
- Option 3 : Contacter directement le RH Groupe M6
- Recommande : WTTJ deja dans les sources + LinkedIn complement

### Budget (5 jours)

| Poste | Jours | Montant |
|-------|-------|---------|
| Setup n8n + hebergement | 0.5 | 180€ |
| Scripts scraping (5 sources) | 1.5 | 540€ |
| Pipeline GPT + tests | 1 | 360€ |
| Template email + integrations | 1 | 360€ |
| Documentation + support 1 mois | 1 | 360€ |
| **Total** | **5** | **1 800€ TTC** |

### Deploiement

**Hebergement necessaire :**
- Option A : VPS 8€/mois (Hetzner, Scaleway) + n8n auto-heberge
- Option B : n8n Cloud (20$/mois) — zero maintenance
- Recommande : Option A (VPS 8€) pour le rapport qualite/prix

### Scripts fournis
Les scripts Python dans `/scripts/scraping/` permettent de tester chaque source
independamment avant l'integration dans n8n.

### Maintenance
- Support 1 mois inclus (corrections si les sites changent de structure)
- Au-dela : forfait maintenance 150€/mois (veille + correctifs)
