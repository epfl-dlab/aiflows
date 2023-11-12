import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import litellm
import ast

def send_email_gmail(email_address, source_address, message, subject, attachment_path=None):
    """Send an email via Gmail's SMTP server with an optional attachment.

    Parameters
    ----------
    email_address : str
        The recipient's email address.
    source_address : str
        Your Gmail email address.
    message : str
        The email message content.
    subject : str
        The subject of the email.
    attachment_path : str, optional
        The path to the attachment file (default is None).

    Returns
    -------
    None
        The function sends the email using Gmail's SMTP server.

    Notes
    -----
    This function sends an email using your Gmail account via Gmail's SMTP server.
    You need to set the password for your Gmail account as the 'GMAIL_PASSWORD' environment
    variable for authentication. Make sure to enable "Less secure apps" access in your Gmail
    account settings to use this method.
    """
    # Create a message object
    msg = MIMEMultipart()
    msg['From'] = source_address
    msg['To'] = email_address
    msg['Subject'] = subject

    password = os.getenv("GMAIL_PASSWORD")

    # Attach the message to the email
    msg.attach(MIMEText(message, 'plain'))

    if attachment_path:
        # Attach the attachment file, if provided
        attachment = open(attachment_path, 'rb')
        part = MIMEBase('application', 'octet-stream')
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= " + os.path.basename(attachment_path))
        msg.attach(part)

    # Establish a connection with Gmail's SMTP server
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()  # Use TLS encryption

    # Log in to your Gmail account
    server.login(source_address, password)

    # Send the email
    server.sendmail(source_address, email_address, msg.as_string())

    # Close the connection
    server.quit()
    
def plot_stock_prices_to_pdf(data_file, symbol, output_file):
    """Load stock price data from a CSV file, plot it, and save the plot as a PDF.

    Parameters
    ----------
    data_file : str
        The filename of the CSV file containing stock price data.
    symbol : str
        The stock symbol, e.g., 'AAPL' for Apple Inc.
    output_file : str
        The filename where the plot will be saved in PDF format.

    Returns
    -------
    None
        The function loads the data, creates a plot, and saves it to a PDF file.

    Notes
    -----
    This function loads historical stock price data from a CSV file, creates a plot of
    the closing prices, and saves the plot to a PDF file. The data is expected to be
    in a CSV format with a date index and a 'Close' column representing closing prices.
    """
   
    # Load the stock price data from the CSV file
    data = pd.read_csv(data_file, index_col=0, parse_dates=True)
    
    if not data.empty:
        # Plot the closing prices
        plt.figure(figsize=(12, 6))
        plt.plot(data.index, data['Close'], label=f'{symbol} Closing Price', color='b')
        plt.title(f'{symbol} Closing Prices')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.grid(True)
        
        # Save the plot to a PDF file
        plt.savefig(output_file, format='pdf')
        print(f"Plot saved to {output_file}")
    
    
def download_and_save_stock_prices(symbol, start_date, end_date, output_file):
    """Download historical stock prices and save them to a CSV file.

    Parameters
    ----------
    symbol : str
        The stock symbol, e.g., 'AAPL' for Apple Inc.
    start_date : str
        The start date for historical data in 'YYYY-MM-DD' format.
    end_date : str
        The end date for historical data in 'YYYY-MM-DD' format.
    output_file : str
        The filename where the data will be saved in CSV format.

    Returns
    -------
    None
        The function saves the data to the specified file.

    Notes
    -----
    This function uses the yfinance library to download historical stock price data
    for a specific stock symbol and date range. The data is saved to a CSV file
    with the specified filename.
    """
    try:
        # Create a Yahoo Finance ticker object for the given symbol
        ticker = yf.Ticker(symbol)
        
        # Download historical stock price data for the specified date range
        data = ticker.history(start=start_date, end=end_date)
        
        if data is not None and not data.empty:
            # Save the data to a CSV file
            data.to_csv(output_file)
            print(f"Stock price data saved to {output_file}")
        else:
            print("Error: No data to save.")
    except Exception as e:
        print(f"Error: {e}")