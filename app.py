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

# Subject → Topic mapping
subject_topic_map = (
    df.groupby("subject")["topic"]
    .unique()
    .apply(list)
    .to_dict()
)

SUBJECT_TOPIC_JSON = json.dumps(subject_topic_map)

# ================= BASE TEMPLATE =================
BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AI Study Quiz</title>
<style>
body {
    margin:0;
    font-family:Arial, sans-serif;
}
.bg {
    background-image: url('{{ url_for("static", filename="study_table.jpeg") }}');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    min-height:100vh;
    padding-top:40px;
}
.container {
    width:65%;
    margin:auto;
    background:rgba(255,255,255,0.95);
    padding:40px;
    border-radius:12px;
    box-shadow:0 10px 25px rgba(0,0,0,0.25);
}
select, button {
    width:70%;
    padding:12px;
    margin:10px 0;
    font-size:16px;
}
button {
    background:#2c3e50;
    color:white;
    border:none;
    cursor:pointer;
}
input[type=radio] {
    margin-right:8px;
}
</style>
</head>
<body class="bg">
{{ content|safe }}
</body>
</html>
"""

# ================= PAGE 1 — INTRO =================
@app.route("/", methods=["GET","POST"])
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
      const subjectSel = document.getElementById("subject");
      const topicSel = document.getElementById("topic");

      subjectSel.addEventListener("change", function() {{
        topicSel.innerHTML = "<option value=''>-- Select Topic --</option>";
        (mapping[this.value] || []).forEach(t => {{
            let o = document.createElement("option");
            o.value = t;
            o.textContent = t;
            topicSel.appendChild(o);
        }});
      }});
    </script>
    """

    return render_template_string(BASE_HTML, content=content)

# ================= PAGE 2 — QUIZ =================
@app.route("/quiz", methods=["GET","POST"])
def quiz():
    if "subject" not in session or "topic" not in session:
        return redirect(url_for("intro"))

    subject = session["subject"]
    topic = session["topic"]

    pool = df[(df.subject == subject) & (df.topic == topic)]

    questions = pool.sample(
        n=min(5, len(pool)),
        replace=False,
        random_state=random.randint(1, 9999)
    ).to_dict("records")

    session["questions"] = questions

    if request.method == "POST":
        score = 0
        for i in range(len(questions)):
            ans = request.form.get(f"q{i}")
            if ans == "strong":
                score += 2
            elif ans == "partial":
                score += 1

        session["score"] = score
        session["total"] = len(questions) * 2
        return redirect(url_for("remarks"))

    content = "<div class='container'><h2>Quiz</h2><form method='post'>"

    for i, q in enumerate(questions):
        content += f"""
        <p><b>Q{i+1}.</b> {q['text']}</p>
        <label><input type="radio" name="q{i}" value="strong" required>Strong understanding</label><br>
        <label><input type="radio" name="q{i}" value="partial">Partial understanding</label><br>
        <label><input type="radio" name="q{i}" value="weak">Need revision</label><br><br>
        """

    content += "<button type='submit'>Submit Quiz</button></form></div>"
    return render_template_string(BASE_HTML, content=content)

# ================= PAGE 3 — REMARKS =================
@app.route("/remarks")
def remarks():
    if "topic" not in session:
        return redirect(url_for("intro"))

    content = f"""
    <div class="container">
      <h2>Performance Remarks</h2>
      <p><b>Score:</b> {session['score']} / {session['total']}</p>
      <p>Your responses indicate active engagement with <b>{session['topic']}</b>.</p>
      <p>Revisiting tricky concepts will improve mastery.</p>
      <a href="{url_for('focus')}"><button>Next</button></a>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

# ================= PAGE 4 — FOCUS =================
@app.route("/focus")
def focus():
    if "subject" not in session:
        return redirect(url_for("intro"))

    content = f"""
    <div class="container">
      <h2>Key Focus Areas</h2>
      <ul>
        <li>Conceptual clarity in {session['topic']}</li>
        <li>Terminology accuracy</li>
        <li>Applied understanding</li>
        <li>Connections within {session['subject']}</li>
      </ul>
      <a href="{url_for('report')}"><button>Final Report</button></a>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

# ================= PAGE 5 — REPORT =================
@app.route("/report")
def report():
    if "subject" not in session:
        return redirect(url_for("intro"))

    content = f"""
    <div class="container">
      <h2>Final Learning Report</h2>
      <p><b>Subject:</b> {session['subject']}</p>
      <p><b>Topic:</b> {session['topic']}</p>
      <p><b>Final Score:</b> {session['score']} / {session['total']}</p>
      <p><b>Status:</b> Quiz Completed</p>
      <hr>
      <p><i>Consistent practice transforms understanding into mastery.</i></p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
