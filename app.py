from flask import Flask, render_template_string, request, redirect, url_for, session
import pandas as pd
import json
from pathlib import Path
import random

# ================= APP SETUP =================
app = Flask(__name__)
app.secret_key = "final_capstone_secret"

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "snippets.csv"

# ================= LOAD DATA =================
df = pd.read_csv(CSV_PATH)
df = df.dropna(subset=["subject", "topic", "text"])

df["subject"] = df["subject"].astype(str).str.strip()
df["topic"] = df["topic"].astype(str).str.strip()
df["text"] = df["text"].astype(str).str.strip()

subject_topic_map = (
    df.groupby("subject")["topic"]
    .unique()
    .apply(list)
    .to_dict()
)

SUBJECT_TOPIC_JSON = json.dumps(subject_topic_map)

# ================= PREVENT BACK BUTTON =================
@app.after_request
def disable_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ================= BASE TEMPLATE =================
BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AI Study Quiz</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<style>
body { margin:0; font-family: Arial, sans-serif; }

.bg {
    min-height: 100vh;
    background-image: url("/static/project.jpeg");
    background-size: cover;
    background-position: center;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
}

.container {
    max-width: 800px;
    width: 100%;
    background: rgba(255,255,255,0.85);
    padding: 25px;
    border-radius: 12px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.25);
    animation: fadeIn 0.6s ease-in-out;
}

@keyframes fadeIn {
    from { opacity:0; transform: translateY(10px); }
    to { opacity:1; transform: translateY(0); }
}

select, button {
    width:100%;
    padding:12px;
    margin:10px 0;
    font-size:16px;
}

button {
    background:#7a4a2e;
    color:white;
    border:none;
    border-radius:8px;
    cursor:pointer;
    font-weight:600;
}

button:hover { background:#5f3822; }
</style>
</head>

<body class="bg">
{{ content|safe }}
</body>
</html>
"""

# ================= PAGE 1 — INTRO =================
@app.route("/", methods=["GET", "POST"])
def intro():
    if request.method == "POST":
        session.clear()
        session["subject"] = request.form["subject"]
        session["topic"] = request.form["topic"]
        return redirect(url_for("quiz"))

    subjects = sorted(df["subject"].unique())

    content = f"""
    <div class="container">
        <h1>AI Study Model</h1>
        <p>Select a subject and topic</p>

        <form method="post">
            <select id="subject" name="subject" required>
                <option value="">-- Select Subject --</option>
                {''.join([f"<option value='{s}'>{s}</option>" for s in subjects])}
            </select>

            <select id="topic" name="topic" required>
                <option value="">-- Select Topic --</option>
            </select>

            <button type="submit">Begin Quiz</button>
        </form>
    </div>

    <script>
    const mapping = {SUBJECT_TOPIC_JSON};

    const subjectSelect = document.getElementById("subject");
    const topicSelect = document.getElementById("topic");

    subjectSelect.addEventListener("change", function () {{
        topicSelect.innerHTML = "<option value=''>-- Select Topic --</option>";
        (mapping[this.value] || []).forEach(t => {{
            const opt = document.createElement("option");
            opt.value = t;
            opt.textContent = t;
            topicSelect.appendChild(opt);
        }});
    }});
    </script>
    """
    return render_template_string(BASE_HTML, content=content)

# ================= PAGE 2 — QUIZ =================
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "subject" not in session:
        return redirect(url_for("intro"))

    pool = df[(df.subject == session["subject"]) & (df.topic == session["topic"])]
    questions = pool.sample(n=min(5, len(pool))).to_dict("records")

    if request.method == "POST":
        score = 0
        for i in range(len(questions)):
            ans = request.form.get(f"q{i}")
            if ans == "strong":
                score += 2
            elif ans == "partial":
                score += 1

        total = len(questions) * 2
        percent = (score / total) * 100

        if percent >= 80:
            remark = "Excellent performance! You have strong command over this topic."
        elif percent >= 50:
            remark = "Good attempt! With some revision, you can improve further."
        else:
            remark = "Needs improvement. Revise fundamentals and try again."

        session["score"] = score
        session["total"] = total
        session["remark"] = remark

        return redirect(url_for("remarks"))

    content = "<div class='container'><h2>Quiz</h2><form method='post'>"

    for i, q in enumerate(questions):
        content += f"""
        <p><b>Q{i+1}.</b> {q['text']}</p>
        <label><input type="radio" name="q{i}" value="strong" required> Strong</label><br>
        <label><input type="radio" name="q{i}" value="partial"> Partial</label><br>
        <label><input type="radio" name="q{i}" value="weak"> Weak</label><br><br>
        """

    content += "<button type='submit'>Submit Quiz</button></form></div>"
    return render_template_string(BASE_HTML, content=content)

# ================= PAGE 3 — REMARKS =================
@app.route("/remarks")
def remarks():
    if "score" not in session:
        return redirect(url_for("intro"))

    content = f"""
    <div class="container">
        <h2>Performance Remarks</h2>
        <p><b>Score:</b> {session['score']} / {session['total']}</p>
        <p><i>{session['remark']}</i></p>
        <a href="{url_for('report')}"><button>View Final Report</button></a>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

# ================= PAGE 4 — REPORT =================
@app.route("/report")
def report():
    if "score" not in session:
        return redirect(url_for("intro"))

    content = f"""
    <div class="container">
        <h2>Final Learning Report</h2>
        <p><b>Subject:</b> {session['subject']}</p>
        <p><b>Topic:</b> {session['topic']}</p>
        <p><b>Final Score:</b> {session['score']} / {session['total']}</p>
        <hr>
        <p><i>{session['remark']}</i></p>
        <br>
        <a href="{url_for('intro')}"><button>Take Another Quiz</button></a>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
