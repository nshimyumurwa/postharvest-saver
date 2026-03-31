# PostHarvestSaver — Rwanda Crop Spoilage Risk Analyzer

> **Protecting Rwandan harvests through real-time weather intelligence**

PostHarvestSaver is a web application that helps Rwandan smallholder farmers assess the spoilage risk of their stored crops based on **live weather conditions** in their district. By combining real-time weather data with crop-specific thresholds, the app delivers instant, actionable storage recommendations — reducing post-harvest losses that cost Rwanda's agricultural economy millions every year.

---

## The Problem This Solves

Rwanda loses an estimated **30% of agricultural produce** after harvest due to poor storage decisions. Most smallholder farmers don't have access to tools that connect current weather conditions (temperature, humidity, rainfall) to crop-specific spoilage risk. PostHarvestSaver fills this critical gap, directly supporting Rwanda's **Vision 2050** food security targets and **NST2** agricultural transformation goals.

---

## Features

- **8 crops supported**: Maize, Beans, Tomatoes, Irish Potatoes, Bananas, Sorghum, Cassava, Sweet Potato — all in Kinyarwanda and English
- **All 30 Rwanda districts covered** with precise GPS coordinates for accurate hyperlocal weather
- **Live weather data** via OpenWeatherMap API (temperature, humidity, rainfall, wind)
- **Dynamic risk meter** scoring spoilage risk from 0–100 with four levels: LOW / MEDIUM / HIGH / CRITICAL
- **Crop-specific recommendations** tailored to the detected risk level
- **Filter history** by risk level (Low, Medium, High, Critical)
- ↕**Sort history** by newest, oldest, highest risk, or lowest risk
- **Persistent history** stored locally — analyses survive page refresh
- **Comprehensive error handling** for API downtime, invalid inputs, network errors, and rate limits
- 📱 **Fully responsive** — works on mobile, tablet, and desktop
- **/health endpoint** for load balancer health checks

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3, Flask 3.1 |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| API | OpenWeatherMap Current Weather API |
| Server | Gunicorn (production), Flask dev server (local) |
| Load Balancer | Nginx |

---

## Part One: Running Locally

### Prerequisites

- Python 3.8 or higher
- pip
- A free OpenWeatherMap API key (instructions below)

### Step 1 — Get Your Free API Key

