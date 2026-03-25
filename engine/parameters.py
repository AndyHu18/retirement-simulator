"""參數定義、先驗分布、校準值"""

from dataclasses import dataclass, field
from typing import List
import copy
import numpy as np


@dataclass
class PhaseConfig:
    """單期配置"""
    units: int
    construction_cost: float = 0.0  # TWD


@dataclass
class SimParams:
    """模擬參數（使用者可調整 + 蒙地卡羅可抽樣）"""

    # === 結構性 ===
    total_phases: int = 8
    phase_configs: List[PhaseConfig] = field(default_factory=list)
    phase_activation_threshold: float = 0.80
    location: str = 'suao'

    # === 財務 ===
    deposit_amount: float = 25_000_000       # TWD 2,500萬
    monthly_fee: float = 100_000             # TWD 10萬/月
    refund_percentage: float = 0.90          # 90%可退還
    staff_ratio: float = 0.4                 # 每戶0.4名員工
    avg_staff_cost_monthly: float = 50_000   # TWD 5萬/月/人
    has_onsen: bool = True
    onsen_cost_multiplier: float = 1.8
    suao_labor_premium: float = 1.15
    other_revenue_monthly: float = 5_000_000  # TWD 500萬/月
    maintenance_cost_quarterly: float = 5_000_000  # TWD 500萬/季

    # === 需求 ===
    target_pool: int = 35_000                # 大台北高淨值55+
    base_annual_conversion: float = 0.005    # 0.5%基礎年轉化率
    insurance_factor: float = 1.0            # 1.0=無, 2.0=有, 3.0=泰康級
    experience_level: int = 1                # 0-3
    distance_friction: float = 0.85          # 蘇澳距離折扣

    # === 信託 ===
    trust_independent: bool = False
    trust_mechanism_level: int = 0           # 0-3

    # === 醫療 ===
    medical_integration: int = 1             # 1-3
    ccrc_care_ratio: float = 0.15            # 15%介護棟

    # === 品牌 ===
    initial_brand_trust: float = 30.0
    debranding_level: int = 2                # 去標籤化程度 1-3

    # === 營運 ===
    has_professional_operator: bool = False
    initial_operational_capability: float = 20.0
    team_quality: float = 1.0                # 0.5-1.5
    staff_turnover_rate: float = 0.15        # 年化

    # === 環境 ===
    initial_cultural_acceptance: float = 0.05
    annual_acceptance_growth: float = 0.02
    community_self_sufficiency: int = 1      # 園區配套完整度 0-3

    # === 分期啟動 ===
    min_days_cash_for_new_phase: int = 250
    capex_coverage_ratio: float = 0.3        # 至少30%建設資金

    # === 蒙地卡羅抽樣控制 ===
    random_seed: int = -1                    # -1=隨機, >=0=固定種子


def get_default_params() -> SimParams:
    """取得蘇澳校準預設參數"""
    params = SimParams()
    # 8 期規模（前小後大）
    units_list = [500, 700, 800, 1000, 1000, 1200, 1300, 1500]
    # 建設成本（TWD）: 每戶約 500 萬
    params.phase_configs = [
        PhaseConfig(units=u, construction_cost=u * 5_000_000)
        for u in units_list
    ]
    return params


# 預設參數常數
DEFAULT_PARAMS = get_default_params()


# === 死亡率查表（年化，CCRC 住戶，自選擇效應較低） ===
MORTALITY_TABLE = {
    55: 0.005, 60: 0.008, 65: 0.012, 70: 0.020,
    75: 0.035, 80: 0.060, 85: 0.100, 90: 0.160, 95: 0.250
}

# === 轉介護率查表（年化） ===
CARE_TRANSFER_TABLE = {
    55: 0.005, 60: 0.008, 65: 0.010, 70: 0.020,
    75: 0.050, 80: 0.100, 85: 0.150, 90: 0.200
}


def interpolate_table(table: dict, age: float) -> float:
    """線性內插查表"""
    ages = sorted(table.keys())
    if age <= ages[0]:
        return table[ages[0]]
    if age >= ages[-1]:
        return table[ages[-1]]
    for i in range(len(ages) - 1):
        if ages[i] <= age <= ages[i + 1]:
            frac = (age - ages[i]) / (ages[i + 1] - ages[i])
            return table[ages[i]] * (1 - frac) + table[ages[i + 1]] * frac
    return table[ages[-1]]


def sample_parameters(base_params: SimParams, rng: np.random.Generator) -> SimParams:
    """從參數分布中抽樣（蒙地卡羅用）"""
    p = copy.deepcopy(base_params)

    # α級參數：窄分布（±15%）
    p.monthly_fee *= max(0.5, rng.normal(1.0, 0.05))
    p.staff_ratio *= max(0.2, rng.normal(1.0, 0.10))
    p.avg_staff_cost_monthly *= max(0.5, rng.normal(1.0, 0.08))

    # β級參數：中等分布（±30%）
    p.base_annual_conversion *= max(0.1, rng.normal(1.0, 0.20))
    p.distance_friction *= max(0.5, min(1.0, rng.normal(p.distance_friction, 0.05)))
    p.staff_turnover_rate = max(0.02, min(0.5, rng.normal(p.staff_turnover_rate, 0.05)))

    # γ級參數：寬分布（±50%）
    p.insurance_factor = max(1.0, p.insurance_factor * max(0.3, rng.normal(1.0, 0.40)))
    p.initial_cultural_acceptance = max(0.01, min(0.20, rng.normal(
        p.initial_cultural_acceptance, 0.02
    )))

    # 相關性處理：宏觀衝擊同時影響多個參數
    macro_shock = rng.normal(0, 1)
    if macro_shock < -1.5:
        p.base_annual_conversion *= 0.5
        p.distance_friction *= 0.9

    return p
