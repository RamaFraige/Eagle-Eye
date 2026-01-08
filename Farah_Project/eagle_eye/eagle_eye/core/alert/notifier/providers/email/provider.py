import logging
import smtplib
import ssl
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from eagle_eye.config.settings import settings
from eagle_eye.core.alert.event import AlertEvent
from eagle_eye.core.alert.snapshot import AlertSnapshot

from ...base import NotificationProvider

logger = logging.getLogger(__name__)


class EmailNotificationProvider(NotificationProvider):
    def __init__(
        self,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 465,
        username: str = None,
        password: str = None,
        from_email: str = None,
        to_emails: list[str] = None,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username or settings.GMAIL_USER
        self.password = password or settings.GMAIL_PASSWORD
        self.from_email = from_email or self.username
        self.to_emails = to_emails or settings.TO_EMAILS

        # Setup Jinja2 environment
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

    def send(self, event: AlertEvent, snapshot: AlertSnapshot) -> None:
        if not self.username or not self.password:
            logger.error("Email credentials not configured.")
            return

        if not self.to_emails:
            logger.error("No recipient emails configured.")
            return

        # Use thumbnail from AlertSnapshot
        snapshot_bytes = snapshot.thumbnail_bytes

        # Prepare timestamp
        event_dt = datetime.fromtimestamp(event.timestamp)

        # Decide video filename
        video_filename = f"alert_{event.timestamp}.mp4"
        video_cid = video_filename  # use filename as CID for referencing

        # Render HTML body
        template = self.env.get_template("alert.html")
        html_content = template.render(
            event=event,
            event_dt=event_dt,
            now=datetime.now(),
            has_snapshot=bool(snapshot_bytes),
            video_cid=video_cid,
            filename=video_filename,  # for hyperlink in template
        )

        # Create root message
        msg = MIMEMultipart("mixed")
        msg["Subject"] = f"Security Alert: {event.name.title()}"
        msg["From"] = self.from_email
        msg["To"] = ", ".join(self.to_emails)

        # Create `related` section for HTML + inline images
        msg_related = MIMEMultipart("related")
        msg.attach(msg_related)

        msg_alternative = MIMEMultipart("alternative")
        msg_related.attach(msg_alternative)

        msg_alternative.attach(MIMEText(html_content, "html"))

        # Inline snapshot image
        if snapshot_bytes:
            img = MIMEImage(snapshot_bytes)
            img.add_header("Content-ID", "<snapshot>")
            img.add_header("Content-Disposition", "inline", filename="snapshot.jpg")
            msg_related.attach(img)

        # Attach video as regular attachment with a Content-ID
        part = MIMEBase("application", "octet-stream")
        part.set_payload(snapshot.video_bytes)
        encoders.encode_base64(part)

        # Add attachment headers
        part.add_header(
            "Content-Disposition", f'attachment; filename="{video_filename}"'
        )
        part.add_header("Content-ID", f"<{video_cid}>")
        msg.attach(part)

        # Send the email
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(
                self.smtp_server, self.smtp_port, context=context
            ) as server:
                server.login(self.username, self.password)
                server.send_message(msg)
            logger.info(f"Email sent to {self.to_emails}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
