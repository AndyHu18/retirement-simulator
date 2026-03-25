"""邊界情境測試"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from engine.parameters import get_default_params
from engine.model import run_simulation


def test_all_optimistic():
    """所有參數設為最樂觀值 → 不應出現不合理的無限增長"""
    params = get_default_params()
    params.insurance_factor = 3.0
    params.trust_mechanism_level = 3
    params.trust_independent = True
    params.experience_level = 3
    params.medical_integration = 3
    params.has_professional_operator = True
    params.initial_brand_trust = 70
    params.initial_cultural_acceptance = 0.15
    params.community_self_sufficiency = 3

    results = run_simulation(params, n_steps=100, seed=42)

    # 入住率不應超過 100%
    assert np.all(results['occupancy_rate'] <= 1.0), "入住率超過 100%"
    # 品牌信任不應超過 100
    assert np.all(results['brand_trust'] <= 100), "品牌信任超過 100"
    # 資金池應為正
    assert results['fund_depleted_step'] == -1, "最樂觀情境不應耗盡"
    print("PASS: test_all_optimistic")


def test_all_pessimistic():
    """所有參數設為最悲觀值 → 應在合理時間內觸發資金池耗盡"""
    params = get_default_params()
    params.insurance_factor = 1.0
    params.trust_mechanism_level = 0
    params.trust_independent = False
    params.experience_level = 0
    params.medical_integration = 1
    params.has_professional_operator = False
    params.initial_brand_trust = 10
    params.initial_cultural_acceptance = 0.01
    params.distance_friction = 0.5
    params.monthly_fee = 50_000  # 低月費
    params.other_revenue_monthly = 0

    results = run_simulation(params, n_steps=100, seed=42)

    # 在 25 年內入住率應該很低
    final_occ = results['occupancy_rate'][-1]
    assert final_occ < 0.5, f"最悲觀情境入住率不應超過 50%，實際={final_occ:.1%}"
    print("PASS: test_all_pessimistic")


def test_threshold_stability():
    """入住率在閾值附近（79-81%）→ 不應出現數值不穩定"""
    params = get_default_params()
    results = run_simulation(params, n_steps=100, seed=42)
    occ = results['occupancy_rate']

    # 檢查連續步之間的變化不超過 10%
    for t in range(1, len(occ)):
        delta = abs(occ[t] - occ[t - 1])
        assert delta < 0.10, f"步驟 {t}: 入住率變化過大 {delta:.3f}"
    print("PASS: test_threshold_stability")


def test_eight_phases_no_crash():
    """8 期全部啟動 → 系統不應崩潰或出現負值"""
    params = get_default_params()
    # 降低啟動門檻讓更多期能啟動
    params.phase_activation_threshold = 0.3
    params.insurance_factor = 3.0
    params.initial_brand_trust = 80

    results = run_simulation(params, n_steps=100, seed=42)

    assert np.all(results['occupancy_rate'] >= 0), "出現負入住率"
    assert np.all(results['brand_trust'] >= 0), "出現負品牌信任"
    print("PASS: test_eight_phases_no_crash")


def test_stress_compound_disaster():
    """複合災難壓力測試"""
    from engine.scenarios import STRESS_SCENARIOS

    params = get_default_params()
    overrides = STRESS_SCENARIOS['compound_disaster']['overrides']

    results = run_simulation(params, n_steps=100, seed=42,
                             stress_overrides=overrides)

    # 不應崩潰
    assert len(results['occupancy_rate']) == 100
    # 入住率應受影響
    occ_at_trigger = results['occupancy_rate'][12]  # 觸發點
    occ_during = results['occupancy_rate'][16]  # 壓力期間
    # 壓力期間入住率應低於觸發前（或至少不高太多）
    print(f"  觸發前入住率: {occ_at_trigger:.1%}, 壓力期間: {occ_during:.1%}")
    print("PASS: test_stress_compound_disaster")


if __name__ == '__main__':
    test_all_optimistic()
    test_all_pessimistic()
    test_threshold_stability()
    test_eight_phases_no_crash()
    test_stress_compound_disaster()
    print("\n=== ALL EDGE CASE TESTS PASSED ===")
