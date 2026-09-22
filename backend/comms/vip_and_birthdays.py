import datetime
from typing import List, Dict, Any

# VIP Contacts Database
VIP_CONTACTS = {
    "+15553921829": {"name": "Aman Sharma", "relation": "Close Friend", "priority": "CRITICAL"},
    "david.miller@techcorp.io": {"name": "David Miller", "relation": "Lead Executive", "priority": "HIGH"},
    "+15559988776": {"name": "Mom", "relation": "Family", "priority": "EMERGENCY_VIP"},
}

# Milestones & Birthdays Database
MILESTONES = [
    {"name": "Aman Sharma", "date": "09-18", "type": "Birthday", "platform": "WhatsApp", "draft": "Happy Birthday brother! Hope you have an incredible year ahead. Let's celebrate soon!"},
    {"name": "TechCorp Partnership", "date": "09-20", "type": "Anniversary", "platform": "Email", "draft": "Wishing the team a fantastic partnership anniversary. Looking forward to our upcoming milestones!"},
]

def check_vip_status(sender_identifier: str) -> Dict[str, Any]:
    """Check if sender is a VIP and return prioritization."""
    clean_id = sender_identifier.strip().lower()
    for contact_key, data in VIP_CONTACTS.items():
        if contact_key.lower() in clean_id or data["name"].lower() in clean_id:
            return {"is_vip": True, **data}
    return {"is_vip": False, "priority": "STANDARD"}

def get_upcoming_milestones(days_ahead: int = 2) -> List[Dict[str, Any]]:
    """Check for birthdays and milestones within the next X days."""
    today = datetime.date.today()
    upcoming = []
    
    for m in MILESTONES:
        m_month, m_day = map(int, m["date"].split("-"))
        m_date = datetime.date(today.year, m_month, m_day)
        diff = (m_date - today).days
        if 0 <= diff <= days_ahead:
            upcoming.append({
                **m,
                "days_until": diff,
                "urgency": "TODAY" if diff == 0 else f"IN_{diff}_DAYS"
            })
    return upcoming
