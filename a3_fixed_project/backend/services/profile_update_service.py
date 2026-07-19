"""画像更新服务 - 可解释的画像更新闭环

更新公式（基于加权平均的贝叶斯风格更新）:
    new_mastery = (1 - α) * old_mastery + α * weighted_evidence_score
    其中 α = min(0.3, 0.1 + 0.05 * evidence_count) 学习率

更新画像：
    knowledge_mastery = mean(node_mastery for all nodes)
    response_speed = 1 - mean(response_time_ms) / MAX_TIME_MS
    learning_stability = 1 - std(recent_normalized_scores)
"""
from datetime import datetime
import json
import math
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from models.database_models import (
    LearningEvidence, StudentProfile, KnowledgeNode, Subject,
    ProfileSnapshot, StudyPlan
)
from services.evidence_service import EvidenceService


# 学习率上限和默认值
LEARNING_RATE_MAX = 0.3
LEARNING_RATE_BASE = 0.1
LEARNING_RATE_STEP = 0.05

# 响应时间归一化（最大10分钟）
MAX_RESPONSE_TIME_MS = 600_000


class ProfileUpdateError(Exception):
    """画像更新异常"""
    pass


class ProfileUpdateService:
    """可解释的画像更新服务"""

    def __init__(self, db: Session):
        self.db = db
        self.evidence_service = EvidenceService(db)

    def _compute_learning_rate(self, evidence_count: int) -> float:
        """根据证据数量计算学习率（证据越多，单条影响越小）"""
        alpha = LEARNING_RATE_BASE + LEARNING_RATE_STEP * min(evidence_count, 4)
        return min(alpha, LEARNING_RATE_MAX)

    def _compute_evidence_weight(
        self, evidence: LearningEvidence
    ) -> float:
        """计算单条证据的权重（类型权重 × 时效衰减）"""
        type_weight = EvidenceService.EVIDENCE_WEIGHTS.get(
            evidence.evidence_type, 0.5
        )
        # 时效衰减：30天内全权重，超过30天按对数衰减
        age_days = (datetime.utcnow() - evidence.created_at).days if evidence.created_at else 0
        if age_days <= 30:
            decay = 1.0
        else:
            decay = 1.0 / math.log2(age_days + 1)
        # 提示次数惩罚：提示越多权重越低
        hint_penalty = max(0.3, 1.0 - 0.1 * (evidence.hint_count or 0))
        # 尝试次数惩罚：多次尝试权重降低
        attempt_penalty = 1.0 / (evidence.attempt_count or 1)
        return type_weight * decay * hint_penalty * attempt_penalty

    def _update_node_mastery(
        self, old_mastery: float, evidences: List[LearningEvidence]
    ) -> Tuple[float, Dict[str, Any]]:
        """更新单个知识点的掌握度"""
        if not evidences:
            return old_mastery, {"formula": "no_evidence", "evidence_count": 0}

        # 加权平均
        total_weight = 0.0
        weighted_score = 0.0
        evidence_details = []
        for ev in evidences:
            w = self._compute_evidence_weight(ev)
            s = ev.normalized_score if ev.normalized_score is not None else 0.0
            if ev.is_correct is True:
                s = max(s, 0.6)
            elif ev.is_correct is False:
                s = min(s, 0.4)
            weighted_score += w * s
            total_weight += w
            evidence_details.append({
                "evidence_id": ev.id,
                "evidence_type": ev.evidence_type,
                "score": ev.score,
                "max_score": ev.max_score,
                "normalized_score": ev.normalized_score,
                "is_correct": ev.is_correct,
                "weight": round(w, 4),
            })

        if total_weight == 0:
            return old_mastery, {"formula": "no_valid_evidence", "evidence_count": len(evidences)}

        avg_score = weighted_score / total_weight
        alpha = self._compute_learning_rate(len(evidences))
        new_mastery = (1 - alpha) * old_mastery + alpha * avg_score
        new_mastery = max(0.0, min(1.0, new_mastery))

        return new_mastery, {
            "formula": "new = (1-α)*old + α*weighted_avg",
            "alpha": round(alpha, 4),
            "old_mastery": round(old_mastery, 4),
            "new_mastery": round(new_mastery, 4),
            "weighted_avg_score": round(avg_score, 4),
            "total_weight": round(total_weight, 4),
            "evidence_count": len(evidences),
            "evidence_details": evidence_details,
        }

    def update_profile(
        self, user_id: int, knowledge_node_ids: Optional[List[int]] = None,
        reason: str = ""
    ) -> Dict[str, Any]:
        """更新画像并记录快照

        Args:
            user_id: 学生ID
            knowledge_node_ids: 指定更新的知识点ID列表，None表示全部
            reason: 更新原因

        Returns:
            更新结果详情（含更新前/后画像、使用的证据、公式等）
        """
        # 1. 获取当前画像
        profile = self.db.query(StudentProfile).filter(
            StudentProfile.student_id == user_id
        ).first()
        if not profile:
            raise ProfileUpdateError("学生画像不存在: user_id=" + str(user_id))

        old_profile = {
            "knowledge_mastery": profile.knowledge_mastery,
            "learning_stability": profile.learning_stability,
            "response_speed": profile.response_speed,
            "emotional_state": profile.emotional_state,
            "profile_version": profile.profile_version,
            "weak_points_count": len(profile.weak_points or []),
        }

        # 2. 获取需要更新的知识点
        query = self.db.query(KnowledgeNode).filter(
            KnowledgeNode.subject_id.in_(
                self.db.query(Subject.id).filter(Subject.id == KnowledgeNode.subject_id)
            )
        )
        if knowledge_node_ids:
            query = query.filter(KnowledgeNode.id.in_(knowledge_node_ids))

        all_nodes = query.all()
        node_updates = []
        new_knowledge_states = dict(profile.knowledge_states or {})

        # 3. 对每个知识点计算新掌握度
        for node in all_nodes:
            # 获取该节点最近50条证据
            evidences = self.evidence_service.get_user_node_evidence(
                user_id, node.id, limit=50
            )
            if not evidences:
                continue

            # 从knowledge_states中取旧掌握度
            old_node_mastery = (profile.knowledge_states or {}).get(
                str(node.id), {}
            ).get("mastery", 0.0) if isinstance(
                (profile.knowledge_states or {}).get(str(node.id)), dict
            ) else 0.0

            new_mastery, detail = self._update_node_mastery(
                old_node_mastery, evidences
            )

            # 更新knowledge_states
            new_knowledge_states[str(node.id)] = {
                "mastery": round(new_mastery, 4),
                "last_updated": datetime.utcnow().isoformat(),
                "evidence_count": len(evidences),
            }

            node_updates.append({
                "node_id": node.id,
                "node_code": node.node_code,
                "node_name": node.name,
                "old_mastery": round(old_node_mastery, 4),
                "new_mastery": round(new_mastery, 4),
                "delta": round(new_mastery - old_node_mastery, 4),
                "update_detail": detail,
            })

        # 4. 重新计算画像整体指标
        if node_updates:
            new_masteries = [nu["new_mastery"] for nu in node_updates]
            new_knowledge_mastery = sum(new_masteries) / len(new_masteries)
        else:
            new_knowledge_mastery = profile.knowledge_mastery

        # 响应速度：基于最近证据
        recent_evidences = self.evidence_service.get_user_evidence(
            user_id, limit=20
        )
        if recent_evidences:
            avg_rt = sum(e.response_time_ms or 0 for e in recent_evidences) / len(recent_evidences)
            new_response_speed = max(0.0, min(1.0, 1.0 - avg_rt / MAX_RESPONSE_TIME_MS))
            # 学习稳定性：最近分数的标准差（越小越稳定）
            scores = [e.normalized_score or 0.0 for e in recent_evidences]
            if len(scores) > 1:
                mean_s = sum(scores) / len(scores)
                variance = sum((s - mean_s) ** 2 for s in scores) / len(scores)
                std_s = math.sqrt(variance)
                new_stability = max(0.0, min(1.0, 1.0 - std_s))
            else:
                new_stability = profile.learning_stability
        else:
            new_response_speed = profile.response_speed
            new_stability = profile.learning_stability

        # 5. 更新画像
        new_profile_version = (profile.profile_version or 0) + 1
        profile.knowledge_mastery = new_knowledge_mastery
        profile.learning_stability = new_stability
        profile.response_speed = new_response_speed
        profile.knowledge_states = new_knowledge_states
        profile.profile_version = new_profile_version
        profile.updated_at = datetime.utcnow()

        # 更新弱知识点
        weak_nodes = []
        for nu in node_updates:
            if nu["new_mastery"] < 0.6:
                weak_nodes.append({
                    "node_id": nu["node_id"],
                    "node_code": nu["node_code"],
                    "name": nu["node_name"],
                    "mastery": nu["new_mastery"],
                })
        profile.weak_points = weak_nodes[:20]  # 最多保留20个

        # 6. 记录画像快照（含完整更新链）
        new_profile_data = {
            "knowledge_mastery": new_knowledge_mastery,
            "learning_stability": new_stability,
            "response_speed": new_response_speed,
            "emotional_state": profile.emotional_state,
            "profile_version": new_profile_version,
            "weak_points_count": len(weak_nodes),
        }

        # 7. 调整受影响的学习计划
        affected_plans = self._adjust_study_plans(user_id, new_profile_version, weak_nodes)

        snapshot = ProfileSnapshot(
            student_id=user_id,
            profile_id=profile.id,
            knowledge_mastery=new_knowledge_mastery,
            learning_stability=new_stability,
            response_speed=new_response_speed,
            emotional_state=profile.emotional_state,
            weak_points_count=len(weak_nodes),
            profile_version_before=old_profile["profile_version"],
            profile_version_after=new_profile_version,
            update_reason=reason or "学习证据触发自动更新",
            evidence_summary=node_updates,
            affected_plans=affected_plans,
            correct_total=sum(1 for e in recent_evidences if e.is_correct),
            error_total=sum(1 for e in recent_evidences if e.is_correct is False),
        )
        self.db.add(snapshot)

        # 8. 回写证据的profile_version_after
        for nu in node_updates:
            for ev_detail in nu["update_detail"].get("evidence_details", []):
                self.db.query(LearningEvidence).filter(
                    LearningEvidence.id == ev_detail["evidence_id"]
                ).update({"profile_version_after": new_profile_version})

        self.db.commit()

        return {
            "user_id": user_id,
            "old_profile": old_profile,
            "new_profile": new_profile_data,
            "updated_nodes_count": len(node_updates),
            "node_updates": node_updates,
            "affected_plans": affected_plans,
            "snapshot_id": snapshot.id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _adjust_study_plans(
        self, user_id: int, new_version: int, weak_nodes: List[Dict]
    ) -> List[Dict]:
        """调整受影响的学习计划"""
        affected = []
        # 找出活跃的学习计划
        plans = self.db.query(StudyPlan).filter(
            and_(
                StudyPlan.student_id == user_id,
                StudyPlan.status.in_(["pending", "active"])
            )
        ).all()

        for plan in plans:
            old_weak = plan.weak_points or []
            old_weak_ids = set(wp.get("node_id") for wp in old_weak if isinstance(wp, dict))
            new_weak_ids = set(wn["node_id"] for wn in weak_nodes)
            
            # 如果弱知识点集合发生变化，标记计划需要调整
            if old_weak_ids != new_weak_ids:
                affected.append({
                    "plan_id": plan.id,
                    "title": plan.title,
                    "old_profile_version": plan.profile_version,
                    "new_profile_version": new_version,
                    "change_type": "weak_points_updated",
                    "added": list(new_weak_ids - old_weak_ids),
                    "removed": list(old_weak_ids - new_weak_ids),
                })
                # 更新计划的弱知识点和画像版本
                plan.weak_points = weak_nodes[:20]
                plan.profile_version = new_version

        self.db.flush()
        return affected


def get_profile_update_service(db: Optional[Session] = None) -> ProfileUpdateService:
    if db is None:
        from database import SessionLocal
        db = SessionLocal()
    return ProfileUpdateService(db)
