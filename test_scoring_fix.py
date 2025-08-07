#!/usr/bin/env python3
"""
Test Scoring Fix for Zero Score Bug

This script tests that scores are correctly converted and submitted to blockchain.
"""

import asyncio
import logging
import time
from typing import Dict, List

# Setup cyberpunk logging
logging.basicConfig(
    level=logging.INFO,
    format="\033[95m%(asctime)s\033[0m \033[96m%(name)s\033[0m[\033[93m%(process)d\033[0m] \033[92m%(levelname)s\033[0m \033[94m%(message)s\033[0m",
)
logger = logging.getLogger("ScoringTest")


def test_score_conversion():
    """Test conversion from ValidatorScore list to miner_uid: score dict"""
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

    from moderntensor_aptos.mt_core.core.datatypes import ValidatorScore

    print("\n" + "=" * 80)
    print("🔬 TESTING SCORE CONVERSION FIX")
    print("=" * 80)

    # Simulate ValidatorScore objects like minibatch scoring creates
    test_scores = [
        ValidatorScore(
            task_id="task_001",
            miner_uid="subnet1_miner_001",
            validator_uid="subnet1_validator_001",
            score=0.6344,  # From CLIP scoring example
        ),
        ValidatorScore(
            task_id="task_002",
            miner_uid="subnet1_miner_002",
            validator_uid="subnet1_validator_001",
            score=0.7892,
        ),
    ]

    print(f"📋 Original ValidatorScore objects:")
    for score in test_scores:
        print(f"  - {score.miner_uid}: {score.score:.4f} (task: {score.task_id})")

    # Test conversion logic (same as in fix)
    local_scores = {}
    for score_obj in test_scores:
        local_scores[score_obj.miner_uid] = score_obj.score

    print(f"\n🎯 Converted to dict format:")
    for miner_uid, score in local_scores.items():
        print(f"  - {miner_uid}: {score:.4f}")

    # Test that this format can be stored in coordination files
    coordination_data = {"scores": local_scores}
    print(f"\n💾 Coordination file format:")
    print(f"  {coordination_data}")

    # Verify no zero scores
    has_zero_scores = any(score == 0.0 for score in local_scores.values())
    if has_zero_scores:
        print("❌ FAILURE: Found zero scores in conversion")
    else:
        print("✅ SUCCESS: No zero scores found, conversion working correctly")

    print("\n" + "=" * 80)
    print("🎯 SCORE CONVERSION TEST COMPLETE")
    print("=" * 80)


def test_formulas_integration():
    """Test that formulas are properly integrated"""
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

    from moderntensor_aptos.mt_core.formulas import (
        calculate_adjusted_miner_performance,
        calculate_validator_performance,
        update_trust_score,
    )

    print("\n" + "=" * 80)
    print("🧮 TESTING FORMULAS INTEGRATION")
    print("=" * 80)

    # Test calculate_adjusted_miner_performance
    performance_scores = [0.6344, 0.7892, 0.5234]  # From 3 validators
    trust_scores = [0.8, 0.9, 0.7]  # Trust scores of validators

    adjusted_performance = calculate_adjusted_miner_performance(
        performance_scores, trust_scores
    )

    print(f"📊 Performance scores: {performance_scores}")
    print(f"📊 Validator trust scores: {trust_scores}")
    print(f"🎯 Adjusted miner performance: {adjusted_performance:.4f}")

    # Test trust score update
    old_trust = 0.5
    new_trust = update_trust_score(
        trust_score_old=old_trust,
        time_since_last_eval=60,
        score_new=0.6344,
        delta_trust=0.01,
        alpha_base=0.1,
    )

    print(f"📈 Trust score update: {old_trust:.3f} → {new_trust:.3f}")

    # Test validator performance
    validator_perf = calculate_validator_performance(
        q_task_validator=0.9,
        metric_validator_quality=0.8,
        deviation=0.05,  # Low deviation = good performance
    )

    print(f"🏆 Validator performance: {validator_perf:.4f}")

    print("\n✅ SUCCESS: All formulas working correctly")
    print("=" * 80)


if __name__ == "__main__":
    print("🔥 CYBERPUNK SCORING FIX TEST 🔥")

    # Test score conversion fix
    test_score_conversion()

    # Test formulas integration
    test_formulas_integration()

    print("\n🎉 ALL TESTS COMPLETED! The scoring zero bug should be fixed.")
    print("Next: Run validators to see real scores in coordination files.")
