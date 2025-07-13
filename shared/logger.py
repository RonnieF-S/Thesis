"""
Lightweight Shared Logger
Simple logging utility for UAV and Ground Station
"""

import time

class SimpleLogger:
    """Lightweight logger for console output"""
    
    @staticmethod
    def info(msg):
        print(f"[{time.strftime('%H:%M:%S')}] INFO: {msg}")
    
    @staticmethod
    def warning(msg):
        print(f"[{time.strftime('%H:%M:%S')}] WARN: {msg}")
    
    @staticmethod
    def error(msg):
        print(f"[{time.strftime('%H:%M:%S')}] ERROR: {msg}")
    
    @staticmethod
    def debug(msg):
        print(f"[{time.strftime('%H:%M:%S')}] DEBUG: {msg}")
