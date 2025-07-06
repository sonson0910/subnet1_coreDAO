#!/usr/bin/env python3
"""
Script to run 2 Cardano validators and 1 miner with detailed logging
Run from subnet1/scripts directory
"""
import subprocess
import sys
import os
import time
from datetime import datetime
import signal
import logging
from pathlib import Path
import threading
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cardano_full_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CardanoFullRunner:
    def __init__(self):
        self.processes = []
        self.log_files = []
        self.running = True
        
    def start_process(self, script_path, log_file_name, description):
        """Start a process with logging"""
        try:
            log_file = open(log_file_name, 'w')
            self.log_files.append(log_file)
            
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes.append({
                'process': process,
                'name': description,
                'log_file': log_file_name,
                'script': script_path
            })
            
            logger.info(f"Started {description} (PID: {process.pid}) - Log: {log_file_name}")
            return process
            
        except Exception as e:
            logger.error(f"Failed to start {description}: {e}")
            return None
    
    def monitor_log_file(self, log_file_path, process_name):
        """Monitor log file for important events"""
        try:
            with open(log_file_path, 'r') as f:
                f.seek(0, 2)  # Go to end of file
                while self.running:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    
                    line = line.strip()
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    # Look for transaction IDs
                    if re.search(r'0x[a-fA-F0-9]{64}', line):
                        logger.info(f"🔗 [{timestamp}] [{process_name}] TXID: {line}")
                    
                    # Look for consensus events
                    elif any(keyword in line.lower() for keyword in [
                        'consensus', 'finalize', 'submit', 'broadcast', 'cardano'
                    ]):
                        logger.info(f"📊 [{timestamp}] [{process_name}] CONSENSUS: {line}")
                    
                    # Look for scores and mining
                    elif any(keyword in line.lower() for keyword in ['score', 'mining', 'generated', 'task']):
                        logger.info(f"📈 [{timestamp}] [{process_name}] SCORE/MINING: {line}")
                    
                    # Look for P2P events
                    elif any(keyword in line.lower() for keyword in ['p2p', 'peer', 'broadcast']):
                        logger.info(f"🌐 [{timestamp}] [{process_name}] P2P: {line}")
                    
                    # Look for errors
                    elif any(keyword in line.lower() for keyword in ['error', 'failed', 'exception']):
                        logger.warning(f"❌ [{timestamp}] [{process_name}] ERROR: {line}")
                    
                    # Look for task assignment
                    elif any(keyword in line.lower() for keyword in ['assignment', 'received', 'miner']):
                        logger.info(f"📋 [{timestamp}] [{process_name}] TASK: {line}")
                        
        except Exception as e:
            logger.error(f"Error monitoring {log_file_path}: {e}")
    
    def cleanup(self):
        """Clean up all processes and files"""
        logger.info("Cleaning up processes...")
        self.running = False
        
        for proc_info in self.processes:
            try:
                process = proc_info['process']
                if process.poll() is None:  # Still running
                    logger.info(f"Terminating {proc_info['name']} (PID: {process.pid})")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Force killing {proc_info['name']}")
                        process.kill()
            except Exception as e:
                logger.error(f"Error terminating {proc_info['name']}: {e}")
        
        for log_file in self.log_files:
            try:
                log_file.close()
            except:
                pass
    
    def run_full_test(self, duration=600):
        """Run the full test with validators and miner"""
        logger.info("=" * 80)
        logger.info("🚀 STARTING CARDANO FULL TEST (2 VALIDATORS + 1 MINER)")
        logger.info("=" * 80)
        
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get paths relative to project root
        project_root = Path(__file__).parent.parent.parent  # Go back to moderntensor_aptos
        
        try:
            # Start Cardano Validator 1
            validator1_script = project_root / "test_cardano_consensus.py"
            self.start_process(
                str(validator1_script),
                f"logs/cardano_validator1_{timestamp}.log",
                "Cardano Validator 1"
            )
            
            # Wait a bit
            time.sleep(3)
            
            # Start Cardano Validator 2
            validator2_script = project_root / "test_cardano_validator2.py"
            self.start_process(
                str(validator2_script), 
                f"logs/cardano_validator2_{timestamp}.log",
                "Cardano Validator 2"
            )
            
            # Wait a bit more
            time.sleep(3)
            
            # Start Miner
            miner_script = Path(__file__).parent / "run_miner_aptos.py"
            self.start_process(
                str(miner_script),
                f"logs/cardano_miner_{timestamp}.log",
                "Aptos Miner"
            )
            
            logger.info("🎯 All processes started! Monitoring for activity...")
            logger.info("📝 Log files:")
            for proc_info in self.processes:
                logger.info(f"   - {proc_info['name']}: {proc_info['log_file']}")
            
            # Start monitoring threads
            monitor_threads = []
            for proc_info in self.processes:
                thread = threading.Thread(
                    target=self.monitor_log_file,
                    args=(proc_info['log_file'], proc_info['name']),
                    daemon=True
                )
                thread.start()
                monitor_threads.append(thread)
            
            # Monitor for specified duration
            logger.info(f"⏱️  Monitoring for {duration} seconds...")
            start_time = time.time()
            
            while time.time() - start_time < duration:
                # Check if any process has died
                for proc_info in self.processes:
                    if proc_info['process'].poll() is not None:
                        logger.warning(f"⚠️  {proc_info['name']} has stopped!")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error in full test: {e}")
        finally:
            self.cleanup()
            logger.info("✅ Cardano full test completed!")

def main():
    """Main function"""
    runner = CardanoFullRunner()
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        runner.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run for 10 minutes by default, or specify duration
    duration = 600
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except ValueError:
            logger.warning("Invalid duration, using default 600 seconds")
    
    runner.run_full_test(duration)

if __name__ == "__main__":
    main() 