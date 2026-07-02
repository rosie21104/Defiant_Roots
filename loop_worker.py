import os
import sys
import json
import database
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_loop_worker(target_experiment_id: int = None):
    """Runs a simulated weekly check-in, weather query, and nudge message generation."""
    print("🌿 Starting Proactive Loop Background Worker...")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in environment variables.")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)
    
    # 1. Fetch active experiments
    if target_experiment_id:
        active_exps = database.get_active_experiment_by_id(target_experiment_id)
    else:
        active_exps = database.get_all_active_experiments()
    if not active_exps:
        print("ℹ️ No active experiments found in database. Exiting.")
        return
        
    print(f"🔬 Found {len(active_exps)} active experiment(s) to process.")
    
    for row in active_exps:
        exp_id = row["id"]
        plant_name = row["plant_name"]
        location = row["location"]
        week_num = row["current_week"]
        preference = row["contact_preference"] if "contact_preference" in row.keys() else "Email"
        user_name = row["user_name"]
        
        print(f"\n──────────────────────────────────────────────────")
        print(f"👉 Processing Experiment #{exp_id}: {plant_name} in {location} (Week {week_num}) for user {user_name}")
        print(f"Preference: {preference}")
        
        # 2. Gather Live Weather Context via Extreme Climate Agent with Search Grounding
        print("🔍 Querying Extreme Climate Agent with Google Search Grounding...")
        weather_prompt = f"""
        You are the Extreme Climate Agent. 
        Perform a live search and return a concise, realistic summary of the CURRENT weather condition, temperature, 
        and any upcoming meteorological hazards (e.g. extreme heat, frost, storms) for the next 7 days in '{location}'.
        Include the current temperature explicitly in your summary.
        """
        
        try:
            weather_resp = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=weather_prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            weather_context = weather_resp.text.strip()
            print("🌦️ Weather Context Gathered:")
            print(weather_context)
        except Exception as e:
            print(f"⚠️ Search grounding failed. Falling back to default weather. Error: {e}")
            weather_context = f"Sunny, warm conditions around 85°F in {location}. No critical storm warnings."
            
        # 3. Draft Proactive Nudge using Gemini
        print("✍️ Drafting contact-preference nudge message...")
        nudge_prompt = f"""
        You are the Proactive Progress Agent for the Defiant Roots project.
        Draft a hyper-local, encouraging check-in nudge message for grower '{user_name}' who is growing a '{plant_name}' in '{location}'.
        
        CURRENT STATE: Week {week_num} of the experiment.
        WEATHER CONTEXT:
        {weather_context}
        
        CONTACT PREFERENCE: {preference}
        
        Formatting instructions:
        - If preference is 'SMS / Text': Make the message a single short, punchy SMS text (under 160 characters). Focus on the immediate weather hazard and ask how the plant is doing. Do not include subject lines or greetings like 'Dear Rosalyn'. Keep it conversational like a text.
        - If preference is 'Email': Make the message a full friendly email with a clear 'Subject:' line at the start, followed by the email body. Explain the weather hazard, refer to their week {week_num} progress, and suggest check-in tips.
        
        Keep the tone warm, biophilic, friendly, and supportive. Focus on low-cost micro-climate adaptation hacks.
        """
        
        try:
            # Ensure we use Gemini Developer API, not Vertex AI
            os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)
            nudge_resp = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=nudge_prompt
            )
            nudge_msg = nudge_resp.text.strip()
            print("✉️ Generated Nudge Message:")
            print(nudge_msg)
        except Exception as e:
            print(f"❌ Failed to draft nudge. Error: {e}")
            nudge_msg = f"Hey {user_name}! Quick check-in for your {plant_name} in {location} for week {week_num}. How is it holding up with the local weather?"
            
        # 4. Save to Database with Simulated Delivery Log
        phone_val = row["user_phone"] if row["user_phone"] else "+1-555-0199"
        email_val = row["user_email"] if row["user_email"] else "rosalyn@example.com"
        
        if "sms" in preference.lower():
            delivery_log = f"Sent via SMS to {phone_val}"
        else:
            delivery_log = f"Sent via Email to {email_val}"
            
        print(f"📡 SIMULATED DELIVERY: {delivery_log}")
        database.add_weekly_nudge(exp_id, week_num, weather_context, nudge_msg, delivery_log=delivery_log)
        print(f"✅ Saved nudge, weather context, and delivery log to weekly_logs for Experiment #{exp_id} (Week {week_num}).")

if __name__ == "__main__":
    run_loop_worker()
