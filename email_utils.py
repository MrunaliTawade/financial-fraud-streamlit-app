import smtplib
from email.mime.text import MIMEText

def send_email_alert(txn_id, amount):

    sender_email = "mrunalitawade11@gmail.com"
    app_password = "vrdu yspg irrj jxlq"

    receiver_email = "mrunalitawade11@gmail.com"  
    subject = "🚨 Fraud Transaction Alert"
    body = f"""
    Fraud detected!

    Transaction ID: {txn_id}
    Amount: {amount}

    Please take action immediately.
    """

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()

        print("✅ Email sent successfully")

    except Exception as e:
        print("❌ Email failed:", e)