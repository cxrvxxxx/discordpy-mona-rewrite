from datetime import datetime

def console_log(message):
    timestamp = str(datetime.now())
    print(f"{timestamp[:-7]}: SYSTEM: {message}")