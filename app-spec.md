# Defiant Roots: Application Specification

## 1. Project Overview
* **Target Audience:** Urban growers, beginners, and hobbyists trying to cultivate "impossible" plants in non-native, harsh, or extreme environments.
* **Core Mission:** Instead of telling a user what they can't grow, this multi-agent application acts as an environmental problem-solving partner—calculating micro-climate engineering hacks, trade-offs, and low-cost adaptation strategies to bridge the gap between plant needs and regional constraints.

## 2. Visual Design & User Experience (UX)
The UI must feel like a warm, supportive sanctuary, completely avoiding cold, sterile, or overly corporate tech layouts.
* **UI Style Keywords:**
  * **Biophilic Design:** Incorporate organic shapes, soft plant-like tones (sage greens, warm terracottas, soft creams), and plenty of whitespace.
  * **Soft Minimalist / Friendly Neo-Brutalisim:** Clean, highly readable text with rounded, card-based layouts that pop subtly off the background.
* **Tone & Microcopy:** Microcopy should be deeply encouraging and gamified. Instead of *"Error: Plant Status Poor,"* use *"Growth is a series of experiments! Let's adapt."* The more friendly, engaging, and encouraging the UI and agents can be, the better!

## 3. Core Features & UI Layout (Traditional Dashboard)

### Tab 1: The Adaptation Engine (The Input Form)
* **Structured Inputs:** An engaging, friendly interface with a simple form where a user plugs in what they want to grow (e.g., mangos) and what city/state they live in (e.g., Washington, Utah).
* **The "Bridge the Gap" Output:** A beautifully formatted, rounded card displaying:
  * **The Conflict:** Why this plant struggles here (e.g., *"Mangos need humidity and mild winters; Washington, Utah is an arid desert with extreme 100°F+ summer heat and winter frost risks"*).
  * **Low-Cost Adaptation Blueprint:** Actionable, creative, and highly realistic hacks. All recommendations must be low or reasonable cost and not too complicated. For example, to create humidity for a mango, recommend placing plastic over the pot and poking holes in it.

### Tab 2: Proactive Nudges & The Weekly Experiment Log
* **Proactive Nudge Engine:** The app does not wait for the user to check in. A background service triggers a periodic ping via Email or SMS (based on user preference toggled in the UI) every few days or once a week.
* **Dynamic Check-Ins:** The message pulls current local weather context (e.g., *"Hey! Temperatures are climbing past 100°F in Washington this weekend. How is your Mango seedling holding up? Reply to log your update!"*).
* **The Iterative Log View:** A dashboard view that tracks weekly progress and recommends vital, real-time modifications. For instance, if it's summer and temperatures are over 100°F, the agent must explicitly warn the user not to keep the plastic cover over the mango pot (as it creates an oven of 130°F that will kill the young germinating seedling) and instead suggest moving the pot inside an air-conditioned house or apartment where growth might be slower but steady.

### Tab 3: The "What I'm Learning" Community Board
* **Philosophy:** Grounded strictly in realism and vulnerability. The goal is to be community-minded and not a place to 'show off' (e.g., *'hey, look how amazing I did!'*). Instead, it highlights: *'This is what I’m trying and here’s what I’m learning.'*
* **Social Features:** A clean table or grid displaying active user growing progress where other community members have the option to comment on each other's logs to share tips, troubleshoot together, and trade climate-hacking advice.

## 4. Architecture & Multi-Agent Workflow
The backend uses a decoupled, multi-agent architecture split into two distinct operational cycles: a linear Onboarding Pipeline and an iterative Proactive Loop.
[Web App Dashboard (app.py)] ──(Writes User Logs)──► [ SQLite Database ] ◄──(Reads & Pings User)── [Background Worker (loop_worker.py)]

### Phase A: User Onboarding & Initialization (One-time Linear Pipeline)
1. **User Auth:** User logs in via a "Sign in with Google" layout (storing their `user_id` and email permanently in `defiant_roots.db`).
2. **Setup Request:** User submits their target plant (e.g., "Mango") and location (e.g., "Washington, Utah") via the dashboard form.
3. **Deep Research:** * **Plant Specialist Agent:** Fetches biological baseline facts and climate vulnerabilities.
   * **Extreme Climate Agent:** Investigates local hardiness zones and historical regional hazards.
