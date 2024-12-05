from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import requests
from dotenv import load_dotenv
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import openai

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "mysecretkey")

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client.weather_app

# Configuration
MAX_FACTS = int(os.getenv("MAX_FACTS", 6))
API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')

# Default data
DEFAULT_FACTS = [
    "Snowflakes are made of ice crystals.",
    "Winter storms form when cold air meets warm moist air.",
    "Polar bears are well adapted to winter temperatures.",
    "The Earth is closest to the sun in winter."
]

DEFAULT_LOCATIONS = [
    {"city": "Tel Aviv", "country": "IL"},
    {"city": "New York", "country": "US"},
    {"city": "London", "country": "GB"},
    {"city": "Tokyo", "country": "JP"},
    {"city": "Sydney", "country": "AU"},
    {"city": "Paris", "country": "FR"}
]

@app.route("/generate_chatgpt_fact", methods=["POST"])
def generate_chatgpt_fact():
    if "user" not in session:
        return jsonify({"success": False, "message": "You must be logged in to generate a fact."}), 403

    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            return jsonify({"success": False, "message": "OpenAI API key is missing."}), 500

        fact_count = db.facts.count_documents({})
        if fact_count >= MAX_FACTS:
            return jsonify({"success": False, "message": f"You cannot add more than {MAX_FACTS} facts."}), 400

        # Configure OpenAI API key
        openai.api_key = openai_api_key

        # Use the chat completion endpoint
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that provides fun and educational winter facts."},
                {"role": "user", "content": "Generate a fun fact about winter, dont use 'Sure! Here's a fun fact about winter' at the start, neither 'Fun Fact:', keep it short, 2-3 sentences."}
            ],
            temperature=0.7,
            max_tokens=50
        )

        # Extract the generated fact
        fact = response["choices"][0]["message"]["content"].strip()

        # Save the fact to the database
        db.facts.insert_one({"text": fact})

        return jsonify({"success": True, "message": "Fact generated successfully!", "fact": fact})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

# Utility: Ensure default locations and facts
def ensure_defaults():
    if db.locations.count_documents({}) == 0:
        db.locations.insert_many(DEFAULT_LOCATIONS)

    if db.facts.count_documents({}) == 0:
        for fact in DEFAULT_FACTS:
            db.facts.insert_one({"text": fact})


# User Registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        if not username or not password:
            return render_template("register.html", message="Username and password are required.")

        # Check if user already exists
        if db.users.find_one({"username": username}):
            return render_template("register.html", message="Username already exists.")

        # Hash the password and save the user
        hashed_password = generate_password_hash(password)
        db.users.insert_one({"username": username, "password": hashed_password})
        return redirect(url_for("login"))

    return render_template("register.html")


# User Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password").strip()

        if not username or not password:
            return render_template("login.html", message="Username and password are required.")

        # Verify user credentials
        user = db.users.find_one({"username": username})
        if not user or not check_password_hash(user["password"], password):
            return render_template("login.html", message="Invalid username or password.")

        # Log the user in
        session["user"] = username
        return redirect(url_for("home"))

    return render_template("login.html")


# User Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))


# Add Location
@app.route("/add_location", methods=["POST"])
def add_location():
    if "user" not in session:
        return jsonify({"success": False, "message": "You must be logged in to add a location."}), 403

    city = request.form.get("city").strip()
    country = request.form.get("country").strip()

    if not city or not country:
        return jsonify({"success": False, "message": "City and country are required."}), 400

    # Validate weather data
    weather = get_weather(city, country)
    if not weather:
        return jsonify({"success": False, "message": "Invalid city or country."}), 400

    # Check if the location already exists
    if db.locations.find_one({"city": city, "country": country}):
        return jsonify({"success": False, "message": "Location already exists."}), 400

    db.locations.insert_one({"city": city, "country": country})
    return jsonify({"success": True, "message": "Location added successfully!"})


# Generate a Fact
@app.route("/generate_fact", methods=["POST"])
def generate_fact():
    if "user" not in session:
        return jsonify({"success": False, "message": "You must be logged in to add a fact."}), 403

    fact_text = request.form.get("fact").strip()
    if not fact_text:
        return jsonify({"success": False, "message": "Fact text is required."}), 400

    if db.facts.count_documents({}) >= MAX_FACTS:
        return jsonify({"success": False, "message": f"Maximum of {MAX_FACTS} facts reached."}), 400

    db.facts.insert_one({"text": fact_text})
    return jsonify({"success": True, "message": "Fact added successfully!"})


# Remove a Fact
@app.route("/remove_fact", methods=["POST"])
def remove_fact():
    if "user" not in session:
        return jsonify({"success": False, "message": "You must be logged in to remove a fact."}), 403

    fact_id = request.form.get("fact_id").strip()
    if not fact_id:
        return jsonify({"success": False, "message": "Fact ID is required."}), 400

    try:
        result = db.facts.delete_one({"_id": ObjectId(fact_id)})
        if result.deleted_count == 0:
            return jsonify({"success": False, "message": "Fact not found."}), 404
        return jsonify({"success": True, "message": "Fact removed successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {e}"}), 500


# Home
@app.route("/", methods=["GET", "POST"])
def home():
    ensure_defaults()

    locations = list(db.locations.find({}, {"_id": 0}))
    facts = list(db.facts.find({}))

    selected_location = request.form.get("location", "Tel Aviv,IL")
    city, country = selected_location.split(",")
    weather = get_weather(city, country)

    return render_template(
        "index.html",
        weather=weather,
        locations=locations,
        facts=facts,
        selected_location=selected_location,
        user=session.get("user")
    )


# Fetch Weather
def get_weather(city, country):
    if not API_KEY:
        print("Error: OPENWEATHERMAP_API_KEY is not set.")
        return None

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={API_KEY}&units=metric"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if "main" not in data or "weather" not in data or "wind" not in data:
            return None

        return {
            "temperature": round(data["main"]["temp"], 1),
            "description": data["weather"][0]["description"].capitalize(),
            "humidity": data["main"]["humidity"],
            "wind_speed": round(data["wind"]["speed"], 1)
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather: {e}")
        return None


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
