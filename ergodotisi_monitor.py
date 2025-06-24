# ergodotisi_monitor.py

import requests
from bs4 import BeautifulSoup
import os
import csv
import time
import telegram

URL = "https://www.ergodotisi.com/en-CY"
CSV_FILE = "ergodotisi_jobs.csv"

# Keywords to match
KEYWORDS = [
    "bioinformatics", "biology", "data analysis", "cancer", "genomics", "research", "machine learning",
    "biobank", "cyprus", "european university cyprus", "university of cyprus", "teacher", "part time",
    "full time", "lecturer", "junior", "entry level", "nicosia", "limassol", "paphos", "larnaca",
    "chemistry", "biomedical sciences", "biomedical scientist", "medical representative", "medical counseling"
]

# Telegram credentials from GitHub secrets
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telegram.Bot(token=BOT_TOKEN)

def load_seen_jobs():
    if not os.path.exists(CSV_FILE):
        return set()
    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        return {row[0] for row in csv.reader(f)}

def save_job(ref_number, data):
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([ref_number] + data)

def match_keywords(text):
    text = text.lower()
    return any(keyword in text for keyword in KEYWORDS)

def send_telegram_message(message):
    bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")

def main():
    seen_jobs = load_seen_jobs()
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    jobs = soup.find_all("div", class_="listing")

    new_jobs = []
    for job in jobs:
        title_tag = job.find("a", class_="listing-title")
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        link = "https://www.ergodotisi.com" + title_tag["href"]
        location = job.find("span", class_="listing-location")
        location = location.get_text(strip=True) if location else "Unknown"

        job_id = link.split("/")[-1]
        job_page = requests.get(link)
        job_soup = BeautifulSoup(job_page.text, 'html.parser')
        ref_number_tag = job_soup.find(string="Reference Number")
        ref_number = ref_number_tag.find_next().text.strip() if ref_number_tag else job_id  # fallback to URL ID
        job_text = f"{title} {location}".lower()

        if ref_number not in seen_jobs and match_keywords(job_text):
            new_jobs.append((ref_number, title, location, link))
            save_job(ref_number, [title, location, link])

    if new_jobs:
    msg = f"🚨 *{len(new_jobs)} new job(s) on Ergodotisi!*\n\n"
    for i, (job_id, title, loc, link) in enumerate(new_jobs, 1):
        msg += f"*{i}. {title}*\n📍 {loc}\n🔗 [View Job]({link})\n\n"
    send_telegram_message(msg)
else:
    send_telegram_message("✅ No new matching jobs found on Ergodotisi.")
