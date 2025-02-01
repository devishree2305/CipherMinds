# -*- coding: utf-8 -*-
"""phisihng_mail.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1Rxh7x2OxOEHDDnod7sEL8dU8U-mdocuD
"""

pip install imapclient

pip install python-whois

import imaplib
import email
import time
import re
import csv
import os
from email.header import decode_header

# Email Credentials
EMAIL = ""  # Replace with your email
PASSWORD = ""  # Use the Gmail App Password
IMAP_SERVER = "imap.gmail.com"

# Load PhishTank Database
PHISHTANK_CSV = "/content/verified_online.csv"
phishing_urls = set()

def load_phishtank_data():
    """Load PhishTank phishing URLs into a set."""
    global phishing_urls
    if os.path.exists(PHISHTANK_CSV):
        with open(PHISHTANK_CSV, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["verified"].lower() == "yes":
                    phishing_urls.add(row["url"])
    else:
        print("⚠️ PhishTank CSV not found. Please download it.")

# Load PhishTank data
load_phishtank_data()

# Suspicious Keywords
SUSPICIOUS_KEYWORDS = [
    "verify", "urgent", "account", "payment", "suspended",
    "click here", "password", "reset", "limited", "security alert"
]

def extract_urls(text):
    """Find all URLs in the email body."""
    url_pattern = r"https?://[^\s<>\"']+"
    return re.findall(url_pattern, text)

def extract_metadata(msg):
    """Extract metadata and phishing indicators from the email headers."""
    metadata = {
        "From": msg.get("From"),
        "Reply-To": msg.get("Reply-To", "N/A"),
        "Return-Path": msg.get("Return-Path", "N/A"),
        "User-Agent": msg.get("User-Agent", msg.get("X-Mailer", "N/A")),
        "Sent Date": msg.get("Date"),
        "Message-ID": msg.get("Message-ID"),
        "Received": msg.get_all("Received", []),
        "Authentication-Results": msg.get("Authentication-Results", "N/A"),
        "SPF-Received": msg.get("Received-SPF", "N/A"),
        "DKIM-Signature": msg.get("DKIM-Signature", "N/A"),
        "DomainKey-Signature": msg.get("DomainKey-Signature", "N/A"),
    }

    # Extract Sender IP Address from "Received" headers
    received_headers = metadata["Received"]
    ip_addresses = re.findall(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", " ".join(received_headers))
    metadata["Sender IP"] = ip_addresses[-1] if ip_addresses else "Unknown"

    return metadata

def check_suspicious_content(subject, body, metadata):
    """Check for phishing indicators in email content and metadata to classify risk level."""
    phishing_score = 0

    # Check for suspicious keywords
    if any(word in subject.lower() for word in SUSPICIOUS_KEYWORDS):
        phishing_score += 2
    if any(word in body.lower() for word in SUSPICIOUS_KEYWORDS):
        phishing_score += 2

    # Extract URLs and check against PhishTank
    urls = extract_urls(body)
    for url in urls:
        if url in phishing_urls:
            phishing_score += 5

    # Check email metadata for suspicious elements
    if metadata["SPF-Received"] == "fail":
        phishing_score += 3
    if "dkim=fail" in metadata["Authentication-Results"]:
        phishing_score += 3
    if "Sender IP" in metadata and metadata["Sender IP"] == "Unknown":
        phishing_score += 2
    if metadata["Reply-To"] and metadata["Reply-To"] != metadata["From"]:
        phishing_score += 2
    if metadata["Return-Path"] and metadata["Return-Path"] != metadata["From"]:
        phishing_score += 2

    # Assign risk level based on score
    risk_level = "High Risk" if phishing_score >= 10 else "Medium Risk" if phishing_score >= 7 else "Low Risk" if phishing_score >= 4 else "Safe"

    return phishing_score, urls, risk_level

def fetch_latest_email(mail):
    """Fetch and analyze the latest unread email."""
    try:
        mail.select("inbox")
        status, messages = mail.search(None, "UNSEEN")
        email_ids = messages[0].split()
        if not email_ids:
            return

        latest_email_id = email_ids[-1]
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])

                # Decode Subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")

                sender = msg.get("From")
                sent_date = msg.get("Date")

                # Extract Metadata
                metadata = extract_metadata(msg)

                # Extract Email Body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                # Analyze phishing risk
                phishing_score, urls, risk_level = check_suspicious_content(subject, body, metadata)

                # Print email details
                print("\n📩 **New Email Received**")
                print(f"📌 **From:** {sender}")
                print(f"📌 **Sent Date:** {sent_date}")
                print(f"📌 **Subject:** {subject}")
                print(f"⚠️ **Risk Level:** {risk_level} (Score: {phishing_score})")

                # Print metadata
                print("\n🔍 **Email Metadata**")
                for key, value in metadata.items():
                    print(f"📌 **{key}:** {value}")

                # Print extracted URLs
                if urls:
                    print("\n🔗 **Extracted URLs:**")
                    for url in urls:
                        print(f"🌐 {url}")

                # Mark email as read
                mail.store(latest_email_id, '+FLAGS', '\\Seen')

    except Exception as e:
        print(f"Error fetching email: {e}")

