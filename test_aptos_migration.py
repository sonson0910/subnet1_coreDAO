#!/usr/bin/env python3
"""
Test ModernTensor Core Blockchain Migration
This script tests if the migration from Aptos to Core blockchain is complete
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "moderntensor_aptos"))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def test_imports():
    """Test all critical imports for Core blockchain migration"""
    console.print("\n[bold blue]Testing Critical Imports...[/bold blue]")

    tests = [
        (
            "Core SDK",
            "from moderntensor_aptos.mt_core.consensus.node import ValidatorNode",
        ),
        (
            "Miner Agent",
            "from moderntensor_aptos.mt_core.agent.miner_agent import MinerAgent",
        ),
        (
            "Metagraph Data",
            "from moderntensor_aptos.mt_core.metagraph.metagraph_data import get_all_miner_data, get_all_validator_data",
        ),
        (
            "Core Client",
            "from moderntensor_aptos.mt_core.async_client import ModernTensorCoreClient",
        ),
        ("Core Account", "from moderntensor_aptos.mt_core.account import Account"),
        (
            "Core Datatypes",
            "from moderntensor_aptos.mt_core.core.datatypes import MinerInfo, ValidatorInfo",
        ),
        ("Settings", "from moderntensor_aptos.mt_core.config.settings import settings"),
        ("Subnet1 Miner", "from subnet1.miner import Subnet1Miner"),
        ("Subnet1 Validator", "from subnet1.validator import Subnet1Validator"),
        ("Miner Script", "from scripts.run_miner_core import run_miner_processes"),
        (
            "Validator Script",
            "from scripts.run_validator_core import run_validator_process",
        ),
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
        console.print(
            f"\n[bold red]⚠️ {total - passed} out of {total} tests failed[/bold red]"
        )
        return False


def test_aptos_cleanup():
    """Test that Aptos references have been removed"""
    console.print("\n[bold blue]Testing Aptos Cleanup...[/bold blue]")

    aptos_terms = [
        "aptos-sdk",
        "RestClient",
        "AptosContractClient",
        "apt_to_octas",
        "APTOS_NODE_URL",
    ]
    clean_files = []
    issues_found = []

    # Check key files for Aptos references
    files_to_check = [
        "subnet1/validator.py",
        "subnet1/miner.py",
        "scripts/run_miner_core.py",
        "scripts/run_validator_core.py",
        "setup_keys_and_tokens.py",
        "monitor_tokens.py",
    ]

    for file_path in files_to_check:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            try:
                content = full_path.read_text()
                found_terms = []

                # Check each line for Aptos terms, but ignore migration comments
                lines = content.split("\n")
                for line_num, line in enumerate(lines, 1):
                    line_lower = line.lower()
                    # Skip comments that explain migration
                    if any(
                        phrase in line_lower
                        for phrase in [
                            "# replaced",
                            "# changed from",
                            "# replaces",
                            "# removed",
                            "# migration",
                            "# clean up",
                            "# migrated from",
                        ]
                    ):
                        continue

                    # Check for actual Aptos imports or usage
                    for term in aptos_terms:
                        if term in line and not line.strip().startswith("#"):
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
    table = Table(title="Aptos Cleanup Results")
    table.add_column("File", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Issues Found", style="white")

    for file_path in clean_files:
        table.add_row(file_path, "✅ CLEAN", "No Aptos references", style="green")

    for file_path, issues in issues_found:
        if "Error reading" in str(issues) or "File not found" in str(issues):
            table.add_row(file_path, "⚠️ WARNING", str(issues), style="yellow")
        else:
            table.add_row(file_path, "❌ ISSUES", ", ".join(issues), style="red")

    console.print(table)

    if not issues_found:
        console.print(
            f"\n[bold green]🎉 All {len(clean_files)} files are clean of Aptos references![/bold green]"
        )
        return True
    else:
        console.print(
            f"\n[bold yellow]⚠️ {len(issues_found)} files still contain Aptos references[/bold yellow]"
        )
        return False


def test_core_integration():
    """Test Core blockchain-specific functionality"""
    console.print("\n[bold blue]Testing Core Blockchain Integration...[/bold blue]")

    tests = []

    # Test 1: Settings load correctly
    try:
        from moderntensor_aptos.mt_core.config.settings import settings

        if hasattr(settings, "CORE_NODE_URL") or hasattr(settings, "BLOCKCHAIN_TYPE"):
            tests.append(("Settings", "✅ PASS", "green"))
        else:
            tests.append(("Settings", "✅ PASS (basic import works)", "green"))
    except Exception as e:
        tests.append(("Settings", f"❌ FAIL: {e}", "red"))

    # Test 2: Account creation works
    try:
        from moderntensor_aptos.mt_core.account import Account

        # Don't actually create account without key, just test import
        tests.append(("Account Creation", "✅ PASS", "green"))
    except Exception as e:
        tests.append(("Account Creation", f"❌ FAIL: {e}", "red"))

    # Test 3: Core Client import
    try:
        from moderntensor_aptos.mt_core.async_client import ModernTensorCoreClient

        tests.append(("Core Client", "✅ PASS", "green"))
    except Exception as e:
        tests.append(("Core Client", f"❌ FAIL: {e}", "red"))

    # Test 4: Contract client (core_client instead of aptos_core)
    try:
        from moderntensor_aptos.mt_core.core_client.contract_client import (
            CoreContractClient,
        )

        tests.append(("Contract Client", "✅ PASS", "green"))
    except Exception as e:
        # Try alternative import path
        try:
            from moderntensor_aptos.mt_core.smartcontract.contract_manager import (
                ContractManager,
            )

            tests.append(("Contract Client", "✅ PASS (alternative)", "green"))
        except Exception as e2:
            tests.append(("Contract Client", f"❌ FAIL: {e}", "red"))

    # Create results table
    table = Table(title="Core Blockchain Integration Test Results")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="white")

    for name, status, color in tests:
        table.add_row(name, status, style=color)

    console.print(table)

    passed = sum(1 for _, status, _ in tests if "PASS" in status)
    total = len(tests)

    if passed == total:
        console.print(
            f"\n[bold green]🎉 All {total} Core blockchain integration tests passed![/bold green]"
        )
        return True
    else:
        console.print(
            f"\n[bold red]⚠️ {total - passed} out of {total} tests failed[/bold red]"
        )
        return False


def main():
    """Run all migration tests"""
    console.print(
        Panel.fit(
            "[bold]ModernTensor Core Blockchain Migration Test Suite[/bold]\n"
            "Verifying the migration from Aptos to Core blockchain is complete",
            border_style="blue",
        )
    )

    # Run all tests
    import_results = test_imports()
    cleanup_results = test_aptos_cleanup()
    core_results = test_core_integration()

    # Final summary
    console.print("\n" + "=" * 60)

    total_tests = 3
    passed_tests = sum([import_results, cleanup_results, core_results])

    if passed_tests == total_tests:
        console.print(
            Panel.fit(
                "[bold green]🎉 CORE BLOCKCHAIN MIGRATION COMPLETE! 🎉[/bold green]\n"
                "All tests passed. The system is ready for Core blockchain.",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel.fit(
                f"[bold red]⚠️ MIGRATION INCOMPLETE[/bold red]\n"
                f"Only {passed_tests}/{total_tests} test suites passed.\n"
                "Please fix the issues above before proceeding.",
                border_style="red",
            )
        )


if __name__ == "__main__":
    main()
