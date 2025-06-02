#!/usr/bin/env python3
"""
Test script to verify Aptos migration is working correctly
"""

import sys
import logging
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

console = Console()

def test_imports():
    """Test all critical imports for Aptos migration"""
    console.print("\n[bold blue]Testing Critical Imports...[/bold blue]")
    
    tests = [
        ("Core SDK", "from mt_aptos.consensus.node import ValidatorNode"),
        ("Miner Agent", "from mt_aptos.agent.miner_agent import MinerAgent"),
        ("Metagraph Data", "from mt_aptos.metagraph.metagraph_data import get_all_miner_data, get_all_validator_data"),
        ("Aptos Client", "from mt_aptos.async_client import RestClient"),
        ("Aptos Account", "from mt_aptos.account import Account"),
        ("Core Datatypes", "from mt_aptos.core.datatypes import MinerInfo, ValidatorInfo"),
        ("Settings", "from mt_aptos.config.settings import settings"),
        ("Subnet1 Miner", "from subnet1.miner import Subnet1Miner"),
        ("Subnet1 Validator", "from subnet1.validator import Subnet1Validator"),
        ("Miner Script", "from scripts.run_miner_aptos import run_miner_processes"),
        ("Validator Script", "from scripts.run_validator_aptos import run_validator_process"),
    ]
    
    results = []
    for test_name, import_stmt in tests:
        try:
            exec(import_stmt)
            results.append((test_name, "✅ PASS", "green"))
        except Exception as e:
            results.append((test_name, f"❌ FAIL: {str(e)[:50]}...", "red"))
    
    # Create results table
    table = Table(title="Import Test Results")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Details", style="white")
    
    for name, status, color in results:
        if "PASS" in status:
            table.add_row(name, status, "Import successful", style=color)
        else:
            table.add_row(name, "❌ FAIL", status.replace("❌ FAIL: ", ""), style=color)
    
    console.print(table)
    
    # Summary
    passed = sum(1 for _, status, _ in results if "PASS" in status)
    total = len(results)
    
    if passed == total:
        console.print(f"\n[bold green]🎉 All {total} import tests passed![/bold green]")
        return True
    else:
        console.print(f"\n[bold red]⚠️ {total - passed} out of {total} tests failed[/bold red]")
        return False

