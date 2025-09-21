from flask import Flask, request, render_template, jsonify
import os
import time
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

BOOKING_FILE = "bookings.txt"
TEMP_DIR = "booking_temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# Email-to-SMS configuration
SMTP_SERVER = "smtp.gmail.com"  # Change if needed
SMTP_PORT = 587
EMAIL_USER = os.environ.get("EMAIL_USER")        # Your email address
EMAIL_PASS = os.environ.get("EMAIL_PASS")        # Your email password/app password
SMS_TO = "2503515498@vmobile.ca"                # Your Virgin Mobile number

# Rate-limiting dictionary
RATE_LIMIT = {}  # IP: timestamp of last booking
MIN_INTERVAL = 30  # seconds

# Allowed location postal codes for Vernon (example)
VERNON_POSTAL_CODES = ["V1B", "V1T", "V1H"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/booking", methods=["POST"])
def booking():
    ip = request.remote_addr
    now = time.time()
    last = RATE_LIMIT.get(ip, 0)
    if now - last < MIN_INTERVAL:
        return "Too many requests. Please wait a moment.", 429
    RATE_LIMIT[ip] = now

    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    service = request.form.get("service", "").strip()
    postal = request.form.get("postal_code", "").strip().upper()

    # Location restriction
    if not any(postal.startswith(code) for code in VERNON_POSTAL_CODES):
        return "Webpage unavailable: You are not in Vernon. Booking denied.", 403

    # Load current bookings
    lines = []
    if os.path.exists(BOOKING_FILE):
        with open(BOOKING_FILE, "r") as f:
            lines = f.readlines()

    booking_number = len(lines) + 1

    # Backup current bookings temporarily
    if lines:
        temp_file = os.path.join(TEMP_DIR, f"booking_backup_{int(time.time())}.txt")
        with open(temp_file, "w") as f:
            f.writelines(lines)
        os.system(f"(sleep 60 && rm -f {temp_file}) &")

    # Append new booking
    with open(BOOKING_FILE, "a") as f:
        f.write(f"Booking {booking_number}\t{email}\t{phone}\t{service}\t{postal}\n")

    # Send SMS via email
    sms_body = (
        f"New Booking #{booking_number}\n"
        f"Email: {email}\n"
        f"Phone: {phone}\n"
        f"Service: {service}\n"
        f"Postal: {postal}"
    )

    msg = MIMEText(sms_body)
    msg["From"] = EMAIL_USER
    msg["To"] = SMS_TO
    msg["Subject"] = f"Booking #{booking_number}"

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, SMS_TO, msg.as_string())
        server.quit()
    except Exception as e:
        print("Failed to send SMS:", e)

    return f"Booking #{booking_number} received and SMS sent!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