def listen_for_new_email():
    """Listen for new email using IMAP polling (checks every 5 seconds)."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        print("🔄 Listening for new emails...")

        while True:
            mail.select("inbox")
            status, response = mail.search(None, "UNSEEN")  # Check for unread emails
            unread_email_ids = response[0].split()

            if unread_email_ids:
                fetch_latest_email(mail)

            time.sleep(5)  # Reduce server load; adjust as needed

    except KeyboardInterrupt:
        print("\n🛑 Stopping email listener.")
    except imaplib.IMAP4.error:
        print("❌ Authentication failed. Check email & password.")
    except Exception as e:
        print(f"⚠️ Error: {e}")
    finally:
        try:
            mail.logout()
        except:
            pass

if __name__ == "__main__":
    listen_for_new_email()

import imaplib
import smtplib
import email
import time
import re
import csv
import os
from email.header import decode_header
from email.mime.text import MIMEText

# Email Credentials
EMAIL = "edswfrgrf"
PASSWORD = "2143254765"
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
FORWARD_TO = "dsgfgh"

# Load PhishTank Database
PHISHTANK_CSV = "/content/verified_online.csv"
phishing_urls = set()

def load_phishtank_data():
    """Load PhishTank phishing URLs into a set."""
    global phishing_urls
    if os.path.exists(PHISHTANK_CSV):
        with open(PHISHTANK_CSV, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["verified"].lower() == "yes":
                    phishing_urls.add(row["url"])
    else:
        print("⚠️ PhishTank CSV not found. Please download it.")

# Load data initially
load_phishtank_data()

SUSPICIOUS_KEYWORDS = ["verify", "urgent", "account", "payment", "suspended", "click here", "password", "reset", "limited", "security alert"]

def extract_urls(text):
    """Find all URLs in the email body."""
    url_pattern = r"https?://[^\s<>\"']+"
    return re.findall(url_pattern, text)

def check_suspicious_content(subject, body):
    """Check for phishing indicators in email content and classify risk level."""
    phishing_score = 0

    if any(word in subject.lower() for word in SUSPICIOUS_KEYWORDS):
        phishing_score += 2
    if any(word in body.lower() for word in SUSPICIOUS_KEYWORDS):
        phishing_score += 2

    urls = extract_urls(body)
    for url in urls:
        if url in phishing_urls:
            phishing_score += 5

    return phishing_score, urls

def fetch_latest_email(mail):
    """Fetch and analyze the latest unread email."""
    try:
        mail.select("inbox")
        status, messages = mail.search(None, "UNSEEN")
        email_ids = messages[0].split()
        if not email_ids:
            return

        latest_email_id = email_ids[-1]
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")

                sender = msg.get("From")
                sent_date = msg.get("Date")

                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                phishing_score, urls = check_suspicious_content(subject, body)
                risk_level = "High Risk" if phishing_score >= 10 else "Medium Risk" if phishing_score >= 7 else "Low Risk" if phishing_score >= 4 else "Safe"

                print(f"\n📩 **New Email Received**")
                print(f"📌 **From:** {sender}")
                print(f"📌 **Sent Date:** {sent_date}")
                print(f"📌 **Subject:** {subject}")
                print(f"⚠️ **Risk Level:** {risk_level} (Score: {phishing_score})")

                if urls:
                    print(f"🔗 **Extracted URLs:**")
                    for url in urls:
                        print(f"🌐 {url}")

                # Forward email only if the phishing score is 10 or more
                if phishing_score >= 10:
                    forward_email(msg)

                # Mark email as read
                mail.store(latest_email_id, '+FLAGS', '\\Seen')
    except Exception as e:
        print(f"Error fetching email: {e}")

def forward_email(msg):
    """Forward an email via SMTP."""
    try:
        smtp = smtplib.SMTP(SMTP_SERVER, 587)
        smtp.starttls()
        smtp.login(EMAIL, PASSWORD)

        subject = "FWD: " + (msg["Subject"] if msg["Subject"] else "(No Subject)")

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")

        msg_forward = MIMEText(body)
        msg_forward["From"] = EMAIL
        msg_forward["To"] = FORWARD_TO
        msg_forward["Subject"] = subject

        smtp.sendmail(EMAIL, FORWARD_TO, msg_forward.as_string())
        smtp.quit()
        print("📨 Email forwarded successfully.")
    except Exception as e:
        print(f"⚠️ Error forwarding email: {e}")

def listen_for_new_email():
    """Listen for new email using IMAP polling."""
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)

    mail.login(EMAIL, PASSWORD)
    print("🔄 Listening for new emails...")

    try:
        while True:
            mail.select("inbox")
            status, response = mail.search(None, "UNSEEN")  # Check for unread emails
            unread_email_ids = response[0].split()

            if unread_email_ids:
                fetch_latest_email(mail)

            time.sleep(5)  # Reduce server load; adjust as needed

    except KeyboardInterrupt:
        print("\n🛑 Stopping email listener.")
    finally:
        mail.logout()

if __name__ == "__main__":
    listen_for_new_email()