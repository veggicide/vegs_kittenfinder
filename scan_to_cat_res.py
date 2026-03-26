import requests
from bs4 import BeautifulSoup
import json
import os

def update_pet_files(final_data):
    # 1. Load existing database (tocatres.json) to see what we already know
    if os.path.exists('tocatres.json'):
        with open('tocatres.json', 'r') as f:
            old_data = json.load(f)
    else:
        old_data = []

    # 2. Identify "New" pets by comparing links
    existing_links = {pet['link'] for pet in old_data}
    new_pets = [pet for pet in final_data if pet['link'] not in existing_links]

    if not new_pets:
        print("No new pets found.")
        return

    # 3. Append new pets to new.json
    if os.path.exists('new.json'):
        with open('new.json', 'r') as f:
            try:
                current_new_list = json.load(f)
            except json.JSONDecodeError:
                current_new_list = []
    else:
        current_new_list = []

    current_new_list.extend(new_pets)

    with open('new.json', 'w') as f:
        json.dump(current_new_list, f, indent=4)
    
    # 4. Update tocatres.json so they aren't "new" next time
    # (Optional: If you want to replace the old file with the latest full scrape)
    with open('tocatres.json', 'w') as f:
        json.dump(final_data, f, indent=4)

    print(f"Added {len(new_pets)} new pets to new.json and updated tocatres.json.")

def scrape_adopt_a_pet_grid():
    url = "https://searchtools.adoptapet.com/cgi-bin/searchtools.cgi/portable_pet_list?color=%23E5F7FB&title=&shelter_id=75215&size=450x600_gridnew&sort_by=pet_name&clan_name=cat&age=baby"
    base_url = "https://searchtools.adoptapet.com"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    pets_json = []
    
    # Find all divs with class "pet"
    pet_divs = soup.find_all('div', class_='pet')

    for pet in pet_divs:
        # 1. Name and Link
        name_link = pet.find('a', class_='name')
        name = name_link.get_text(strip=True) if name_link else "Unknown"
        link = base_url + name_link['href'] if name_link else ""

        # 2. Image
        img_tag = pet.find('img')
        image = img_tag['src'] if img_tag else ""

        # 3. Breed (it's the second <p> tag usually)
        paragraphs = pet.find_all('p', class_='truncate')
        breed = paragraphs[1].get_text(strip=True) if len(paragraphs) > 1 else "Unknown"

        # 4. Gender and Age (Loose text at the end of the div)
        # We grab all text and look for the "Male/Female, Kitten" part
        full_text = pet.get_text("|", strip=True)
        # Usually looks like: "Name|Breed|Gender, Age"
        details_part = full_text.split('|')[-1] 
        
        gender = "Unknown"
        age = "Kitten"
        if "," in details_part:
            gender_raw, age_raw = details_part.split(',', 1)
            gender = gender_raw.strip()
            age = age_raw.strip()

        # Build the consistent object
        pet_entry = {
            "name": name,
            "status": "Available",
            "link": link,
            "image": image,
            "details": {
                "Gender": gender,
                "Neutered": "Unknown", # Not listed in the grid view
                "Breed": breed,
                "Age": age,
                "On Hold": "No"
            }
        }
        pets_json.append(pet_entry)

    return pets_json

# Run and Print
final_data = scrape_adopt_a_pet_grid()

update_pet_files(final_data)

print(json.dumps(final_data, indent=4))
if final_data:
            with open("tocatres.json", "w", encoding="utf-8") as f:
                # indent=4 makes the file human-readable/pretty
                # ensure_ascii=False handles special characters if they exist
                json.dump(final_data, f, indent=4, ensure_ascii=False)
