"""
PostHarvestSaver - Rwanda Crop Spoilage Risk Analyzer
Uses OpenWeatherMap API to give real-time spoilage risk for Rwandan farmers.
Author: [Your Name]
"""

from flask import Flask, render_template, request, jsonify
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', '')
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# All 30 districts of Rwanda with coordinates
DISTRICTS = {
    "Bugesera":    {"lat": -2.1833, "lon": 30.2167, "region": "Eastern"},
    "Burera":      {"lat": -1.4667, "lon": 29.8333, "region": "Northern"},
    "Gakenke":     {"lat": -1.6842, "lon": 29.7728, "region": "Northern"},
    "Gasabo":      {"lat": -1.8900, "lon": 30.1200, "region": "Kigali City"},
    "Gatsibo":     {"lat": -1.5992, "lon": 30.4545, "region": "Eastern"},
    "Gicumbi":     {"lat": -1.5742, "lon": 30.0717, "region": "Northern"},
    "Gisagara":    {"lat": -2.6333, "lon": 29.8333, "region": "Southern"},
    "Huye":        {"lat": -2.5967, "lon": 29.7396, "region": "Southern"},
    "Kamonyi":     {"lat": -2.0333, "lon": 29.8833, "region": "Southern"},
    "Karongi":     {"lat": -2.0618, "lon": 29.3837, "region": "Western"},
    "Kayonza":     {"lat": -1.8784, "lon": 30.6438, "region": "Eastern"},
    "Kicukiro":    {"lat": -1.9800, "lon": 30.1000, "region": "Kigali City"},
    "Kirehe":      {"lat": -2.3667, "lon": 30.7000, "region": "Eastern"},
    "Muhanga":     {"lat": -2.0833, "lon": 29.7500, "region": "Southern"},
    "Musanze":     {"lat": -1.4994, "lon": 29.6343, "region": "Northern"},
    "Ngoma":       {"lat": -2.1500, "lon": 30.4833, "region": "Eastern"},
    "Ngororero":   {"lat": -1.8833, "lon": 29.5167, "region": "Western"},
    "Nyabihu":     {"lat": -1.6500, "lon": 29.5000, "region": "Western"},
    "Nyagatare":   {"lat": -1.2985, "lon": 30.3283, "region": "Eastern"},
    "Nyamagabe":   {"lat": -2.4627, "lon": 29.4810, "region": "Southern"},
    "Nyamasheke":  {"lat": -2.3347, "lon": 29.1385, "region": "Western"},
    "Nyanza":      {"lat": -2.3526, "lon": 29.7411, "region": "Southern"},
    "Nyarugenge":  {"lat": -1.9500, "lon": 30.0600, "region": "Kigali City"},
    "Nyaruguru":   {"lat": -2.7500, "lon": 29.4333, "region": "Southern"},
    "Rubavu":      {"lat": -1.6784, "lon": 29.3381, "region": "Western"},
    "Ruhango":     {"lat": -2.2167, "lon": 29.7833, "region": "Southern"},
    "Rulindo":     {"lat": -1.7167, "lon": 30.0333, "region": "Northern"},
    "Rusizi":      {"lat": -2.4796, "lon": 28.9067, "region": "Western"},
    "Rutsiro":     {"lat": -1.9833, "lon": 29.4167, "region": "Western"},
    "Rwamagana":   {"lat": -1.9500, "lon": 30.4346, "region": "Eastern"},
}

