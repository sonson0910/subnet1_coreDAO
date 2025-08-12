#!/usr/bin/env python3
"""
Quick Cleanup Script for Subnet1 Aptos
Removes obvious duplicate files and backup files safely.
"""

import os
import shutil
from pathlib import Path
import re


def quick_cleanup():
    """Quick cleanup of obvious duplicates and backup files"""

    # Get current directory
    current_dir = Path.cwd()
    print(f"Cleaning up directory: {current_dir}")

    # Create backup directory
    backup_dir = current_dir / "quick_cleanup_backup"
    backup_dir.mkdir(exist_ok=True)

    removed_count = 0
    backup_count = 0

    # Files to remove (obvious duplicates and backups)
    files_to_remove = []

    # Find files matching patterns
    for file_path in current_dir.rglob("*"):
        if file_path.is_file():
            filename = file_path.name

            # Skip critical files
            if filename in ["README.md", ".env", "requirements.txt"]:
                continue

            # Skip if in protected directories
            if any(
                protected in str(file_path)
                for protected in ["subnet1/", "config/", "entities/"]
            ):
                continue

            # Check for obvious duplicates and backups
            if (
                re.match(r".* \d+\.py$", filename)
                or re.match(r".* \d+\.json$", filename)
                or re.match(r".* \d+\.md$", filename)
                or re.match(r".* \d+\.txt$", filename)
                or re.match(r".* \d+\.backup.*$", filename)
                or re.match(r".* \d+\.v\d+$", filename)
                or re.match(r".*\.backup.*$", filename)
                or re.match(r".*\.v\d+$", filename)
                or re.match(r".*_backup.*$", filename)
                or re.match(r".*_v\d+$", filename)
                or re.match(r"test_.* \d+\.py$", filename)
                or re.match(r"start_.* \d+\.py$", filename)
                or filename.endswith(".log")
            ):

                files_to_remove.append(file_path)

    print(f"Found {len(files_to_remove)} files to remove")

    # Remove files with backup
    for file_path in files_to_remove:
        try:
            # Create backup
            backup_path = backup_dir / file_path.relative_to(current_dir)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            backup_count += 1

            # Remove file
            file_path.unlink()
            removed_count += 1
            print(f"Removed: {file_path}")

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    # Clean up specific directories
    cleanup_dirs = ["backup", "fixes"]
    for dir_name in cleanup_dirs:
        dir_path = current_dir / dir_name
        if dir_path.exists() and dir_path.is_dir():
            try:
                # Create backup
                backup_path = backup_dir / dir_name
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                shutil.copytree(dir_path, backup_path)
                backup_count += 1

                # Remove directory
                shutil.rmtree(dir_path)
                removed_count += 1
                print(f"Removed directory: {dir_path}")

            except Exception as e:
                print(f"Error processing directory {dir_path}: {e}")

    print(f"\nQuick cleanup completed!")
    print(f"Files removed: {removed_count}")
    print(f"Backups created: {backup_count}")
    print(f"Backup location: {backup_dir}")


if __name__ == "__main__":
    print("Quick Cleanup for Subnet1 Aptos")
    print("This will remove obvious duplicate files and backup files.")
    print("A backup will be created before any deletion.")

    response = input("Continue? (y/N): ")
    if response.lower() in ["y", "yes"]:
        quick_cleanup()
    else:
        print("Cleanup cancelled.")
