"""
agent.py
The AI "brain" of the medication reminder system.
Implements: Observe -> Think -> Act -> Learn, returning structured
results so the Streamlit UI can render them nicely.
Uses the Google Gen AI SDK (google-genai).
"""

from google import genai
import json


def get_client(api_key):
    """
    Creates and returns a Gemini client if an API key is provided,
    otherwise returns None (caller should use rule-based fallback).
    """
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def analyze_behavior(user_data, api_key=None):
    """
    Takes a user's data dictionary and decides what action the agent
    should take. Tries Gemini AI first, falls back to rule-based logic.

    Returns a dict:
        {"action": "NORMAL_REMINDER" | "URGENT_ALERT" | "NOTIFY_FAMILY",
         "message": "...", "source": "ai" | "rules"}
    """
    name = user_data["name"]
    medication = user_data["medication_name"]
    missed = user_data["missed_doses"]
    last_taken = user_data["last_taken"]

    client = get_client(api_key)

    if client:
        prompt = (
            f"You are a warm, encouraging medical reminder AI. User {name} has missed "
            f"{missed} doses of {medication}. Their last dose was at {last_taken}. "
            f"Decide the action: if 0-1 missed doses say NORMAL_REMINDER, "
            f"if 2-3 say URGENT_ALERT, if 4+ say NOTIFY_FAMILY. "
            f"Also write a short, kind, personalized reminder message (1-2 sentences). "
            f"Respond ONLY in this exact JSON format with no extra text, no markdown: "
            f'{{"action": "NORMAL_REMINDER", "message": "your message here"}}'
        )
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            text = response.text.strip()
            if text.startswith("```"):
                text = text.strip("`")
                text = text.replace("json", "", 1).strip()
            result = json.loads(text)
            if "action" in result and "message" in result:
                result["source"] = "ai"
                return result
        except Exception:
            pass  # fall through to rule-based

    return rule_based_decision(name, medication, missed)


def rule_based_decision(name, medication, missed):
    """
    Simple if/else fallback logic used when AI is unavailable.
    """
    if missed >= 4:
        action = "NOTIFY_FAMILY"
        message = (
            f"{name} has missed {missed} doses of {medication} in a row. "
            f"A family member is being notified to check in."
        )
    elif missed >= 2:
        action = "URGENT_ALERT"
        message = (
            f"{name}, you've missed {missed} doses of {medication}. "
            f"Please try to take it as soon as possible."
        )
    else:
        action = "NORMAL_REMINDER"
        message = f"Hi {name}, here's your friendly reminder to take {medication} today!"

    return {"action": action, "message": message, "source": "rules"}
