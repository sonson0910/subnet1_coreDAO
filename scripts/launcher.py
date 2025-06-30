#!/usr/bin/env python3
"""
ModernTensor Subnet1 Script Launcher
Easy launcher for all miners and validators
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional

def get_script_path(script_name: str) -> str:
    """Get the full path to a script."""
    scripts_dir = Path(__file__).parent
    return str(scripts_dir / script_name)

def run_script(script_name: str, background: bool = False) -> Optional[subprocess.Popen]:
    """Run a script either in foreground or background."""
    script_path = get_script_path(script_name)
    
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return None
    
    print(f"🚀 Starting {script_name}{'in background' if background else ''}...")
    
    try:
        if background:
            # Run in background
            process = subprocess.Popen([sys.executable, script_path])
            print(f"✅ Started {script_name} with PID: {process.pid}")
            return process
        else:
            # Run in foreground
            subprocess.run([sys.executable, script_path])
            return None
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="ModernTensor Subnet1 Script Launcher")
    parser.add_argument("target", nargs="?", help="What to run: miner1, miner2, validator1, validator2, validator3, all-miners, all-validators, all")
    parser.add_argument("--background", "-b", action="store_true", help="Run in background")
    parser.add_argument("--list", "-l", action="store_true", help="List available scripts")
    
    args = parser.parse_args()
    
    # Available scripts
    scripts = {
        "miner1": "run_miner1_aptos.py",
        "miner2": "run_miner2_aptos.py", 
        "validator1": "run_validator1_aptos.py",
        "validator2": "run_validator2_aptos.py",
        "validator3": "run_validator3_aptos.py"
    }
    
    if args.list:
        print("📋 Available scripts:")
        for name, script in scripts.items():
            print(f"  - {name}: {script}")
        print("\n🔧 Special commands:")
        print("  - all-miners: Run both miners")
        print("  - all-validators: Run all validators") 
        print("  - all: Run everything")
        return
    
    if not args.target:
        print("❌ Please specify what to run. Use --list to see options.")
        parser.print_help()
        return
    
    processes: List[subprocess.Popen] = []
    
    try:
        if args.target == "all-miners":
            print("🚀 Starting all miners...")
            for script in ["run_miner1_aptos.py", "run_miner2_aptos.py"]:
                process = run_script(script, background=True)
                if process:
                    processes.append(process)
                    
        elif args.target == "all-validators":
            print("🚀 Starting all validators...")
            for script in ["run_validator1_aptos.py", "run_validator2_aptos.py", "run_validator3_aptos.py"]:
                process = run_script(script, background=True)
                if process:
                    processes.append(process)
                    
        elif args.target == "all":
            print("🚀 Starting everything...")
            for script in scripts.values():
                process = run_script(script, background=True)
                if process:
                    processes.append(process)
                    
        elif args.target in scripts:
            script = scripts[args.target]
            process = run_script(script, args.background)
            if process and args.background:
                processes.append(process)
                
        else:
            print(f"❌ Unknown target: {args.target}")
            print("Use --list to see available options.")
            return
        
        # If running multiple processes in background, wait for user input
        if processes:
            print(f"\n✅ Started {len(processes)} processes in background:")
            for i, process in enumerate(processes, 1):
                print(f"  {i}. PID: {process.pid}")
            
            print("\n💡 Press Ctrl+C to stop all processes, or Enter to continue...")
            try:
                input()
            except KeyboardInterrupt:
                print("\n🛑 Stopping all processes...")
                for process in processes:
                    try:
                        process.terminate()
                        print(f"  Stopped PID: {process.pid}")
                    except:
                        pass
                        
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
        for process in processes:
            try:
                process.terminate()
            except:
                pass

if __name__ == "__main__":
    main() 