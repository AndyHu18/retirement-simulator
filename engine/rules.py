"""10 條交互規則的觸發邏輯"""

from __future__ import annotations
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .model import SimState
    from .parameters import SimParams


def evaluate_rules(state: 'SimState', params: 'SimParams') -> List[dict]:
    """評估所有規則，回傳觸發狀態列表"""
    results = []
    for rule in RULES:
        try:
            triggered = rule['check'](state, params)
        except Exception:
            triggered = False

        # 計算警告狀態（接近觸發）
        try:
            warning = rule.get('warning_check', lambda s, p: False)(state, params)
        except Exception:
            warning = False

        status = 'triggered' if triggered else ('warning' if warning else 'safe')
        results.append({
            'id': rule['id'],
            'name': rule['name'],
            'type': rule['type'],
            'severity': rule['severity'],
            'description': rule['description'],
            'status': status,
        })
    return results


RULES = [
    {
        "id": "R01",
        "name": "押金擠兌螺旋",
        "type": "death_spiral",
        "check": lambda state, params: (
            state.overall_occupancy_rate < 0.80
            and not params.trust_independent
            and state.fund_pool.run_rate_pressure > 0.8
        ),
        "warning_check": lambda state, params: (
            state.overall_occupancy_rate < 0.85
            and not params.trust_independent
            and state.fund_pool.run_rate_pressure > 0.5
        ),
        "severity": 10,
        "description": "入住率<80% + 無獨立信託 + 擠兌壓力指數>0.8",
    },
    {
        "id": "R02",
        "name": "增長飛輪",
        "type": "growth_flywheel",
        "check": lambda state, params: (
            state.overall_occupancy_rate > 0.85
            and state.brand_trust.value > 60
            and params.insurance_factor > 1.5
        ),
        "warning_check": lambda state, params: (
            state.overall_occupancy_rate > 0.80
            and state.brand_trust.value > 50
            and params.insurance_factor > 1.2
        ),
        "severity": 9,
        "description": "入住率>85% + 品牌信任>60 + 保險綁定啟動",
    },
    {
        "id": "R03",
        "name": "品牌老化時間炸彈",
        "type": "aging_bomb",
        "check": lambda state, params: (
            state.age_structure.median_age > 75
            and state.age_structure.brand_vitality_index < 50
        ),
        "warning_check": lambda state, params: (
            state.age_structure.median_age > 72
            and state.age_structure.brand_vitality_index < 60
        ),
        "severity": 8,
        "description": "住戶中位年齡>75 + 品牌活力指數<50",
    },
    {
        "id": "R04",
        "name": "信任資本飛輪",
        "type": "trust_flywheel",
        "check": lambda state, params: (
            params.trust_mechanism_level >= 2
            and state.brand_trust.value > 50
            and state.fund_pool.run_rate_pressure < 0.3
        ),
        "warning_check": lambda state, params: (
            params.trust_mechanism_level >= 1
            and state.brand_trust.value > 40
        ),
        "severity": 8,
        "description": "信託機制≥2級 + 品牌信任>50 + 擠兌壓力<0.3",
    },
    {
        "id": "R05",
        "name": "賣光沒住滿的空城陷阱",
        "type": "ghost_town",
        "check": lambda state, params: (
            state.sales_rate > 0.80
            and state.overall_occupancy_rate < 0.50
        ),
        "warning_check": lambda state, params: (
            state.sales_rate > 0.70
            and state.overall_occupancy_rate < 0.60
        ),
        "severity": 7,
        "description": "銷售率>80% 但實際入住率<50%",
    },
    {
        "id": "R06",
        "name": "規模×缺陷放大",
        "type": "scale_amplifier",
        "check": lambda state, params: (
            state.total_active_units > 1000
            and (
                not params.trust_independent
                or params.insurance_factor < 1.5
                or state.overall_occupancy_rate < 0.75
            )
        ),
        "warning_check": lambda state, params: (
            state.total_active_units > 800
            and (
                not params.trust_independent
                or params.insurance_factor < 1.5
            )
        ),
        "severity": 9,
        "description": "活躍戶數>1000 且 任一核心因素有缺陷",
    },
    {
        "id": "R07",
        "name": "醫療×品牌張力",
        "type": "tension",
        "check": lambda state, params: (
            params.medical_integration < 2
            and params.debranding_level > 2
        ),
        "warning_check": lambda state, params: (
            params.medical_integration < 2
            and params.debranding_level >= 2
        ),
        "severity": 6,
        "description": "醫療整合不足 但 去標籤化過於激進",
    },
    {
        "id": "R08",
        "name": "蘇澳距離摩擦",
        "type": "friction",
        "check": lambda state, params: (
            params.location == 'suao'
            and params.experience_level < 1
            and params.community_self_sufficiency < 2
        ),
        "warning_check": lambda state, params: (
            params.location == 'suao'
            and (params.experience_level < 2
                 or params.community_self_sufficiency < 2)
        ),
        "severity": 5,
        "description": "蘇澳選址 + 體驗機制不足 + 園區配套不完整",
    },
    {
        "id": "R09",
        "name": "營運能力缺口",
        "type": "capability_gap",
        "check": lambda state, params: (
            state.operational_capability.value < 40
            and state.overall_occupancy_rate > 0.50
        ),
        "warning_check": lambda state, params: (
            state.operational_capability.value < 50
            and state.overall_occupancy_rate > 0.40
        ),
        "severity": 7,
        "description": "營運能力<40 但已有大量住戶（服務品質風險）",
    },
    {
        "id": "R10",
        "name": "保險飛輪台灣適配",
        "type": "strategic_dependency",
        "check": lambda state, params: (
            params.insurance_factor < 1.5
            and state.total_active_units > 500
        ),
        "warning_check": lambda state, params: (
            params.insurance_factor < 1.5
            and state.total_active_units > 300
        ),
        "severity": 8,
        "description": "無保險綁定 且 規模已超過500戶",
    },
]
