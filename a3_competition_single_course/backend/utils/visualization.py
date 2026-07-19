import json


def generate_radar_chart_data(profile) -> dict:
    return {
        "type": "radar",
        "data": {
            "labels": [
                "知识掌握",
                "学习稳定性",
                "反应速度",
                "错因健康度",
                "自主学习",
                "迁移能力",
                "情绪状态"
            ],
            "datasets": [{
                "label": "当前状态",
                "data": [
                    profile.knowledge_mastery,
                    profile.learning_stability,
                    profile.response_speed,
                    profile.error_pattern_score,
                    profile.self_driven_score,
                    profile.transfer_ability,
                    profile.emotional_state
                ],
                "backgroundColor": "rgba(54, 162, 235, 0.2)",
                "borderColor": "rgba(54, 162, 235, 1)",
                "borderWidth": 2
            }]
        },
        "options": {
            "scale": {
                "min": 0,
                "max": 100,
                "beginAtZero": True
            }
        }
    }


def generate_progress_chart(data: list[dict]) -> dict:
    return {
        "type": "line",
        "data": {
            "labels": [d["date"] for d in data],
            "datasets": [{
                "label": "正确率",
                "data": [d["accuracy"] for d in data],
                "fill": False,
                "borderColor": "rgba(75, 192, 192, 1)",
                "tension": 0.1
            }]
        }
    }


def generate_heatmap_data(knowledge_states: dict) -> dict:
    rows = []
    for kid, ks in knowledge_states.items():
        rows.append({
            "knowledge_point": ks.name,
            "mastery": ks.mastery,
            "error_count": ks.error_count,
            "correct_count": ks.correct_count
        })
    return {"rows": rows}