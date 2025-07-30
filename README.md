# 🌊 SAIL — Smart Itinerary Planner

SAIL is an intelligent travel planning web app that generates **personalized itineraries in seconds**. Instead of spending hours browsing sites, users input a destination, date, and interests — and SAIL handles the rest.

**🌐 Live Demo:** [https://sail.pythonanywhere.com/](https://sail.pythonanywhere.com/)


## ✨ Features

- 🧭 **Instant Itinerary Generation** — AI-powered suggestions based on user preferences.
- 🌤 **Weather-Aware Planning** — Activities tailored to real-time and forecasted weather.
- 🎯 **Interest-Based Curation** — Recommendations filtered by interests like food, nature, museums, and more.
- 💾 **Save & Manage Plans** — Users can bookmark locations and itineraries for future reference.
- 🗺 **Popular Cities Preview** — Browse trending cities with top attractions.

## 🛠 Tech Stack

- **Frontend:** HTML, CSS, Bootstrap (via Jinja templates)
- **Backend:** Flask (Python), Flask-SQLAlchemy
- **Database:** SQLite
- **AI & APIs:**
  - Google Generative AI (Gemini) — for activity recommendation logic
  - Google Maps API — for location data & previews
  - OpenWeather API — for real-time weather data
  - populartimes — for peak hours and popularity insights

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd SAIL
```

### 2. Set Up a Virtual Environment

On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows (Command Prompt):
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root and set the following variables:

```
FRONTEND_MAP_API=your_value
BACKEND_MAP_API=your_value
SECRET_KEY=your_value
GEMINI_KEY=your_value
GEODB_KEY=your_value
```