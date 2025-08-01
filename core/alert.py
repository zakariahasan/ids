import smtplib, time
from email.message import EmailMessage
from . import config

class EmailAlert:
    _last_sent = {}

    @classmethod
    def send(cls, alert_type: str, subject: str, body: str):
        now = time.time()
        last = cls._last_sent.get(alert_type, 0)
        if now - last < config.ALERT_THROTTLE_SEC:
            print(f"[THROTTLED] {alert_type} alert suppressed.")
            return

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = config.SMTP_USERNAME
        msg["To"] = config.ALERT_RECIPIENT
        msg.set_content(body)

        try:
            with smtplib.SMTP(config.SMTP_SERVER, 587) as smtp:
                smtp.ehlo()
                smtp.starttls()     # ✅ Required by Gmail
                smtp.ehlo()         # ✅ Re-issue EHLO after TLS

                smtp.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
                smtp.send_message(msg)
                print(f"[EMAIL] Sent alert for {alert_type}")
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send alert: {e}")

        cls._last_sent[alert_type] = now