# Crop-specific spoilage thresholds and advice
CROPS = {
    "maize": {
        "name": "Maize (Ibigori)",
        "icon": "🌽",
        "optimal_temp_min": 10, "optimal_temp_max": 25,
        "optimal_humidity_min": 40, "optimal_humidity_max": 70,
        "critical_humidity": 85, "critical_temp": 32,
        "base_recommendations": [
            "Store in dry, well-ventilated granaries elevated off the ground",
            "Use hermetic bags (PICS bags) to block weevils and moisture",
            "Ensure grain moisture content is below 13% before storage",
            "Inspect every 2 weeks for weevils, mold spots, or unusual smell"
        ]
    },
    "beans": {
        "name": "Beans (Ibishyimbo)",
        "icon": "🫘",
        "optimal_temp_min": 10, "optimal_temp_max": 25,
        "optimal_humidity_min": 40, "optimal_humidity_max": 65,
        "critical_humidity": 78, "critical_temp": 30,
        "base_recommendations": [
            "Dry thoroughly to below 12% moisture before storing",
            "Mix with wood ash or diatomite to deter bean weevils naturally",
            "Store in sealed tins or hermetic bags away from sunlight",
            "Do not store near onions or potatoes — gases accelerate spoilage"
        ]
    },
    "tomatoes": {
        "name": "Tomatoes (Inyanya)",
        "icon": "🍅",
        "optimal_temp_min": 13, "optimal_temp_max": 21,
        "optimal_humidity_min": 85, "optimal_humidity_max": 90,
        "critical_humidity": 95, "critical_temp": 28,
        "base_recommendations": [
            "Store in a cool, shaded area at 13–21°C for longest shelf life",
            "Never stack more than 3 layers deep to prevent bruising",
            "Remove overripe tomatoes daily to prevent spread of rot",
            "Consider selling or processing within 48 hrs if weather is hot"
        ]
    },
    "irish_potatoes": {
        "name": "Irish Potatoes (Ibirayi)",
        "icon": "🥔",
        "optimal_temp_min": 4, "optimal_temp_max": 12,
        "optimal_humidity_min": 85, "optimal_humidity_max": 95,
        "critical_humidity": 98, "critical_temp": 20,
        "base_recommendations": [
            "Store in total darkness — light causes greening and solanine toxicity",
            "Keep at 4–12°C if possible; use underground pits in highland areas",
            "Do not store with bananas or tomatoes — ethylene causes sprouting",
            "Check weekly and remove any rotting tubers immediately"
        ]
    },
    "bananas": {
        "name": "Bananas (Umuneke/Ibitoki)",
        "icon": "🍌",
        "optimal_temp_min": 13, "optimal_temp_max": 18,
        "optimal_humidity_min": 85, "optimal_humidity_max": 95,
        "critical_humidity": 98, "critical_temp": 25,
        "base_recommendations": [
            "Harvest bunches at 3/4 maturity for maximum shelf life",
            "Hang bunches in shaded, ventilated areas — do not pile on ground",
            "Keep away from direct sunlight and heat sources",
            "If overripe, process into banana flour or juice immediately"
        ]
    },
    "sorghum": {
        "name": "Sorghum (Amasaka)",
        "icon": "🌾",
        "optimal_temp_min": 10, "optimal_temp_max": 25,
        "optimal_humidity_min": 40, "optimal_humidity_max": 65,
        "critical_humidity": 80, "critical_temp": 30,
        "base_recommendations": [
            "Dry grain to below 12% moisture before any storage",
            "Use hermetic metal silos or PICS bags for long-term storage",
            "Store away from damp walls, water sources, or bare earth",
            "Apply approved grain protectant (e.g. Actellic Super) if storing 3+ months"
        ]
    },
    "cassava": {
        "name": "Cassava (Imyumbati)",
        "icon": "🍠",
        "optimal_temp_min": 0, "optimal_temp_max": 5,
        "optimal_humidity_min": 85, "optimal_humidity_max": 95,
        "critical_humidity": 98, "critical_temp": 30,
        "base_recommendations": [
            "Fresh cassava deteriorates within 2–3 days — process or sell quickly",
            "Dry into chips (imyumbati yumye) for storage up to 6 months",
            "Store dried chips in sealed containers away from moisture",
            "For short-term: peel, cut, and submerge in clean water (max 5 days)"
        ]
    },
    "sweet_potato": {
        "name": "Sweet Potato (Ibijumba)",
        "icon": "🍠",
        "optimal_temp_min": 13, "optimal_temp_max": 16,
        "optimal_humidity_min": 85, "optimal_humidity_max": 95,
        "critical_humidity": 98, "critical_temp": 28,
        "base_recommendations": [
            "Cure freshly harvested tubers at 29–32°C for 4–7 days to heal skin",
            "Store in cool, dark, ventilated spaces — avoid refrigeration",
            "Never wash tubers before storage — moisture promotes rot",
            "Inspect every 10 days; remove any soft or rotting tubers"
        ]
    }
}


def calculate_risk(temp, humidity, rainfall, crop_key):
    """Calculate spoilage risk score (0-100) based on weather and crop type."""
    crop = CROPS[crop_key]
    score = 0
    factors = []

    # Temperature scoring
    if temp > crop['critical_temp']:
        score += 35
        factors.append(f"Temperature ({temp:.1f}°C) is critically high for {crop['name']}")
    elif temp > crop['optimal_temp_max']:
        excess = temp - crop['optimal_temp_max']
        score += min(20 + excess * 2, 30)
        factors.append(f"Temperature ({temp:.1f}°C) exceeds safe storage range")
    elif temp < crop['optimal_temp_min']:
        score += 8
        factors.append(f"Temperature ({temp:.1f}°C) is below optimal — monitor for chilling")

    # Humidity scoring
    if humidity > crop['critical_humidity']:
        score += 40
        factors.append(f"Humidity ({humidity}%) is critically high — severe mold and rot risk")
    elif humidity > crop['optimal_humidity_max']:
        excess = humidity - crop['optimal_humidity_max']
        score += min(20 + excess, 35)
        factors.append(f"Humidity ({humidity}%) exceeds safe storage levels")
    elif humidity < crop['optimal_humidity_min']:
        score += 8
        factors.append(f"Humidity ({humidity}%) is low — crops may dry out or crack")

    # Rainfall scoring
    if rainfall > 10:
        score += 20
        factors.append(f"Heavy rainfall ({rainfall:.1f}mm) — high risk of moisture entering storage")
    elif rainfall > 2:
        score += 10
        factors.append(f"Moderate rainfall ({rainfall:.1f}mm) — inspect storage for leaks")
    elif rainfall > 0:
        score += 4
        factors.append(f"Light rain ({rainfall:.1f}mm) detected — keep storage sealed")

    score = min(score, 100)

    if score >= 75:
        level, color, emoji, label = "CRITICAL", "#dc2626", "🔴", "Act Immediately"
    elif score >= 50:
        level, color, emoji, label = "HIGH", "#ea580c", "🟠", "Act Within 24 Hours"
    elif score >= 25:
        level, color, emoji, label = "MEDIUM", "#ca8a04", "🟡", "Monitor Closely"
    else:
        level, color, emoji, label = "LOW", "#16a34a", "🟢", "Conditions Favorable"

    return {
        "score": score,
        "level": level,
        "color": color,
        "emoji": emoji,
        "label": label,
        "factors": factors if factors else ["Current conditions are within safe ranges"]
    }


