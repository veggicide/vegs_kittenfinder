from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import os

def scrape_cats():
    url = "https://ws.petango.com/webservices/adoptablesearch/wsAdoptableAnimals.aspx?species=Cat&sex=A&agegroup=All&location=&site=&onhold=N&orderby=Name&colnum=2&css=https://sms.petpoint.com/WebServices/adoptablesearch/css/styles.css&authkey=ykyvhkpv1ae6vngswl56tmsld1o3asnjpvpadm4akvx2yxyiu3&recAmount=100&detailsInPopup=Yes&featuredPet=Include&mobile=True"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector(".list-animal-info-block")
        source = page.content()
        browser.close()

    soup = BeautifulSoup(source, 'html.parser')
    animal_blocks = soup.find_all('div', class_='list-animal-info-block')

    all_pets = []

    for block in animal_blocks:
        # Get parent TD to find the image in the sibling photo-block
        parent_td = block.find_parent('td')
        img_tag = parent_td.find('img', class_='list-animal-photo') if parent_td else None
        
        # Parse the Sex/Neutered string (e.g., "Female/Spayed")
        sex_sn = block.find('div', class_='list-animal-sexSN').get_text(strip=True) if block.find('div', class_='list-animal-sexSN') else "Unknown/Unknown"
        gender, neutered = sex_sn.split('/') if '/' in sex_sn else (sex_sn, "Unknown")

        animal_id = block.find('div', class_='list-animal-id').get_text(strip=True)

        pet_info = {
            "name": block.find('div', class_='list-animal-name').get_text(strip=True),
            "status": "Available",  # Defaulting as per your format
            "link": f"https://ws.petango.com/webservices/adoptablesearch/wsAdoptableAnimalDetails.aspx?id={animal_id}",
            "image": img_tag['src'] if img_tag else "",
            "details": {
                "Gender": gender.strip(),
                "Neutered": neutered.strip(),
                "Breed": block.find('div', class_='list-animal-breed').get_text(strip=True) if block.find('div', class_='list-animal-breed') else "Unknown",
                "Age": block.find('div', class_='list-animal-age').get_text(strip=True) if block.find('div', class_='list-animal-age') else "Unknown",
                "On Hold": "No" # Site URL filter is set to onhold=N
            }
        }
        all_pets.append(pet_info)

    # --- SAVE AND COMPARE ---
    FILE_NAME = "pet_data_ava.json"
    
    # 1. Check for new ones before overwriting
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as f:
            old_pets = json.load(f)
        
        old_links = {p['link'] for p in old_pets}
        new_pets = [p for p in all_pets if p['link'] not in old_links]
        
        if new_pets:
            print(f"🚀 Found {len(new_pets)} New Pets!")

            # 1. Load what is currently in new.json (the "waiting room")
            current_new_list = []
            if os.path.exists("new.json"):
                with open("new.json", "r", encoding="utf-8") as f:
                    try:
                        current_new_list = json.load(f)
                    except json.JSONDecodeError:
                        current_new_list = []

            # 2. Add the freshly found pets to that list
            current_new_list.extend(new_pets)

            # 3. Save the combined list back to new.json
            with open("new.json", "w", encoding="utf-8") as f:
                json.dump(current_new_list, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Added to new.json. Total pending: {len(current_new_list)}")
                  
        else:
            print("No new pets found.")

    # 2. Save current list in your requested format
    with open(FILE_NAME, "w") as f:
        json.dump(all_pets, f, indent=4)

if __name__ == "__main__":
    scrape_cats()
