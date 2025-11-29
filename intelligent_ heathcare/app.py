# app.py
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import sqlite3, re, io
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

DB = 'app.db'
app = Flask(__name__)
app.secret_key = "your_secret_key_here"

DISEASES ={ 


    "Common Cold / Fever": {
        "feelings": [
            "fever", "body hot", "hot", "warm", "cold is there", "cold", "sneezing",
            "runny nose", "nose water", "blocked nose", "throat pain", "sore throat",
            "cough", "coughing", "weak", "tired", "body pain", "chills"
        ],
        "prescription": "Take rest, drink warm water, take Paracetamol 500mg if needed.",
        "serious": False
    },

    "Food Poisoning / Stomach Infection": {
        "feelings": [
            "vomit", "vomiting", "want to vomit", "nausea", "loose motion",
            "loose motions", "watery motion", "stomach pain", "stomach upset",
            "abdominal pain", "cramps", "diarrhea"
        ],
        "prescription": "Drink ORS, avoid oily food, eat light food like rice/curd.",
        "serious": True
    },

    "Possible Heart Problem": {
        "feelings": [
            "chest pain", "chest tight", "tight chest", "heart pain", "left hand pain",
            "breathing problem", "breath not coming", "short of breath",
            "heavy chest", "pressure on chest"
        ],
        "prescription": "Go to a hospital immediately. Do not ignore chest symptoms.",
        "serious": True
    },

    "Migraine / Normal Headache": {
        "feelings": [
            "headache", "head pain", "head is spinning", "dizzy", "dizziness",
            "light disturbing", "light hurting eyes", "noise irritating",
            "stress", "pressure in head"
        ],
        "prescription": "Rest in a quiet dark room, drink water, take mild pain relief if needed.",
        "serious": False
    },

    "Skin Allergy": {
        "feelings": [
            "itch", "itching", "skin itching", "rashes", "rash", "red marks",
            "red skin", "bumps", "skin burning", "allergy", "hives"
        ],
        "prescription": "Take an antihistamine (like cetrizine) and avoid scratching.",
        "serious": False
    },
        "Anxiety / Stress Symptoms": {
        "feelings": [
            "nervous", "anxious", "overthinking", "scared", "fear",
            "heart racing", "shaking", "sweating", "restless",
            "cant focus", "worry", "tense", "pressure", "tight chest anxiety",
            "panic", "panic attack"
        ],
        "prescription": "Try deep breathing, grounding exercises, and take breaks. If symptoms continue, talk to a mental health professional.",
        "serious": False
    },

    "Depression-like Feelings": {
        "feelings": [
            "sad", "feeling low", "empty", "hopeless", "no interest",
            "tired all time", "no energy", "crying", "sleeping too much",
            "not sleeping", "lonely", "feeling alone", "numb", "worthless",
            "overthinking life", "dark thoughts"
        ],
        "prescription": "Talk to someone you trust, maintain routine, try light activity. If these feelings persist, please consult a mental health expert.",
        "serious": True
    },

    "Panic / Emotional Overload": {
        "feelings": [
            "heart beating fast", "cant breathe properly", "shaking body",
            "heavy fear", "sudden fear", "dizzy with fear", "freeze feeling",
            "suffocating", "panic feeling", "panic suddenly"
        ],
        "prescription": "Sit down, breathe slowly, drink water. If repeated episodes occur, consult a mental health specialist.",
        "serious": True
    },

    "Sleep Problems / Insomnia": {
        "feelings": [
            "cant sleep", "not sleeping", "wake up often", "bad dreams",
            "sleep problem", "insomnia", "no sleep", "sleep late", "day tired"
        ],
        "prescription": "Avoid screens before bed, reduce caffeine, follow a sleep routine. If sleep issues last long, consult a doctor.",
        "serious": False
    },

    "Burnout / Emotional Exhaustion": {
        "feelings": [
            "no motivation", "emotionally tired", "mentally tired",
            "cant do anything", "drained", "empty feeling", "exhausted mind",
            "overworked", "too much stress"
        ],
        "prescription": "Take a break, rest properly, lighten workload, talk to someone. Seek help if exhaustion continues.",
        "serious": False
    },

}


def tokenize(text):
    return re.findall(r"\w+", (text or "").lower())

def analyze_text(text):
    tokens = set(tokenize(text))
    best = {"disease": "Not Sure", "score": 0, "entry": None}
    for name, entry in DISEASES.items():
        score = sum(1 for kw in entry["feelings"] if kw in tokens)
        if score > best["score"]:
            best = {"disease": name, "score": score, "entry": entry}
    if best["score"] == 0:
        return {"disease": "Not Sure",
                "prescription": "Please describe how you feel.",
                "serious": True}
    return {"disease": best["disease"],
            "prescription": best["entry"]["prescription"],
            "serious": best["entry"]["serious"]}

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# -------------------- ROUTES --------------------

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    text = request.form.get("symptoms", "")
    result = analyze_text(text)

    if session.get("user_id"):
        conn = get_db()
        conn.execute("INSERT INTO reports (user_id, symptoms, diagnosis, prescription, serious) VALUES (?,?,?,?,?)",
                     (session["user_id"], text, result["disease"], result["prescription"], int(result["serious"])))
        conn.commit()
        conn.close()

    return render_template("result.html", data=result, input_text=text)

@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    session.setdefault("chat_history", [])
    if request.method == "POST":
        q = request.form.get("q", "")
        session["chat_history"].append(("user", q))

        if "chest" in q.lower():
            bot = "Do you feel chest pressure often? If severe, seek doctor."
        else:
            res = analyze_text(q)
            bot = f"I think: {res['disease']}. Advice: {res['prescription']}"

        session["chat_history"].append(("bot", bot))
        return redirect(url_for("chatbot"))

    return render_template("chatbot.html", history=session["chat_history"])

@app.route("/voice")
def voice():
    return render_template("voice.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username,password) VALUES (?,?)",
                         (username, generate_password_hash(password)))
            conn.commit()
            flash("Registered successfully.")
            return redirect(url_for("login"))
        except:
            flash("Username already taken")
        conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = username
            return redirect(url_for("home"))
        flash("Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out")
    return redirect(url_for("home"))

@app.route("/history")
def history():
    if not session.get("user_id"):
        flash("Login required")
        return redirect(url_for("login"))
    conn = get_db()
    rows = conn.execute("SELECT * FROM reports WHERE user_id=?", (session["user_id"],)).fetchall()
    conn.close()
    return render_template("history.html", reports=rows)

@app.route("/admin")
def admin():
    if session.get("username") != "admin":
        flash("Admin only")
        return redirect(url_for("login"))
    conn = get_db()
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_reports = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    top = conn.execute("SELECT diagnosis, COUNT(*) as c FROM reports GROUP BY diagnosis").fetchall()
    conn.close()
    return render_template("admin.html", users=total_users, reports=total_reports, top=top)

@app.route("/doctor_finder", methods=["GET","POST"])
def doctor_finder():
    doctors = None
    if request.method == "POST":
        city = request.form.get("city", "").lower()
        sample = {
            "bangalore": [("City Hospital","General"), ("Heart Center","Cardiology")],
            "mumbai": [("Metro Hospital","General")],
        }
        doctors = sample.get(city, [("Nearby Clinic","General")])
    return render_template("doctor_finder.html", doctors=doctors)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