def get_recommendations(risk_level, crop_key):
    """Return tailored recommendations based on risk level and crop."""
    crop = CROPS[crop_key]
    recs = list(crop['base_recommendations'])

    urgency_prefix = {
        "CRITICAL": "⚠️ URGENT: Move produce to market or process immediately to avoid total loss",
        "HIGH":     "⚡ Inspect all stored produce now and take corrective action within 24 hours",
        "MEDIUM":   "👀 Monitor your storage closely over the next 48 hours",
        "LOW":      "✅ Conditions are favorable — maintain your current good storage practices"
    }

    recs.insert(0, urgency_prefix[risk_level])
    return recs


@app.route('/')
def index():
    """Serve the main application page."""
    return render_template('index.html',
                           districts=sorted(DISTRICTS.keys()),
                           crops=CROPS)


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Main analysis endpoint — fetches weather and returns spoilage risk."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Invalid request format'}), 400

    crop_key = data.get('crop', '').strip()
    district_name = data.get('district', '').strip()

    if not crop_key or not district_name:
        return jsonify({'error': 'Please select both a crop and a district to analyze'}), 400

    if crop_key not in CROPS:
        return jsonify({'error': 'Invalid crop selected. Please choose from the list.'}), 400

    if district_name not in DISTRICTS:
        return jsonify({'error': 'Invalid district selected. Please choose a valid Rwanda district.'}), 400

    if not OPENWEATHER_API_KEY:
        return jsonify({'error': 'Weather API key is not configured. Please set OPENWEATHER_API_KEY.'}), 500

    district = DISTRICTS[district_name]

    try:
        response = requests.get(BASE_URL, params={
            'lat': district['lat'],
            'lon': district['lon'],
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric'
        }, timeout=10)

        if response.status_code == 401:
            return jsonify({'error': 'Invalid API key. Please check your OpenWeatherMap API key.'}), 401

        if response.status_code == 429:
            return jsonify({'error': 'Too many requests. Please wait a moment and try again.'}), 429

        if response.status_code != 200:
            return jsonify({'error': f'Weather service temporarily unavailable (Error {response.status_code}). Please try again.'}), 503

        w = response.json()
        temp = w['main']['temp']
        humidity = w['main']['humidity']
        rainfall = w.get('rain', {}).get('1h', 0)
        weather_desc = w['weather'][0]['description'].title()
        wind_speed = w['wind']['speed']
        feels_like = w['main']['feels_like']
        pressure = w['main']['pressure']

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Weather service timed out. Please check your connection and try again.'}), 503
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Cannot reach weather service. Please check your internet connection.'}), 503
    except KeyError as e:
        return jsonify({'error': f'Unexpected data from weather service. Please try again.'}), 503
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

    risk = calculate_risk(temp, humidity, rainfall, crop_key)
    recommendations = get_recommendations(risk['level'], crop_key)
    crop = CROPS[crop_key]

    return jsonify({
        'success': True,
        'crop': crop['name'],
        'crop_icon': crop['icon'],
        'district': district_name,
        'region': district['region'],
        'weather': {
            'temperature': round(temp, 1),
            'feels_like': round(feels_like, 1),
            'humidity': humidity,
            'rainfall': round(rainfall, 1),
            'description': weather_desc,
            'wind_speed': round(wind_speed * 3.6, 1),  # m/s to km/h
            'pressure': pressure
        },
        'risk': risk,
        'recommendations': recommendations,
        'optimal_conditions': {
            'temp': f"{crop['optimal_temp_min']}–{crop['optimal_temp_max']}°C",
            'humidity': f"{crop['optimal_humidity_min']}–{crop['optimal_humidity_max']}%"
        },
        'timestamp': datetime.now().strftime('%d %B %Y at %H:%M')
    })


@app.route('/api/districts')
def get_districts():
    """Return all Rwanda districts."""
    return jsonify([{"name": k, "region": v["region"]} for k, v in sorted(DISTRICTS.items())])


@app.route('/api/crops')
def get_crops():
    """Return all supported crops."""
    return jsonify({k: {'name': v['name'], 'icon': v['icon']} for k, v in CROPS.items()})


@app.route('/health')
def health():
    """Health check endpoint for load balancer."""
    return jsonify({'status': 'ok', 'app': 'PostHarvestSaver', 'version': '1.0.0'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
