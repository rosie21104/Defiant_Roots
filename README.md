# Defiant Roots: Grow What You Love, Wherever You Are

A multi-agent, climate-adaptive gardening companion that helps urban growers and hobbyists cultivate "impossible" plants in non-native, harsh, or extreme environments by engineering low-cost micro-climate adaptation blueprints.

---

## 🌿 Project Overview

### Problem
Most gardening resources answer a simple question: **"Can this plant grow where I live?"**

However, successful growing depends on much more than USDA zones or ideal climates. Environmental conditions change throughout the season, plants experience different stresses over time, and beginners often struggle to translate general gardening advice into practical actions for their own unique environment.

Existing gardening applications typically provide static recommendations but rarely adapt as growing conditions evolve. As a result, users may abandon ambitious growing projects after encountering their first setback rather than learning how to adapt.

### Solution
**Defiant Roots** is a multi-agent gardening companion that helps users grow plants in challenging environments through personalized adaptation rather than one-time recommendations.

Instead of simply telling a user what grows naturally in their region, Defiant Roots analyzes the relationship between plant biology and local environmental conditions to generate practical, low-cost adaptation strategies tailored to the user's goals.

The platform continues supporting the grower throughout the season by:
* Creating personalized adaptation blueprints.
* Monitoring changing regional weather extremes.
* Providing proactive weekly check-ins via SMS/Email.
* Updating recommendations dynamically based on user feedback and photos.
* Encouraging experimentation and continuous learning.

In addition to AI-powered guidance, the **Plant Gossip** community board enables growers to share real-world experiences, lessons learned, and practical tips so the community grows alongside the plants.

---

## 🏗️ Architecture & Multi-Agent Workflow

Defiant Roots is built using a decoupled architecture divided into two distinct operational cycles: a linear **Onboarding Pipeline** (Tab 1) and an iterative **Proactive Loop** (Tab 2).

```mermaid
graph TD
    subgraph Onboarding ["Phase A: Linear Onboarding Pipeline (Tab 1)"]
        A[User Input: Crop & City] --> B[Nominatim Geocoding API Validation]
        B --> C[Root Orchestrator Agent]
        C --> D[Plant Specialist Agent <br/> Ideal Biology & Vulnerabilities]
        C --> E[Extreme Climate Agent <br/> USDA Zone & Hazards]
        C --> F[YouBuddy YouTube Analyst <br/> ADK Crowd-Sourced Insights]
        D & E & F --> G[Synthesized Adaptation Blueprint & Start-up Phase]
        G --> H[(SQLite Database defiant_roots.db)]
    end

    subgraph ProactiveLoop ["Phase B: Iterative Proactive Loop (Tab 2)"]
        H --> I[Background Worker loop_worker.py]
        I --> J[Extreme Climate Agent <br/> Live Forecast & Google Search Grounding]
        J --> K[Proactive Progress Agent <br/> Compare Weather vs. Plant Biology]
        K --> L[Proactive Nudge Sent <br/> Capped & Stripped SMS / Email Alert]
        L --> M[Grower Check-in Update <br/> Log Feedback & Upload Plant Photos]
        M --> N[Image Safety Gate <br/> Magic Bytes, Size, EXIF Metadata Stripped]
        N --> O[Gemini 2.5 Flash <br/> Multimodal Reasoning & Action Plan]
        O -->|Commit & Advance Week| H
    end
```

#### Architecture Diagram Visual
![Architecture & Multi-Agent Workflow](assets/Arch_Multi-Agent_workflow.png)

