import os
from flask import Flask, render_template
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

def get_israel_weather():
    """Fetch current weather for Israel (using Tel Aviv as the reference city)"""
    API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')
    if not API_KEY:
        return None
    
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q=Tel Aviv,IL&appid={API_KEY}&units=metric"
        response = requests.get(url)
        
        data = response.json()
        
        # Additional error checking
        if 'main' not in data or 'weather' not in data or 'wind' not in data:
            print("Unexpected API response structure")
            return None
        
        return {
            'temperature': round(data['main']['temp'], 1),
            'description': data['weather'][0]['description'].capitalize(),
            'humidity': data['main']['humidity'],
            'wind_speed': round(data['wind']['speed'], 1)
        }
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return None

@app.route("/")
def home():
    weather = get_israel_weather()
    return render_template("index.html", weather=weather)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)