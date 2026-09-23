import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger("EmailEngine")

class EmailEngine:
    def __init__(self):
        self.imap_server = os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")
        self.smtp_server = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
        self.email_address = os.getenv("EMAIL_ADDRESS", "")
        self.email_password = os.getenv("EMAIL_PASSWORD", "")  # App Password for Gmail
        self.is_configured = bool(self.email_address and self.email_password)

    def fetch_unread_emails(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Connect to mailbox via IMAP and retrieve latest unread emails."""
        if not self.is_configured:
            logger.info("Email credentials not configured in environment. Using demo mailbox simulation.")
            return self._mock_unread_emails()

        emails_data = []
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_address, self.email_password)
            mail.select("inbox")

            status, messages = mail.search(None, "UNSEEN")
            if status != "OK" or not messages[0]:
                mail.logout()
                return []

            msg_ids = messages[0].split()[-limit:]
            for msg_id in reversed(msg_ids):
                # Use BODY.PEEK[] so reading emails does NOT mark them as read in user's Gmail
                status, msg_data = mail.fetch(msg_id, "(BODY.PEEK[])")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Decode Subject
                        subject, encoding = decode_header(msg.get("Subject", "No Subject"))[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")
                        
                        # Sender
                        from_ = msg.get("From", "Unknown Sender")
                        
                        # Extract Body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                if content_type == "text/plain" and "attachment" not in content_disposition:
                                    payload = part.get_payload(decode=True)
                                    if payload:
                                        body = payload.decode(errors="ignore")
                                        break
                        else:
                            payload = msg.get_payload(decode=True)
                            if payload:
                                body = payload.decode(errors="ignore")

                        emails_data.append({
                            "id": msg_id.decode(),
                            "sender": from_,
                            "subject": subject,
                            "body": body.strip(),
                            "platform": "Email"
                        })
            mail.logout()
        except Exception as e:
            logger.error(f"Failed to fetch emails via IMAP: {e}")
            return self._mock_unread_emails()

        return emails_data

    def categorize_email(self, sender: str, subject: str, body: str) -> str:
        """Categorize incoming email into intuitive groups."""
        text = f"{sender} {subject} {body}".lower()
        if any(w in text for w in ["assignment", "professor", "university", "college", "exam", "internshala", "course", "lecture"]):
            return "🎓 Education & Internships"
        elif any(w in text for w in ["job", "recruiter", "interview", "application", "glassdoor", "hiring", "vacancy", "career"]):
            return "💼 Jobs & Careers"
        elif any(w in text for w in ["invitation", "network", "connect", "linkedin"]):
            return "🤝 Professional Network"
        elif any(w in text for w in ["invoice", "receipt", "payment", "bank", "otp", "statement", "debit", "credit"]):
            return "💳 Finance & Billing"
        elif any(w in text for w in ["security alert", "delivery status", "failure", "alert", "password", "verification"]):
            return "🔔 System & Security Alerts"
        else:
            return "📢 General / Updates"

    def fetch_and_summarize_emails(self, limit: int = 5) -> Dict[str, Any]:
        """Fetch latest unread emails and return an organized briefing."""
        raw_emails = self.fetch_unread_emails(limit=limit)
        if not raw_emails:
            return {
                "count": 0,
                "summary": "Your inbox is completely clear, Sir. No unread emails found.",
                "emails": []
            }

        categorized_emails = []
        for em in raw_emails:
            category = self.categorize_email(em["sender"], em["subject"], em.get("body", ""))
            clean_body = re.sub(r'\s+', ' ', em.get("body", "")).strip()[:140]
            categorized_emails.append({
                "id": em["id"],
                "sender": em["sender"],
                "subject": em["subject"],
                "category": category,
                "preview": clean_body
            })

        return {
            "count": len(categorized_emails),
            "summary": f"Found {len(categorized_emails)} unread emails in your Gmail inbox.",
            "emails": categorized_emails
        }

    def send_reply(self, to_email: str, subject: str, reply_text: str) -> bool:
        """Send email reply via SMTP with automated safeguards."""
        if not self.is_configured:
            logger.info(f"[SIMULATED EMAIL SENT] To: {to_email} | Subject: Re: {subject} | Content: {reply_text}")
            return True

        # Safety Guard: Never auto-reply to robotic/no-reply/system addresses
        low_target = to_email.lower()
        if any(bot in low_target for bot in ["no-reply", "noreply", "donotreply", "mailer-daemon", "newsletters", "invitations", "student@mail"]):
            logger.info(f"Auto-reply blocked for automated address: {to_email}")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_address
            msg["To"] = to_email
            msg["Subject"] = f"Re: {subject}" if not subject.startswith("Re:") else subject
            msg.attach(MIMEText(reply_text, "plain"))

            server = smtplib.SMTP_SSL(self.smtp_server, 465)
            server.login(self.email_address, self.email_password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _mock_unread_emails(self) -> List[Dict[str, Any]]:
        """Realistic simulated emails for demonstration if user hasn't set credentials yet."""
        return [
            {
                "id": "mock_email_01",
                "sender": "David Miller <david.miller@techcorp.io>",
                "subject": "Quick confirmation: Thursday strategy sync",
                "body": "Hi Jashan, just wanted to check if our 3 PM call on Thursday is still good for you? Let me know, thanks!",
                "platform": "Email"
            },
            {
                "id": "mock_email_02",
                "sender": "Apex Financial Group <billing@apexfinancial.com>",
                "subject": "URGENT: Invoice #9482 Payment Authorization Required",
                "body": "Dear Mr. Singh, please review the attached invoice for $4,500 due on September 22nd. Please authorize bank wire transfer.",
                "platform": "Email"
            }
        ]
