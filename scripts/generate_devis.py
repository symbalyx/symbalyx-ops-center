#!/usr/bin/env python3
"""
Symbalyx — Generateur de Devis PDF automatique
Usage: python3 generate_devis.py --client "Boulangerie Moderne" --email contact@boulangerie.fr --site boulangerie-moderne.fr --phone "06 12 34 56 78" --services "correctif,audit" --total 128
       python3 generate_devis.py --interactive (mode assiste)
"""

import sys, os, json, re
from datetime import datetime
from fpdf import FPDF

# ─── CONFIG ───
COMPANY_NAME = "Symbalyx"
COMPANY_SLOGAN = "Studio web & automatisation"
AGENT_NAME = "Arsene"
AGENT_EMAIL = "arsene@symbalyx.com"
AGENT_PHONE = "06 XX XX XX XX"  # TODO: add real phone
AGENT_ADDRESS = "Bordeaux"
WEBSITE = "https://symbalyx.com"
SIRET = ""  # TODO: add SIRET if available

OUTPUT_DIR = "/tmp/devis"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SERVICES_MAP = {
    "correctif": {"name": "Correctif Express", "price": 99, "desc": "Correction des failles de securite identifiees. Mise a jour WordPress, plugins, theme. Livre sous 24 heures."},
    "audit": {"name": "Rapport d'audit PDF", "price": 29, "desc": "Rapport professionnel de 5 pages avec l'ensemble des anomalies, captures d'ecran et recommandations detaillees."},
    "maintenance": {"name": "Maintenance & Surveillance", "price": 99, "desc": "Mises a jour automatiques, surveillance de la securite, backups quotidiens. Abonnement mensuel."},
    "site": {"name": "Refonte Site Vitrine", "price": 450, "desc": "Site 3 a 5 pages, responsive, optimise SEO. Design sur mesure. Livre en 7 jours ouvre."},
    "ssl": {"name": "Installation SSL", "price": 49, "desc": "Certificat SSL Let's Encrypt + configuration HTTPS + redirection automatique."},
    "seo": {"name": "Optimisation SEO", "price": 149, "desc": "Audit SEO, meta-descriptions, balisage, Google My Business. Referencement local."},
    "urgence": {"name": "Correctif Urgent 24h", "price": 149, "desc": "Intervention prioritaire. Correction des failles critiques sous 24 heures maximum."},
}