4. **The Blueprint:** The **Proactive Progress Agent** synthesizes the research data to build the initial low-cost adaptation instructions, establishing the baseline thresholds (e.g., maximum heat/frost limits) that it will track in the cyclical loop.

Tools: youbuddy_search_api (plus your standard location/weather or plant database APIs).
•	Instruction Prompt:
"When a user provides a new plant type and location, you must call the youbuddy tool alongside your primary plant databases to gather community-driven experiences.
Analysis & Summary Guidelines:
•	Summarize the findings in an organized, highly readable, and encouraging format.
•	Discrepancy Tracking: Actively look for conflicting data (e.g., 'Some users in this zone report success with full sun, while others note severe leaf scorch'). Present these variations clearly as 'Community Notes' or 'Points of Consideration' rather than declaring a definitive, single 'correct' method. Do not issue a final verdict on disputed care tactics.
Output Generation:
Based on the combined technical data and the youbuddy crowd-sourced insights, generate a tailored, low-cost blueprint plan for the user to successfully establish and care for their plant."



5. **Establish State & Seed Memory:** The system saves this transaction to defiant_roots.db as an "Active Experiment" linked to the `user_id` saving the blueprint as the foundational entry in the experiment's history with an initial state of Week 1. The results are written to Streamlit's `st.session_state` to keep the UI persistent. To support multimodal capabilities in Phase B, ensure the database schema includes an optional image path or BLOB field for log entries.

### Phase B: The Proactive Iteration Loop (Repeated Weekly Cyclical Loop)
Instead of waiting for a user action on the frontend, a decoupled background worker (`loop_worker.py`) handles ongoing engagement for each active experiment that a user has:
1. **Time Trigger:** Triggers on a simulated weekly/periodic interval.
2. **Fetch State:** Reads all active experiments from `defiant_roots.db`.
3. **Live Context Gathering:** Calls the **Extreme Climate Agent** to fetch the *actual, real-time current weather data* for the user's location.
4. **Intelligent Comparison:** The **Proactive Progress Agent** compares the current weather extremes against the plant's biological thresholds.
5. **Generate Nudge:** The **Proactive Progress Agent** sends user via SMS or email  a hyper-localized, friendly check-in alert text/email with suggestions and encouragement (e.g., *"Hey Plant Friend! It's crossing 100°F in Washington this weekend! How has your plant been doing this past week? It might be time to pull the plastic dome off your mango seedling so it doesn't bake. Let me know and I can help you figure out the next best step!"*).
6. **User Interation and next step generation:** The user logs their feedback and questions via Tab 2 of the dashboard. This might also include photos or images. The agent analyzes this feedback using Gemini's multimodal capabilities (gemini-2.5-flash) to process image inputs if a user uploads a photo of their plant.

Tools: youbuddy_search_api
Instruction Prompt:
"Evaluate the user's weekly check-in feedback and explicit requests for assistance. You are granted autonomous discretion to call the youbuddy tool under the following conditions:
	1.	The user asks a highly specific troubleshooting question that standard documentation doesn't cover.
	2.	The user expresses frustration or mentions a symptom (e.g., yellowing leaves, pests) where crowd-sourced, real-world remedies could offer practical, low-cost interventions.
Adjust your reliance on this tool dynamically based on the complexity of the user's weekly update and their level of need."

Based on the previous results and the user's feedback, the agent is to generate a personalized weekly plan for the user, which is immediately committed back to defiant_roots.db to advance the experiment state.

## 5. Technical Constraints & Guardrails
* **Timeline Constraint:** Must be fully functional for capstone presentation by July 4.
* **Tech Stack:** Python, Streamlit (Frontend dashboard layout), Gemini API (`gemini-2.5-flash` for fast, cost-effective reasoning), and lightweight local storage (SQLite or JSON files) for data caching.
