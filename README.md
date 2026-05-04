# Smart Waste Segregation System

A college project that simulates an AI + IoT smart bin which classifies waste
(banana, apple, plastic, metal, paper, food scraps) and routes it into the
correct compartment — **Wet** or **Dry**. Built with Python Flask, vanilla
HTML/CSS/JS, and Chart.js, with optional real image classification powered by
a vision-language model.

---

## Features

- **Home** — Project overview, problem/solution, prototype illustration, and pipeline diagram.
- **Simulation** — Three input modes:
  - Upload an image
  - **Live Camera** — capture a frame from your webcam
  - **Run Demo** — random prediction
  Shows the predicted label, confidence, the source of the prediction, the
  bin decision (Wet / Dry), and an animated bin lid opening.
- **Analytics** — Total/Wet/Dry counters, doughnut + bar charts (Chart.js),
  recent prediction history, and a reset button.
- **About AI** — Explains the Edge Impulse training, CNN approach, classes,
  decision rule, and includes screenshots of the model training process.

---

## Project Structure

```
.
├── app.py                  # Flask application (routes + AI logic)
├── requirements.txt        # Python dependencies
├── .env.example            # Template for environment variables
├── README.md
├── templates/
│   ├── base.html
│   ├── index.html          # Home page
│   ├── simulate.html       # Simulation page
│   ├── analytics.html      # Analytics dashboard
│   └── ai.html             # About AI page
└── static/
    ├── css/style.css
    ├── js/script.js
    ├── images/             # Edge Impulse screenshots / hardware photos
    └── uploads/            # captured / uploaded images (auto-created)
```

---

## Requirements

- Python 3.9 or newer
- pip
- A modern browser (Chrome, Edge, Firefox, Safari) for the live-camera feature
- (Optional) A **Groq** API key — used for real image classification on uploads.
  Without it, the app still runs and falls back to random predictions.

---

## Setup & Run (Local)

### 1. Get the code

Clone or download this folder and open a terminal in it.

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate          # macOS / Linux
venv\Scripts\activate             # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a file named **`.env`** in the project root (same folder as `app.py`)
by copying the template:

```bash
cp .env.example .env              # macOS / Linux
copy .env.example .env            # Windows
```

Open `.env` and fill in your values:

```env
# Flask session secret (any long random string)
SESSION_SECRET=change-this-to-a-long-random-string

# Optional — enables real image classification on uploads / camera captures.
# Get a free key at https://console.groq.com
GROQ_API_KEY=your-groq-api-key-here

# Optional — port the app listens on (default 5000)
PORT=5000
```

The app now loads `.env` automatically when `python-dotenv` is installed.
If you prefer not to use a `.env` file, export the variables manually in your shell:

```bash
# macOS / Linux
export GROQ_API_KEY=your-groq-api-key-here
export SESSION_SECRET=change-me

# Windows (PowerShell)
$env:GROQ_API_KEY="your-groq-api-key-here"
$env:SESSION_SECRET="change-me"
```

### 5. Run the app

```bash
python app.py
```

Then open <http://localhost:5000> in your browser.

> The app listens on the `PORT` environment variable if set, otherwise port `5000`.

---

## Environment Variables

| Variable          | Required | Default                                   | Description                                                                 |
| ----------------- | -------- | ----------------------------------------- | --------------------------------------------------------------------------- |
| `SESSION_SECRET`  | No       | `smart-waste-dev-secret`                  | Flask session secret. Use a long random string in production.               |
| `GROQ_API_KEY`    | No       | (empty — uses random fallback)            | Enables real image classification on uploads / camera captures.             |
| `GROQ_VISION_MODEL` | No     | `meta-llama/llama-4-scout-17b-16e-instruct` | Vision model ID used for classification.                                  |
| `PORT`            | No       | `5000`                                    | Port the Flask server listens on.                                           |

---

## Using the Live Camera

1. Open the **Simulation** page.
2. Click the **Live Camera** tab.
3. Click **Start Camera** and allow the browser to use your webcam.
4. Click **Capture & Classify** — the captured frame is classified and the
   bin decision (Wet / Dry) is shown with an animation.

> Browsers only allow camera access on `http://localhost`, `http://127.0.0.1`,
> or any `https://` URL. If you serve over plain HTTP from another host, the
> camera will be blocked.

---

## Decision Logic

```python
if label in ["banana", "apple", "food_scraps"]:
    bin_type = "WET WASTE"
else:
    bin_type = "DRY WASTE"
```

Labels: `banana`, `apple`, `plastic`, `metal`, `paper`, `food_scraps`.

---

## Notes

- Counters live in memory and reset every time the server restarts (or via
  the **Reset Stats** button on the Analytics page).
- The **Run Demo** button always uses a random label so you can showcase the
  flow without uploading anything or needing an API key.
- Built for a college project — focus is on UX, clarity, and a clean Flask
  code structure.
- **Never commit your `.env` file to git.** Make sure `.env` is listed in
  `.gitignore`.
