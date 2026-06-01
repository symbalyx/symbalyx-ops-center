#!/usr/bin/env python3
"""
Symbalyx — Devis Auto-Service
Reçoit une demande de devis, génère le PDF, l'envoie par email au client.

Usage:
  python3 serve_devis.py           # Serveur HTTP (port 8765)
  python3 serve_devis.py --generate "Nom" email@site.fr site.fr 99  # Génération directe
  
API:
  POST /devis
    {"client": "Nom", "email": "client@site.fr", "site": "site.fr", 
     "service": "correctif", "amount": 99}
    → 200 {"status": "sent", "pdf": "devis_xxx.pdf", "to": "client@site.fr"}
"""

import sys, os, json, smtplib, base64
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add venv fpdf to path
sys.path.insert(0, "/opt/data/home/.venv/lib/python3.13/site-packages")

from generate_devis import generate_devis, SERVICES_MAP

# ─── SMTP CONFIG ───
SMTP_HOST = "smtp.zoho.eu"
SMTP_PORT = 465
SMTP_USER = "arsene@symbalyx.com"
SMTP_PASS = "h622sZ8AHrN2"
FROM_NAME = "Arsene — Symbalyx"
FROM_EMAIL = "arsene@symbalyx.com"

# ─── STATE ───
STATE_FILE = "/tmp/devis_service_state.json"
OUTPUT_DIR = "/tmp/devis"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def send_pdf_by_email(client_name, client_email, pdf_path, amount, service_name):
    """Send the PDF devis to the client via Zoho SMTP."""
    msg = MIMEText(f"Bonjour,\n\nVous trouverez ci-joint votre devis personnalise.\n\nClient: {client_name}\nPrestation: {service_name}\nMontant: {amount} EUR\n\narsene@symbalyx.com", "plain")
    msg["From"] = FROM_EMAIL
    msg["To"] = client_email
    msg["Subject"] = f"Devis {client_name} — {amount} EUR — Symbalyx"
    
    # Attach PDF as a plain attachment in raw SMTP
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    
    import base64 as b64
    pdf_b64 = b64.b64encode(pdf_data).decode()
    
    boundary = "==SYMBALYX_DEVIS_BOUNDARY=="
    raw_msg = f"""From: {FROM_EMAIL}
To: {client_email}
Subject: Devis {client_name} - {amount} EUR - Symbalyx
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="{boundary}"

--{boundary}
Content-Type: text/plain; charset="utf-8"

Bonjour,

Vous trouverez ci-joint votre devis personnalise.

Client: {client_name}
Prestation: {service_name}
Montant: {amount} EUR

Bien cordialement,
Arsene
Symbalyx - Studio web & automatisation
arsene@symbalyx.com

---
Ce devis est valable 30 jours. Conforme RGPD.

--{boundary}
Content-Type: application/pdf
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename="{os.path.basename(pdf_path)}"

{pdf_b64}
--{boundary}--"""
    
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(FROM_EMAIL, [client_email], raw_msg.encode("utf-8"))
    
    return True


class DevisHandler(BaseHTTPRequestHandler):
    """HTTP handler for devis requests."""
    
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._response(400, {"error": "JSON invalide"})
            return
        
        client = data.get("client", "").strip()
        email = data.get("email", "").strip()
        site = data.get("site", "").strip()
        service = data.get("service", "correctif")
        amount = data.get("amount", 99)
        
        if not client or not email:
            self._response(400, {"error": "client et email requis"})
            return
        
        # Validate service
        if service not in SERVICES_MAP:
            service = "correctif"
        
        service_name = SERVICES_MAP[service]["name"]
        if not amount:
            amount = SERVICES_MAP[service]["price"]
        
        try:
            # Generate PDF
            findings = data.get("findings", None)
            pdf_path, devis_num = generate_devis(client, email, site, "", [service], int(amount), findings)
            
            # Send by email
            send_pdf_by_email(client, email, pdf_path, int(amount), service_name)
            
            # Log
            state = {"last": {"client": client, "email": email, "amount": amount, "devis_num": devis_num, "at": datetime.now().isoformat()}}
            with open(STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
            
            self._response(200, {
                "status": "sent",
                "pdf": os.path.basename(pdf_path),
                "devis_num": devis_num,
                "to": email,
                "amount": amount
            })
            
        except Exception as e:
            self._response(500, {"error": str(e)[:200]})
    
    def do_GET(self):
        if self.path == "/status":
            state = {"status": "ok", "service": "Symbalyx Devis Auto", "version": "1.0"}
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE) as f:
                    state["last"] = json.load(f)
            self._response(200, state)
        else:
            self._response(200, {
                "service": "Symbalyx Devis Auto-Service",
                "usage": "POST /devis avec JSON {client, email, site, service, amount}",
                "endpoints": {"/devis": "POST - generer et envoyer un devis", "/status": "GET - etat du service"}
            })
    
    def _response(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))
    
    def log_message(self, format, *args):
        pass  # Quiet


def generate_and_send(client, email, site, amount):
    """Direct CLI mode: generate PDF and send by email."""
    service = "correctif"
    if amount == 29: service = "audit"
    elif amount == 450: service = "site"
    elif amount == 149: service = "seo"
    
    service_name = SERVICES_MAP[service]["name"]
    pdf_path, devis_num = generate_devis(client, email, site, "", [service], int(amount))
    send_pdf_by_email(client, email, pdf_path, int(amount), service_name)
    print(f"Devis {devis_num} envoye a {email}")
    print(f"Montant: {amount} EUR — {service_name}")
    return pdf_path


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--generate":
        # Direct mode: --generate "Nom" email site.fr 99
        client = sys.argv[2]
        email = sys.argv[3]
        site = sys.argv[4]
        amount = int(sys.argv[5]) if len(sys.argv) > 5 else 99
        generate_and_send(client, email, site, amount)
    else:
        # HTTP server mode
        port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8765
        server = HTTPServer(("0.0.0.0", port), DevisHandler)
        print(f"Symbalyx Devis Service — en ecoute sur http://0.0.0.0:{port}")
        print(f"  POST /devis    — Creer et envoyer un devis")
        print(f"  GET  /status   — Etat du service")
        print(f"  GET  /         — Aide")
        server.serve_forever()
