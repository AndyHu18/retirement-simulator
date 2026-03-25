"""模型單元測試"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from engine.parameters import get_default_params, interpolate_table, MORTALITY_TABLE
from engine.model import (
    run_simulation, initialize_state, PhaseOccupancy,
    calc_new_move_ins, calc_exits,
)


def test_initialization():
    """測試初始化狀態"""
    params = get_default_params()
    state = initialize_state(params)
    assert len(state.phases) == 8
    assert state.phases[0].total_units == 500
    assert state.brand_trust.value == 30.0
    assert state.operational_capability.value == 20.0
    print("PASS: test_initialization")


def test_simulation_runs():
    """測試模擬能跑完 100 步不崩潰"""
    params = get_default_params()
    results = run_simulation(params, n_steps=100, seed=42)
    assert len(results['occupancy_rate']) == 100
    assert results['fund_depleted_step'] == -1 or results['fund_depleted_step'] >= 0
    print("PASS: test_simulation_runs")


def test_no_negative_stocks():
    """測試所有存量不為負"""
    params = get_default_params()
    results = run_simulation(params, n_steps=100, seed=42)
    assert np.all(results['occupancy_rate'] >= 0)
    assert np.all(results['brand_trust'] >= 0)
    assert np.all(results['brand_vitality'] >= 0)
    assert np.all(results['operational_capability'] >= 0)
    print("PASS: test_no_negative_stocks")


def test_occupancy_rate_bounded():
    """測試入住率在 0-1 之間"""
    params = get_default_params()
    results = run_simulation(params, n_steps=100, seed=42)
    assert np.all(results['occupancy_rate'] >= 0)
    assert np.all(results['occupancy_rate'] <= 1.0)
    print("PASS: test_occupancy_rate_bounded")


def test_brand_trust_bounded():
    """測試品牌信任在 0-100 之間"""
    params = get_default_params()
    results = run_simulation(params, n_steps=100, seed=42)
    assert np.all(results['brand_trust'] >= 0)
    assert np.all(results['brand_trust'] <= 100)
    print("PASS: test_brand_trust_bounded")


def test_mortality_table_interpolation():
    """測試死亡率查表插值"""
    rate_65 = interpolate_table(MORTALITY_TABLE, 65)
    assert abs(rate_65 - 0.012) < 0.001

    rate_67 = interpolate_table(MORTALITY_TABLE, 67.5)
    assert 0.012 < rate_67 < 0.020

    rate_95 = interpolate_table(MORTALITY_TABLE, 95)
    assert rate_95 == 0.250
    print("PASS: test_mortality_table_interpolation")


def test_deterministic_with_seed():
    """測試固定種子結果一致"""
    params = get_default_params()
    r1 = run_simulation(params, n_steps=50, seed=123)
    r2 = run_simulation(params, n_steps=50, seed=123)
    assert np.allclose(r1['occupancy_rate'], r2['occupancy_rate'])
    assert np.allclose(r1['fund_pool_total'], r2['fund_pool_total'])
    print("PASS: test_deterministic_with_seed")


def test_professional_operator_boost():
    """測試專業營運夥伴提升初始營運能力"""
    params = get_default_params()
    params.has_professional_operator = True
    state = initialize_state(params)
    assert state.operational_capability.value >= 50
    print("PASS: test_professional_operator_boost")


if __name__ == '__main__':
    test_initialization()
    test_simulation_runs()
    test_no_negative_stocks()
    test_occupancy_rate_bounded()
    test_brand_trust_bounded()
    test_mortality_table_interpolation()
    test_deterministic_with_seed()
    test_professional_operator_boost()
    print("\n=== ALL TESTS PASSED ===")
