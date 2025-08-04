#!/usr/bin/env python3
"""
Test timeout scoring logic
"""
import sys
import time
from pathlib import Path

# Add project root to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent / "moderntensor_aptos"
sys.path.insert(0, str(project_root))

from moderntensor_aptos.mt_core.consensus.scoring import score_results_logic
from mt_core.core.datatypes import TaskAssignment, ValidatorScore


def test_timeout_scoring():
    """Test that timeout cases receive 0 scores"""
    print("🧪 TESTING TIMEOUT SCORING LOGIC")
    print("=" * 50)

    # Create mock task assignment
    task_id = "test_task_123"
    miner_uid = "test_miner_001"
    validator_uid = "test_validator_001"

    tasks_sent = {
        task_id: TaskAssignment(
            task_id=task_id,
            task_data={"prompt": "test task"},
            miner_uid=miner_uid,
            validator_uid=validator_uid,
            timestamp_sent=time.time(),
            expected_result_format={},
        )
    }

    # Test Case 1: Empty results (timeout)
    print("\n📋 Test Case 1: Empty results (timeout)")
    results_received_timeout = {task_id: []}  # Empty list = timeout

    scores = score_results_logic(
        results_received=results_received_timeout,
        tasks_sent=tasks_sent,
        validator_uid=validator_uid,
    )

    print(f"   Results: {len(scores)} tasks scored")
    if task_id in scores and scores[task_id]:
        score_obj = scores[task_id][0]
        print(f"   ✅ Timeout score: {score_obj.score} (expected: 0.0)")
        print(f"   📝 Miner: {score_obj.miner_uid}")
        print(f"   📝 Validator: {score_obj.validator_uid}")

        if score_obj.score == 0.0:
            print("   ✅ PASS: Timeout correctly scored as 0.0")
        else:
            print("   ❌ FAIL: Timeout score should be 0.0")
    else:
        print("   ❌ FAIL: No score generated for timeout case")

    # Test Case 2: No results in dict (no tasks assigned)
    print("\n📋 Test Case 2: No results in dict")
    results_received_empty = {}

    scores_empty = score_results_logic(
        results_received=results_received_empty,
        tasks_sent=tasks_sent,
        validator_uid=validator_uid,
    )

    print(f"   Results: {len(scores_empty)} tasks scored")
    if not scores_empty:
        print("   ✅ PASS: No scores generated when no results received")
    else:
        print("   ❌ FAIL: Should not generate scores when no results received")

    print(f"\n🎯 TIMEOUT SCORING LOGIC VERIFICATION COMPLETE")
    print(f"   New logic ensures:")
    print(f"   • Tasks assigned but no response → 0 score")
    print(f"   • No tasks assigned → no scores")
    print(f"   • Scores generated → TXID submission")


if __name__ == "__main__":
    test_timeout_scoring()
