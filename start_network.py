#!/usr/bin/env python3
"""
Network Startup Script for Subnet1
Start validators and miners in proper sequence
"""

import subprocess
import time
import json
import os
import signal
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv


class NetworkManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.processes = []
        self.running = False

        # Load environment
        env_path = self.project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)

    def check_prerequisites(self):
        """Check if entities are generated and registered"""
        entities_dir = self.project_root / "entities"

        if not entities_dir.exists():
            print("❌ No entities directory found")
            print("🔧 Run: python quick_setup_entities.py")
            return False

        miners = list(entities_dir.glob("miner_*.json"))
        validators = list(entities_dir.glob("validator_*.json"))

        if not miners or not validators:
            print("❌ No entities found")
            print("🔧 Run: python quick_setup_entities.py")
            return False

        print(f"✅ Found {len(miners)} miners and {len(validators)} validators")
        return True

    def start_validator(self, validator_id):
        """Start a single validator"""
        script_path = self.project_root / "scripts" / "run_validator_core.py"

        if not script_path.exists():
            print(f"❌ Validator script not found: {script_path}")
            return None

        env = os.environ.copy()
        env["VALIDATOR_ID"] = str(validator_id)
        env["PYTHONPATH"] = str(self.project_root.parent)

        try:
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            print(f"🟢 Started Validator {validator_id} (PID: {process.pid})")
            return process

        except Exception as e:
            print(f"❌ Failed to start validator {validator_id}: {e}")
            return None

    def start_miner(self, miner_id):
        """Start a single miner"""
        script_path = self.project_root / "scripts" / "run_miner_core.py"

        if not script_path.exists():
            print(f"❌ Miner script not found: {script_path}")
            return None

        env = os.environ.copy()
        env["MINER_ID"] = str(miner_id)
        env["PYTHONPATH"] = str(self.project_root.parent)

        try:
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            print(f"🔨 Started Miner {miner_id} (PID: {process.pid})")
            return process

        except Exception as e:
            print(f"❌ Failed to start miner {miner_id}: {e}")
            return None

    def start_network(self):
        """Start the entire network"""
        if not self.check_prerequisites():
            return

        print("🚀 Starting Subnet1 Network")
        print("=" * 40)

        self.running = True

        # Start validators first
        print("\n🔄 Starting Validators...")
        for i in range(1, 4):  # 3 validators
            process = self.start_validator(i)
            if process:
                self.processes.append(("validator", i, process))
                time.sleep(2)  # Stagger startup

        print("\n🔄 Starting Miners...")
        for i in range(1, 3):  # 2 miners
            process = self.start_miner(i)
            if process:
                self.processes.append(("miner", i, process))
                time.sleep(2)  # Stagger startup

        print(f"\n✅ Network started with {len(self.processes)} processes")

        # Monitor processes
        self.monitor_network()

    def monitor_network(self):
        """Monitor network health and restart failed processes"""
        print("\n📊 Monitoring Network (Ctrl+C to stop)")
        print("-" * 40)

        try:
            while self.running:
                time.sleep(10)

                # Check process health
                for i, (entity_type, entity_id, process) in enumerate(self.processes):
                    if process.poll() is not None:
                        print(
                            f"⚠️  {entity_type.title()} {entity_id} stopped (exit code: {process.returncode})"
                        )

                        # Restart process
                        if entity_type == "validator":
                            new_process = self.start_validator(entity_id)
                        else:
                            new_process = self.start_miner(entity_id)

                        if new_process:
                            self.processes[i] = (entity_type, entity_id, new_process)
                            print(f"🔄 Restarted {entity_type.title()} {entity_id}")

                # Display status
                running_count = sum(1 for _, _, p in self.processes if p.poll() is None)
                print(
                    f"💚 Network Status: {running_count}/{len(self.processes)} processes running"
                )

        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down network...")
            self.stop_network()

    def stop_network(self):
        """Stop all network processes"""
        self.running = False

        for entity_type, entity_id, process in self.processes:
            if process.poll() is None:
                print(f"🔴 Stopping {entity_type.title()} {entity_id}...")
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"⚡ Force killing {entity_type.title()} {entity_id}")
                    process.kill()
                    process.wait()

        print("✅ Network stopped")

    def show_status(self):
        """Show current network status"""
        if not self.processes:
            print("❌ Network not running")
            return

        print("📊 Network Status")
        print("-" * 30)

        for entity_type, entity_id, process in self.processes:
            status = "🟢 Running" if process.poll() is None else "🔴 Stopped"
            print(f"{entity_type.title()} {entity_id}: {status} (PID: {process.pid})")


def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
    else:
        command = "start"

    manager = NetworkManager()

    if command == "start":
        manager.start_network()
    elif command == "status":
        manager.show_status()
    elif command == "stop":
        manager.stop_network()
    else:
        print("🔧 Usage:")
        print("  python start_network.py start   # Start network")
        print("  python start_network.py status  # Show status")
        print("  python start_network.py stop    # Stop network")


if __name__ == "__main__":
    main()
