import json
from typing import List, Dict, Any

# 1. OS & Hardware Tools
from backend.tools.os_control import (
    open_application,
    close_application,
    set_system_volume,
    get_system_volume,
    get_system_diagnostics,
    lock_screen,
    media_play_pause,
    media_next,
    media_previous
)
from backend.tools.system_tasks import (
    execute_shell_command,
    capture_screen_snapshot
)
from backend.tools.web_search import search_web

# 2. Comms & Telephony Suite
from backend.comms.hub import CommunicationsHub
from backend.comms.vip_and_birthdays import check_vip_status, get_upcoming_milestones
from backend.comms.unsubscriber import EmailUnsubscriber

# 3. Intelligence & Memory Suite
from backend.intelligence.researcher import GhostResearcher
from backend.intelligence.copilot import MeetingCopilot
from backend.intelligence.memory import EpisodicMemory

# 4. System & Dev Ops
from backend.system_ops.butler import DesktopButler
from backend.system_ops.environments import EnvironmentModes
from backend.system_ops.dev_and_social import DeveloperCopilot, SocialContentEngine

# 5. Security & Voice Suite
from backend.security.biometrics import VoiceprintBiometrics
from backend.voice.persona_adaptive import AdaptivePersonaEngine

# 6. Self-Evolution & Remote Phone Bridge Suite
from backend.intelligence.learning_engine import learning_engine
from backend.comms.telegram_bridge import telegram_bridge

comms_hub = CommunicationsHub()
copilot = MeetingCopilot()
memory = EpisodicMemory()

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "scan_inboxes_and_comms",
            "description": "Scan incoming Email, WhatsApp, and Instagram messages, auto-replying to routine inquiries and holding sensitive ones for review.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_user_emails",
            "description": "Fetch, inspect, and summarize the user's latest unread Gmail emails with smart category breakdown (Education & Internships, Jobs & Careers, Professional Network, Finance, System Alerts).",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of unread emails to retrieve (default: 5)."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_phone_call_briefing",
            "description": "Make an outbound phone call to the user to deliver a voice briefing on handled messages and pending approvals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {"type": "string", "description": "Optional phone number."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "conduct_ghost_research",
            "description": "Conduct deep overnight research on any topic and leave an executive brief on the user's desktop.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "The topic to research."}
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sweep_desktop_and_downloads",
            "description": "Organize Downloads and Desktop files into structured contextual folders (Invoices, Media, Code, Documents).",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "activate_environment_mode",
            "description": "Activate system-wide macro mode: 'FOCUS' (mutes notifications/music, focuses display) or 'GOODNIGHT' (locks system, quiet auto-responder).",
            "parameters": {
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "enum": ["FOCUS", "GOODNIGHT"], "description": "The macro mode."}
                },
                "required": ["mode"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall_episodic_memory",
            "description": "Query Stacky's persistent memory archive for past discussions, notes, recommendations, or accountant advice.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to recall."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "meeting_copilot_control",
            "description": "Start meeting listener, fetch live teleprompter answers, or stop and compile minutes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["start", "get_answers", "stop"], "description": "Copilot action."}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fix_developer_port",
            "description": "Free up a blocked or locked development port (e.g. 3000, 8000, 5432).",
            "parameters": {
                "type": "object",
                "properties": {
                    "port": {"type": "integer", "description": "Port number to free."}
                },
                "required": ["port"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "draft_social_posts",
            "description": "Draft high-performing social media posts for Twitter/X and LinkedIn in user's tone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "The industry topic or milestone."}
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "verify_voiceprint",
            "description": "Verify the speaker's vocal biometric authorization before executing sensitive commands.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_upcoming_birthdays",
            "description": "Check upcoming birthdays and milestones for family, friends, and VIP contacts.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Open or bring to focus any installed application on the Mac.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "The name of the application."}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_system_volume",
            "description": "Set the Mac sound output volume percentage (0 to 100).",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "integer", "description": "Volume percentage."}
                },
                "required": ["level"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_diagnostics",
            "description": "Get real-time CPU, RAM, Disk, and Battery diagnostics.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lock_screen",
            "description": "Locks the Mac workstation screen immediately.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for real-time information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_remote_file_to_phone",
            "description": "Search user's Mac for a file (assignment, presentation, code) and dispatch it directly to their phone via Telegram while away at college.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Name or topic of file to find."}
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_remote_screenshot_to_phone",
            "description": "Capture live Mac desktop screenshot and send photo to user's phone via Telegram.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_learned_preference",
            "description": "Record an evolved habit, preference, or college fact to adapt Stacky over time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "insight": {"type": "string", "description": "The insight or preference."}
                },
                "required": ["insight"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_file_to_telegram",
            "description": "Save and upload the current or most recently edited/saved file from the Mac directly to the user's Telegram chat.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Optional specific file name or keyword to send."}
                }
            }
        }
    }
]

