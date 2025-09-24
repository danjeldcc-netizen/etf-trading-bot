import os
import yfinance as yf
import pandas as pd
import numpy as np
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from datetime import datetime
import requests

# Konfiguracija iz environment variables
SYMBOLS = ['XLI', 'XLK', 'XLY', 'XLP', 'XLF', 'XLV', 'XLC', 'XLE', 'XLB', 'SPY', 'QQQ', 'SLV', 'GLD']

EMAIL_CONFIG = {
    'email': os.getenv('EMAIL'),
    'password': os.getenv('EMAIL_PASSWORD'),
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587
}

class ETFSuperTrendBot:
    def __init__(self):
        self.atr_length = 10
        self.factor = 3.0
        
    def calculate_supertrend(self, df):
        high = df['High']
        low = df['Low'] 
        close = df['Close']
        
        # ATR izračun
        tr = np.maximum(high - low, 
                       np.maximum(abs(high - close.shift(1)), 
                                 abs(low - close.shift(1))))
        atr = tr.rolling(window=self.atr_length).mean()
        
        # SuperTrend logika
        hl2 = (high + low) / 2
        upper_band = hl2 + (self.factor * atr)
        lower_band = hl2 - (self.factor * atr)
        
        supertrend = [np.nan] * len(close)
        direction = [0] * len(close)
        
        for i in range(1, len(close)):
            if i < self.atr_length:
                continue
                
            # Poenostavljena implementacija
            if pd.isna(direction[i-1]):
                direction[i] = 1
            elif direction[i-1] == -1:
                direction[i] = -1 if close.iloc[i] > upper_band.iloc[i] else 1
            else:
                direction[i] = 1 if close.iloc[i] < lower_band.iloc[i] else -1
                
            supertrend[i] = lower_band.iloc[i] if direction[i] == -1 else upper_band.iloc[i]
        
        return supertrend, direction
    
    def check_buy_signal(self, symbol):
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='3mo', interval='1d')
            
            if len(data) < self.atr_length:
                return False, None, None
                
            supertrend, direction = self.calculate_supertrend(data)
            
            if len(direction) >= 2:
                if direction[-2] == -1 and direction[-1] == 1:
                    return True, data['Close'].iloc[-1], data.index[-1]
                    
        except Exception as e:
            print(f"Error with {symbol}: {e}")
            
        return False, None, None
    
    def send_email(self, symbol, price, timestamp):
        try:
            msg = MimeMultipart()
            msg['Subject'] = f"🚀 ETF BUY: {symbol}"
            msg['From'] = EMAIL_CONFIG['email']
            msg['To'] = EMAIL_CONFIG['email']
            
            body = f"BUY Signal: {symbol} at ${price:.2f} - {timestamp}"
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
            server.starttls()
            server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Email error: {e}")
            return False
    
    def run_check(self):
        print(f"Checking {len(SYMBOLS)} ETFs at {datetime.now()}")
        
        for symbol in SYMBOLS:
            signal, price, timestamp = self.check_buy_signal(symbol)
            if signal:
                print(f"BUY: {symbol} at ${price:.2f}")
                self.send_email(symbol, price, timestamp)
            else:
                print(f"No signal: {symbol}")

if __name__ == "__main__":
    bot = ETFSuperTrendBot()
    bot.run_check()
