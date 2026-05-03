# 🌍 VoteIQ — Global Election Intelligence System

VoteIQ is a **Flask-based global election intelligence platform** that helps users from **195+ countries** understand voting eligibility, registration, and election-related information — all in a **multilingual, AI-assisted interface**.

---

## 🚀 Features

### ✅ Eligibility Checker

* Rule-based eligibility verification for different countries
* Inputs: age, citizenship, residency
* Instant result with confidence score

### 📋 Voting Guide

* Step-by-step voting and registration instructions
* Country-specific data support
* Global fallback for unsupported countries

### 🔍 Fact Checker (Misinformation Detector)

* Analyze election-related claims
* Risk classification: **High / Medium / Low / Safe**
* Explanation of results

### 🤖 AI Assistant

* Ask election-related questions
* Context-aware (based on selected country)
* Designed to provide safe, factual responses

### 🌐 Multilingual Support

* Supports multiple languages (currently **English & Hindi**)
* Easily extendable via JSON translation files

---

## 🧠 Tech Stack

* **Backend:** Flask (Python)
* **Frontend:** HTML, CSS, JavaScript
* **AI Integration:** OpenAI API
* **Data Storage:** JSON-based country datasets
* **Authentication:** Session-based login system

---

## 📁 Project Structure

```
election-app/
│
├── backend/
│   ├── data/
│   │   ├── countries/
│   │   └── translations/
│   ├── routes/
│   ├── services/
│   └── __init__.py
│
├── templates/
├── static/
├── app.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/promptwars_election.git
cd promptwars_election
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate   # Windows
# OR
source venv/bin/activate  # Mac/Linux
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Set Environment Variables

Create a `.env` file:

```
OPENAI_API_KEY=your_api_key_here
SESSION_SECRET=your_secret_key
```

---

### 5️⃣ Run the Application

```bash
python app.py
```

App will run at:

```
http://127.0.0.1:5000
```

---

## 🌍 Supported Countries

* 🇮🇳 India
* 🇺🇸 United States
* 🇬🇧 United Kingdom
* 🇨🇦 Canada
* 🇦🇺 Australia
* 🇩🇪 Germany
* * Global fallback for all other countries

---

## 🌐 Translation System

Translations are stored in:

```
backend/data/translations/
```

Example:

* `en.json`
* `hi.json`

You can add more languages by:

1. Creating a new JSON file
2. Adding it to `SUPPORTED_LANGUAGES`
3. Updating UI selector

---

## ⚠️ Known Limitations

* AI Assistant depends on API availability
* Fact Checker currently uses basic analysis logic
* Some countries rely on fallback data

---

## 🔮 Future Improvements

* Real-time election data APIs
* Advanced misinformation detection models
* More language support
* Better UI/UX interactions
* Mobile responsiveness improvements

---

## 🛡️ Disclaimer

This platform provides **informational guidance only**.
Always verify with your **official election authority** before making decisions.

---

## 👤 Author

Developed by **Juveria**

---

## ⭐ Contribution

Feel free to fork, improve, and submit pull requests!

---

## 📜 License

This project is open-source and available under the MIT License.
