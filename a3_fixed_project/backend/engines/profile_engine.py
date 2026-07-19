from graph.state import LearningProfile, KnowledgeState, ErrorCause
from datetime import datetime
import json


class ProfileEngine:

    def __init__(self):
        self.profiles: dict[str, LearningProfile] = {}
        self._SessionLocal = None
        self._StudentProfile = None
        self._Student = None
        try:
            from database import SessionLocal
            self._SessionLocal = SessionLocal
        except Exception:
            self._SessionLocal = None
        try:
            from models.database_models import StudentProfile, Student
            self._StudentProfile = StudentProfile
            self._Student = Student
        except Exception:
            self._StudentProfile = None
            self._Student = None

    def _student_id_to_int(self, student_id):
        try:
            return int(student_id)
        except (TypeError, ValueError):
            return None

    def _resolve_db_student_id(self, session, student_id_str):
        """把字符串 student_id 解析为 Student.id。如果 student_id 本身就是数字,也能查到对应行。"""
        if self._Student is None:
            return None
        int_id = self._student_id_to_int(student_id_str)
        if int_id is not None:
            try:
                s = session.query(self._Student).filter(self._Student.id == int_id).first()
                if s:
                    return s.id
            except Exception:
                pass
        try:
            s = session.query(self._Student).filter(self._Student.username == str(student_id_str)).first()
            if s:
                return s.id
        except Exception:
            return None
        return None

    def _open_session(self):
        if self._SessionLocal is None:
            return None
        try:
            return self._SessionLocal()
        except Exception:
            return None

    def create_profile(self, student_id: str, grade: str = "", subject: str = "",
                       education_level: str = "high_school") -> LearningProfile:
        profile = LearningProfile(
            student_id=student_id,
            grade=grade,
            subject=subject,
            last_updated=datetime.now()
        )
        profile.education_level = education_level if hasattr(profile, "education_level") else None
        self.profiles[student_id] = profile
        self._upsert_db(profile, education_level=education_level)
        return profile

    def get_profile(self, student_id: str) -> LearningProfile | None:
        if student_id in self.profiles:
            return self.profiles[student_id]

        if self._SessionLocal is None or self._StudentProfile is None:
            return None

        session = self._open_session()
        if session is None:
            return None
        try:
            with session:
                sid = self._resolve_db_student_id(session, student_id)
                if sid is None:
                    return None
                row = session.query(self._StudentProfile).filter(
                    self._StudentProfile.student_id == sid
                ).first()
                if row is None:
                    return None
                profile = self.deserialize_profile(row, student_id)
                self.profiles[student_id] = profile
                return profile
        except Exception as e:
            print(f"[ProfileEngine] get_profile db error: {e}")
            return None

    def update_profile(self, student_id: str, updates: dict) -> LearningProfile | None:
        profile = self.get_profile(student_id)
        if not profile:
            return None

        profile_before = profile.to_radar_data()

        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        profile.last_updated = datetime.now()

        profile_diff = {
            "before": profile_before,
            "after": profile.to_radar_data(),
            "updated_at": profile.last_updated.isoformat()
        }
        profile.update_history.append(profile_diff)

        self._upsert_db(profile, education_level=getattr(profile, "education_level", "high_school"))
        return profile

    def update_knowledge_state(
        self,
        student_id: str,
        node_id: str,
        name: str,
        mastery_change: float = 0.0,
        correct: bool = False,
        error_cause: str | None = None
    ) -> LearningProfile | None:
        profile = self.get_profile(student_id)
        if not profile:
            return None

        if node_id not in profile.knowledge_states:
            profile.knowledge_states[node_id] = KnowledgeState(node_id=node_id, name=name)

        ks = profile.knowledge_states[node_id]

        if correct:
            ks.correct_count += 1
            ks.mastery = min(1.0, ks.mastery + 0.05)
            ks.stability = min(1.0, ks.stability + 0.02)
        else:
            ks.error_count += 1
            ks.mastery = max(0.0, ks.mastery - 0.03)
            ks.stability = max(0.0, ks.stability - 0.05)
            if error_cause:
                ks.primary_error_cause = error_cause
                profile.error_distribution[error_cause] = profile.error_distribution.get(error_cause, 0) + 1

        ks.last_practiced = datetime.now()

        self._recalculate_profile_dimensions(profile)

        self._upsert_db(profile, education_level=getattr(profile, "education_level", "high_school"))
        return profile

    def _recalculate_profile_dimensions(self, profile: LearningProfile):
        if not profile.knowledge_states:
            return

        total_mastery = sum(ks.mastery for ks in profile.knowledge_states.values())
        profile.knowledge_mastery = (total_mastery / len(profile.knowledge_states)) * 100

        total_correct = sum(ks.correct_count for ks in profile.knowledge_states.values())
        total_errors = sum(ks.error_count for ks in profile.knowledge_states.values())
        total_attempts = total_correct + total_errors
        
        if total_attempts > 0:
            accuracy = total_correct / total_attempts
            profile.learning_efficiency = min(100, accuracy * 80 + profile.learning_efficiency * 0.2)

        if profile.error_distribution:
            total_err_dist = sum(profile.error_distribution.values())
            max_errors = max(profile.error_distribution.values())
            profile.error_pattern_score = (1 - max_errors / max(total_err_dist, 1)) * 100

        avg_mastery = profile.knowledge_mastery / 100
        profile.learning_persistence = min(100, avg_mastery * 60 + profile.learning_persistence * 0.3 + 10)

        knowledge_count = len(profile.knowledge_states)
        high_mastery_count = sum(1 for ks in profile.knowledge_states.values() if ks.mastery > 0.7)
        if knowledge_count > 0:
            transfer_ratio = high_mastery_count / knowledge_count
            profile.transfer_ability = min(100, transfer_ratio * 80 + 20)

        low_mastery_nodes = [kid for kid, ks in profile.knowledge_states.items() if ks.mastery < 0.4]
        if hasattr(profile, 'prerequisite_gap'):
            profile.prerequisite_gap = min(100, len(low_mastery_nodes) / max(knowledge_count, 1) * 100)

        if not hasattr(profile, 'confidence_scores'):
            profile.confidence_scores = {}
        profile.confidence_scores.update({
            "knowledge_mastery": min(1.0, total_attempts / 10.0 + 0.5),
            "prerequisite_gap": min(1.0, knowledge_count / 5.0 + 0.3),
            "error_pattern_score": min(1.0, total_err_dist / 5.0 + 0.4) if profile.error_distribution else 0.5,
            "learning_efficiency": min(1.0, total_attempts / 8.0 + 0.4),
            "learning_persistence": min(1.0, profile.learning_persistence / 100.0 + 0.3),
            "learning_goals_constraints": 0.90 if profile.learning_goals_constraints else 0.3,
            "resource_preference": 0.70 if profile.resource_preference else 0.3,
        })

        if not hasattr(profile, 'evidence_sources'):
            profile.evidence_sources = {}
        profile.evidence_sources.update({
            "knowledge_mastery": f"共{total_attempts}次作答，正确率{round(accuracy*100) if total_attempts > 0 else 0}%" if total_attempts > 0 else "暂无作答记录",
            "prerequisite_gap": f"{len(low_mastery_nodes)}个知识点掌握度低于40%",
            "error_pattern_score": f"错误分布: {dict(profile.error_distribution)}" if profile.error_distribution else "暂无错误记录",
            "learning_efficiency": f"共{total_attempts}次作答",
            "learning_persistence": f"学习持续性评分: {round(profile.learning_persistence)}",
            "learning_goals_constraints": "用户设定的学习目标" if profile.learning_goals_constraints else "未设定学习目标",
            "resource_preference": "基于用户交互行为统计" if profile.resource_preference else "暂无交互数据",
        })

    def get_profile_history(self, student_id: str, limit: int = 10) -> list[dict]:
        profile = self.get_profile(student_id)
        if not profile:
            return []
        return profile.update_history[-limit:]

    def serialize_profile(self, profile: LearningProfile) -> dict:
        return {
            "student_id": profile.student_id,
            "knowledge_mastery": profile.knowledge_mastery,
            "prerequisite_gap": getattr(profile, "prerequisite_gap", 0.0),
            "error_pattern_score": profile.error_pattern_score,
            "learning_efficiency": getattr(profile, "learning_efficiency", 50.0),
            "learning_persistence": getattr(profile, "learning_persistence", 50.0),
            "learning_goals_constraints": getattr(profile, "learning_goals_constraints", {}),
            "resource_preference": getattr(profile, "resource_preference", {}),
            "emotional_state": profile.emotional_state,
            "cognitive_preference": profile.cognitive_preference,
            "self_driven_score": profile.self_driven_score,
            "transfer_ability": profile.transfer_ability,
            "confidence_scores": getattr(profile, "confidence_scores", {}),
            "evidence_sources": getattr(profile, "evidence_sources", {}),
            "knowledge_states": {
                kid: {
                    "node_id": ks.node_id,
                    "name": ks.name,
                    "mastery": ks.mastery,
                    "stability": ks.stability,
                    "error_count": ks.error_count,
                    "correct_count": ks.correct_count,
                }
                for kid, ks in profile.knowledge_states.items()
            },
            "error_distribution": profile.error_distribution,
            "grade": profile.grade,
            "subject": profile.subject,
            "subjects": profile.subjects,
            "learning_goal": profile.learning_goal,
            "weak_points": profile.weak_points,
            "last_updated": profile.last_updated.isoformat() if profile.last_updated else None,
            "update_history": profile.update_history,
        }

    def deserialize_profile(self, row, original_student_id: str) -> LearningProfile:
        profile = LearningProfile(
            student_id=original_student_id,
            grade=getattr(row, "grade", "") or "",
            subject=getattr(row, "education_level", "high_school") or "high_school",
            last_updated=datetime.now(),
        )
        if hasattr(profile, "education_level"):
            profile.education_level = getattr(row, "education_level", "high_school") or "high_school"
        profile.knowledge_mastery = float(getattr(row, "knowledge_mastery", 0.0) or 0.0)
        profile.prerequisite_gap = float(getattr(row, "prerequisite_gap", 0.0) or 0.0)
        profile.error_pattern_score = float(getattr(row, "error_pattern_score", 50.0) or 50.0)
        profile.learning_efficiency = float(getattr(row, "learning_efficiency", 50.0) or 50.0)
        profile.learning_persistence = float(getattr(row, "learning_persistence", 50.0) or 50.0)
        profile.emotional_state = float(getattr(row, "emotional_state", 70.0) or 70.0)
        profile.cognitive_preference = getattr(row, "cognitive_preference", "visual") or "visual"
        profile.learning_goal = getattr(row, "learning_goal", "") or ""
        
        profile.learning_goals_constraints = {}
        try:
            lgc_raw = row.learning_goals_constraints if isinstance(row.learning_goals_constraints, dict) else json.loads(
                row.learning_goals_constraints) if isinstance(row.learning_goals_constraints, str) else {}
            profile.learning_goals_constraints = lgc_raw
        except Exception:
            profile.learning_goals_constraints = {}
            
        profile.resource_preference = {}
        try:
            rp_raw = row.resource_preference if isinstance(row.resource_preference, dict) else json.loads(
                row.resource_preference) if isinstance(row.resource_preference, str) else {}
            profile.resource_preference = rp_raw
        except Exception:
            profile.resource_preference = {}
            
        profile.confidence_scores = {}
        try:
            cs_raw = row.confidence_scores if isinstance(row.confidence_scores, dict) else json.loads(
                row.confidence_scores) if isinstance(row.confidence_scores, str) else {}
            profile.confidence_scores = cs_raw
        except Exception:
            profile.confidence_scores = {}
            
        profile.evidence_sources = {}
        try:
            es_raw = row.evidence_sources if isinstance(row.evidence_sources, dict) else json.loads(
                row.evidence_sources) if isinstance(row.evidence_sources, str) else {}
            profile.evidence_sources = es_raw
        except Exception:
            profile.evidence_sources = {}

        try:
            ks_raw = row.knowledge_states if isinstance(row.knowledge_states, dict) else json.loads(
                row.knowledge_states) if isinstance(row.knowledge_states, str) else {}
        except Exception:
            ks_raw = {}
        if isinstance(ks_raw, list):
            ks_raw = {}
        profile.knowledge_states = {}
        for kid, kv in (ks_raw or {}).items():
            if not isinstance(kv, dict):
                continue
            ks = KnowledgeState(
                node_id=str(kv.get("node_id", kid)),
                name=str(kv.get("name", kv.get("node_id", kid))),
                mastery=float(kv.get("mastery", 0.0)),
                stability=float(kv.get("stability", 0.5)),
                error_count=int(kv.get("error_count", 0)),
                correct_count=int(kv.get("correct_count", 0)),
            )
            err_cause = kv.get("primary_error_cause") or kv.get("error_cause")
            if err_cause:
                try:
                    ks.primary_error_cause = ErrorCause(err_cause)
                except Exception:
                    ks.primary_error_cause = None
            p = kv.get("last_practiced")
            if isinstance(p, str) and p:
                try:
                    ks.last_practiced = datetime.fromisoformat(p)
                except Exception:
                    ks.last_practiced = None
            elif isinstance(p, datetime):
                ks.last_practiced = p
            profile.knowledge_states[kid] = ks

        try:
            subj_raw = row.subjects if isinstance(row.subjects, (list, dict)) else json.loads(
                row.subjects) if isinstance(row.subjects, str) else []
        except Exception:
            subj_raw = []
        if isinstance(subj_raw, dict):
            subj_raw = list(subj_raw.values())
        profile.subjects = [str(s) for s in (subj_raw or [])]

        try:
            wp_raw = row.weak_points if isinstance(row.weak_points, (list, dict)) else json.loads(
                row.weak_points) if isinstance(row.weak_points, str) else []
        except Exception:
            wp_raw = []
        if isinstance(wp_raw, dict):
            wp_raw = list(wp_raw.values())
        profile.weak_points = [str(w) for w in (wp_raw or [])]

        return profile

    def _upsert_db(self, profile: LearningProfile, education_level: str = "high_school"):
        if self._SessionLocal is None or self._StudentProfile is None:
            return
        session = self._open_session()
        if session is None:
            return
        try:
            with session:
                sid = self._resolve_db_student_id(session, profile.student_id)
                if sid is None and self._Student is not None:
                    try:
                        new_student = self._Student(
                            username=str(profile.student_id),
                            password_hash="",
                        )
                        session.add(new_student)
                        session.flush()
                        sid = new_student.id
                    except Exception:
                        sid = self._resolve_db_student_id(session, profile.student_id)
                        if sid is None:
                            return
                if sid is None:
                    return

                ks_json = {}
                for kid, ks in profile.knowledge_states.items():
                    ks_json[kid] = {
                        "node_id": ks.node_id,
                        "name": ks.name,
                        "mastery": ks.mastery,
                        "stability": ks.stability,
                        "error_count": ks.error_count,
                        "correct_count": ks.correct_count,
                        "primary_error_cause": ks.primary_error_cause.value if ks.primary_error_cause else None,
                        "last_practiced": ks.last_practiced.isoformat() if ks.last_practiced else None,
                    }

                subj_json = list(profile.subjects) if isinstance(profile.subjects, (list, tuple)) else []
                wp_json = list(profile.weak_points) if isinstance(profile.weak_points, (list, tuple)) else []

                row = session.query(self._StudentProfile).filter(
                    self._StudentProfile.student_id == sid
                ).first()

                data = dict(
                    education_level=education_level or "high_school",
                    grade=profile.grade or "",
                    subjects=subj_json,
                    cognitive_preference=profile.cognitive_preference or "visual",
                    learning_goal=profile.learning_goal or "",
                    weak_points=wp_json,
                    knowledge_mastery=float(profile.knowledge_mastery or 0.0),
                    prerequisite_gap=float(getattr(profile, "prerequisite_gap", 0.0) or 0.0),
                    error_pattern_score=float(profile.error_pattern_score or 50.0),
                    learning_efficiency=float(getattr(profile, "learning_efficiency", 50.0) or 50.0),
                    learning_persistence=float(getattr(profile, "learning_persistence", 50.0) or 50.0),
                    learning_goals_constraints=getattr(profile, "learning_goals_constraints", {}),
                    resource_preference=getattr(profile, "resource_preference", {}),
                    confidence_scores=getattr(profile, "confidence_scores", {}),
                    evidence_sources=getattr(profile, "evidence_sources", {}),
                    emotional_state=float(profile.emotional_state or 70.0),
                    knowledge_states=ks_json,
                )

                if row is None:
                    data["student_id"] = sid
                    row = self._StudentProfile(**data)
                    session.add(row)
                else:
                    for k, v in data.items():
                        setattr(row, k, v)
                session.commit()
        except Exception as e:
            print(f"[ProfileEngine] upsert_db error: {e}")
            try:
                session.rollback()
            except Exception:
                pass

    def take_snapshot(self, student_id: str, note: str = "") -> bool:
        profile = self.get_profile(student_id)
        if not profile:
            return False
        if self._SessionLocal is None:
            return False
        session = self._open_session()
        if session is None:
            return False
        try:
            from models.database_models import ProfileSnapshot
            sid = self._resolve_db_student_id(session, student_id)
            if sid is None:
                return False
            correct_total = sum(ks.correct_count for ks in profile.knowledge_states.values())
            error_total = sum(ks.error_count for ks in profile.knowledge_states.values())
            snap = ProfileSnapshot(
                student_id=sid,
                knowledge_mastery=float(profile.knowledge_mastery or 0),
                learning_stability=float(profile.learning_stability or 0),
                response_speed=float(profile.response_speed or 0),
                emotional_state=float(profile.emotional_state or 70),
                self_driven_score=float(profile.self_driven_score or 50),
                transfer_ability=float(profile.transfer_ability or 50),
                weak_points_count=len(profile.weak_points or []),
                correct_total=correct_total,
                error_total=error_total,
                note=note,
            )
            session.add(snap)
            session.commit()
            return True
        except Exception as e:
            print(f"[ProfileEngine] take_snapshot error: {e}")
            return False

    def get_snapshots(self, student_id: str, limit: int = 30) -> list[dict]:
        if self._SessionLocal is None:
            return []
        session = self._open_session()
        if session is None:
            return []
        try:
            from models.database_models import ProfileSnapshot
            sid = self._resolve_db_student_id(session, student_id)
            if sid is None:
                return []
            rows = session.query(ProfileSnapshot).filter(
                ProfileSnapshot.student_id == sid
            ).order_by(ProfileSnapshot.created_at.desc()).limit(limit).all()
            rows.reverse()
            return [
                {
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "knowledge_mastery": float(r.knowledge_mastery or 0),
                    "learning_stability": float(r.learning_stability or 0),
                    "response_speed": float(r.response_speed or 0),
                    "emotional_state": float(r.emotional_state or 70),
                    "self_driven_score": float(r.self_driven_score or 50),
                    "transfer_ability": float(r.transfer_ability or 50),
                    "weak_points_count": int(r.weak_points_count or 0),
                    "correct_total": int(r.correct_total or 0),
                    "error_total": int(r.error_total or 0),
                    "note": r.note or "",
                }
                for r in rows
            ]
        except Exception as e:
            print(f"[ProfileEngine] get_snapshots error: {e}")
            return []

    def auto_snapshot_if_needed(self, student_id: str) -> None:
        if self._SessionLocal is None:
            return
        session = self._open_session()
        if session is None:
            return
        try:
            from models.database_models import ProfileSnapshot
            from datetime import datetime, timedelta
            sid = self._resolve_db_student_id(session, student_id)
            if sid is None:
                self.take_snapshot(student_id, note="auto")
                return
            last = session.query(ProfileSnapshot).filter(
                ProfileSnapshot.student_id == sid
            ).order_by(ProfileSnapshot.created_at.desc()).first()
            if last is None:
                self.take_snapshot(student_id, note="auto:first")
                return
            if last.created_at and datetime.now() - last.created_at > timedelta(minutes=30):
                self.take_snapshot(student_id, note="auto:30min")
        except Exception:
            pass
