import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.message import EmailMessage
import smtplib
import os
from dotenv import load_dotenv
def send_pet_email():
    file_path = 'new.json'
    
    # 1. Load the data
    if not os.path.exists(file_path):
        print("No new.json file found.")
        return

    with open(file_path, 'r') as f:
        try:
            pets = json.load(f)
        except json.JSONDecodeError:
            print("new.json is empty or invalid.")
            return

    if not pets:
        print("No new pets to email.")
        return

    # 2. Email Configuration (Change these!)

    load_dotenv()

    GEMAIL = os.getenv("GMAIL_USER")
    SENDER_PASSWORD = os.getenv("GMAIL_KEY")
    
    sender_email = GEMAIL
    receiver_email = GEMAIL
    app_password = SENDER_PASSWORD
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🐾 {len(pets)} New Pets Found!"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    # 3. Create HTML Body for the Email
    html = "<html><body><h2>New Pets Alert</h2>"
    for pet in pets:
        html += f"""
        <div style="border-bottom: 1px solid #ddd; padding: 10px; margin-bottom: 10px;">
            <img src="{pet['image']}" width="150" style="float: left; margin-right: 15px;">
            <p><strong>Name:</strong> {pet['name']} ({pet['status']})</p>
            <p><strong>Details:</strong> {pet['details']['Breed']} | {pet['details']['Age']} | {pet['details']['Gender']}</p>
            <p><a href="{pet['link']}">View Pet Details</a></p>
            <div style="clear: both;"></div>
        </div>
        """
    html += "</body></html>"
    
    msg.attach(MIMEText(html, 'html'))

    # 4. Send the Email
    try:
    # Send it
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
        print("Email sent successfully!")

        # 5. Clear the file after successful send
        with open(file_path, 'w') as f:
            json.dump([], f)
        print("new.json has been cleared.")

    except Exception as e:
        print(f"Error sending email: {e}")

# Run the function
send_pet_email()
