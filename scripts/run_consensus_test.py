#!/usr/bin/env python3
"""
Script to run 2 validators and 1 miner simultaneously with detailed logging
"""
import asyncio
import subprocess
import sys
import os
import time
from datetime import datetime
import signal
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('consensus_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProcessManager:
    def __init__(self):
        self.processes = []
        self.log_files = []
        
    def start_process(self, script_name, log_file_name, description):
        """Start a process with logging"""
        try:
            log_file = open(log_file_name, 'w')
            self.log_files.append(log_file)
            
            process = subprocess.Popen(
                [sys.executable, script_name],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=os.path.dirname(script_name),
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes.append({
                'process': process,
                'name': description,
                'log_file': log_file_name,
                'script': script_name
            })
            
            logger.info(f"Started {description} (PID: {process.pid}) - Log: {log_file_name}")
            return process
            
        except Exception as e:
            logger.error(f"Failed to start {description}: {e}")
            return None
    
    def monitor_logs_for_txid(self, log_file_path, process_name):
        """Monitor log file for transaction IDs"""
        try:
            with open(log_file_path, 'r') as f:
                f.seek(0, 2)  # Go to end of file
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    
                    # Look for transaction IDs
                    if 'txid' in line.lower() or '0x' in line:
                        logger.info(f"🔗 [{process_name}] TRANSACTION: {line.strip()}")
                    
                    # Look for consensus events
                    if any(keyword in line.lower() for keyword in ['consensus', 'broadcast', 'score', 'finalize']):
                        logger.info(f"📊 [{process_name}] CONSENSUS: {line.strip()}")
                        
        except Exception as e:
            logger.error(f"Error monitoring {log_file_path}: {e}")
    
    def cleanup(self):
        """Clean up all processes and files"""
        logger.info("Cleaning up processes...")
        
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
    
    def wait_and_monitor(self, duration=300):  # 5 minutes default
        """Wait and monitor processes"""
        logger.info(f"Monitoring for {duration} seconds...")
        
        # Start log monitoring threads
        monitor_tasks = []
        for proc_info in self.processes:
            task = asyncio.create_task(
                self.async_monitor_logs(proc_info['log_file'], proc_info['name'])
            )
            monitor_tasks.append(task)
        
        start_time = time.time()
        try:
            while time.time() - start_time < duration:
                # Check if any process has died
                for proc_info in self.processes:
                    if proc_info['process'].poll() is not None:
                        logger.warning(f"{proc_info['name']} has stopped!")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        
        # Cancel monitoring tasks
        for task in monitor_tasks:
            task.cancel()
    
    async def async_monitor_logs(self, log_file_path, process_name):
        """Async version of log monitoring"""
        try:
            with open(log_file_path, 'r') as f:
                f.seek(0, 2)  # Go to end of file
                while True:
                    line = f.readline()
                    if not line:
                        await asyncio.sleep(0.1)
                        continue
                    
                    # Look for transaction IDs
                    if 'txid' in line.lower() or '0x' in line:
                        logger.info(f"🔗 [{process_name}] TRANSACTION: {line.strip()}")
                    
                    # Look for consensus events
                    if any(keyword in line.lower() for keyword in ['consensus', 'broadcast', 'score', 'finalize']):
                        logger.info(f"📊 [{process_name}] CONSENSUS: {line.strip()}")
                        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error monitoring {log_file_path}: {e}")

def main():
    """Main function to run the consensus test"""
    logger.info("=" * 80)
    logger.info("🚀 STARTING MODERNTENSOR CONSENSUS TEST")
    logger.info("=" * 80)
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    manager = ProcessManager()
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        manager.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start Validator 1
        manager.start_process(
            "run_validator1_aptos.py",
            f"logs/validator1_{timestamp}.log",
            "Validator 1"
        )
        
        # Wait a bit between starts
        time.sleep(2)
        
        # Start Validator 2
        manager.start_process(
            "run_validator2_aptos.py", 
            f"logs/validator2_{timestamp}.log",
            "Validator 2"
        )
        
        # Wait a bit more
        time.sleep(2)
        
        # Start Miner 1
        manager.start_process(
            "run_miner1_aptos.py",
            f"logs/miner1_{timestamp}.log", 
            "Miner 1"
        )
        
        logger.info("🎯 All processes started! Monitoring for activity...")
        logger.info("📝 Log files:")
        for proc_info in manager.processes:
            logger.info(f"   - {proc_info['name']}: {proc_info['log_file']}")
        
        # Monitor for 10 minutes
        manager.wait_and_monitor(duration=600)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        manager.cleanup()
        logger.info("✅ Consensus test completed!")

if __name__ == "__main__":
    main() 