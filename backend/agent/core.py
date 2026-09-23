import os
import json
import re
import logging
from typing import List, Dict, Any
from openai import AsyncOpenAI
from backend.config import GROQ_API_KEY, OPENROUTER_API_KEY, OPENAI_API_KEY, DEFAULT_MODEL
from backend.agent.personality import SYSTEM_PROMPT
from backend.agent.router import select_optimal_model, get_fallback_model
from backend.tools.registry import TOOL_DEFINITIONS, dispatch_tool_call

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StackyAgent")

class StackyAgent:
    def __init__(self):
        self.dynamic_routing = os.getenv("STACKY_DYNAMIC_ROUTING", "true").lower() == "true"
        if GROQ_API_KEY:
            self.client = AsyncOpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=GROQ_API_KEY
            )
            self.model = DEFAULT_MODEL or "openai/gpt-oss-120b"
            routing_mode = "DYNAMIC MULTI-MODEL CASCADE" if self.dynamic_routing else f"STATIC [{self.model}]"
            logger.info(f"Stacky Brain armed with Groq Ultra-Fast Inference ({routing_mode})")
        elif OPENROUTER_API_KEY:
            self.client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=OPENROUTER_API_KEY
            )
            self.model = DEFAULT_MODEL
        elif OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            self.model = "gpt-4o"
        else:
            self.client = None
            self.model = "offline"

        self.conversation_history: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    async def _offline_intent_resolver(self, user_input: str) -> Dict[str, Any]:
        """Universal local intent resolver covering all roadmap systems."""
        inp = user_input.lower()
        tools_executed = []

        # 1. Episodic Memory Recall
        if any(w in inp for w in ["recall", "remember", "memory", "recommend", "accountant"]):
            res = await dispatch_tool_call("recall_episodic_memory", {"query": user_input})
            tools_executed.append({"name": "recall_episodic_memory", "args": {"query": user_input}, "result": res})
            content = res[0].get("content", "No record found.")
            return {"reply": f"Retrieved from episodic memory archives, Sir: {content}", "tools_used": tools_executed}

        # 2. Email & Comms Inspection
        if any(w in inp for w in ["check email", "check my email", "unread email", "gmail", "my emails", "emails", "mail"]):
            res = await dispatch_tool_call("check_user_emails", {"limit": 5})
            tools_executed.append({"name": "check_user_emails", "args": {"limit": 5}, "result": res})
            emails = res.get("emails", [])
            if not emails:
                return {"reply": "Your inbox is completely clear, Sir. No unread emails found.", "tools_used": tools_executed}
            
            lines = [f"Found {len(emails)} unread emails in your inbox, Sir:\n"]
            for idx, em in enumerate(emails, 1):
                lines.append(f"{idx}. [{em['category']}] **{em['sender']}**: *{em['subject']}*")
            return {"reply": "\n".join(lines), "tools_used": tools_executed}

        if any(w in inp for w in ["scan", "inbox", "whatsapp", "instagram"]):
            res = await dispatch_tool_call("scan_inboxes_and_comms", {})
            tools_executed.append({"name": "scan_inboxes_and_comms", "args": {}, "result": res})
            reply = f"Communications channels scanned, Sir. Handled {len(res.get('auto_replied', []))} routine items, and flagged {len(res.get('held_for_review', []))} for your personal authorization."
            return {"reply": reply, "tools_used": tools_executed}

        if any(w in inp for w in ["phone briefing", "voice briefing", "dial phone"]):
            res = await dispatch_tool_call("trigger_phone_call_briefing", {})
            tools_executed.append({"name": "trigger_phone_call_briefing", "args": {}, "result": res})
            return {"reply": "Outbound voice briefing dispatched to your mobile phone, Sir. Telephony channel connected.", "tools_used": tools_executed}

        # 2. Ghost Research
        if any(w in inp for w in ["research", "investigate", "brief", "study"]):
            topic = user_input.replace("research", "").replace("Stacky", "").replace("please", "").strip() or "AI Systems"
            res = await dispatch_tool_call("conduct_ghost_research", {"topic": topic})
            tools_executed.append({"name": "conduct_ghost_research", "args": {"topic": topic}, "result": res})
            return {"reply": f"Executive intelligence brief compiled for '{topic}', Sir. File placed on your desktop at: {res.get('report_path')}", "tools_used": tools_executed}

        # 3. Desktop Butler & File Organization
        if any(w in inp for w in ["clean", "organize", "sweep", "downloads", "desktop"]):
            res = await dispatch_tool_call("sweep_desktop_and_downloads", {})
            tools_executed.append({"name": "sweep_desktop_and_downloads", "args": {}, "result": res})
            return {"reply": f"Desktop and Downloads folders swept and organized, Sir. Classified {res.get('files_organized_count', 0)} files into structured directories.", "tools_used": tools_executed}

        # 4. Environment Macros
        if "focus" in inp:
            res = await dispatch_tool_call("activate_environment_mode", {"mode": "FOCUS"})
            tools_executed.append({"name": "activate_environment_mode", "args": {"mode": "FOCUS"}, "result": res})
            return {"reply": "Focus mode engaged, Sir. Audio muted, notifications locked, Do Not Disturb gatekeeper armed.", "tools_used": tools_executed}

        if "goodnight" in inp or "sleep" in inp:
            res = await dispatch_tool_call("activate_environment_mode", {"mode": "GOODNIGHT"})
            tools_executed.append({"name": "activate_environment_mode", "args": {"mode": "GOODNIGHT"}, "result": res})
            return {"reply": "Goodnight protocol activated, Sir. Workstation locked and overnight auto-responders armed.", "tools_used": tools_executed}

        # 5. Episodic Memory Recall
        if any(w in inp for w in ["recall", "remember", "memory", "recommend", "accountant"]):
            res = await dispatch_tool_call("recall_episodic_memory", {"query": user_input})
            tools_executed.append({"name": "recall_episodic_memory", "args": {"query": user_input}, "result": res})
            content = res[0].get("content", "No record found.")
            return {"reply": f"Retrieved from episodic memory archives, Sir: {content}", "tools_used": tools_executed}

        # 6. Meeting Co-Pilot
        if "meeting" in inp:
            res = await dispatch_tool_call("meeting_copilot_control", {"action": "get_answers"})
            tools_executed.append({"name": "meeting_copilot_control", "args": {"action": "get_answers"}, "result": res})
            q1 = res[0]["detected_question"]
            a1 = res[0]["suggested_answer"]
            return {"reply": f"Meeting Co-Pilot Teleprompter: Detected query '{q1}'. Suggested answer: {a1}", "tools_used": tools_executed}

        # 7. Dev Ops Port Fix
        if "port" in inp:
            res = await dispatch_tool_call("fix_developer_port", {"port": 3000})
            tools_executed.append({"name": "fix_developer_port", "args": {"port": 3000}, "result": res})
            return {"reply": res.get("message", "Port checked, Sir."), "tools_used": tools_executed}

        # 8. Social Posts
        if any(w in inp for w in ["post", "tweet", "social", "linkedin", "x"]):
            res = await dispatch_tool_call("draft_social_posts", {"topic": "Autonomous AI Systems"})
            tools_executed.append({"name": "draft_social_posts", "args": {"topic": "AI"}, "result": res})
            return {"reply": f"Drafted X and LinkedIn posts in your signature tone, Sir. Ready in your HUD console.", "tools_used": tools_executed}

        # 9. Voiceprint Biometrics
        if "voice" in inp and "verify" in inp:
            res = await dispatch_tool_call("verify_voiceprint", {})
            tools_executed.append({"name": "verify_voiceprint", "args": {}, "result": res})
            return {"reply": f"Vocal biometric acoustic signature matched at {res['confidence']*100}%. Authorization granted, Sir.", "tools_used": tools_executed}

        # 10. Birthdays
        if "birthday" in inp or "milestone" in inp:
            res = await dispatch_tool_call("check_upcoming_birthdays", {})
            tools_executed.append({"name": "check_upcoming_birthdays", "args": {}, "result": res})
            if res:
                b = res[0]
                return {"reply": f"Milestone alert: {b['name']}'s {b['type']} is approaching ({b['urgency']}). I have prepared a drafted message.", "tools_used": tools_executed}
            return {"reply": "No milestones in the next 48 hours, Sir.", "tools_used": tools_executed}

        # 11. On-Demand Voice / Chat Command: "Stacky, please save this file to the Telegram"
        if any(phrase in inp for phrase in [
            "save this file to telegram",
            "save this file to the telegram",
            "save to telegram",
            "send this file to telegram",
            "send this file to the telegram",
            "upload this file to telegram",
            "save file to telegram",
            "send file to telegram",
            "sync to telegram",
            "sync to phone",
            "save to phone"
        ]):
            from backend.comms.telegram_bridge import telegram_bridge
            target_hint = None
            clean_cmd = inp
            for phrase in ["stacky", "please", "save", "this", "file", "to", "the", "telegram", "send", "upload", "sync", "phone"]:
                clean_cmd = re.sub(rf"\b{phrase}\b", "", clean_cmd, flags=re.IGNORECASE)
            clean_cmd = clean_cmd.strip()
            if clean_cmd and len(clean_cmd) > 2:
                target_hint = clean_cmd

            res = telegram_bridge.save_current_or_latest_file_to_telegram(target_hint)
            return {"reply": res, "tools_used": [{"name": "save_to_telegram", "result": res}]}

        # 12. Hardware Diagnostics
        if re.search(r"\b(battery|cpu|ram|telemetry|diagnostics)\b", inp):
            diag = await dispatch_tool_call("get_system_diagnostics", {})
            tools_executed.append({"name": "get_system_diagnostics", "args": {}, "result": diag})
            cpu = diag.get("cpu_usage_percent", 0)
            batt = diag.get("battery", {}).get("percentage", "N/A")
            return {"reply": f"Diagnostics nominal, Sir. CPU load is at {cpu}%, battery currently at {batt}%.", "tools_used": tools_executed}

        # 13. Volume & Locking
        if "volume" in inp:
            level = 50
            for w in inp.split():
                if w.isdigit():
                    level = int(w)
                    break
            res = await dispatch_tool_call("set_system_volume", {"level": level})
            tools_executed.append({"name": "set_system_volume", "args": {"level": level}, "result": res})
            return {"reply": res, "tools_used": tools_executed}

        if "lock" in inp:
            res = await dispatch_tool_call("lock_screen", {})
            tools_executed.append({"name": "lock_screen", "args": {}, "result": res})
            return {"reply": res, "tools_used": tools_executed}

        # 14. Remote File Dispatch to Phone (While at College)
        if any(w in inp for w in ["send me", "send file", "fetch file", "to my phone", "send the file"]):
            res = await dispatch_tool_call("fetch_remote_file_to_phone", {"filename": user_input})
            return {"reply": res, "tools_used": [{"name": "fetch_remote_file_to_phone", "result": res}]}

        # 15. Remote Mac Screenshot to Phone
        if "screenshot" in inp and any(w in inp for w in ["phone", "send", "telegram"]):
            res = await dispatch_tool_call("send_remote_screenshot_to_phone", {})
            return {"reply": "Captured live Mac desktop screen and dispatched directly to your phone, Sir.", "tools_used": [{"name": "send_remote_screenshot_to_phone", "result": res}]}

        return {
            "reply": "All 27 Jarvis subsystems are armed and operational, Sir. Awaiting your command.",
            "tools_used": []
        }

    async def chat(self, user_input: str) -> Dict[str, Any]:
        """Process user text or voice command, invoke tools, and return Jarvis reply."""
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Continuously adapt and learn from user statement
        from backend.intelligence.learning_engine import learning_engine
        try:
            learning_engine.analyze_and_learn(user_input)
        except Exception:
            pass

        if not self.client:
            offline_res = await self._offline_intent_resolver(user_input)
            self.conversation_history.append({"role": "assistant", "content": offline_res["reply"]})
            return offline_res

        # Dynamic Model Routing: Select optimal brain based on prompt type
        active_model = self.model
        route_reason = "configured"
        if self.dynamic_routing:
            active_model, route_reason = select_optimal_model(user_input)
            logger.info(f"[Dynamic Model Routing]: Selected '{active_model}' ({route_reason})")

        tools_executed = []
        max_turns = 5
        turn = 0

        while turn < max_turns:
            turn += 1
            response = None
            try:
                response = await self.client.chat.completions.create(
                    model=active_model,
                    messages=self.conversation_history,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    timeout=8.0
                )
            except Exception as e:
                fallback = get_fallback_model(active_model)
                if fallback != active_model:
                    try:
                        logger.warning(f"Model '{active_model}' error ({e}). Cascading to fallback: '{fallback}'")
                        active_model = fallback
                        response = await self.client.chat.completions.create(
                            model=active_model,
                            messages=self.conversation_history,
                            tools=TOOL_DEFINITIONS,
                            tool_choice="auto",
                            timeout=8.0
                        )
                    except Exception as e2:
                        logger.warning(f"Fallback model failed: {e2}. Reverting to offline engine.")
                        offline_res = await self._offline_intent_resolver(user_input)
                        self.conversation_history.append({"role": "assistant", "content": offline_res["reply"]})
                        return offline_res
                else:
                    logger.warning(f"Cloud reasoning error: {e}. Reverting to offline engine.")
                    offline_res = await self._offline_intent_resolver(user_input)
                    self.conversation_history.append({"role": "assistant", "content": offline_res["reply"]})
                    return offline_res

            choice = response.choices[0]
            message = choice.message

            if not message.tool_calls:
                final_text = message.content or "Task completed, Sir."
                self.conversation_history.append({"role": "assistant", "content": final_text})
                return {"reply": final_text, "tools_used": tools_executed, "model_used": active_model}

            self.conversation_history.append(message.to_dict())

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = {}
                try:
                    func_args = json.loads(tool_call.function.arguments)
                except Exception:
                    pass
                
                logger.info(f"Executing tool: {func_name} with {func_args}")
                tool_result = await dispatch_tool_call(func_name, func_args)
                tools_executed.append({
                    "name": func_name,
                    "args": func_args,
                    "result": tool_result
                })

                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": json.dumps(tool_result, default=str)
                })

        return {"reply": "Processes executed, Sir.", "tools_used": tools_executed, "model_used": active_model}
