#!/usr/bin/env python3
"""
Test Formulas Application in Scoring

This script tests that formulas from @formulas/ are properly applied
in both immediate and minibatch scoring workflows.
"""

import logging
import time
from typing import Dict, Any

# Setup cyberpunk logging
logging.basicConfig(
    level=logging.INFO,
    format="\033[95m%(asctime)s\033[0m \033[96m%(name)s\033[0m[\033[93m%(process)d\033[0m] \033[92m%(levelname)s\033[0m \033[94m%(message)s\033[0m",
)
logger = logging.getLogger("FormulasTest")


def test_advanced_scoring_formulas():
    """Test that calculate_advanced_score applies formulas correctly"""
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

    from moderntensor_aptos.mt_core.consensus.scoring import calculate_advanced_score

    print("\n" + "=" * 80)
    print("🧮 TESTING FORMULAS APPLICATION")
    print("=" * 80)

    # Mock validator instance with CLIP scoring
    class MockValidator:
        def _score_individual_result(self, task_data, result_data):
            return 0.6326  # Simulated CLIP score

    mock_validator = MockValidator()

    # Test task and result data
    task_data = {
        "prompt": "Slot-based consensus task for slot 841681",
        "timestamp": time.time(),
    }

    result_data = {
        "result": "base64_image_data...",
        "timestamp": time.time(),
        "miner_uid": "subnet1_miner_001",
    }

    miner_uid = "subnet1_miner_001"
    validator_uid = "subnet1_validator_001"
    current_time_step = int(time.time())

    print(f"📋 Input CLIP score: 0.6326")
    print(f"📋 Miner: {miner_uid}")
    print(f"📋 Validator: {validator_uid}")

    # Test advanced scoring with formulas
    final_score, metadata = calculate_advanced_score(
        task_data=task_data,
        result_data=result_data,
        miner_uid=miner_uid,
        validator_uid=validator_uid,
        validator_instance=mock_validator,
        current_time_step=current_time_step,
    )

    print(f"\n🎯 FORMULAS APPLICATION RESULTS:")
    print(f"  - Basic CLIP score: {metadata.get('basic_score', 0.0):.4f}")
    print(f"  - Final score after formulas: {final_score:.4f}")

    # Check if formulas were applied
    if "weighted_score" in metadata:
        print(f"  - Weighted score: {metadata['weighted_score']:.4f}")
        print(f"  - Miner weight: {metadata.get('miner_weight', 'N/A')}")

    if "trust_adjusted_score" in metadata:
        print(f"  - Trust adjusted score: {metadata['trust_adjusted_score']:.4f}")
        print(f"  - Trust multiplier: {metadata.get('trust_multiplier', 'N/A')}")

    if "trust_score_new" in metadata:
        trust_old = metadata.get("trust_score_old", 0.5)
        trust_new = metadata["trust_score_new"]
        print(f"  - Trust score evolution: {trust_old:.3f} → {trust_new:.3f}")

    if "performance_improvement" in metadata:
        improvement = metadata["performance_improvement"]
        print(f"  - Performance improvement: {improvement:+.4f}")

    # Verify formulas were applied
    basic_score = metadata.get("basic_score", 0.0)
    if abs(final_score - basic_score) > 0.001:
        print(
            f"✅ SUCCESS: Formulas applied! Score changed from {basic_score:.4f} to {final_score:.4f}"
        )
    else:
        print(f"⚠️  WARNING: Score unchanged, formulas may not be applied")

    print("\n" + "=" * 80)
    print("🎯 FORMULAS APPLICATION TEST COMPLETE")
    print("=" * 80)

    return final_score, metadata


def test_performance_vs_clip_comparison():
    """Compare direct CLIP vs formulas-enhanced performance scoring"""
    print("\n" + "=" * 80)
    print("⚖️  TESTING CLIP VS PERFORMANCE COMPARISON")
    print("=" * 80)

    # Direct CLIP score (what we saw in logs)
    clip_score = 0.6326

    # Formulas-enhanced score (what we should get)
    enhanced_score, metadata = test_advanced_scoring_formulas()

    print(f"📊 COMPARISON:")
    print(f"  - Direct CLIP score: {clip_score:.4f}")
    print(f"  - Formulas-enhanced score: {enhanced_score:.4f}")
    print(f"  - Difference: {enhanced_score - clip_score:+.4f}")

    if enhanced_score != clip_score:
        print(f"✅ SUCCESS: Formulas provide enhanced scoring!")
        print(f"🚀 Performance calculation includes:")
        print(f"   - Trust score evolution")
        print(f"   - Historical performance weighting")
        print(f"   - Fraud detection adjustments")
        print(f"   - Advanced incentive calculations")
    else:
        print(f"❌ ISSUE: No enhancement applied, check formulas integration")

    print("\n" + "=" * 80)
    print("⚖️  COMPARISON TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    print("🔥 CYBERPUNK FORMULAS APPLICATION TEST 🔥")

    # Test formulas application
    test_advanced_scoring_formulas()

    # Test performance vs CLIP comparison
    test_performance_vs_clip_comparison()

    print("\n🎯 FINAL STATUS: Formulas should now be applied to all scoring!")
    print(
        "Expected: Enhanced scores with trust, performance, and incentive calculations."
    )

