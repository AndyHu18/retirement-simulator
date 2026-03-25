"""蒙地卡羅模擬引擎"""

from __future__ import annotations
import copy
from typing import Optional, Dict, List
import numpy as np
from scipy import stats

from .parameters import SimParams, sample_parameters
from .model import initialize_state, simulation_step, check_phase_activation
from .rules import evaluate_rules


def run_monte_carlo(params: SimParams, n_simulations: int = 10000,
                    n_steps: int = 100,
                    stress_overrides: Optional[dict] = None,
                    progress_callback=None) -> dict:
    """
    跑 n_simulations 次完整模擬

    Args:
        params: 基礎參數
        n_simulations: 模擬次數
        n_steps: 時間步數（100=25年）
        stress_overrides: 壓力測試覆蓋
        progress_callback: 進度回調 fn(current, total)

    Returns:
        包含所有模擬結果的字典
    """
    metrics = [
        'occupancy_rate', 'fund_pool_total', 'brand_trust',
        'brand_vitality', 'days_cash_on_hand', 'run_rate_pressure',
        'operating_cash', 'operational_capability', 'median_age',
    ]

    results = {m: np.zeros((n_simulations, n_steps)) for m in metrics}
    results['fund_depleted_step'] = np.full(n_simulations, -1)

    base_seed = params.random_seed if params.random_seed >= 0 else 12345

    for sim in range(n_simulations):
        rng = np.random.default_rng(base_seed + sim)
        sampled_params = sample_parameters(params, rng)
        state = initialize_state(sampled_params)
        check_phase_activation(state, sampled_params, 0)

        for t in range(n_steps):
            state = simulation_step(state, sampled_params, t, rng, stress_overrides)

            results['occupancy_rate'][sim, t] = state.overall_occupancy_rate
            results['fund_pool_total'][sim, t] = state.fund_pool.total
            results['brand_trust'][sim, t] = state.brand_trust.value
            results['brand_vitality'][sim, t] = state.age_structure.brand_vitality_index
            results['days_cash_on_hand'][sim, t] = state.fund_pool.days_cash_on_hand
            results['run_rate_pressure'][sim, t] = state.fund_pool.run_rate_pressure
            results['operating_cash'][sim, t] = state.fund_pool.operating_cash
            results['operational_capability'][sim, t] = state.operational_capability.value
            results['median_age'][sim, t] = state.age_structure.median_age

            if state.fund_pool.total <= 0 and results['fund_depleted_step'][sim] == -1:
                results['fund_depleted_step'][sim] = t

        if progress_callback and (sim + 1) % max(1, n_simulations // 20) == 0:
            progress_callback(sim + 1, n_simulations)

    return results


def compute_percentiles(mc_results: dict, metric: str) -> dict:
    """計算百分位數據（用於扇形圖）"""
    data = mc_results[metric]  # shape: (n_sims, n_steps)
    return {
        'p5': np.percentile(data, 5, axis=0),
        'p25': np.percentile(data, 25, axis=0),
        'p50': np.percentile(data, 50, axis=0),
        'p75': np.percentile(data, 75, axis=0),
        'p95': np.percentile(data, 95, axis=0),
    }


def calculate_summary_metrics(mc_results: dict) -> dict:
    """計算關鍵摘要指標"""
    n_sims = mc_results['fund_depleted_step'].shape[0]
    n_steps = mc_results['occupancy_rate'].shape[1]

    # 25 年資金池耗盡機率
    depleted = mc_results['fund_depleted_step']
    depletion_prob = np.sum(depleted >= 0) / n_sims

    # 首期達 85% 入住率的中位數年數
    occ = mc_results['occupancy_rate']
    fill_times = []
    for sim in range(n_sims):
        found = np.where(occ[sim] >= 0.85)[0]
        if len(found) > 0:
            fill_times.append(found[0] / 4)  # 轉為年
        else:
            fill_times.append(25.0)
    median_fill_years = float(np.median(fill_times))

    # 品牌老化觸發時間（品牌活力 < 50 的首次時間）
    bv = mc_results['brand_vitality']
    aging_times = []
    for sim in range(n_sims):
        found = np.where(bv[sim] < 50)[0]
        if len(found) > 0:
            aging_times.append(found[0] / 4)
        else:
            aging_times.append(25.0)
    median_aging_trigger = float(np.median(aging_times))

    # 無新血存活期（用最後狀態的資金池推估）
    # 簡化：看資金池在第 20 步之後的下降速率
    fund = mc_results['fund_pool_total']
    last_fund = fund[:, -1]
    operating_cost_proxy = mc_results.get('operating_cash', fund)
    # 粗略：月均成本 ≈ 最後季度營運現金流的絕對值
    no_new_blood_months = []
    for sim in range(n_sims):
        if fund[sim, -1] > 0:
            # 用最後 4 步的平均下降來估算
            if n_steps > 4:
                decline = np.mean(np.diff(fund[sim, -5:]))
                if decline < 0:
                    months_left = fund[sim, -1] / abs(decline) * 3
                    no_new_blood_months.append(min(120, months_left))
                else:
                    no_new_blood_months.append(120)
            else:
                no_new_blood_months.append(60)
        else:
            no_new_blood_months.append(0)
    median_no_new_blood = float(np.median(no_new_blood_months))

    # 擠兌壓力指數 P95
    rrp = mc_results['run_rate_pressure']
    rrp_p95 = float(np.percentile(np.max(rrp, axis=1), 95))

    return {
        'depletion_prob': depletion_prob,
        'median_fill_years': median_fill_years,
        'median_aging_trigger': median_aging_trigger,
        'no_new_blood_survival': median_no_new_blood,
        'rrp_p95': rrp_p95,
    }


def run_sensitivity_analysis(params: SimParams, n_simulations: int = 1000,
                             n_steps: int = 100) -> List[dict]:
    """
    敏感度分析：哪個參數對結果影響最大
    用 Spearman 等級相關計算每個參數與最終入住率、資金池的相關性
    """
    param_names = [
        ('monthly_fee', '月費'),
        ('deposit_amount', '押金'),
        ('insurance_factor', '保險綁定'),
        ('base_annual_conversion', '基礎轉化率'),
        ('staff_ratio', '人員配比'),
        ('distance_friction', '距離摩擦'),
        ('staff_turnover_rate', '人員流失率'),
        ('initial_cultural_acceptance', '文化接受度'),
    ]

    base_seed = params.random_seed if params.random_seed >= 0 else 12345
    param_values = {name: [] for name, _ in param_names}
    final_occupancy = []
    final_fund = []

    for sim in range(n_simulations):
        rng = np.random.default_rng(base_seed + sim + 100000)
        sampled = sample_parameters(params, rng)

        for attr, _ in param_names:
            param_values[attr].append(getattr(sampled, attr))

        state = initialize_state(sampled)
        check_phase_activation(state, sampled, 0)

        sim_rng = np.random.default_rng(base_seed + sim + 200000)
        for t in range(n_steps):
            state = simulation_step(state, sampled, t, sim_rng)

        final_occupancy.append(state.overall_occupancy_rate)
        final_fund.append(state.fund_pool.total)

    final_occ_arr = np.array(final_occupancy)
    final_fund_arr = np.array(final_fund)

    sensitivity = []
    for attr, label in param_names:
        vals = np.array(param_values[attr])
        if np.std(vals) < 1e-10:
            corr_occ = 0.0
            corr_fund = 0.0
        else:
            corr_occ = float(stats.spearmanr(vals, final_occ_arr).statistic)
            corr_fund = float(stats.spearmanr(vals, final_fund_arr).statistic)

        sensitivity.append({
            'param': attr,
            'label': label,
            'corr_occupancy': corr_occ,
            'corr_fund': corr_fund,
            'impact': abs(corr_occ) + abs(corr_fund),
        })

    sensitivity.sort(key=lambda x: x['impact'], reverse=True)
    return sensitivity
