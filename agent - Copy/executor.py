from models.llm_router import LLMRouter

class ExecutorAgent:
    def __init__(self):
        self.llm = LLMRouter()
        from memory.memory_manager import MemoryManager
        self.memory = MemoryManager()

    def execute(self, plan, user_query):
        self._current_query = user_query
        query_lower = user_query.lower()

        # ── STEP 1: Confirm send (highest priority) ──────────────
        CONFIRM_PHRASES = ["confirm send", "confirm email", 
                          "yes send", "send it", "send now", "ok send"]
        if any(p in query_lower for p in CONFIRM_PHRASES):
            return self._confirm_send()

        # ── STEP 2: Send email intent ─────────────────────────────
        import re
        has_email_address = bool(re.search(r'[\w.]+@[\w.]+\.\w+', user_query))
        SEND_WORDS = ["send email", "send mail", "email to", 
                      "mail to", "send to", "write to"]
        if has_email_address and any(w in query_lower for w in SEND_WORDS):
            return self._draft_email(user_query)

        # ── STEP 3: Calendar CREATE intent ───────────────────────
        CREATE_WORDS = ["create event", "add event", "book", 
                        "schedule a", "set up meeting", "arrange meeting",
                        "new meeting", "new event", "make appointment"]
        READ_WORDS = ["what", "show", "list", "check", "do i have",
                      "my schedule", "my events", "my meetings", "whats on"]
        is_create = any(w in query_lower for w in CREATE_WORDS)
        is_read = any(w in query_lower for w in READ_WORDS)
        
        if "calendar" in query_lower or "schedule" in query_lower or "meeting" in query_lower or "event" in query_lower:
            if is_create and not is_read:
                return self._create_calendar_event(user_query)
            else:
                return self._read_calendar(user_query)

        # ── STEP 4: Gmail READ intent ─────────────────────────────
        EMAIL_READ_WORDS = ["email", "mail", "inbox", "messages",
                           "unread", "newsletter", "received"]
        if any(w in query_lower for w in EMAIL_READ_WORDS):
            return self._read_emails(user_query)

        # ── STEP 5: Document Q&A ──────────────────────────────────
        if self._has_uploaded_document():
            return self._answer_from_document(user_query)

        # ── STEP 6: Web search intent ─────────────────────────────
        SEARCH_KEYWORDS = [
            "search", "google", "look up", "find out",
            "what is happening", "latest", "news about",
            "current", "today's news", "who is", "what is",
            "who won", "who will", "what happened",
            "2024", "2025", "2026",  # any recent year = search
            "recently", "right now", "this year",
            "ipl", "icc", "world cup", "cricket", "football",
            "election", "president", "prime minister",
            "price of", "stock", "weather"
        ]

        def should_search(query):
            ql = query.lower()
            if any(w in ql for w in ["email", "calendar", "schedule", "meeting", "send"]):
                return False
            if any(word in ql for word in SEARCH_KEYWORDS):
                return True
            import re
            has_year = bool(re.search(r'202[4-9]|203\d', query))
            has_q = ql.startswith(("who", "what", "when", "where", "which", "how"))
            return has_year or (has_q and len(query.split()) > 4)

        is_chat_only = plan and all(isinstance(s, dict) and s.get("tool") == "chat" for s in plan)
        has_question = query_lower.startswith(("who", "what", "when", "where", "which", "how"))
        looks_factual = has_question and len(user_query.split()) > 4

        if should_search(user_query) or (is_chat_only and looks_factual):
            return self._web_search(user_query)

        # ── STEP 7: General chat fallback ─────────────────────────
        return self._chat(user_query)

    # ── Private methods ───────────────────────────────────────────

    def _read_emails(self, query):
        from tools.gmail_reader_tool import get_latest_emails, get_today_emails
        emails = get_today_emails() if "today" in query.lower() else get_latest_emails(10)
        email_text = "\n".join([
            f"Email {i+1}: From: {e.get('from','?')} | Subject: {e.get('subject','?')} | {e.get('snippet','')[:200]}"
            for i, e in enumerate(emails)
        ])
        prompt = f"User asked: {query}\n\nEmails:\n{email_text}\n\nAnswer the user's question directly based on these emails."
        return self.llm.generate(prompt, task_type="general")

    def _read_calendar(self, query):
        from tools.calendar_tool import get_today_events, list_events
        events = get_today_events() if "today" in query.lower() else list_events()
        if not events:
            return "You have no upcoming events."
        event_text = "\n".join([
            f"Event {i+1}: {e.get('title','?')} | {e.get('start','?')} to {e.get('end','?')} | Location: {e.get('location','?')}"
            for i, e in enumerate(events)
        ])
        prompt = f"User asked: {query}\n\nCalendar events:\n{event_text}\n\nAnswer naturally. Convert timestamps to readable format like 'March 10th at 3:00 PM'."
        return self.llm.generate(prompt, task_type="general")

    def _create_calendar_event(self, query):
        from tools.calendar_tool import create_event
        return create_event(user_query=query)

    def _draft_email(self, query):
        import json, re
        extraction_prompt = f"""Extract email details from: "{query}"
Return ONLY valid JSON:
{{"to": "email@example.com", "subject": "subject", "body": "body"}}
No explanation, no markdown, just JSON."""
        response = self.llm.generate(extraction_prompt, task_type="general")
        clean = response.strip().replace("```json","").replace("```","").strip()
        start, end = clean.find("{"), clean.rfind("}") + 1
        try:
            details = json.loads(clean[start:end])
        except:
            email_match = re.search(r'[\w.]+@[\w.]+\.\w+', query)
            saying_match = re.search(r'saying (.+)$', query, re.IGNORECASE)
            details = {
                "to": email_match.group() if email_match else "unknown",
                "subject": "Message from AI Agent",
                "body": saying_match.group(1) if saying_match else query
            }
        if details.get("to") == "unknown":
            return "Please provide recipient email address."
        # Clear old draft and save new one
        self._clear_pending_draft()
        self.memory.add_fact(f"PENDING_DRAFT:{json.dumps(details)}")
        return f"📝 Email Draft Ready:\nTo: {details['to']}\nSubject: {details['subject']}\nBody: {details['body']}\n\nReply 'confirm send' to send."

    def _confirm_send(self):
        import json
        facts = self.memory.get_all_facts()
        pending = next((f for f in facts if "PENDING_DRAFT:" in str(f)), None)
        if not pending:
            return "No pending email draft found. Please draft an email first."
        draft_str = str(pending).split("PENDING_DRAFT:")[1]
        details = json.loads(draft_str)
        from tools.gmail_reader_tool import send_email
        result = send_email(details["to"], details["subject"], details["body"])
        self._clear_pending_draft()
        return result

    def _clear_pending_draft(self):
        try:
            facts = self.memory.get_all_facts()
            for fact in facts:
                if "PENDING_DRAFT:" in str(fact):
                    self.memory.semantic.delete_fact(str(fact))
        except:
            pass

    def _web_search(self, query):
        from tools.web_search_tool import search_and_answer
        return search_and_answer(query, self.llm)

    def _chat(self, query):
        context = self.memory.get_context(query)
        prompt = f"Context from memory:\n{context}\n\nUser: {query}\n\nAnswer helpfully and concisely."
        return self.llm.generate(prompt, task_type="general")

    def _answer_from_document(self, query):
        prompt = f"{self._current_query}\n\nAnswer based on the document content above."
        return self.llm.generate(prompt, task_type="general")

    def _has_uploaded_document(self):
        try:
            from api.routes import uploaded_document_text
            return bool(uploaded_document_text)
        except:
            return False
