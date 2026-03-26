from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import os

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.message import EmailMessage
import smtplib

EMAIL_ADDRESS = ''
EMAIL_PASSWORD = ''
TO_EMAIL = ''
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
def send_pet_email(new_pets_list):
    # Set up your credentials (use an "App Password" for Gmail)


    msg = EmailMessage()
    msg['Subject'] = f"{len(new_pets_list)} New Pets Found!"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_ADDRESS

    # Build the body text from your loop
    body = "Here are the new pets found in the latest scan:\n\n"
    for p in new_pets_list:
        breed = p['details'].get('Breed', 'Unknown Breed')
        age = p['details'].get('Age', 'Unknown Age')
        body += f"NEW: {p['name']} ({breed})\n"
        body += f"Age: {age}\n"
        body += f"Link: {p['link']}\n"
        body += "-" * 30 + "\n"

    msg.set_content(body)

    # Send it
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

def scan_cats():
    with sync_playwright() as p:
        # headless=True is the default, but we'll be explicit
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("Connecting to Toronto Humane Society...")
        
        # Navigate to the site
        page.goto("https://www.torontohumanesociety.com/cats/", wait_until="domcontentloaded")

        # Wait for the cat listing container to ensure data has loaded
        # Note: THS uses dynamic loading for their pet 'cards'
        try:
            page.wait_for_selector(".card_sect", timeout=10000)
            print("Cat listings detected.")
        except:
            print("Timeout: Could not find specific pet cards, capturing full source anyway.")

        # Capture the rendered HTML
        html_source = page.content()

        # Output or process the source
        print(f"Captured {len(html_source)} characters of source code.")
        
        
            
        browser.close()

        soup = BeautifulSoup(html_source, 'html.parser')

        cards = soup.find_all('div', class_='card_sect')
       
        all_pets = []
        for card in cards:
            # 1. Extract Name & Status
            # Using .get_text(strip=True) to clean up whitespace
            name = card.find('h2').get_text(strip=True) if card.find('h2') else "N/A"
            status = card.find('h3', class_='first-txt').get_text(strip=True) if card.find('h3') else "Available"
            
            # 2. Extract Link & Image
            link_tag = card.find('a')
            link = link_tag['href'] if link_tag else None
            
            img_tag = card.find('img')
            image_url = img_tag['src'] if img_tag else None
            
            # 3. Extract Details (Gender, Age, etc.)
            # We create a sub-dictionary for the bulleted info
            details = {}
            detail_div = card.find('div', class_='detail')
            if detail_div:
                for p in detail_div.find_all('p'):
                    text = p.get_text(strip=True)
                    if ":" in text:
                        key, value = text.split(":", 1)
                        details[key.strip()] = value.strip()
            
            # Combine everything into one dictionary for this pet
            pet_info = {
                "name": name,
                "status": status,
                "link": link,
                "image": image_url,
                "details": details
            }
            
            all_pets.append(pet_info)

        #print(all_pets)

        file_name = "pet_data.json"

        old_pets = []
        if os.path.exists(file_name):
            with open(file_name, "r", encoding="utf-8") as f:
                try:
                    old_pets = json.load(f)
                except json.JSONDecodeError:
                    old_pets = []

        # 2. Create a set of previously seen links for lightning-fast lookup
        old_links = {pet['link'] for pet in old_pets}

        # 3. Identify the newcomers
        new_pets = []
        for pet in all_pets:
            if pet['link'] not in old_links:
                new_pets.append(pet)

        # 4. Report the findings
        if new_pets:
            with open("new.json", "w", encoding="utf-8") as f:
                # indent=4 makes the file human-readable/pretty
                # ensure_ascii=False handles special characters if they exist
                json.dump(new_pets, f, indent=4, ensure_ascii=False)
            
            #send_pet_email(new_pets)
            print(f"\n🚀 FOUND {len(new_pets)} NEW PETS!")
            print("-" * 30)
            for p in new_pets:
                # Pulling breed/age out of the nested 'details' dict safely
                breed = p['details'].get('Breed', 'Unknown Breed')
                print(f"✨ NEW: {p['name']} ({breed})")
                print(f"🔗 Link: {p['link']}\n")
        else:
            print("\n😴 No new pets found since the last check.")



        # save the file to compare against next time.
        # Define your filename


        # 'w' means Write mode (this overwrites the file each time)
        with open(file_name, "w", encoding="utf-8") as f:
            # indent=4 makes the file human-readable/pretty
            # ensure_ascii=False handles special characters if they exist
            json.dump(all_pets, f, indent=4, ensure_ascii=False)

        print(f"Successfully saved {len(all_pets)} pets to {file_name}")
        


if __name__ == "__main__":
    scan_cats()
