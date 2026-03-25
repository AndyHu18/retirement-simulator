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
    recession_annual_prob: float = 0.05      # 年衰退機率
    recession_severity: float = 0.6          # 衰退嚴重度

    # === 分期啟動 ===
    min_days_cash_for_new_phase: int = 250
    capex_coverage_ratio: float = 0.3        # 至少30%建設資金

    # === v2 資本結構 ===
    total_budget_twd: float = 80_000_000_000  # 800 億
    annual_cost_of_capital: float = 0.035     # 年化 3.5%
    payback_tolerance_years: int = 20
    financial_stress_sensitivity: str = 'medium'
    refinancing_risk: bool = False

    # === v2 押金模式 ===
    refund_condition: str = 'new_occupant'    # 退費條件
    squeeze_risk: str = 'high'
    amortization_years: int = 0               # 0=不償卻, >0=Benesse 模式
    deposit_amount_multiplier: float = 1.0
    monthly_fee_multiplier: float = 1.0

    # === v2 需求引擎 ===
    insurance_start_quarter: int = 8          # 保險通路上線時間
    experience_monthly_cost: float = 8_000_000
    conversion_boost: float = 1.2
    h_hotel_funnel_active: bool = True
    h_hotel_annual_contacts: int = 6000
    h_hotel_inquiry_rate: float = 0.03
    h_hotel_close_rate: float = 0.12
    marketing_budget_monthly: float = 5_000_000
    resort_revenue: float = 0                 # 度假旅居月收入

    # === v2 產品營運 ===
    medical_setup_cost: float = 200_000_000
    medical_monthly_cost: float = 8_000_000
    medical_occupancy_boost: float = 1.15
    medical_brand_trust_boost: float = 5
    medical_external_revenue: bool = False
    care_transfer_internal: bool = False
    onsen_setup_cost: float = 300_000_000
    onsen_external_revenue: float = 2_000_000
    brand_differentiation_boost: float = 0.10
    learning_rate: float = 1.0
    service_quality_cap: float = 100
    operator_cost_share: float = 0.0

    # === v2 開發節奏 ===
    brand_vitality_decay_reduction: float = 0.0  # 老化對抗總減幅
    new_resident_avg_age_reduction: float = 0    # 新住戶年齡降低
    aging_countermeasure_cost: float = 0         # 額外成本
    aging_countermeasure_revenue: float = 0      # 額外收入

    # === v2 多元收入流 ===
    revenue_streams: list = field(default_factory=list)  # 選中的收入流名稱
    revenue_stream_setup_cost: float = 0
    total_stream_monthly_revenue: float = 0

    # === v2 外部環境 ===
    regulatory_protection: int = 0
    regulation_start_year: int = 99           # 99=不啟動
    voluntary_trust_brand_value: float = 2.0
    compliance_cost_annual: float = 0
    mandatory_reserve_ratio: float = 0

    # === v2 競品 ===
    competitor_entry: bool = False
    competitor_year: int = 8
    competitor_diversion_rate: float = 0.12
    competitor_brand_shock: float = 5

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


# ============================================================
# v2 策略 PRESET 定義
# ============================================================

CAPITAL_STRUCTURE_PRESETS = {
    "自有資金開發": {
        "total_budget_twd": 50_000_000_000,
        "annual_cost_of_capital": 0.03,
        "payback_tolerance_years": 10,
        "financial_stress_sensitivity": "high",
        "refinancing_risk": False,
    },
    "壽險資金合作": {
        "total_budget_twd": 130_000_000_000,
        "annual_cost_of_capital": 0.025,
        "payback_tolerance_years": 30,
        "financial_stress_sensitivity": "low",
        "refinancing_risk": False,
    },
    "專案融資（銀行貸款）": {
        "total_budget_twd": 80_000_000_000,
        "annual_cost_of_capital": 0.05,
        "payback_tolerance_years": 7,
        "financial_stress_sensitivity": "very_high",
        "refinancing_risk": True,
    },
    "混合模式（壽險+自有+銀行）": {
        "total_budget_twd": 100_000_000_000,
        "annual_cost_of_capital": 0.035,
        "payback_tolerance_years": 20,
        "financial_stress_sensitivity": "medium",
        "refinancing_risk": False,
    },
}

