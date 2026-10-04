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

    def test_photo_is_related_in_email_and_embedded_in_saved_attachment(self):
        import base64
        photo = b"normalized-jpeg-test-bytes"
        uri = "data:image/jpeg;base64," + base64.b64encode(photo).decode()
        config = {"host":"smtp.example.org","port":1025,"security":"none","sender":"apos@example.org","username":""}
        smtp = MagicMock()
        smtp.send_message.return_value = {}
        with patch("mail_delivery.smtplib.SMTP") as factory:
            factory.return_value.__enter__.return_value = smtp
            send_bon(config,"secret","guest@example.org","Bon","Tea",'<img src="'+uri+'">',photo=photo)
        message = smtp.send_message.call_args.args[0]
        image = next(part for part in message.walk() if part.get_content_type()=="image/jpeg")
        self.assertEqual(image.get_payload(decode=True),photo)
        self.assertEqual(image['Content-ID'],'<profile-photo@apos>')
        body = next(part for part in message.walk() if part.get_content_type()=="text/html" and part.get_filename() is None)
        self.assertIn('cid:profile-photo@apos',body.get_content())
        attachment = next(part for part in message.walk() if part.get_filename()=="bon.html")
        self.assertIn(uri,attachment.get_payload(decode=True).decode())
