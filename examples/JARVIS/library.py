import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_email_gmail(email_address, message, source_address):
    # Create a message object
    msg = MIMEMultipart()
    msg['From'] = source_address
    msg['To'] = email_address
    msg['Subject'] = "Your Subject Here"  # Replace with your email subject
    password = os.getenv("GMAIL_PASSWORD")
    # Attach the message to the email
    msg.attach(MIMEText(message, 'plain'))

    # Establish a connection with Gmail's SMTP server
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()  # Use TLS encryption

    # Log in to your Gmail account
    server.login(source_address, password)

    # Send the email
    server.sendmail(source_address, email_address, msg.as_string())

    # Close the connection
    server.quit()


