# Alternatives pour les sources bloquees

## Source #2 — Ecran Total (ecran-total.fr)
**Probleme :** Site protege par Cloudflare (BigScoots). Challenge JS + CAPTCHA.
Tentatives de scraping echouees (curl, wget, requests).

### Solutions possibles

| Solution | Cout | Fiabilite | Effort |
|----------|------|-----------|--------|
| **ScrapingBee API** | 0.01$/appel (~0.30$/semaine) | Haute | Integration n8n simple (HTTP node) |
| **Rotation proxies + Playwright** | ~5$/mois (proxies) | Moyenne | Maintenance lourde, detection possible |
| **Google Cache** | Gratuit | Moyenne | Donnees potentiellement obsoletes |
| **Remplacement LinkedIn** | Gratuit | Haute | Scraper les offres emploi media via LinkedIn |
| **API Pole Emploi** | Gratuite | Haute | Offres du secteur culture/media referencees |

### Recommandation : ScrapingBee (0.30$/semaine)
1. Creer un compte ScrapingBee (offre gratuite 25 appels/mois)
2. Appeler : `https://app.scrapingbee.com/api/v1/?api_key=KEY&url=https://ecran-total.fr/offres`
3. Pas de gestion de CAPTCHA, pas de proxies
4. Cout quasi nul pour une veille hebdomadaire

Si Jerome prefere eviter tout cout : remplacer par les offres "culture/cinema" de **Welcome to the Jungle** et **LinkedIn**.

---

## Source #6 — Groupe M6
**Probleme :** `m6.fr` = site de replay (M6+). Pas de page recrutement.
`groupe-m6.fr` = erreur TLS (certificat invalide). Impossible de trouver le portail RH.

### Solutions possibles

| Solution | Fiabilite | Effort |
|----------|-----------|--------|
| **LinkedIn Groupe M6** | Haute | Gratuit, offres RH officielles |
| **WTTJ recherche 'M6'** | Haute | Deja dans les sources, simple filtre |
| **Welcome to the Jungle / Groupe M6** | Haute | Page carriere officielle |
| **Contact RH direct** | Tres haute | Demande un email ou appel |

### Recommandation : WTTJ + LinkedIn
1. WTTJ est deja dans les sources → ajouter "M6" aux mots-cles de recherche
2. LinkedIn : scraper les offres Groupe M6 via API (ou consultation manuelle)
3. Alternative : les offres M6 sont souvent publiees sur **ProfilCulture** (deja scrape)

---

## Sources de remplacement supplementaires (a proposer a Jerome)

| Source | URL | Type | Pourquoi |
|--------|-----|------|----------|
| **LinkedIn** | linkedin.com/jobs | API/Scraping | Tous les groupes media y postent |
| **Pole Emploi** | api.pole-emploi.io | API gratuite | Secteur culture/media reference |
| **Indeed** | indeed.fr | Scraping | Large volume d'offres media |
| **Afdas** | afdas.com | Site pro | Offres specifiques secteur culture |
| **La Ciotat - Series Mania** | seriesmania.com | Evenementiel | Appels d'offres et emplois |
| **CNC** | cnc.fr | Site institutionnel | Appels d'offres cinema/audiovisuel |

---

## Plan d'action si Jerome veut les 7 sources

1. **Semaine 1** : Deployer les 5 sources accessibles (ProfilCulture, TF1, Arte, France TV, WTTJ)
2. **Semaine 2** : Ajouter ScrapingBee pour Ecran Total (0.30$/semaine)
3. **Semaine 3** : Integrer LinkedIn API pour M6 + sources supplementaires selon ses besoins
4. **Maintenance** : 1 mois inclus, puis 150€/mois si correctifs necessaires
