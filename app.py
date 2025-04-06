from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Constants
API_URL = "https://api-inference.huggingface.co/models/linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"
HEADERS = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_TOKEN')}"}
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Routes
@app.route("/")
def home():
    return jsonify({"message": "GardienAI Backend is Running ✅"})

@app.route("/predict", methods=["POST"])
def predict():
    image_file = request.files.get("image")
    if image_file is None:
        return jsonify({"error": "No image file provided"})

    image_bytes = image_file.read()
    try:
        response = requests.post(API_URL, headers=HEADERS, data=image_bytes)
        prediction = response.json()[0]['label']
        return jsonify({"prediction": prediction})
    except Exception as e:
        return jsonify({"error": "Prediction failed", "details": str(e)})


@app.route("/watering-alert", methods=["GET"])
def watering_alert():
    city = request.args.get("city", "London")
    api_key = os.getenv("OPENWEATHER_API_KEY")
    
    if not api_key:
        return jsonify({"error": "Missing OpenWeather API key."})

    weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(weather_url)
        data = response.json()

        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        weather = data["weather"][0]["description"]

        # Simple rule-based watering advice
        if humidity < 50 and temp > 20:
            watering_tip = "💧 It's dry and warm. Water your plants today!"
        elif humidity > 80:
            watering_tip = "🌧️ It's very humid. Hold off on watering."
        elif "rain" in weather.lower():
            watering_tip = "🌦️ It's rainy. No need to water today."
        else:
            watering_tip = "🪴 Check soil moisture before watering."

        return jsonify({
            "temperature": temp,
            "humidity": humidity,
            "weather": weather,
            "watering_tip": watering_tip
        })

    except Exception as e:
        return jsonify({"error": "Failed to get weather data", "details": str(e)})


@app.route("/daily-care", methods=["POST"])
def daily_care():
    data = request.get_json()
    city = data.get("city")
    plant_type = data.get("plant_type")

    if not city or not plant_type:
        return jsonify({"error": "City and plant type are required."})

    # Fetch weather data
    weather_api_key = os.getenv("OPENWEATHER_API_KEY")
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric"
    weather_response = requests.get(weather_url)
    weather_data = weather_response.json()

    if weather_response.status_code != 200:
        return jsonify({"error": "Failed to fetch weather data."})

    temperature = weather_data["main"]["temp"]
    humidity = weather_data["main"]["humidity"]
    description = weather_data["weather"][0]["description"]

    # Example care suggestions
    care_suggestions = []

    if plant_type.lower() == "cactus":
        care_suggestions.append("🌵 Minimal watering needed. Great for dry conditions.")
        if humidity > 70:
            care_suggestions.append("⚠️ Reduce watering. Humidity is high.")
    elif plant_type.lower() == "fern":
        care_suggestions.append("🌿 Keep soil moist. Foliage loves humidity.")
        if humidity < 50:
            care_suggestions.append("💧 Mist your plant to maintain moisture.")
    else:
        care_suggestions.append("🪴 Water when top soil is dry.")
        if temperature < 10:
            care_suggestions.append("❄️ Keep your plant away from cold drafts.")

    return jsonify({
        "plant": plant_type,
        "city": city,
        "temperature": temperature,
        "humidity": humidity,
        "weather": description,
        "care_suggestions": care_suggestions
    })


@app.route("/weather", methods=["GET"])
def get_weather():
    city = request.args.get("city", "London")
    if not OPENWEATHER_API_KEY:
        return jsonify({"error": "OpenWeather API key is missing in .env"})

    try:
        weather_url = (
            f"http://api.openweathermap.org/data/2.5/weather?q={city}"
            f"&appid={OPENWEATHER_API_KEY}&units=metric"
        )
        response = requests.get(weather_url)
        data = response.json()

        if response.status_code != 200:
            return jsonify({"error": data.get("message", "Unable to fetch weather")})

        temperature = data["main"]["temp"]
        weather_desc = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]

        tips = []
        if temperature > 30:
            tips.append("🌞 It's hot! Water your plants early morning or late evening.")
        elif temperature < 10:
            tips.append("❄️ Cold alert! Protect your plants from frost.")
        else:
            tips.append("✅ Normal weather. Water as usual.")

        if "rain" in weather_desc.lower():
            tips.append("🌧️ It's raining. Reduce watering.")
        if humidity > 80:
            tips.append("💧 High humidity. Improve ventilation to avoid fungal diseases.")

        return jsonify({
            "temperature": temperature,
            "description": weather_desc,
            "humidity": humidity,
            "tips": tips,
        })

    except Exception as e:
        return jsonify({"error": "Weather fetch failed", "details": str(e)})

import datetime

@app.route("/plant-journal", methods=["POST"])
def plant_journal():
    note = request.form.get("note")
    image_file = request.files.get("image")

    if not note:
        return jsonify({"error": "Note text is required"}), 400

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    entry_folder = f"journal_entries/{timestamp}"
    os.makedirs(entry_folder, exist_ok=True)

    # Save note
    with open(f"{entry_folder}/note.txt", "w") as f:
        f.write(note)

    # Save image if provided
    if image_file:
        image_path = os.path.join(entry_folder, image_file.filename)
        image_file.save(image_path)

    return jsonify({
        "message": "Journal entry saved successfully",
        "timestamp": timestamp,
        "image_saved": bool(image_file)
    })

@app.route("/plant-selector", methods=["POST"])
def plant_selector():
    data = request.get_json()
    environment = data.get("environment", "").lower()
    preference = data.get("preference", "").lower()

    plant_database = {
        "low light": {
            "low maintenance": ["Snake Plant", "ZZ Plant", "Pothos"],
            "air purifying": ["Peace Lily", "Spider Plant"]
        },
        "bright light": {
            "flowering": ["African Violet", "Orchid"],
            "low maintenance": ["Succulent", "Aloe Vera"]
        },
        "humid": {
            "tropical": ["Fern", "Calathea"],
            "colorful": ["Croton", "Bromeliad"]
        }
    }

    recommended = plant_database.get(environment, {}).get(preference, [])

    return jsonify({
        "environment": environment,
        "preference": preference,
        "recommended_plants": recommended
    })

  

if __name__ == "__main__":
    app.run(debug=True)