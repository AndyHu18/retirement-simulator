"""存量-流量模型核心引擎"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import numpy as np

from .parameters import (
    SimParams, PhaseConfig,
    MORTALITY_TABLE, CARE_TRANSFER_TABLE,
    interpolate_table,
)


# ============================================================
# 存量 1：住戶池（每期獨立）
# ============================================================

@dataclass
class PhaseOccupancy:
    phase_index: int
    total_units: int
    occupied: float = 0.0
    avg_resident_age: float = 65.0
    is_active: bool = False
    activation_step: int = -1
    last_new_move_ins: float = 0.0
    last_exits: float = 0.0

    @property
    def occupancy_rate(self) -> float:
        if self.total_units <= 0:
            return 0.0
        return self.occupied / self.total_units

    def activate(self, t: int):
        self.is_active = True
        self.activation_step = t


# ============================================================
# 存量 2：資金池（四個子池）
# ============================================================

@dataclass
class FundPool:
    deposit_trust: float = 0.0
    operating_cash: float = 500_000_000  # 初始營運資金 5 億
    capex_reserve: float = 2_000_000_000  # 初始資本支出 20 億
    emergency_reserve: float = 200_000_000  # 初始應急 2 億
    pending_refund_total: float = 0.0
    unfulfilled_refund: float = 0.0
    last_quarterly_operating_cost: float = 0.0
    expected_12m_new_deposits: float = 0.0

    @property
    def total(self) -> float:
        return (self.deposit_trust + self.operating_cash
                + self.capex_reserve + self.emergency_reserve)

    @property
    def days_cash_on_hand(self) -> float:
        daily_cost = self.last_quarterly_operating_cost / 90
        if daily_cost <= 0:
            return 999.0
        return self.emergency_reserve / daily_cost

    @property
    def run_rate_pressure(self) -> float:
        available = self.deposit_trust + self.expected_12m_new_deposits
        if available <= 0:
            return 10.0
        return self.pending_refund_total / max(available, 1)

    def step(self, inflows: dict, outflows: dict, params: SimParams):
        # --- 子池 1：押金信託 ---
        new_deposits = inflows.get('new_deposits', 0)
        refund_requests = outflows.get('refund_requests', 0)

        if params.trust_independent:
            actual_refund = min(refund_requests, self.deposit_trust * 0.1)
        else:
            actual_refund = min(refund_requests, self.deposit_trust + self.operating_cash)

        self.deposit_trust = max(0, self.deposit_trust + new_deposits - actual_refund)
        self.unfulfilled_refund = max(0, refund_requests - actual_refund)
        self.pending_refund_total = max(0, self.pending_refund_total
                                        + refund_requests - actual_refund)

        # --- 子池 2：營運現金流 ---
        monthly_fees = inflows.get('monthly_fees', 0)
        other_revenue = inflows.get('other_revenue', 0)
        operating_cost = outflows.get('operating_cost', 0)
        self.last_quarterly_operating_cost = operating_cost

        self.operating_cash += monthly_fees + other_revenue - operating_cost

        # 如果非獨立信託且退費從營運現金支付
        if not params.trust_independent and actual_refund > new_deposits:
            overflow = actual_refund - new_deposits
            self.operating_cash -= overflow

        # --- 子池 3：資本支出 ---
        maintenance = outflows.get('maintenance', 0)
        new_phase_cost = outflows.get('new_phase_construction', 0)
        self.capex_reserve = max(0, self.capex_reserve - maintenance - new_phase_cost)

        # --- 子池 4：應急儲備 ---
        quarterly_surplus = self.operating_cash - operating_cost
        if quarterly_surplus > 0:
            transfer = quarterly_surplus * 0.2
            self.emergency_reserve += transfer
            self.operating_cash -= transfer

        # 保護：不允許負值（除了 operating_cash 可以為負代表虧損）
        self.deposit_trust = max(0, self.deposit_trust)
        self.capex_reserve = max(0, self.capex_reserve)
        self.emergency_reserve = max(0, self.emergency_reserve)


# ============================================================
# 存量 3：品牌信任 (0-100)
# ============================================================

@dataclass
class BrandTrust:
    value: float = 30.0
    recovery_debt: float = 0.0

    def step(self, occupancy_rate: float, trust_level: int,
             years_since_open: float, avg_resident_age: float,
             random_event_trigger: bool, unfulfilled_refund: bool,
             rng: np.random.Generator):
        # === 流入 ===
        if occupancy_rate > 0.85:
            word_of_mouth = 2.0
        elif occupancy_rate > 0.70:
            word_of_mouth = 0.5
        else:
            word_of_mouth = -1.0

        trust_mechanism_boost = trust_level * 1.5
        media_boost = max(0, 3.0 - years_since_open * 0.3)

        # === 流出 ===
        natural_decay = 0.5

        if avg_resident_age > 75:
            aging_decay = (avg_resident_age - 75) * 0.3
        else:
            aging_decay = 0

        # === 離散事件衝擊 ===
        event_damage = 0.0
        if random_event_trigger:
            event_damage = rng.uniform(10, 30)
            self.recovery_debt += event_damage

        recovery = self.recovery_debt * 0.04
        self.recovery_debt = max(0, self.recovery_debt - recovery)

        # === 更新 ===
        delta = (word_of_mouth + trust_mechanism_boost + media_boost
                 - natural_decay - aging_decay + recovery)
        self.value = max(0, min(100, self.value + delta))

        # 退費未兌現 → 信任崩潰
        if unfulfilled_refund:
            self.value *= 0.8


# ============================================================
# 存量 4：住戶年齡結構
# ============================================================

@dataclass
class AgeStructure:
    cohorts: Dict[int, dict] = field(default_factory=dict)
    current_year: float = 0.0

    def add_cohort(self, year: float, count: float, avg_entry_age: float = 65.0):
        key = round(year, 2)
        if key in self.cohorts:
            self.cohorts[key]['count'] += count
        else:
            self.cohorts[key] = {'count': count, 'entry_age': avg_entry_age}

    def remove_residents(self, count: float):
        """按比例從各世代移除（退出/死亡）"""
        total = self.total_residents
        if total <= 0 or count <= 0:
            return
        ratio = min(1.0, count / total)
        for key in self.cohorts:
            self.cohorts[key]['count'] = max(0, self.cohorts[key]['count'] * (1 - ratio))

    @property
    def total_residents(self) -> float:
        return sum(c['count'] for c in self.cohorts.values())

    def get_current_ages(self) -> List[float]:
        ages = []
        for entry_year, info in self.cohorts.items():
            if info['count'] < 0.5:
                continue
            current_age = info['entry_age'] + (self.current_year - entry_year)
            ages.extend([current_age] * int(round(info['count'])))
        return ages

    @property
    def median_age(self) -> float:
        ages = self.get_current_ages()
        if not ages:
            return 65.0
        return float(np.median(ages))

    @property
    def brand_vitality_index(self) -> float:
        return self.calc_brand_vitality()

    def calc_brand_vitality(self, decay_reduction: float = 0.0) -> float:
        """品牌活力指數，支援老化對抗減幅"""
        ages = self.get_current_ages()
        if not ages:
            return 100.0
        median = np.median(ages)
        pct_over_80 = sum(1 for a in ages if a > 80) / len(ages)
        base_decay = max(0, median - 70) * 5 + pct_over_80 * 100
        modified_decay = base_decay * (1 - min(0.70, decay_reduction))
        return max(0, 100 - modified_decay)


# ============================================================
# 存量 5：營運能力 (0-100)
# ============================================================

@dataclass
class OperationalCapability:
    value: float = 20.0

    def step(self, team_quality: float, staff_turnover_rate: float,
             location: str):
        learning = 1.0 * team_quality
        turnover_loss = staff_turnover_rate * 2
        labor_penalty = 0.3 if location == 'suao' else 0.0
        self.value = max(0, min(100, self.value + learning - turnover_loss - labor_penalty))


# ============================================================
# 存量 6：外部環境
# ============================================================

@dataclass
class ExternalEnvironment:
    macro_economic: float = 1.0
    cultural_acceptance: float = 0.05
    competitor_pressure: float = 0.0
    recession_counter: int = 0

    def step(self, rng: np.random.Generator):
        # 文化接受度年增 1.5-2.5 百分點（季度化）
        self.cultural_acceptance += rng.uniform(0.015, 0.025) / 4
        self.cultural_acceptance = min(1.0, self.cultural_acceptance)

        # 經濟週期
        if self.recession_counter > 0:
            self.recession_counter -= 1
            self.macro_economic = 0.6
        elif rng.random() < 0.0125:  # 5%/年，季度化
            self.recession_counter = rng.integers(4, 9)
            self.macro_economic = 0.6
        else:
            self.macro_economic = min(1.0, self.macro_economic + 0.05)


# ============================================================
# 模擬狀態容器
# ============================================================

@dataclass
class SimState:
    t: int = 0
    phases: List[PhaseOccupancy] = field(default_factory=list)
    fund_pool: FundPool = field(default_factory=FundPool)
    brand_trust: BrandTrust = field(default_factory=BrandTrust)
    age_structure: AgeStructure = field(default_factory=AgeStructure)
    operational_capability: OperationalCapability = field(default_factory=OperationalCapability)
    environment: ExternalEnvironment = field(default_factory=ExternalEnvironment)
    triggered_rules: List[dict] = field(default_factory=list)

    @property
    def overall_occupancy_rate(self) -> float:
        active = [p for p in self.phases if p.is_active]
        if not active:
            return 0.0
        total_occupied = sum(p.occupied for p in active)
        total_units = sum(p.total_units for p in active)
        if total_units <= 0:
            return 0.0
        return total_occupied / total_units

    @property
    def total_active_units(self) -> int:
        return sum(p.total_units for p in self.phases if p.is_active)

    @property
    def total_occupied(self) -> float:
        return sum(p.occupied for p in self.phases if p.is_active)

    @property
    def sales_rate(self) -> float:
        """銷售率（已簽約/總戶數）- 簡化為入住率"""
        return self.overall_occupancy_rate


# ============================================================
# 流量計算
# ============================================================

def calc_new_move_ins(phase: PhaseOccupancy, all_phases: List[PhaseOccupancy],
                      brand_trust: float, insurance_factor: float,
                      experience_level: int, macro_shock: float,
                      distance_friction: float, params: SimParams) -> float:
    """計算單期新入住數"""
    target_pool = params.target_pool
    base_annual_rate = params.base_annual_conversion
    base_demand = target_pool * base_annual_rate / 4  # 季度化

    # 品牌信任係數（0-100 → 0-2）
    trust_factor = max(0, brand_trust / 50)

    # 保險管道係數
    ins_factor = insurance_factor

    # 冷啟動乘數
    total_occupied = sum(p.occupied for p in all_phases if p.is_active)
    tipping_point = 800
    if total_occupied < tipping_point:
        cold_start = max(0.2, (max(total_occupied, 1) / tipping_point) ** 0.5)
    else:
        cold_start = 1.0

    # 體驗轉化加成
    experience_boost = 1.0 + experience_level * 0.3

    # 計算
    raw = (base_demand * trust_factor * ins_factor * cold_start
           * macro_shock * distance_friction * experience_boost)

    # 不能超過該期空房的 15%
    available = phase.total_units - phase.occupied
    return max(0, min(raw, available * 0.15))


def calc_exits(phase: PhaseOccupancy) -> float:
    """計算單期退出數"""
    avg_age = phase.avg_resident_age

    annual_mortality = interpolate_table(MORTALITY_TABLE, avg_age)
    base_voluntary = 0.03
    annual_care_transfer = interpolate_table(CARE_TRANSFER_TABLE, avg_age)

    quarterly_exits = phase.occupied * (
        annual_mortality + base_voluntary + annual_care_transfer
    ) / 4

    return max(0, quarterly_exits)


def get_construction_cost(state: SimState, params: SimParams, t: int) -> float:
    """取得當前步需要支付的建設成本"""
    cost = 0.0
    for phase in state.phases:
        if phase.activation_step == t:
            idx = phase.phase_index
            if idx < len(params.phase_configs):
                cost += params.phase_configs[idx].construction_cost
    return cost


# ============================================================
# 分期啟動邏輯
# ============================================================

def check_phase_activation(state: SimState, params: SimParams, t: int):
    """只有前期達到入住率門檻且資金充足時，才啟動新期"""
    for i, phase in enumerate(state.phases):
        if phase.is_active or i >= len(params.phase_configs):
            continue

        # 首期 t=0 自動啟動
        if i == 0:
            phase.activate(t)
            continue

        prev_phase = state.phases[i - 1]
        if not prev_phase.is_active:
            continue

        conditions = [
            prev_phase.occupancy_rate >= params.phase_activation_threshold,
            state.fund_pool.days_cash_on_hand >= params.min_days_cash_for_new_phase,
            state.fund_pool.capex_reserve >= (
                params.phase_configs[i].construction_cost * params.capex_coverage_ratio
            ),
        ]

        if all(conditions):
            phase.activate(t)
            state.fund_pool.capex_reserve -= params.phase_configs[i].construction_cost


# ============================================================
# 主模擬步驟
# ============================================================

def simulation_step(state: SimState, params: SimParams, t: int,
                    rng: np.random.Generator,
                    stress_overrides: Optional[dict] = None) -> SimState:
    """一個季度的完整更新"""
    state.t = t

    # 應用壓力測試覆蓋
    effective_macro = state.environment.macro_economic
    new_move_in_multiplier = 1.0
    extra_refund_rate = 0.0
    cost_inflation_multiplier = 1.0
    brand_trust_shock = 0.0

    if stress_overrides:
        so = stress_overrides
        trigger_q = so.get('trigger_quarter', 0)
        duration_q = so.get('duration_quarters', 0)
        if trigger_q <= t < trigger_q + duration_q:
            if 'macro_economic' in so:
                effective_macro = so['macro_economic']
            if 'new_move_in_multiplier' in so:
                new_move_in_multiplier = so['new_move_in_multiplier']
            if 'extra_refund_rate' in so:
                extra_refund_rate = so['extra_refund_rate']
            if 'cost_inflation_annual' in so:
                years_in = (t - trigger_q) / 4
                cost_inflation_multiplier = (1 + so['cost_inflation_annual']) ** years_in
            if 'brand_trust_shock' in so and t == trigger_q:
                brand_trust_shock = so['brand_trust_shock']

    # v2: 保險通路上線時間 — 未上線前 insurance_factor 為 1.0
    effective_insurance = params.insurance_factor if t >= params.insurance_start_quarter else 1.0

    # v2: 行銷預算改善距離摩擦
    effective_friction = min(0.95, params.distance_friction + params.marketing_budget_monthly / 10_000_000 * 0.02)

    # v2: 競品衝擊
    competitor_active = (params.competitor_entry and t >= params.competitor_year * 4)
    if competitor_active and t == params.competitor_year * 4:
        state.brand_trust.value = max(0, state.brand_trust.value - params.competitor_brand_shock)

    # 1. 計算各存量的流入流出
    total_new_ins = 0.0
    total_exits = 0.0

    for phase in state.phases:
        if not phase.is_active:
            continue
        new_ins = calc_new_move_ins(
            phase=phase,
            all_phases=state.phases,
            brand_trust=state.brand_trust.value,
            insurance_factor=effective_insurance,
            experience_level=params.experience_level,
            macro_shock=effective_macro,
            distance_friction=effective_friction,
            params=params,
        )
        # v2: 體驗行銷轉化加成
        new_ins *= params.conversion_boost
        # v2: 醫療設施入住率加成
        new_ins *= params.medical_occupancy_boost
        # v2: 溫泉品牌差異化加成
        new_ins *= (1.0 + params.brand_differentiation_boost)
        # v2: 競品分流
        if competitor_active:
            new_ins *= (1.0 - params.competitor_diversion_rate)

        new_ins *= new_move_in_multiplier
        exits = calc_exits(phase)

        # 壓力測試額外退費
        if extra_refund_rate > 0:
            exits += phase.occupied * extra_refund_rate / 4

        phase.last_new_move_ins = new_ins
        phase.last_exits = exits
        phase.occupied = max(0, phase.occupied + new_ins - exits)
        phase.avg_resident_age += 0.25
        # v2: 新住戶年齡降低（老化對抗措施）
        if new_ins > 0 and params.new_resident_avg_age_reduction > 0:
            age_reduction_effect = params.new_resident_avg_age_reduction * new_ins / max(1, phase.occupied)
            phase.avg_resident_age = max(55, phase.avg_resident_age - age_reduction_effect)

        total_new_ins += new_ins
        total_exits += exits

    # 更新年齡結構
    if total_new_ins > 0:
        state.age_structure.add_cohort(t / 4, total_new_ins, avg_entry_age=65.0)
    if total_exits > 0:
        state.age_structure.remove_residents(total_exits)
    state.age_structure.current_year = t / 4

    # 2. 計算財務
    total_occupied = state.total_occupied
    occupancy_rate = state.overall_occupancy_rate

    monthly_fees = total_occupied * params.monthly_fee * params.monthly_fee_multiplier * 3
    new_deposits = total_new_ins * params.deposit_amount * params.deposit_amount_multiplier
    # v2: 漸進償卻模式 — 退費義務隨時間遞減
    if params.amortization_years > 0:
        avg_years_in = t / 4 / 2  # 粗略平均居住年數
        amort_factor = max(0, params.refund_percentage * (1 - avg_years_in / params.amortization_years))
        refund_requests = total_exits * params.deposit_amount * params.deposit_amount_multiplier * amort_factor
    else:
        refund_requests = total_exits * params.deposit_amount * params.deposit_amount_multiplier * params.refund_percentage

    # 營運成本
    staff_count = total_occupied * params.staff_ratio
    operating_cost = staff_count * params.avg_staff_cost_monthly * 3
    if params.has_onsen:
        operating_cost *= params.onsen_cost_multiplier
    if params.location == 'suao':
        operating_cost *= params.suao_labor_premium
    operating_cost *= cost_inflation_multiplier
    # v2: 醫療設施營運成本
    operating_cost += params.medical_monthly_cost * 3
    # v2: 體驗行銷成本
    operating_cost += params.experience_monthly_cost * 3
    # v2: 營運商分成
    if params.operator_cost_share > 0:
        operating_cost += monthly_fees * params.operator_cost_share
    # v2: 法規合規成本
    if t / 4 >= params.regulation_start_year:
        operating_cost += params.compliance_cost_annual / 4
    # v2: 行銷預算
    operating_cost += params.marketing_budget_monthly * 3
    # v2: 老化對抗成本
    operating_cost += params.aging_countermeasure_cost * 3

    # v2: 資本成本（利息）
    quarterly_capital_cost = params.total_budget_twd * params.annual_cost_of_capital / 4
    operating_cost += quarterly_capital_cost

    # v2: 轉貸風險（每 5 年檢查一次）
    if params.refinancing_risk and t > 0 and t % 20 == 0:
        if rng.random() < 0.10:
            params.annual_cost_of_capital = min(0.10, params.annual_cost_of_capital * 1.5)

    # 其他收入
    other_revenue = params.other_revenue_monthly * 3
    # v2: 溫泉對外營業收入
    other_revenue += params.onsen_external_revenue * 3
    # v2: 度假旅居收入
    other_revenue += params.resort_revenue * 3
    # v2: 醫療對外營業收入
    if params.medical_external_revenue:
        other_revenue += params.medical_integration * 5_000_000 * 3
    # v2: 老化對抗措施額外收入
    other_revenue += params.aging_countermeasure_revenue * 3
    # v2: 多元收入流（帶爬坡期）
    if hasattr(params, '_revenue_stream_configs'):
        for stream_cfg in params._revenue_stream_configs:
            quarters_active = t - stream_cfg.get('activation_quarter', 0)
            if quarters_active < 0:
                continue
            ramp = min(1.0, quarters_active / max(1, stream_cfg.get('ramp_up_quarters', 4)))
            rev = stream_cfg['monthly_revenue'] * ramp * 3
            if stream_cfg.get('scales_with_occupancy'):
                rev *= occupancy_rate
            if stream_cfg.get('requires_brand_trust', 0) > state.brand_trust.value:
                rev = 0
            other_revenue += rev
    # v2: H 會館客群導入（額外入住量，已在上面的 new_ins 裡處理）
    if params.h_hotel_funnel_active:
        h_hotel_quarterly = (params.h_hotel_annual_contacts
                             * params.h_hotel_inquiry_rate
                             * params.h_hotel_close_rate / 4)
        # H 會館帶來的額外押金收入
        other_revenue += h_hotel_quarterly * params.deposit_amount * params.deposit_amount_multiplier * 0.3  # 佔比估算

    construction_cost = get_construction_cost(state, params, t)

    state.fund_pool.expected_12m_new_deposits = new_deposits * 4

    state.fund_pool.step(
        inflows={
            'new_deposits': new_deposits,
            'monthly_fees': monthly_fees,
            'other_revenue': other_revenue,
        },
        outflows={
            'refund_requests': refund_requests,
            'operating_cost': operating_cost,
            'maintenance': params.maintenance_cost_quarterly,
            'new_phase_construction': construction_cost,
        },
        params=params,
    )

    # 3. 品牌信任衝擊
    if brand_trust_shock != 0:
        state.brand_trust.value = max(0, state.brand_trust.value + brand_trust_shock)

    # 4. 更新品牌信任
    state.brand_trust.step(
        occupancy_rate=occupancy_rate,
        trust_level=params.trust_mechanism_level,
        years_since_open=t / 4,
        avg_resident_age=state.age_structure.median_age,
        random_event_trigger=(rng.random() < 0.02),
        unfulfilled_refund=(state.fund_pool.unfulfilled_refund > 0),
        rng=rng,
    )

    # 5. 更新營運能力
    state.operational_capability.step(
        team_quality=params.team_quality,
        staff_turnover_rate=params.staff_turnover_rate,
        location=params.location,
    )

    # 6. 更新外部環境
    state.environment.step(rng)

    # 7. 檢查分期啟動
    check_phase_activation(state, params, t)

    return state


# ============================================================
# 初始化與執行
# ============================================================

def initialize_state(params: SimParams) -> SimState:
    """初始化模擬狀態"""
    state = SimState()

    # 建立各期
    for i, pc in enumerate(params.phase_configs):
        state.phases.append(PhaseOccupancy(
            phase_index=i,
            total_units=pc.units,
        ))

    # 設定初始值
    state.brand_trust.value = params.initial_brand_trust
    state.operational_capability.value = params.initial_operational_capability
    state.environment.cultural_acceptance = params.initial_cultural_acceptance

    if params.has_professional_operator:
        state.operational_capability.value = max(
            state.operational_capability.value, 50.0
        )

    return state


def run_simulation(params: SimParams, n_steps: int = 100,
                   seed: Optional[int] = None,
                   stress_overrides: Optional[dict] = None) -> dict:
    """執行單次完整模擬，回傳時間序列"""
    if seed is not None:
        rng = np.random.default_rng(seed)
    elif params.random_seed >= 0:
        rng = np.random.default_rng(params.random_seed)
    else:
        rng = np.random.default_rng()

    state = initialize_state(params)
    check_phase_activation(state, params, 0)

    results = {
        'occupancy_rate': np.zeros(n_steps),
        'fund_pool_total': np.zeros(n_steps),
        'brand_trust': np.zeros(n_steps),
        'brand_vitality': np.zeros(n_steps),
        'days_cash_on_hand': np.zeros(n_steps),
        'run_rate_pressure': np.zeros(n_steps),
        'operating_cash': np.zeros(n_steps),
        'total_occupied': np.zeros(n_steps),
        'total_active_units': np.zeros(n_steps),
        'operational_capability': np.zeros(n_steps),
        'cultural_acceptance': np.zeros(n_steps),
        'macro_economic': np.zeros(n_steps),
        'median_age': np.zeros(n_steps),
        'fund_depleted_step': -1,
    }

    for t in range(n_steps):
        state = simulation_step(state, params, t, rng, stress_overrides)

        results['occupancy_rate'][t] = state.overall_occupancy_rate
        results['fund_pool_total'][t] = state.fund_pool.total
        results['brand_trust'][t] = state.brand_trust.value
        results['brand_vitality'][t] = state.age_structure.calc_brand_vitality(params.brand_vitality_decay_reduction)
        results['days_cash_on_hand'][t] = state.fund_pool.days_cash_on_hand
        results['run_rate_pressure'][t] = state.fund_pool.run_rate_pressure
        results['operating_cash'][t] = state.fund_pool.operating_cash
        results['total_occupied'][t] = state.total_occupied
        results['total_active_units'][t] = state.total_active_units
        results['operational_capability'][t] = state.operational_capability.value
        results['cultural_acceptance'][t] = state.environment.cultural_acceptance
        results['macro_economic'][t] = state.environment.macro_economic
        results['median_age'][t] = state.age_structure.median_age

        if state.fund_pool.total <= 0 and results['fund_depleted_step'] == -1:
            results['fund_depleted_step'] = t

    results['final_state'] = state
    return results