async def dispatch_tool_call(tool_name: str, args: Dict[str, Any]) -> Any:
    """Master tool dispatcher."""
    if tool_name == "scan_inboxes_and_comms":
        return await comms_hub.scan_and_process_all_inboxes()
    elif tool_name == "check_user_emails":
        limit = args.get("limit", 5)
        return comms_hub.email_engine.fetch_and_summarize_emails(limit=limit)
    elif tool_name == "trigger_phone_call_briefing":
        return await comms_hub.execute_phone_briefing(args.get("phone_number"))
    elif tool_name == "conduct_ghost_research":
        return await GhostResearcher.conduct_deep_research(args.get("topic", "Latest AI Innovations"))
    elif tool_name == "sweep_desktop_and_downloads":
        return DesktopButler.sweep_and_organize_directory()
    elif tool_name == "activate_environment_mode":
        mode = args.get("mode", "FOCUS")
        return EnvironmentModes.activate_focus_mode() if mode == "FOCUS" else EnvironmentModes.activate_goodnight_mode()
    elif tool_name == "recall_episodic_memory":
        return memory.search_memory(args.get("query", ""))
    elif tool_name == "meeting_copilot_control":
        action = args.get("action", "get_answers")
        if action == "start":
            return copilot.start_meeting()
        elif action == "get_answers":
            return copilot.get_live_cheat_sheet()
        else:
            return copilot.stop_meeting_and_generate_minutes()
    elif tool_name == "fix_developer_port":
        return DeveloperCopilot.fix_port_conflict(int(args.get("port", 3000)))
    elif tool_name == "draft_social_posts":
        return SocialContentEngine.draft_trend_posts(args.get("topic", "AI"))
    elif tool_name == "verify_voiceprint":
        return VoiceprintBiometrics.verify_voice_signature()
    elif tool_name == "check_upcoming_birthdays":
        return get_upcoming_milestones()
    elif tool_name == "open_application":
        return open_application(args.get("app_name", ""))
    elif tool_name == "set_system_volume":
        return set_system_volume(int(args.get("level", 50)))
    elif tool_name == "get_system_diagnostics":
        return get_system_diagnostics()
    elif tool_name == "lock_screen":
        return lock_screen()
    elif tool_name == "search_web":
        return await search_web(args.get("query", ""))
    elif tool_name == "fetch_remote_file_to_phone":
        return telegram_bridge.handle_remote_command(f"send me {args.get('filename', '')}")
    elif tool_name == "send_remote_screenshot_to_phone":
        return telegram_bridge.send_screenshot_to_phone()
    elif tool_name == "record_learned_preference":
        return learning_engine.analyze_and_learn(args.get("insight", ""))
    elif tool_name == "save_file_to_telegram":
        return telegram_bridge.save_current_or_latest_file_to_telegram(args.get("filename"))
    else:
        return f"Unknown tool: {tool_name}"