### 🧠 Multi-Agent Roles
1. **Root Orchestrator Agent**: Coordinates the multi-agent hierarchy, dispatches research requests, maps plant vulnerabilities against local climate hazards, and compiles the final plan of action.
2. **Plant Specialist Agent**: Researches botanical baselines, temperature thresholds, sunlight needs, and critical environmental vulnerabilities for target crops.
3. **Extreme Climate Agent**: Investigates regional hardiness zones and historical hazards. In the proactive loop, it queries live forecasts utilizing **Google Search Grounding**.
4. **Proactive Progress Agent**: Maintains long-term state, checks upcoming weather extremes against biological thresholds, drafts personalized text/email nudges, and analyzes user updates.
5. **YouBuddy YouTube Analyst**: A local agent integrated via Google's **Agent Development Kit (ADK)** that crawls YouTube videos to summarize crowd-sourced gardening tips and highlights conflicting community viewpoints.

---

## 🛡️ Security Guardrails & Production Best Practices
To ensure a secure, robust application suitable for evaluation, Defiant Roots incorporates the following security gates:
* **Image Upload Security**: 
  * Strict file size checks limit uploads to **5MB** to prevent denial-of-service (DoS) vectors.
  * **Magic Bytes Validation**: Verifies the MIME type using raw file headers (accepts only `image/png` and `image/jpeg`), bypassing easily forged file extensions.
  * **EXIF Metadata Removal**: Strips metadata (GPS tags, device info, camera profiles) from photos using Pillow before processing to protect user privacy.
* **XSS Safeguards**: Runs all community logs, questions, and replies through `bleach.clean` to strip out styling and script tags, neutralizing HTML injection vectors.
* **SQL Injection Prevention**: All queries to SQLite use parameterized query boundaries (`?` placeholders) instead of raw string concatenation.
* **Subprocess Arguments Escaping**: Subprocess invocations for YouBuddy CLI validate inputs against strict alphanumeric regex guidelines to prevent command injection.
* **Spam Rate Limiting**: Grower entries to the community Grapevine board are capped at **10 posts per day per user** to maintain data integrity.

#### Security Flow Diagram Visual
![Security Guardrails Diagram](assets/Security_diagram.png)

---

## ⚙️ Quick Start & Setup Instructions

### Prerequisites
* **Python 3.10+**
* SQLite3
* A **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/)

### Installation
1. Clone this repository and navigate to the project directory:
   ```bash
   cd Defiant_Roots
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   YOUTUBE_API_KEY=your_optional_youtube_key_here
   ```

### Running the Project

#### 1. Run the Streamlit Application (Web App Dashboard)
Start the frontend dashboard:
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

* *Testing tip*: Click **"Sign in with Google"** in the sidebar to authenticate your profile.

#### 2. Run the Background Proactive Loop Worker
To simulate the background loop triggering weather forecast lookups and drafting SMS/Email nudges:
```bash
python3 loop_worker.py
```

* *Testing tip*: On Tab 2, click the **"Trigger Weekly Check-In Early"** button to execute the loop worker directly for your active crop.

#### 3. Run the YouBuddy CLI Search (Optional)
To query the YouTube Analyst CLI tool directly in the console:
```bash
python3 query_youbuddy_cli.py "growing mangos in dry desert zone 9"
```

---

## 🚀 Google Cloud Run Deployment

To deploy this project to Google Cloud Run:

### 1. Build and Deploy using Google Cloud Build
Run the following command in the project root folder to compile the Docker image and deploy it directly:
```bash
gcloud run deploy defiant-roots \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars GEMINI_API_KEY=your_gemini_api_key_here,YOUTUBE_API_KEY=your_optional_youtube_key_here
```

### ⚠️ Production Database Architecture Note
> [!WARNING]
> **Stateless Ephemeral Storage**: Google Cloud Run is a stateless container execution platform. The local SQLite database (`defiant_roots.db`) is stored inside the container filesystem, meaning that **all user history, logs, and comments will reset whenever the Cloud Run instance scales down to zero or restarts.**
> 
> **For Production/Evaluator Deployment**:
> To ensure data persistence in production, you should connect to a managed database instance (such as **Google Cloud SQL for PostgreSQL**) by updating [database.py](database.py) to target the cloud instance and configuring Cloud SQL connection pools in the Cloud Run deployment settings.

