"""壓力測試情境定義"""

STRESS_SCENARIOS = {
    "mild_recession": {
        "name": "溫和衰退",
        "description": "入住率降至80%持續18個月",
        "overrides": {
            "macro_economic": 0.7,
            "duration_quarters": 6,
            "trigger_quarter": 12,
        },
    },
    "severe_recession": {
        "name": "嚴重衰退",
        "description": "入住率降至70%持續24個月 + 15%退費潮",
        "overrides": {
            "macro_economic": 0.4,
            "extra_refund_rate": 0.15,
            "duration_quarters": 8,
            "trigger_quarter": 12,
        },
    },
    "trust_crisis": {
        "name": "信任危機",
        "description": "重大負面事件，新入住歸零6個月，20%啟動退費",
        "overrides": {
            "new_move_in_multiplier": 0.0,
            "extra_refund_rate": 0.20,
            "brand_trust_shock": -40,
            "duration_quarters": 2,
            "trigger_quarter": 8,
        },
    },
    "cost_inflation": {
        "name": "成本通膨",
        "description": "營運成本年增8%持續3年",
        "overrides": {
            "cost_inflation_annual": 0.08,
            "duration_quarters": 12,
            "trigger_quarter": 16,
        },
    },
    "compound_disaster": {
        "name": "複合災難",
        "description": "嚴重衰退 + 成本通膨同時發生（Friendship Village情境）",
        "overrides": {
            "macro_economic": 0.4,
            "extra_refund_rate": 0.15,
            "cost_inflation_annual": 0.08,
            "duration_quarters": 8,
            "trigger_quarter": 12,
        },
    },
    "no_new_blood": {
        "name": "無新血存活測試",
        "description": "從某天起完全沒有新住戶，測試社區能存活多長時間",
        "overrides": {
            "new_move_in_multiplier": 0.0,
            "duration_quarters": 40,
            "trigger_quarter": 20,
        },
    },
}
