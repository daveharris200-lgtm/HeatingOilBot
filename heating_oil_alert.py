import smtplib
import os
import requests
import re
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

# --- CONFIG ---
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")
RECIPIENTS = os.environ.get("EMAIL_RECIPIENTS").split(",")

# URL with live UK heating oil price
URL = "https://uk-public.boilerjuice.com/uk/heating-oil-prices/"

# --- SCRAPE BoilerJuice ---
response = requests.get(URL)
soup = BeautifulSoup(response.text, "html.parser")

# Convert whole page to text and find pattern "Today’s ... pence per litre"
text = soup.get_text(separator="\n")

# Regex to match something like "Today’s ...: 60.52 pence per litre"
match = re.search(r"Today.*?([\d]+\.\d+)\s*pence per litre", text, re.IGNORECASE)
if match:
    price = match.group(1)
else:
    price = "N/A"

# --- EMAIL CONTENT ---
subject = "UK Heating Oil Price Alert"
body = f"The current average UK heating oil price is: {price} pence per litre (from BoilerJuice)"

msg = MIMEText(body)
msg["Subject"] = subject
msg["From"] = GMAIL_USER
msg["To"] = ", ".join(RECIPIENTS)

# --- SEND EMAIL ---
try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, RECIPIENTS, msg.as_string())
    print("Email sent successfully!")
except Exception as e:
    print(f"Error sending email: {e}")
