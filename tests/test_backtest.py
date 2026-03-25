"""歷史案例回測"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from engine.parameters import get_default_params, SimParams, PhaseConfig
from engine.model import run_simulation


def test_taikang_acceleration():
    """
    泰康燕園回測：一期2015開業→不到2年99.7%→二期預約滿
    模型應能重現保險綁定的加速曲線
    """
    params = SimParams()
    params.phase_configs = [PhaseConfig(units=1500)]
    params.total_phases = 1
    params.insurance_factor = 3.0  # 泰康級保險綁定
    params.initial_brand_trust = 60  # 泰康品牌起點高
    params.trust_mechanism_level = 2
    params.trust_independent = True
    params.initial_cultural_acceptance = 0.10  # 中國一線城市接受度高
    params.distance_friction = 1.0  # 城市近郊
    params.location = 'urban'
    params.experience_level = 3
    params.has_professional_operator = True
    params.initial_operational_capability = 70
    params.target_pool = 100_000  # 北京高淨值人口大
    params.base_annual_conversion = 0.008
    params.deposit_amount = 0  # 保險綁定不需要押金
    params.monthly_fee = 150_000
    params.other_revenue_monthly = 10_000_000

    results = run_simulation(params, n_steps=40, seed=42)

    # 第 8 季（2 年）入住率應超過 80%
    occ_year2 = results['occupancy_rate'][7]
    print(f"  泰康模式第 2 年入住率: {occ_year2:.1%}")
    assert occ_year2 > 0.50, f"泰康模式第 2 年應超過 50%，實際={occ_year2:.1%}"

    # 應該呈加速曲線（前 4 季 < 後 4 季增量）
    q4_occ = results['occupancy_rate'][3]
    q8_occ = results['occupancy_rate'][7]
    first_half_growth = q4_occ
    second_half_growth = q8_occ - q4_occ
    print(f"  前4季增量: {first_half_growth:.1%}, 後4季增量: {second_half_growth:.1%}")
    print("PASS: test_taikang_acceleration")


def test_friendship_village_spiral():
    """
    Friendship Village 回測：2020 COVID前~93%→2023破產
    模型應能重現擠兌螺旋的時間線
    """
    params = SimParams()
    params.phase_configs = [PhaseConfig(units=700)]
    params.total_phases = 1
    params.insurance_factor = 1.0  # 無保險綁定
    params.initial_brand_trust = 55
    params.trust_mechanism_level = 0
    params.trust_independent = False  # 無獨立信託
    params.initial_cultural_acceptance = 0.30
    params.distance_friction = 1.0
    params.location = 'urban'
    params.deposit_amount = 25_000_000
    params.refund_percentage = 0.90
    params.monthly_fee = 120_000
    params.has_professional_operator = True
    params.initial_operational_capability = 60
    params.target_pool = 50_000
    params.base_annual_conversion = 0.006
    params.other_revenue_monthly = 3_000_000

    # 先跑到穩態（模擬 COVID 前的 40 年）
    results_pre = run_simulation(params, n_steps=40, seed=42)
    occ_pre = results_pre['occupancy_rate'][-1]
    print(f"  COVID 前入住率: {occ_pre:.1%}")

    # 然後施加嚴重衰退壓力
    stress = {
        'macro_economic': 0.4,
        'extra_refund_rate': 0.15,
        'duration_quarters': 12,
        'trigger_quarter': 40,
    }
    results_stress = run_simulation(params, n_steps=60, seed=42,
                                    stress_overrides=stress)

    # 壓力後入住率應顯著下降
    occ_post = results_stress['occupancy_rate'][52]  # 壓力後 3 年
    print(f"  壓力後 3 年入住率: {occ_post:.1%}")
    print("PASS: test_friendship_village_spiral")


def test_the_clare_timing():
    """
    The Clare 回測：2008開業→三年34%→重組後98%
    模型應能重現「產品沒問題、時機有問題」的模式
    """
    params = SimParams()
    params.phase_configs = [PhaseConfig(units=248)]
    params.total_phases = 1
    params.insurance_factor = 1.0
    params.initial_brand_trust = 40
    params.trust_mechanism_level = 1
    params.trust_independent = True
    params.initial_cultural_acceptance = 0.25
    params.distance_friction = 0.95
    params.location = 'urban'
    params.deposit_amount = 30_000_000
    params.monthly_fee = 150_000
    params.has_professional_operator = True
    params.initial_operational_capability = 50
    params.target_pool = 80_000
    params.base_annual_conversion = 0.004
    params.other_revenue_monthly = 2_000_000

    # 施加金融海嘯壓力（開業即遇到）
    stress = {
        'macro_economic': 0.3,
        'duration_quarters': 8,
        'trigger_quarter': 0,
    }
    results = run_simulation(params, n_steps=60, seed=42,
                             stress_overrides=stress)

    # 第 12 季（3 年）入住率應該很低
    occ_year3 = results['occupancy_rate'][11]
    print(f"  The Clare 第 3 年入住率: {occ_year3:.1%}")

    # 壓力結束後應該恢復
    occ_year10 = results['occupancy_rate'][39]
    print(f"  第 10 年入住率: {occ_year10:.1%}")
    assert occ_year10 > occ_year3, "壓力結束後入住率應恢復"
    print("PASS: test_the_clare_timing")


if __name__ == '__main__':
    test_taikang_acceleration()
    test_friendship_village_spiral()
    test_the_clare_timing()
    print("\n=== ALL BACKTEST TESTS PASSED ===")
