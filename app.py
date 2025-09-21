from flask import Flask, request, render_template
import os
import time

app = Flask(__name__)

BOOKING_FILE = "bookings.txt"
TEMP_DIR = "booking_temp"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/booking", methods=["POST"])
def booking():
    email = request.form.get("email", "")
    phone = request.form.get("phone", "")
    service = request.form.get("service", "")
    postal = request.form.get("postal_code", "")

    # Load current bookings
    if os.path.exists(BOOKING_FILE):
        with open(BOOKING_FILE, "r") as f:
            lines = f.readlines()
    else:
        lines = []

    booking_number = len(lines) + 1

    # Backup current bookings temporarily
    if lines:
        temp_file = os.path.join(TEMP_DIR, f"booking_backup_{int(time.time())}.txt")
        with open(temp_file, "w") as f:
            f.writelines(lines)
        # Delete after 60 seconds
        os.system(f"(sleep 60 && rm -f {temp_file}) &")

    # Append new booking
    with open(BOOKING_FILE, "a") as f:
        f.write(f"Booking {booking_number}\t{email}\t{phone}\t{service}\t{postal}\n")

    return f"Booking {booking_number} received.", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