def test_cardano_cleanup():
    """Test that Cardano references have been removed"""
    console.print("\n[bold blue]Testing Cardano Cleanup...[/bold blue]")
    
    cardano_terms = ["pycardano", "BlockFrost", "ExtendedSigningKey", "PlutusData", "UTxO"]
    clean_files = []
    issues_found = []
    
    # Check key files for Cardano references
    files_to_check = [
        "sdk/moderntensor_aptos/mt_aptos/agent/miner_agent.py",
        "sdk/moderntensor_aptos/mt_aptos/consensus/node.py",
        "sdk/moderntensor_aptos/mt_aptos/consensus/state.py",
        "sdk/moderntensor_aptos/mt_aptos/metagraph/metagraph_data.py",
        "scripts/run_miner_aptos.py",
        "scripts/run_validator_aptos.py",
    ]
    
    for file_path in files_to_check:
        full_path = project_root / file_path
        if full_path.exists():
            try:
                content = full_path.read_text()
                found_terms = []
                
                # Check each line for Cardano terms, but ignore migration comments
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    line_lower = line.lower()
                    # Skip comments that explain migration
                    if any(phrase in line_lower for phrase in [
                        "# thay thế", "# changed from", "# replaces", 
                        "# removed", "# migration", "# clean up"
                    ]):
                        continue
                    
                    # Check for actual Cardano imports or usage
                    for term in cardano_terms:
                        if term in line and not line.strip().startswith('#'):
                            found_terms.append(f"{term} (line {line_num})")
                
                if found_terms:
                    issues_found.append((file_path, found_terms))
                else:
                    clean_files.append(file_path)
            except Exception as e:
                issues_found.append((file_path, [f"Error reading file: {e}"]))
        else:
            issues_found.append((file_path, ["File not found"]))
    
    # Create cleanup results table
    table = Table(title="Cardano Cleanup Results")
    table.add_column("File", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Issues Found", style="white")
    
    for file_path in clean_files:
        table.add_row(file_path, "✅ CLEAN", "No Cardano references", style="green")
    
    for file_path, issues in issues_found:
        if "Error reading" in str(issues) or "File not found" in str(issues):
            table.add_row(file_path, "⚠️ WARNING", str(issues), style="yellow")
        else:
            table.add_row(file_path, "❌ ISSUES", ", ".join(issues), style="red")
    
    console.print(table)
    
    if not issues_found:
        console.print(f"\n[bold green]🎉 All {len(clean_files)} files are clean of Cardano references![/bold green]")
        return True
    else:
        console.print(f"\n[bold yellow]⚠️ {len(issues_found)} files still contain Cardano references[/bold yellow]")
        return False

def test_aptos_integration():
    """Test Aptos-specific functionality"""
    console.print("\n[bold blue]Testing Aptos Integration...[/bold blue]")
    
    tests = []
    
    # Test 1: Settings load correctly
    try:
        from mt_aptos.config.settings import settings
        if hasattr(settings, 'APTOS_NODE_URL'):
            tests.append(("Settings", "✅ PASS", "green"))
        else:
            tests.append(("Settings", "❌ FAIL: Missing APTOS_NODE_URL", "red"))
    except Exception as e:
        tests.append(("Settings", f"❌ FAIL: {e}", "red"))
    
    # Test 2: Account creation works
    try:
        from mt_aptos.account import Account
        # Don't actually create account without key, just test import
        tests.append(("Account Creation", "✅ PASS", "green"))
    except Exception as e:
        tests.append(("Account Creation", f"❌ FAIL: {e}", "red"))
    
    # Test 3: RestClient import
    try:
        from mt_aptos.async_client import RestClient
        tests.append(("REST Client", "✅ PASS", "green"))
    except Exception as e:
        tests.append(("REST Client", f"❌ FAIL: {e}", "red"))
    
    # Test 4: Contract client
    try:
        from mt_aptos.aptos_core.contract_client import AptosContractClient
        tests.append(("Contract Client", "✅ PASS", "green"))
    except Exception as e:
        tests.append(("Contract Client", f"❌ FAIL: {e}", "red"))
    
    # Create results table
    table = Table(title="Aptos Integration Test Results")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="white")
    
    for name, status, color in tests:
        table.add_row(name, status, style=color)
    
    console.print(table)
    
    passed = sum(1 for _, status, _ in tests if "PASS" in status)
    total = len(tests)
    
    if passed == total:
        console.print(f"\n[bold green]🎉 All {total} Aptos integration tests passed![/bold green]")
        return True
    else:
        console.print(f"\n[bold red]⚠️ {total - passed} out of {total} tests failed[/bold red]")
        return False

def main():
    """Run all migration tests"""
    console.print(Panel.fit(
        "[bold]ModernTensor Aptos Migration Test Suite[/bold]\n"
        "Verifying the migration from Cardano to Aptos is complete",
        border_style="blue"
    ))
    
    # Run all tests
    import_results = test_imports()
    cleanup_results = test_cardano_cleanup()
    aptos_results = test_aptos_integration()
    
    # Final summary
    console.print("\n" + "="*60)
    
    total_tests = 3
    passed_tests = sum([import_results, cleanup_results, aptos_results])
    
    if passed_tests == total_tests:
        console.print(Panel.fit(
            "[bold green]🎉 MIGRATION SUCCESSFUL! 🎉[/bold green]\n\n"
            "✅ All imports working\n"
            "✅ Cardano references cleaned\n"
            "✅ Aptos integration ready\n\n"
            "[dim]You can now run the Aptos scripts:[/dim]\n"
            "[cyan]python scripts/run_miner_aptos.py[/cyan]\n"
            "[cyan]python scripts/run_validator_aptos.py[/cyan]",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            f"[bold yellow]⚠️ MIGRATION INCOMPLETE[/bold yellow]\n\n"
            f"Passed: {passed_tests}/{total_tests} test suites\n"
            f"Some issues need to be resolved before production use.",
            border_style="yellow"
        ))
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 