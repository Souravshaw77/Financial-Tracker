def send_alert_email(recipient, subject, body):
    msg = Message(subject=subject, recipients=[recipient], body=body)
    mail.send(msg)