DEPOSIT_MODEL_PRESETS = {
    "全額可退（90%退還）": {
        "refund_percentage": 0.90,
        "refund_condition": "new_occupant",
        "deposit_amount_multiplier": 1.0,
        "squeeze_risk": "high",
        "amortization_years": 0,
        "monthly_fee_multiplier": 1.0,
    },
    "部分可退（50%退還）": {
        "refund_percentage": 0.50,
        "refund_condition": "on_exit",
        "deposit_amount_multiplier": 1.0,
        "squeeze_risk": "medium",
        "amortization_years": 0,
        "monthly_fee_multiplier": 1.0,
    },
    "漸進償卻（Benesse模式）": {
        "refund_percentage": 0.70,
        "refund_condition": "amortized",
        "deposit_amount_multiplier": 1.1,
        "squeeze_risk": "low",
        "amortization_years": 5,
        "monthly_fee_multiplier": 1.0,
    },
    "不可退但低押金": {
        "refund_percentage": 0.0,
        "deposit_amount_multiplier": 0.25,
        "squeeze_risk": "none",
        "amortization_years": 0,
        "monthly_fee_multiplier": 1.3,
    },
}

EXPERIENCE_PRESETS = {
    "基礎（樣品屋+說明會）": {
        "experience_level": 0.5,
        "experience_monthly_cost": 2_000_000,
        "conversion_boost": 1.05,
        "h_hotel_funnel_active": False,
        "resort_revenue": 0,
    },
    "中度（H會館短住體驗）": {
        "experience_level": 1.5,
        "experience_monthly_cost": 8_000_000,
        "conversion_boost": 1.20,
        "h_hotel_funnel_active": True,
        "resort_revenue": 0,
    },
    "深度（太保樂養式度假轉化）": {
        "experience_level": 2.5,
        "experience_monthly_cost": 20_000_000,
        "conversion_boost": 1.40,
        "h_hotel_funnel_active": True,
        "resort_revenue": 5_000_000,
    },
    "極致（The Villages式沉浸體驗）": {
        "experience_level": 3.0,
        "experience_monthly_cost": 50_000_000,
        "conversion_boost": 1.60,
        "h_hotel_funnel_active": True,
        "resort_revenue": 15_000_000,
    },
}

MEDICAL_PRESETS = {
    "1 - 園區內基本診所": {
        "medical_integration": 1,
        "medical_setup_cost": 50_000_000,
        "medical_monthly_cost": 3_000_000,
        "medical_occupancy_boost": 1.0,
        "medical_brand_trust_boost": 0,
        "care_transfer_internal": False,
    },
    "2 - 區域醫院合作": {
        "medical_integration": 2,
        "medical_setup_cost": 200_000_000,
        "medical_monthly_cost": 8_000_000,
        "medical_occupancy_boost": 1.15,
        "medical_brand_trust_boost": 5,
        "care_transfer_internal": False,
    },
    "3 - 醫學中心級園區內醫院": {
        "medical_integration": 3,
        "medical_setup_cost": 800_000_000,
        "medical_monthly_cost": 25_000_000,
        "medical_occupancy_boost": 1.30,
        "medical_brand_trust_boost": 15,
        "care_transfer_internal": True,
    },
}

ONSEN_PRESETS = {
    "無（不設溫泉設施）": {
        "has_onsen": False,
        "onsen_cost_multiplier": 1.0,
        "onsen_setup_cost": 0,
        "brand_differentiation_boost": 0,
        "onsen_external_revenue": 0,
    },
    "基礎（公共浴場+SPA）": {
        "has_onsen": True,
        "onsen_cost_multiplier": 1.5,
        "onsen_setup_cost": 300_000_000,
        "brand_differentiation_boost": 0.10,
        "onsen_external_revenue": 2_000_000,
    },
    "高規格（湯屋+對外營業）": {
        "has_onsen": True,
        "onsen_cost_multiplier": 1.8,
        "onsen_setup_cost": 800_000_000,
        "brand_differentiation_boost": 0.20,
        "onsen_external_revenue": 10_000_000,
    },
}

OPERATOR_PRESETS = {
    "自行營運（華友聯團隊）": {
        "initial_operational_capability": 20,
        "learning_rate": 0.8,
        "staff_turnover_rate": 0.15,
        "suao_labor_premium": 1.20,
        "service_quality_cap": 100,
        "operator_cost_share": 0,
    },
    "外包物業管理公司": {
        "initial_operational_capability": 35,
        "learning_rate": 0.5,
        "staff_turnover_rate": 0.20,
        "suao_labor_premium": 1.15,
        "service_quality_cap": 60,
        "operator_cost_share": 0,
    },
    "專業養老營運商": {
        "initial_operational_capability": 60,
        "learning_rate": 1.2,
        "staff_turnover_rate": 0.10,
        "suao_labor_premium": 1.10,
        "service_quality_cap": 100,
        "operator_cost_share": 0.05,
    },
    "合資營運公司（萬科模式）": {
        "initial_operational_capability": 55,
        "learning_rate": 1.5,
        "staff_turnover_rate": 0.08,
        "suao_labor_premium": 1.08,
        "service_quality_cap": 100,
        "operator_cost_share": 0.08,
    },
}