# ─── PDF CLASS ───
class DevisPDF(FPDF):
    def __init__(self):
        super().__init__()
        # Add Unicode font
        for style, fname in [("", "DejaVuSans.ttf"), ("B", "DejaVuSans-Bold.ttf"), ("I", "DejaVuSans-Oblique.ttf"), ("BI", "DejaVuSans-BoldOblique.ttf")]:
            path = f"/usr/share/fonts/truetype/dejavu/{fname}"
            if os.path.exists(path):
                self.add_font("DejaVu", style, path, uni=True)
        
    def header(self):
        self.set_font("DejaVu", "B", 22)
        self.set_text_color(196, 85, 58)  # Terracotta
        self.cell(0, 10, "Symbalyx", new_x="LMARGIN", new_y="NEXT")
        self.set_font("DejaVu", "", 10)
        self.set_text_color(74, 74, 74)  # Charcoal
        self.cell(0, 5, "Studio web & automatisation — Bordeaux", new_x="LMARGIN", new_y="NEXT")
        self.set_font("DejaVu", "", 8)
        self.set_text_color(122, 122, 122)  # Gray
        self.cell(0, 4, f"{AGENT_EMAIL} | {WEBSITE}", new_x="LMARGIN", new_y="NEXT")
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "", 7)
        self.set_text_color(180, 180, 180)
        self.cell(0, 10, f"Symbalyx — Devis genere le {datetime.now().strftime('%d/%m/%Y')} | Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.set_font("DejaVu", "B", 10)
        self.set_text_color(12, 12, 12)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(224, 219, 212)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def info_row(self, label, value):
        self.set_font("DejaVu", "", 9)
        self.set_text_color(122, 122, 122)
        self.cell(40, 6, label)
        self.set_text_color(26, 26, 26)
        self.cell(0, 6, value, new_x="LMARGIN", new_y="NEXT")

    def finding_block(self, level, title, desc, impact):
        """Display a finding with severity color."""
        colors = {
            "critical": (192, 57, 43),
            "high": (196, 85, 58),
            "medium": (212, 162, 78),
            "low": (180, 180, 180),
        }
        color = colors.get(level, (74, 74, 74))
        
        # Severity badge
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.set_font("DejaVu", "B", 7)
        badge_w = self.get_string_width(level.upper()) + 6
        self.cell(badge_w, 5, level.upper(), fill=True)
        self.ln(6)
        
        # Title
        self.set_font("DejaVu", "B", 9)
        self.set_text_color(12, 12, 12)
        self.cell(0, 5, title, new_x="LMARGIN", new_y="NEXT")
        
        # Description
        self.set_font("DejaVu", "", 8)
        self.set_text_color(74, 74, 74)
        self.multi_cell(0, 4, desc)
        
        # Impact
        if impact:
            self.set_font("DejaVu", "I", 8)
            self.set_text_color(*color)
            self.cell(0, 4, impact, new_x="LMARGIN", new_y="NEXT")
        
        self.ln(3)

    def service_row(self, name, desc, price):
        self.set_font("DejaVu", "B", 9)
        self.set_text_color(12, 12, 12)
        self.cell(100, 5, name)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(74, 74, 74)
        self.cell(60, 5, desc, align="R")
        self.set_font("DejaVu", "B", 9)
        self.set_text_color(12, 12, 12)
        self.cell(30, 5, f"{price} EUR", align="R", new_x="LMARGIN", new_y="NEXT")


def generate_devis(client_name, client_email, client_site, client_phone, services_list, total, findings=None):
    """Generate a professional PDF quote."""
    pdf = DevisPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    now = datetime.now()
    devis_num = f"DEV-{now.strftime('%Y%m')}-{str(now.timestamp())[-4:]}"
    
    # ─── CLIENT INFO ───
    pdf.section_title("CLIENT")
    pdf.info_row("Nom / Societe", client_name)
    pdf.info_row("Email", client_email)
    pdf.info_row("Site web", client_site)
    if client_phone:
        pdf.info_row("Telephone", client_phone)
    pdf.info_row("Date du devis", now.strftime("%d/%m/%Y"))
    pdf.info_row("Numero de devis", devis_num)
    pdf.ln(4)
    
    # ─── FINDINGS (if any) ───
    if findings:
        pdf.section_title("DIAGNOSTIC")
        for finding in findings:
            pdf.finding_block(
                finding.get("level", "medium"),
                finding.get("title", "Point d'attention"),
                finding.get("desc", ""),
                finding.get("impact", "")
            )
    
    # ─── SERVICES ───
    pdf.section_title("PRESTATIONS")
    pdf.ln(2)
    
    # Header
    pdf.set_font("DejaVu", "", 7)
    pdf.set_text_color(180, 180, 180)
    pdf.cell(100, 4, "PRESTATION")
    pdf.cell(60, 4, "DETAILS", align="R")
    pdf.cell(30, 4, "MONTANT", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(224, 219, 212)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    for svc in services_list:
        if svc in SERVICES_MAP:
            s = SERVICES_MAP[svc]
            pdf.service_row(s["name"], s["desc"], s["price"])
    
    # Total line
    pdf.ln(2)
    pdf.set_draw_color(196, 85, 58)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font("DejaVu", "B", 12)
    pdf.set_text_color(12, 12, 12)
    pdf.cell(160, 8, "TOTAL", align="R")
    pdf.set_text_color(196, 85, 58)
    pdf.cell(30, 8, f"{total} EUR", align="R", new_x="LMARGIN", new_y="NEXT")
    
    # ─── CONDITIONS ───
    pdf.ln(8)
    pdf.section_title("CONDITIONS")
    
    pdf.set_font("DejaVu", "", 7.5)
    pdf.set_text_color(74, 74, 74)
    conditions = [
        "Delai de livraison : 24 a 48 heures ouvre pour les correctifs, 7 jours ouvre pour les sites.",
        "Paiement : virement bancaire ou especes. Facture fournie avec chaque prestation.",
        "Garantie : 30 jours sur les corrections apportees. La garantie couvre les bugs introduces par nos modifications.",
        "RGPD : Les donnees fournies sont utilisees uniquement dans le cadre de la prestation. Conforme au Reglement General sur la Protection des Donnees.",
        "Annulation : Possible sans frais dans les 24h suivant l'acceptation du devis.",
    ]
    for c in conditions:
        pdf.cell(5, 4, "-")
        pdf.multi_cell(0, 4, c)
        pdf.ln(1)
    
    # ─── SIGNATURE ───
    pdf.ln(10)
    pdf.section_title("ACCEPTATION")
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(74, 74, 74)
    pdf.cell(0, 5, "Date et signature du client :", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(12)
    pdf.set_draw_color(180, 180, 180)
    pdf.line(10, pdf.get_y(), 120, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(122, 122, 122)
    pdf.cell(0, 4, "Lu et approuve (nom + signature)", new_x="LMARGIN", new_y="NEXT")
    
    # ─── SAVE ───
    filename = f"devis_{client_name.lower().replace(' ','_')[:20]}_{devis_num}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)
    pdf.output(filepath)
    
    return filepath, devis_num


def parse_args():
    """Parse command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(description="Symbalyx - Generateur de Devis PDF")
    parser.add_argument("--client", help="Nom du client / societe")
    parser.add_argument("--email", help="Email du client")
    parser.add_argument("--site", help="Site web du client")
    parser.add_argument("--phone", help="Telephone du client (optionnel)", default="")
    parser.add_argument("--services", help="Services separes par des virgules (ex: correctif,audit)")
    parser.add_argument("--total", type=int, help="Montant total en EUR")
    parser.add_argument("--findings", help="Fichier JSON contenant les failles detectees (optionnel)")
    parser.add_argument("--interactive", action="store_true", help="Mode assiste interactif")
    return parser.parse_args()


def interactive_mode():
    """Interactive assistant mode."""
    print("=== Symbalyx — Assistant Devis ===")
    print()
    
    client_name = input("Nom du client / societe: ").strip()
    client_email = input("Email du client: ").strip()
    client_site = input("Site web du client: ").strip()
    client_phone = input("Telephone (optionnel): ").strip()
    
    print("\nServices disponibles:")
    for key, svc in SERVICES_MAP.items():
        print(f"  {key}: {svc['name']} — {svc['price']} EUR")
    
    services_input = input("\nServices (separes par des virgules, ex: correctif,audit): ").strip()
    services_list = [s.strip() for s in services_input.split(",") if s.strip() in SERVICES_MAP]
    
    total = sum(SERVICES_MAP[s]["price"] for s in services_list)
    
    # Optional findings
    findings_path = input("\nFichier de diagnostic JSON (optionnel, Enter pour ignorer): ").strip()
    findings = None
    if findings_path and os.path.exists(findings_path):
        with open(findings_path) as f:
            findings = json.load(f)
    
    print(f"\nTotal: {total} EUR")
    confirm = input("Generer le devis ? (O/n): ").strip().lower()
    if confirm != "n":
        filepath, devis_num = generate_devis(client_name, client_email, client_site, client_phone, services_list, total, findings)
        print(f"\nDevis genere: {filepath}")
        print(f"Numero: {devis_num}")
    else:
        print("Annule.")


if __name__ == "__main__":
    args = parse_args()
    
    if args.interactive:
        interactive_mode()
        sys.exit(0)
    
    # Required args for non-interactive mode
    if not all([args.client, args.email, args.site, args.services]):
        print("Mode interactif: python3 generate_devis.py --interactive")
        print("Mode direct: python3 generate_devis.py --client \"Nom\" --email email@site.fr --site site.fr --services correctif,audit --total 128")
        sys.exit(1)
    
    services_list = [s.strip() for s in args.services.split(",")]
    total = args.total or sum(SERVICES_MAP.get(s, {}).get("price", 0) for s in services_list)
    
    # Load findings if provided
    findings = None
    if args.findings and os.path.exists(args.findings):
        with open(args.findings) as f:
            findings = json.load(f)
    
    filepath, devis_num = generate_devis(args.client, args.email, args.site, args.phone, services_list, total, findings)
    print(f"Devis genere: {filepath}")
    print(f"Numero: {devis_num}")
    print(f"Client: {args.client}")
    print(f"Total: {total} EUR")