1. Go to [https://openweathermap.org/api](https://openweathermap.org/api)
2. Click **Sign Up** and create a free account
3. Go to **API Keys** tab in your dashboard
4. Copy your API key (it activates within ~10 minutes of signup)

### Step 2 — Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/postharvest-saver.git
cd postharvest-saver
```

### Step 3 — Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate        # Linux/macOS
# OR
venv\Scripts\activate           # Windows
```

### Step 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5 — Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and replace `your_api_key_here` with your actual OpenWeatherMap API key:

```
OPENWEATHER_API_KEY=abc123youractualkey
```

### Step 6 — Run the Application

```bash
python app.py
```

Open your browser and go to: **http://localhost:5000**

---

## Part Two: Deployment on Web Servers

### Architecture Overview

```
Internet
    │
    ▼
[Lb01 — Nginx Load Balancer]
    │               │
    ▼               ▼
[Web01 — Gunicorn]  [Web02 — Gunicorn]
   Flask App          Flask App
```

### Step 1 — Set Up Both Web Servers (Web01 & Web02)

Run these commands on **both Web01 and Web02**:

#### 1a. Connect to the server
```bash
ssh ubuntu@<WEB01_IP>   # repeat for WEB02
```

#### 1b. Update and install Python
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git -y
```

#### 1c. Clone the repository
```bash
cd /var/www
sudo git clone https://github.com/YOUR_USERNAME/postharvest-saver.git
cd postharvest-saver
```

#### 1d. Create virtual environment and install dependencies
```bash
sudo python3 -m venv venv
sudo venv/bin/pip install -r requirements.txt
```

#### 1e. Set the API key
```bash
sudo nano .env
# Add: OPENWEATHER_API_KEY=your_actual_key_here
```

#### 1f. Test that the app runs
```bash
sudo venv/bin/python app.py
# Should say: Running on http://0.0.0.0:5000
# Press Ctrl+C to stop
```

#### 1g. Create a systemd service for auto-start
```bash
sudo nano /etc/systemd/system/postharvest.service
```

Paste the following:
```ini
[Unit]
Description=PostHarvestSaver Flask App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/var/www/postharvest-saver
Environment="PATH=/var/www/postharvest-saver/venv/bin"
ExecStart=/var/www/postharvest-saver/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

1h. Start and enable the service
```bash
sudo systemctl daemon-reload
sudo systemctl start postharvest
sudo systemctl enable postharvest
sudo systemctl status postharvest   # Should show: active (running)
```

1i. Verify the app is running
```bash
curl http://localhost:5000/health
# Expected: {"app":"PostHarvestSaver","status":"ok","version":"1.0.0"}
```


Step 2 — Configure the Load Balancer (Lb01)

#### 2a. Connect to Lb01
```bash
ssh ubuntu@<54.210.206.210>
```

2b. Install Nginx
```bash
sudo apt update
sudo apt install nginx -y
```

2c. Configure Nginx as a load balancer
```bash
sudo nano /etc/nginx/sites-available/postharvest
```

```nginx
upstream postharvest_servers {
    server <44.203.195.131>:5000 weight=1;
    server <13.222.52.30>:5000 weight=1;
}

server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://postharvest_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 30s;
        proxy_read_timeout 60s;
    }

    location /health {
        proxy_pass http://postharvest_servers;
        access_log off;
    }
}
```

2d. Enable the configuration and restart Nginx
```bash
sudo ln -s /etc/nginx/sites-available/postharvest /etc/nginx/sites-enabled/
sudo nginx -t                  # Test config — should say "syntax is ok"
sudo systemctl restart nginx
sudo systemctl enable nginx
```

2e. Verify load balancing works
```bash
# Hit the load balancer multiple times and watch it rotate servers
for i in {1..6}; do curl -s http://<LB01_IP>/health; echo; done
```

You should see successful responses — Nginx is distributing traffic between Web01 and Web02.


Security Practices

- API keys are stored in `.env` files — **never committed to GitHub**
- `.gitignore` excludes `.env` and `__pycache__`
- All user inputs are validated server-side before API calls
- Error messages never expose internal system details
- Gunicorn is used in production (not Flask dev server)


APIs Used

OpenWeatherMap Current Weather API
- Documentation: https://openweathermap.org/current
- Endpoint: `https://api.openweathermap.org/data/2.5/weather`
- Plan: Free tier (1,000 calls/day)
- Data used: Temperature (°C), Humidity (%), Rainfall (mm/1h), Wind speed (m/s)


Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| Rwanda district names don't map directly to cities in OpenWeatherMap | Used precise lat/lon coordinates for every district instead of city names |
| Different crops have completely different optimal conditions | Built a comprehensive crop-threshold dictionary with crop-specific risk logic |
| API key exposure in frontend | All API calls are made server-side in Flask; the key never touches the browser |
| Load balancer session continuity | Used stateless design (no server-side sessions); history is stored in `localStorage` |
| OpenWeatherMap rate limits during testing | Implemented timeout and 429 error handling with user-friendly messages |


Project Structure

postharvest-saver/
├── app.py               # Flask backend — routes, API calls, risk logic
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── .gitignore           # Excludes .env and build files
├── README.md            # This file
├── templates/
│   └── index.html       # Single-page HTML frontend
└── static/
    ├── css/
    │   └── style.css    # Full stylesheet with responsive design
    └── js/
        └── main.js      # Frontend logic — interactions, history, filtering
```

---

Credits & Attribution

- OpenWeatherMap— Weather data API · https://openweathermap.org
- Flask — Python web framework · https://flask.palletsprojects.com
- Gunicorn — Python WSGI HTTP server · https://gunicorn.org
- Nginx — Load balancer / reverse proxy · https://nginx.org
- FAO — Post-Harvest Management Guidelines · https://www.fao.org/postharvest
- RAB (Rwanda Agriculture Board) — Crop storage best practices
- Google Fonts — Playfair Display + DM Sans typefaces

Demo Video

Watch the demo of the Postharvest Saver App here:  
[Postharvest Saver App Demo Video](https://youtu.be/HMTB8Z5IZog)

Author

Nshimyumurwa Mary Therese 
ALU Software Engineering Project
PostHarvestSaver — Built to reduce food loss in Rwanda
