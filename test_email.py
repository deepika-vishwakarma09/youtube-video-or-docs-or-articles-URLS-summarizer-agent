
import smtplib, os
from dotenv import load_dotenv

load_dotenv()

server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login(os.getenv("SENDER_EMAIL"), os.getenv("SENDER_PASSWORD"))

print("LOGIN SUCCESS ✅")