MACRO_PRESETS = {
    "穩定增長（衰退機率3%/年）": {
        "recession_annual_prob": 0.03,
        "recession_severity": 0.7,
    },
    "溫和波動（歷史平均5%/年）": {
        "recession_annual_prob": 0.05,
        "recession_severity": 0.6,
    },
    "高波動（衰退機率8%/年）": {
        "recession_annual_prob": 0.08,
        "recession_severity": 0.5,
    },
}

REGULATORY_PRESETS = {
    "維持現狀（無CCRC專法）": {
        "regulatory_protection": 0,
        "regulation_start_year": 99,
        "voluntary_trust_brand_value": 2.0,
        "compliance_cost_annual": 0,
        "mandatory_reserve_ratio": 0,
    },
    "5年內出台基本規範": {
        "regulatory_protection": 1,
        "regulation_start_year": 5,
        "voluntary_trust_brand_value": 1.5,
        "compliance_cost_annual": 10_000_000,
        "mandatory_reserve_ratio": 0,
    },
    "10年內達佛羅里達等級": {
        "regulatory_protection": 3,
        "regulation_start_year": 10,
        "voluntary_trust_brand_value": 1.0,
        "compliance_cost_annual": 30_000_000,
        "mandatory_reserve_ratio": 0.50,
    },
}

AGING_COUNTERMEASURE_EFFECTS = {
    "序列開發（每7-10年新產品線）": {
        "brand_vitality_decay_reduction": 0.30,
        "new_resident_avg_age_reduction": 3,
        "additional_cost_per_cycle": 500_000_000,
    },
    "物理區隔（自立棟/介護棟分開）": {
        "brand_vitality_decay_reduction": 0.20,
        "new_resident_avg_age_reduction": 0,
        "additional_cost_per_cycle": 0,
    },
    "年齡漸進式定價（年輕者優惠）": {
        "brand_vitality_decay_reduction": 0.0,
        "new_resident_avg_age_reduction": 5,
        "additional_cost_per_cycle": 0,
    },
    "彈性會員（短住/度假會員）": {
        "brand_vitality_decay_reduction": 0.15,
        "new_resident_avg_age_reduction": 0,
        "additional_cost_per_cycle": 0,
        "additional_monthly_revenue": 3_000_000,
    },
    "社區活動持續投入": {
        "brand_vitality_decay_reduction": 0.10,
        "new_resident_avg_age_reduction": 0,
        "additional_cost_per_cycle": 0,
        "additional_monthly_cost": 5_000_000,
    },
}

REVENUE_STREAM_ESTIMATES = {
    "商業地產出租": {
        "monthly_revenue": 8_000_000,
        "setup_cost": 500_000_000,
        "ramp_up_quarters": 8,
        "scales_with_occupancy": True,
    },
    "醫療健檢對外營業": {
        "monthly_revenue": 5_000_000,
        "setup_cost": 200_000_000,
        "ramp_up_quarters": 4,
        "scales_with_occupancy": False,
    },
    "度假旅居（太保樂養模式）": {
        "monthly_revenue": 12_000_000,
        "setup_cost": 300_000_000,
        "ramp_up_quarters": 6,
        "scales_with_occupancy": False,
    },
    "冷泉溫泉SPA對外營業": {
        "monthly_revenue": 10_000_000,
        "setup_cost": 400_000_000,
        "ramp_up_quarters": 4,
        "scales_with_occupancy": False,
        "requires_onsen": True,
    },
    "活動場地/會議中心出租": {
        "monthly_revenue": 3_000_000,
        "setup_cost": 150_000_000,
        "ramp_up_quarters": 4,
        "scales_with_occupancy": False,
    },
    "長照服務外部接案": {
        "monthly_revenue": 6_000_000,
        "setup_cost": 100_000_000,
        "ramp_up_quarters": 8,
        "scales_with_occupancy": False,
        "requires_ccrc": True,
    },
    "品牌授權/顧問服務": {
        "monthly_revenue": 2_000_000,
        "setup_cost": 20_000_000,
        "ramp_up_quarters": 12,
        "scales_with_occupancy": False,
        "requires_brand_trust": 60,
    },
}


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
