import requests
import json
import pypdf
from flask import (
    Flask,
    render_template,
    request,
    jsonify
)

app = Flask(__name__)

# ==========================================
# CHUTES CONFIG
# ==========================================
CHUTES_API_KEY = "YOUR_CHUTES_API_KEY"
CHUTES_URL = "https://llm.chutes.ai/v1/chat/completions"

# Global database registers
GLOBAL_CANDIDATES_ARRAY = []
# Updated to support objects containing title & custom description/questions
GLOBAL_ACTIVE_JOBS = [
    {"title": "Programmer", "description": "Can you explain your background experience regarding details of a Programmer role?\nWhat core professional development tools or technical software stacks do you optimize with?\nCan you detail a difficult project challenge you encountered and how you successfully navigated it?"},
    {"title": "Marketing Manager", "description": "Can you explain your background experience regarding details of a Marketing Manager role?\nWhat core professional development tools or technical software stacks do you optimize with?\nCan you detail a difficult project challenge you encountered and how you successfully navigated it?"}
]
GLOBAL_INTERVIEWS_REGISTRY = {} # Stores live candidate transcript conversations


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/join")
def public_intake():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Join our Talent Pool - HIREY</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Inter', sans-serif; background: #060816; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
            .intake-card { background: #0d1224; border: 1px solid #1c2440; padding: 40px; border-radius: 20px; max-width: 450px; width: 100%; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-align: center; }
            h1 { color: #9d5cff; margin-bottom: 10px; font-size: 28px; }
            p { color: #7f8db3; font-size: 14px; margin-bottom: 30px; line-height: 1.5; }
            .form-group { text-align: left; margin-bottom: 20px; }
            label { display: block; color: #cbd5e1; font-size: 12px; font-weight: 600; margin-bottom: 8px; text-transform: uppercase; }
            input[type="text"] { width: 100%; background: #161f38; border: 1px solid #263252; padding: 12px; border-radius: 10px; color: white; outline: none; font-size: 14px; }
            .file-dropzone { border: 2px dashed #263252; padding: 30px 20px; border-radius: 12px; background: #0f1526; cursor: pointer; margin-bottom: 25px; }
            .submit-btn { background: linear-gradient(90deg, #7c3aed, #5b21b6); color: white; border: none; padding: 14px; width: 100%; border-radius: 10px; font-weight: 600; cursor: pointer; }
            #statusMsg { margin-top: 15px; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="intake-card">
            <h1>HIREY Talent Portal</h1>
            <p>Submit your resume parameters directly into our recruitment pipeline matrix for instantaneous matching review.</p>
            <form id="publicUploadForm">
                <div class="form-group">
                    <label>Your Full Name</label>
                    <input type="text" id="applicantName" placeholder="e.g. Alex Mercer" required>
                </div>
                <div class="form-group">
                    <label>Select Resume Document (.pdf or .txt)</label>
                    <div class="file-dropzone" onclick="document.getElementById('publicFile').click()">
                        <span id="fileLabel" style="color: #a3b3e0; font-size: 14px;">📄 Click to select your resume</span>
                        <input type="file" id="publicFile" accept=".pdf,.txt" style="display:none;" required>
                    </div>
                </div>
                <button type="submit" class="submit-btn">Submit to Talent Pool</button>
            </form>
            <div id="statusMsg"></div>
        </div>
        <script>
            const fileInput = document.getElementById('publicFile');
            const fileLabel = document.getElementById('fileLabel');
            fileInput.addEventListener('change', () => {
                if(fileInput.files.length > 0) {
                    fileLabel.innerText = "Selected: " + fileInput.files[0].name;
                    fileLabel.style.color = "#10b981";
                }
            });
            document.getElementById('publicUploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const statusMsg = document.getElementById('statusMsg');
                statusMsg.innerText = "Analyzing and uploading candidate parameters...";
                statusMsg.style.color = "#9d5cff";
                const formData = new FormData();
                formData.append('resume', fileInput.files[0]);
                formData.append('explicit_name', document.getElementById('applicantName').value);
                try {
                    const res = await fetch('/analyze_public', { method: 'POST', body: formData });
                    const data = await res.json();
                    if(data.error) { statusMsg.innerText = "Error: " + data.error; statusMsg.style.color = "#ef4444"; }
                    else {
                        statusMsg.innerText = "Success! Your resume has been synced into our pipeline.";
                        statusMsg.style.color = "#10b981";
                        document.getElementById('publicUploadForm').reset();
                        fileLabel.innerText = "📄 Click to select your resume";
                        fileLabel.style.color = "#a3b3e0";
                    }
                } catch(err) { statusMsg.innerText = "Submission layer connection error."; statusMsg.style.color = "#ef4444"; }
            });
        </script>
    </body>
    </html>
    """


# ==========================================================
# PUBLIC LANDING INTERVIEW INTERFACE FOR CANDIDATES
# ==========================================================
@app.route("/interview/<candidate_name>/<job_title>")
def automated_bot_interview_portal(candidate_name, job_title):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HIREY - AI Interrogation Core</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; background: #060816; color: white; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
            .chat-container {{ width: 100%; max-width: 600px; background: #0d1224; border: 1px solid #1c2440; border-radius: 20px; display: flex; flex-direction: column; height: 80vh; box-shadow: 0 8px 32px rgba(0,0,0,0.4); }}
            .chat-header {{ background: #111827; padding: 20px; border-bottom: 1px solid #1c2440; border-radius: 20px 20px 0 0; }}
            .chat-header h2 {{ margin: 0; font-size: 18px; color: #ffffff; }}
            .chat-header p {{ margin: 4px 0 0 0; font-size: 13px; color: #7f8db3; }}
            .messages-view {{ flex-grow: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; }}
            .msg {{ max-width: 80%; padding: 12px 16px; border-radius: 14px; font-size: 14px; line-height: 1.5; }}
            .bot {{ background: #161f38; border: 1px solid #263252; color: #f1f5f9; align-self: flex-start; }}
            .user {{ background: linear-gradient(135deg, #7c3aed, #6d28d9); color: white; align-self: flex-end; }}
            .input-row {{ padding: 15px; border-top: 1px solid #1c2440; display: flex; gap: 10px; background: #090d1a; border-radius: 0 0 20px 20px; }}
            .input-row input {{ flex-grow: 1; background: #161f38; border: 1px solid #263252; padding: 12px; border-radius: 10px; color: white; outline: none; }}
            .input-row input:disabled {{ opacity: 0.5; cursor: not-allowed; }}
            .send-btn {{ background: #9d5cff; color: white; border: none; padding: 0 20px; border-radius: 10px; font-weight: 600; cursor: pointer; }}
            .send-btn:disabled {{ background: #4b5563; cursor: not-allowed; }}
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">
                <h2>HIREY Autonomous Screening Bot</h2>
                <p>Applicant: <strong>{candidate_name}</strong> | Target Role: <strong>{job_title}</strong></p>
            </div>
            <div id="messagesView" class="messages-view"></div>
            <div class="input-row">
                <input type="text" id="userInput" placeholder="Type your answer here..." autocomplete="off">
                <button id="sendBtn" class="send-btn">Send</button>
            </div>
        </div>

        <script>
            const messagesView = document.getElementById('messagesView');
            const userInput = document.getElementById('userInput');
            const sendBtn = document.getElementById('sendBtn');
            const candidate = "{candidate_name}";
            const job = "{job_title}";

            function appendMessage(text, side) {{
                const d = document.createElement('div');
                d.className = 'msg ' + side;
                d.innerText = text;
                messagesView.appendChild(d);
                messagesView.scrollTop = messagesView.scrollHeight;
            }}

            async function initChat() {{
                const res = await fetch('/bot_action', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ candidate: candidate, job: job, message: '', step: 'INIT' }})
                }});
                const data = await res.json();
                appendMessage(data.bot_message, 'bot');
            }}

            async function sendMessage() {{
                const val = userInput.value.trim();
                if(!val) return;
                appendMessage(val, 'user');
                userInput.value = '';
                userInput.disabled = true;
                sendBtn.disabled = true;

                const res = await fetch('/bot_action', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ candidate: candidate, job: job, message: val, step: 'TALK' }})
                }});
                const data = await res.json();
                appendMessage(data.bot_message, 'bot');

                if(!data.complete) {{
                    userInput.disabled = false;
                    sendBtn.disabled = false;
                    userInput.focus();
                }} else {{
                    userInput.placeholder = "Interview successfully completed.";
                }}
            }}

            sendBtn.onclick = sendMessage;
            userInput.onkeydown = (e) => {{ if(e.key === 'Enter') sendMessage(); }};
            initChat();
        </script>
    </body>
    </html>
    """


# ==========================================================
# SEQUENTIAL SCREENING ENGINE WITH AUTO SUMMARY PIPELINE
# ==========================================================
@app.route("/bot_action", methods=["POST"])
def bot_action():
    req = request.json or {}
    candidate = req.get("candidate", "")
    job = req.get("job", "")
    user_msg = req.get("message", "").strip()
    step = req.get("step", "TALK")

    session_key = f"{candidate}||{job}"
    if session_key not in GLOBAL_INTERVIEWS_REGISTRY:
        # Resolve custom requirements/questions set from Job Workspace setup
        resolved_questions = []
        for j in GLOBAL_ACTIVE_JOBS:
            j_title = j if isinstance(j, str) else j.get("title", "")
            if j_title.lower() == job.lower():
                j_desc = "" if isinstance(j, str) else j.get("description", "")
                if j_desc.strip():
                    # Split lines up or treat paragraphs as custom evaluation criteria questions
                    resolved_questions = [q.strip() for q in j_desc.split("\n") if q.strip()]
                break
        
        # Fallback list if no specific requirements/questions were written
        if not resolved_questions:
            resolved_questions = [
                f"Can you explain your background experience regarding details of a {job} role?",
                "What core professional development tools or technical software stacks do you optimize with?",
                "Can you detail a difficult project challenge you encountered and how you successfully navigated it?"
            ]

        GLOBAL_INTERVIEWS_REGISTRY[session_key] = {
            "candidate": candidate,
            "job": job,
            "history": [],
            "current_question_index": 0,
            "questions": resolved_questions
        }

    session = GLOBAL_INTERVIEWS_REGISTRY[session_key]
    total_questions = len(session["questions"])

    if step == "INIT":
        greeting = f"Hello {candidate}, welcome to your HIREY automated AI screening portal tracking the '{job}' opening. Let's begin. Question 1: {session['questions'][0]}"
        session["history"].append({"sender": "Bot", "text": greeting})
        session["current_question_index"] = 1
        return jsonify({"bot_message": greeting, "complete": False})

    # Record applicant reply
    session["history"].append({"sender": candidate, "text": user_msg})
    current_q_idx = session["current_question_index"]

    if current_q_idx < total_questions:
        next_q = session["questions"][current_q_idx]
        bot_reply = f"Thank you. Question {current_q_idx + 1}: {next_q}"
        session["history"].append({"sender": "Bot", "text": bot_reply})
        session["current_question_index"] += 1
        return jsonify({"bot_message": bot_reply, "complete": False})
    else:
        final_reply = "Thank you very much! The interview is completed. HIREY Core has logged your transcript for internal evaluator review."
        session["history"].append({"sender": "Bot", "text": final_reply})
        
        # Compile full conversational log
        transcript_dump = ""
        for item in session["history"]:
            transcript_dump += f"{item['sender']}: {item['text']}\n"

        # Ask the AI to compile an interview evaluation summary note
        try:
            summary_prompt = f"Summarize this candidate interview screening transcript into 2 succinct sentences highlighting core capabilities:\n\n{transcript_dump}"
            headers = {"Authorization": f"Bearer {CHUTES_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "model": "google/gemma-4-31B-turbo-TEE",
                "messages": [{"role": "user", "content": summary_prompt}],
                "temperature": 0.3, "max_tokens": 400
            }
            ai_res = requests.post(CHUTES_URL, headers=headers, json=payload).json()
            summary_note = ai_res["choices"][0]["message"]["content"].strip()
        except:
            summary_note = "Interview completed successfully. Responses logged for internal matching index verification workflows."

        # Inject this summary directly into the localized cache target record
        for c in GLOBAL_CANDIDATES_ARRAY:
            if c["name"].lower() == candidate.lower():
                c["interview_summary"] = summary_note
                break

        return jsonify({"bot_message": final_reply, "complete": True})


@app.route("/get_interviews", methods=["GET"])
def get_interviews():
    return jsonify({"interviews": list(GLOBAL_INTERVIEWS_REGISTRY.values())})


@app.route("/get_candidates", methods=["GET"])
def get_candidates():
    return jsonify({"candidates": GLOBAL_CANDIDATES_ARRAY, "jobs": GLOBAL_ACTIVE_JOBS})


@app.route("/sync_candidates", methods=["POST"])
def sync_candidates():
    global GLOBAL_CANDIDATES_ARRAY, GLOBAL_ACTIVE_JOBS
    data = request.json or {}
    GLOBAL_CANDIDATES_ARRAY = data.get("candidates", [])
    GLOBAL_ACTIVE_JOBS = data.get("jobs", [])
    return jsonify({"status": "success"})


@app.route("/analyze_public", methods=["POST"])
def analyze_public():
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["resume"]
    explicit_name = request.form.get("explicit_name", "Anonymous Applicant").strip()
    try:
        filename = file.filename.lower()
        extracted_text = ""
        if filename.endswith(".pdf"):
            reader = pypdf.PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                if text: extracted_text += text + "\n"
        elif filename.endswith(".txt"):
            extracted_text = file.read().decode("utf-8", errors="ignore")
        else:
            return jsonify({"error": "Unsupported file format."}), 400

        prompt = f"Analyze this resume carefully.\nReturn ONLY in this EXACT format:\nNAME: candidate full name\nSKILLS: main technical skills separated by commas\nSUMMARY: short professional summary\n\nResume:\n{extracted_text[:100000]}"
        headers = {"Authorization": f"Bearer {CHUTES_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "google/gemma-4-31B-turbo-TEE",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2, "max_tokens": 800
        }
        response = requests.post(CHUTES_URL, headers=headers, json=payload)
        data = response.json()
        analysis_result = data["choices"][0]["message"]["content"]
        
        candidate_name = explicit_name
        candidate_skills = "Professional candidate profile."
        candidate_summary = "AI analyzed candidate structure."

        for line in analysis_result.split("\n"):
            line_str = line.strip()
            if line_str.upper().startswith("NAME:"):
                parsed_name = line_str[5:].strip()
                if parsed_name and explicit_name == "Anonymous Applicant": candidate_name = parsed_name
            elif line_str.upper().startswith("SKILLS:"):
                candidate_skills = line_str[7:].strip()
            elif line_str.upper().startswith("SUMMARY:"):
                candidate_summary = line_str[8:].strip()

        GLOBAL_CANDIDATES_ARRAY.insert(0, {
            "name": candidate_name, "skills": candidate_skills, "summary": candidate_summary, "interview_summary": "Awaiting scheduling tracking link execution..."
        })
        return jsonify({"status": "success", "parsed_name": candidate_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/analyze", methods=["POST"])
def analyze():
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["resume"]
    try:
        filename = file.filename.lower()
        extracted_text = ""
        if filename.endswith(".pdf"):
            reader = pypdf.PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                if text: extracted_text += text + "\n"
        elif filename.endswith(".txt"):
            extracted_text = file.read().decode("utf-8", errors="ignore")
        
        prompt = f"Analyze this resume carefully.\nReturn ONLY in this EXACT format:\nNAME: candidate full name\nSKILLS: main technical skills separated by commas\nSUMMARY: short professional summary\n\nResume:\n{extracted_text[:100000]}"
        headers = {"Authorization": f"Bearer {CHUTES_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "google/gemma-4-31B-turbo-TEE",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2, "max_tokens": 800
        }
        response = requests.post(CHUTES_URL, headers=headers, json=payload)
        return jsonify({"result": response.json()["choices"][0]["message"]["content"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/match_job", methods=["POST"])
def match_job():
    req_data = request.get_json() or {}
    job_title = req_data.get("job_title", "")
    candidates = req_data.get("candidates", [])
    if not job_title or not candidates:
        return jsonify({"error": "Missing validation requirements."}), 400
    try:
        candidates_context = ""
        for idx, c in enumerate(candidates):
            candidates_context += f"CANDIDATE_ID: {idx}\nName: {c['name']}\nSkills: {c['skills']}\nSummary: {c['summary']}\n---\n"

        prompt = f"You are an advanced AI Recruiter. Look over the following list of candidates and evaluate, sort, and rank EVERY single candidate from best suited to least suited for the target job opening.\n\nTarget Job Opening: {job_title}\n\nCandidate List:\n{candidates_context}\n\nProvide your decision output by generating a block for EVERY candidate in your sorted order. Do NOT use brackets, markdown styling or extra text. Use this exact formatting block structure:\n\nRANK: Number representing order (starting at 1 for the best match)\nNAME: exact full name of the candidate\nREASONING: brief 2-3 sentence explanation of why their skills match or rank at this position\n==="
        headers = {"Authorization": f"Bearer {CHUTES_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "google/gemma-4-31B-turbo-TEE",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3, "max_tokens": 2000
        }
        response = requests.post(CHUTES_URL, headers=headers, json=payload)
        return jsonify({"match_result": response.json()["choices"][0]["message"]["content"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=9999)