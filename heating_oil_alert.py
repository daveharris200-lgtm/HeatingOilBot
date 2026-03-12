import smtplib
import requests
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import os

# --- CONFIG ---
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")
RECIPIENTS = os.environ.get("EMAIL_RECIPIENTS").split(",")

# --- SCRAPE BoilerJuice ---
url = "https://www.boilerjuice.com/uk/heating-oil-prices"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# Find the current average price (pence per litre)
price_text = soup.find("span", class_="o-curr-price")  # Example selector
if price_text:
    price = price_text.text.strip()
else:
    price = "N/A"

# --- EMAIL CONTENT ---
subject = "UK Heating Oil Price Alert"
body = f"The current average UK heating oil price is: {price} p/litre"

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
