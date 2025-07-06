#!/usr/bin/env python3
"""
Real-time log monitor for ModernTensor consensus
"""
import os
import time
import sys
import threading
from pathlib import Path
import re
from datetime import datetime

class LogMonitor:
    def __init__(self, log_dir="logs"):
        self.log_dir = Path(log_dir)
        self.monitors = {}
        self.running = True
        
    def monitor_file(self, filepath, name):
        """Monitor a single log file"""
        try:
            with open(filepath, 'r') as f:
                f.seek(0, 2)  # Go to end
                while self.running:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    
                    self.process_line(line.strip(), name)
                    
        except Exception as e:
            print(f"❌ Error monitoring {filepath}: {e}")
    
    def process_line(self, line, source):
        """Process a log line and highlight important events"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Transaction IDs
        if re.search(r'0x[a-fA-F0-9]{64}', line):
            print(f"🔗 [{timestamp}] [{source}] TXID: {line}")
        
        # Consensus events
        elif any(keyword in line.lower() for keyword in [
            'consensus', 'broadcast', 'finalize', 'submit', 'transaction'
        ]):
            print(f"📊 [{timestamp}] [{source}] CONSENSUS: {line}")
        
        # Scores
        elif 'score' in line.lower():
            print(f"📈 [{timestamp}] [{source}] SCORE: {line}")
        
        # Errors
        elif any(keyword in line.lower() for keyword in ['error', 'failed', 'exception']):
            print(f"❌ [{timestamp}] [{source}] ERROR: {line}")
        
        # P2P Communication
        elif any(keyword in line.lower() for keyword in ['p2p', 'peer', 'broadcast']):
            print(f"🌐 [{timestamp}] [{source}] P2P: {line}")
    
    def start_monitoring(self):
        """Start monitoring all log files"""
        print("🔍 Starting log monitoring...")
        print("📁 Monitoring directory:", self.log_dir.absolute())
        
        threads = []
        
        # Monitor existing log files
        for log_file in self.log_dir.glob("*.log"):
            name = log_file.stem
            thread = threading.Thread(
                target=self.monitor_file,
                args=(log_file, name),
                daemon=True
            )
            thread.start()
            threads.append(thread)
            print(f"📝 Monitoring: {log_file.name}")
        
        if not threads:
            print("⚠️  No log files found in", self.log_dir)
            return
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitoring...")
            self.running = False
            
        for thread in threads:
            thread.join(timeout=1)

def main():
    if len(sys.argv) > 1:
        log_dir = sys.argv[1]
    else:
        log_dir = "logs"
    
    monitor = LogMonitor(log_dir)
    monitor.start_monitoring()

if __name__ == "__main__":
    main() 