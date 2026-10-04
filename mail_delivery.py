"""Configurable SMTP delivery; saved credentials are encrypted locally."""
import base64
import hashlib
import re
import smtplib
import ssl
from email.message import EmailMessage
from cryptography.fernet import Fernet


def cipher(secret):
    key = secret.encode() if isinstance(secret, str) else secret
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(key).digest()))


def email_address(value):
    value = value.strip()
    if len(value) > 254 or not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,63}", value):
        raise ValueError("Enter a valid email address.")
    return value


def configure_mail(form, previous, secret):
    enabled = form.get("enabled") == "1"
    host = form.get("host", "").strip()
    sender = form.get("sender", "").strip()
    username = form.get("username", "").strip()
    security = form.get("security", "starttls")
    try:
        port = int(form.get("port", "587"))
    except ValueError:
        raise ValueError("SMTP port must be between 1 and 65535.") from None
    if not 1 <= port <= 65535:
        raise ValueError("SMTP port must be between 1 and 65535.")
    if security not in ("starttls", "ssl", "none"):
        raise ValueError("Choose a valid SMTP security mode.")
    if host and (len(host) > 253 or not re.fullmatch(r"[A-Za-z0-9.-]+", host)):
        raise ValueError("Enter a valid SMTP hostname.")
    if sender:
        sender = email_address(sender)
    if len(username) > 254 or any(c in username for c in "\r\n"):
        raise ValueError("Enter a valid SMTP username.")
    password = previous.get("password", "")
    if username != previous.get("username", "") or host != previous.get("host", "") or form.get("clear_password") == "1":
        password = ""
    supplied = form.get("password", "")
    if supplied:
        if len(supplied) > 1024:
            raise ValueError("SMTP password is too long.")
        password = cipher(secret).encrypt(supplied.encode()).decode()
    if enabled and (not host or not sender or (username and not password)):
        raise ValueError("Complete the outbound account before enabling mail.")
    return {"enabled":enabled,"host":host,"port":port,"sender":sender,"username":username,"security":security,"password":password}


def ready(config):
    return bool(config.get("enabled") and config.get("host") and config.get("sender") and config.get("port") and (not config.get("username") or config.get("password")))


def send_bon(config, secret, recipient, subject, text, html, photo=None):
    message = EmailMessage()
    message["From"] = config["sender"]
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(text)
    email_html = html
    if photo:
        image_uri = "data:image/jpeg;base64," + base64.b64encode(photo).decode("ascii")
        email_html = html.replace(image_uri, "cid:profile-photo@apos")
    message.add_alternative(email_html, subtype="html")
    if photo:
        message.get_payload()[-1].add_related(photo, maintype="image", subtype="jpeg", cid="<profile-photo@apos>", disposition="inline")
    message.add_attachment(html.encode("utf-8"), maintype="text", subtype="html", filename="bon.html")
    context = ssl.create_default_context()
    factory = smtplib.SMTP_SSL if config["security"] == "ssl" else smtplib.SMTP
    kwargs = {"timeout":10}
    if config["security"] == "ssl":
        kwargs["context"] = context
    with factory(config["host"],config["port"],**kwargs) as smtp:
        if config["security"] == "starttls":
            smtp.starttls(context=context)
        if config["username"]:
            smtp.login(config["username"],cipher(secret).decrypt(config["password"].encode()).decode())
        refused = smtp.send_message(message)
        if refused:
            raise smtplib.SMTPRecipientsRefused(refused)
