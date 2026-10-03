import unittest
from unittest.mock import patch, MagicMock
from mail_delivery import send_bon, cipher


class MailTransportTest(unittest.TestCase):
    def test_starttls_credentials_and_standalone_attachment(self):
        config = {"host":"smtp.example.org","port":587,"security":"starttls","sender":"apos@example.org","username":"user","password":cipher("secret").encrypt(b"password").decode()}
        smtp = MagicMock()
        smtp.send_message.return_value = {}
        with patch("mail_delivery.smtplib.SMTP") as factory:
            factory.return_value.__enter__.return_value = smtp
            send_bon(config,"secret","guest@example.org","Your bon","Tea €2.50","<html>Tea €2.50</html>")
        smtp.starttls.assert_called_once()
        smtp.login.assert_called_once_with("user","password")
        message = smtp.send_message.call_args.args[0]
        self.assertEqual(message["To"],"guest@example.org")
        attachment = next(message.iter_attachments())
        self.assertEqual(attachment.get_filename(),"bon.html")
        self.assertIn("Tea",attachment.get_payload(decode=True).decode())
