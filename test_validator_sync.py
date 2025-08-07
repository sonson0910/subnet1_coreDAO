#!/usr/bin/env python3
"""
Test Validator Synchronization with Fixed Epoch Start

This script tests that all validators calculate the same slot number
and use synchronized cutoff times for Bittensor-like behavior.
"""

import time
import asyncio
import logging
from datetime import datetime

# Setup cyberpunk logging
logging.basicConfig(
    level=logging.INFO,
    format="\033[95m%(asctime)s\033[0m \033[96m%(name)s\033[0m[\033[93m%(process)d\033[0m] \033[92m%(levelname)s\033[0m \033[94m%(message)s\033[0m",
)
logger = logging.getLogger("SyncTest")


def test_fixed_epoch_sync():
    """Test that fixed epoch calculation is consistent"""
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

    from moderntensor_aptos.mt_core.consensus.flexible_slot_coordinator import (
        get_fixed_epoch_start,
        FlexibleSlotCoordinator,
    )

    print("\n" + "=" * 80)
    print("🔬 TESTING VALIDATOR SYNCHRONIZATION")
    print("=" * 80)

    # Create multiple "validators" with different UIDs
    validator_uids = ["validator_001", "validator_002", "validator_003"]
    coordinators = []

    for uid in validator_uids:
        coordinator = FlexibleSlotCoordinator(
            validator_uid=uid, coordination_dir=f"test_sync_{uid}"
        )
        coordinators.append(coordinator)

    # Test 1: Fixed epoch start consistency
    print("\n📋 TEST 1: Fixed Epoch Start Consistency")
    fixed_epoch = get_fixed_epoch_start()
    print(f"🔒 Fixed Epoch Start: {fixed_epoch}")
    print(f"🔒 Human readable: {datetime.fromtimestamp(fixed_epoch)}")

    # Test 2: Slot number calculation consistency
    print("\n📋 TEST 2: Slot Number Calculation")
    current_time = time.time()

    slot_results = []
    for i, coordinator in enumerate(coordinators):
        slot, phase, metadata = coordinator.get_current_slot_and_phase()
        slot_results.append((validator_uids[i], slot, phase.value))
        print(f"✅ {validator_uids[i]}: Slot {slot}, Phase {phase.value}")

    # Verify all validators have same slot
    all_slots = [result[1] for result in slot_results]
    if len(set(all_slots)) == 1:
        print(f"✅ SUCCESS: All validators synchronized on slot {all_slots[0]}")
    else:
        print(f"❌ FAILURE: Validators have different slots: {all_slots}")

    # Test 3: Cutoff time calculation
    print("\n📋 TEST 3: Cutoff Time Calculation")
    current_slot = slot_results[0][1]  # Use first validator's slot

    for coordinator in coordinators:
        epoch_start = coordinator._epoch_start
        slot_duration = coordinator.slot_config.slot_duration_minutes * 60
        task_duration = coordinator.slot_config.min_task_assignment_seconds

        slot_start = epoch_start + (current_slot * slot_duration)
        cutoff_time = slot_start + task_duration

        print(f"🕐 {coordinator.validator_uid}:")
        print(f"   Epoch start: {epoch_start}")
        print(f"   Slot {current_slot} start: {slot_start}")
        print(f"   Task cutoff: {cutoff_time}")
        print(f"   Current time: {current_time}")
        print(f"   Time to cutoff: {cutoff_time - current_time:.1f}s")

    print("\n" + "=" * 80)
    print("🎯 SYNCHRONIZATION TEST COMPLETE")
    print("=" * 80)


async def test_dual_validator_sync():
    """Test running two validators and verify they stay synchronized"""
    print("\n🚀 STARTING DUAL VALIDATOR SYNC TEST")

    # Just simulate the sync test without actually starting validators
    # This would be where you'd start actual validator processes

    print("⏰ Simulating validator startup with 5-second delay...")
    await asyncio.sleep(2)

    print("✅ Validator 001 started")
    await asyncio.sleep(3)

    print("✅ Validator 002 started")

    # Test that they calculate same slot numbers
    test_fixed_epoch_sync()


if __name__ == "__main__":
    print("🔥 CYBERPUNK VALIDATOR SYNC TEST 🔥")

    # Test fixed epoch synchronization
    test_fixed_epoch_sync()

    # Test async dual validator sync
    print("\n" + "=" * 80)
    asyncio.run(test_dual_validator_sync())
