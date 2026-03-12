import smtplib
import os
import requests
import re
import csv
from datetime import datetime
from statistics import mean
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt

GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")
RECIPIENTS = os.environ.get("EMAIL_RECIPIENTS").split(",")

URL = "https://uk-public.boilerjuice.com/uk/heating-oil-prices/"
DATA_FILE = "heating_oil_prices.csv"
CHART_FILE = "price_chart.png"

# --- SCRAPE PRICE ---
response = requests.get(URL)
soup = BeautifulSoup(response.text, "html.parser")

text = soup.get_text(separator="\n")
match = re.search(r"Today.*?([\d]+\.\d+)\s*pence per litre", text, re.IGNORECASE)

price = float(match.group(1)) if match else None
today = datetime.utcnow().strftime("%Y-%m-%d")

# --- LOAD HISTORY ---
dates = []
prices = []

if os.path.exists(DATA_FILE):
    with open(DATA_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            dates.append(row["date"])
            prices.append(float(row["price_ppl"]))

previous_price = prices[-1] if prices else None

# --- DAILY CHANGE ---
change = None
trend = "➡"

if previous_price and price:
    change = round(price - previous_price, 2)

    if change > 0:
        trend = "📈"
    elif change < 0:
        trend = "📉"

# --- BUY SIGNAL LOGIC ---
buy_signal = False
signal_reason = ""

if len(prices) >= 30:

    avg30 = mean(prices[-30:])

    if price < avg30:
        buy_signal = True
        signal_reason = "Price below 30-day average"

if len(prices) >= 7:

    weekly_change = price - prices[-7]

    if weekly_change <= -3:
        buy_signal = True
        signal_reason = "Price dropped more than 3 ppl in a week"

# --- SAVE TODAY ---
file_exists = os.path.exists(DATA_FILE)

with open(DATA_FILE, "a", newline="") as f:
    writer = csv.writer(f)

    if not file_exists:
        writer.writerow(["date", "price_ppl"])

    writer.writerow([today, price])

# --- UPDATE LISTS ---
dates.append(today)
prices.append(price)

# --- GENERATE CHART ---
if len(prices) > 1:

    last_dates = dates[-30:]
    last_prices = prices[-30:]

    plt.figure()
    plt.plot(last_dates, last_prices)
    plt.xticks(rotation=45)
    plt.title("UK Heating Oil Price – Last 30 Days")
    plt.tight_layout()
    plt.savefig(CHART_FILE)

# --- EMAIL ---
msg = MIMEMultipart()

body = f"""
UK Heating Oil Price Update

Today's price: {price} pence per litre
Change from yesterday: {change} ppl {trend}
"""

if buy_signal:
    body += f"""

🔥 BUY SIGNAL

Reason: {signal_reason}
"""

msg.attach(MIMEText(body))

msg["Subject"] = "UK Heating Oil Price Alert"
msg["From"] = GMAIL_USER
msg["To"] = ", ".join(RECIPIENTS)

# --- ATTACH WEEKLY CHART (Sunday) ---
weekday = datetime.utcnow().weekday()

if weekday == 6 and os.path.exists(CHART_FILE):
    with open(CHART_FILE, "rb") as f:
        img = MIMEImage(f.read())
        img.add_header("Content-Disposition", "attachment", filename="heating_oil_chart.png")
        msg.attach(img)

# --- SEND ---
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(GMAIL_USER, GMAIL_PASSWORD)
    server.sendmail(GMAIL_USER, RECIPIENTS, msg.as_string())

print("Email sent successfully")
