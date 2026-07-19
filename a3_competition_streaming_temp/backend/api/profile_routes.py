import json, time, math
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from database import SessionLocal, get_db
from models.database_models import (
    Student, StudentProfile, ErrorRecord, Feedback,
    KnowledgeNode, Subject, LearningTask, StudyPlan
)
from engines import ProfileEngine

router = APIRouter()

profile_engine = ProfileEngine()


ERROR_LABEL_CN = {
    'concept_unclear': '概念不清',
    'calculation_error': '计算失误',
    'question_misread': '审题不清',
    'transfer_weak': '迁移薄弱',
    'memory_fade': '记忆遗忘',
    'method_wrong': '方法不当',
    'formula_forget': '公式遗忘',
    'logic_jump': '逻辑跳步',
}


def _ensure_profile(db: Session, student_id: str) -> StudentProfile:
    sid = int(student_id) if str(student_id).isdigit() else 1
    profile = db.query(StudentProfile).filter(StudentProfile.student_id == sid).first()
    if not profile:
        student = db.query(Student).filter(Student.id == sid).first()
        if not student:
            student = Student(username='同学', password_hash='')
            db.add(student)
            db.flush()
            sid = student.id
        profile = StudentProfile(
            student_id=sid, education_level='high_school',
            knowledge_states={}, weak_points=[], subjects=[],
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    _recompute_from_history(db, profile)
    return profile


def _error_type(name: str) -> str:
    mapping = {
        'concept': 'concept_unclear', '概念': 'concept_unclear',
        '计算': 'calculation_error', 'calcul': 'calculation_error',
        '审题': 'question_misread', 'reading': 'question_misread',
        '迁移': 'transfer_weak', 'transfer': 'transfer_weak',
        '记忆': 'memory_fade', 'memory': 'memory_fade', '遗忘': 'memory_fade',
        '方法': 'method_wrong', 'method': 'method_wrong',
        '公式': 'formula_forget', 'formula': 'formula_forget',
        '逻辑': 'logic_jump', '跳步': 'logic_jump',
    }
    n = (name or '').lower()
    for k, v in mapping.items():
        if k in n:
            return v
    return 'concept_unclear'


def _recompute_from_history(db: Session, profile: StudentProfile):
    sid = profile.student_id
    profile.updated_at = datetime.now()

    errs = db.query(ErrorRecord).filter(ErrorRecord.student_id == sid).all()
    error_dist: Dict[str, int] = {}
    node_mastery: Dict[int, Dict[str, Any]] = {}
    node_ids = list({e.knowledge_node_id for e in errs if e.knowledge_node_id})
    node_id_to_name: Dict[int, str] = {}
    if node_ids:
        nodes = db.query(KnowledgeNode.id, KnowledgeNode.name).filter(
            KnowledgeNode.id.in_(node_ids)).all()
        for nid, nm in nodes:
            node_id_to_name[nid] = nm

    for e in errs:
        etype = _error_type(e.error_type or '')
        error_dist[etype] = error_dist.get(etype, 0) + 1
        nid = e.knowledge_node_id
        if nid:
            if nid not in node_id_to_name:
                node_id_to_name[nid] = e.error_type or f'知识点{nid}'
            if nid not in node_mastery:
                node_mastery[nid] = {'correct': 0, 'error': 0, 'total': 0}
            node_mastery[nid]['error'] += 1
            node_mastery[nid]['total'] += 1

    feedbacks = db.query(Feedback).filter(Feedback.student_id == sid).order_by(
        Feedback.created_at.desc()).limit(30).all()
    emotion_keywords = {
        'positive': ['简单', '爽', '懂了', '会了', 'good', '开心', '明白了', 'nice', '棒'],
        'negative': ['难', '懵', '不会', '错', '烦', '崩溃', 'bad', '困', '累', '哭'],
    }
    emotion_sum, emotion_cnt = 0, 0
    for f in feedbacks:
        txt = (f.description or '').lower()
        rating = getattr(f, 'rating', None)
        if rating is not None and rating >= 0:
            emotion_sum += rating * 20
            emotion_cnt += 1
            continue
        pos = sum(1 for k in emotion_keywords['positive'] if k in txt)
        neg = sum(1 for k in emotion_keywords['negative'] if k in txt)
        if pos + neg > 0:
            emotion_sum += max(0, min(100, 50 + (pos - neg) * 15))
            emotion_cnt += 1
    profile.emotional_state = round((emotion_sum / emotion_cnt) if emotion_cnt else 70, 1)

    tasks = db.query(LearningTask).filter(LearningTask.student_id == sid).all()
    completed = sum(1 for t in tasks if (t.status or '') == 'completed')
    total_tasks = max(1, len(tasks))
    response_speed = round(min(100, completed / total_tasks * 100 + 40), 1)
    self_driven_score = round(min(100, len(feedbacks) * 12 + len(tasks) * 5 + 35), 1)

    total_mastery = 0
    if node_mastery:
        for nid, d in node_mastery.items():
            cnt = d['total']
            mastery = max(10.0, 100 - d['error'] * 15) if cnt else 50
            d['mastery'] = mastery
            total_mastery += mastery
        profile.knowledge_mastery = round(total_mastery / len(node_mastery), 1)
    else:
        profile.knowledge_mastery = 50.0

    if error_dist:
        total_err = sum(error_dist.values())
        max_err = max(error_dist.values())
        error_pattern_score = round((1 - max_err / total_err) * 100, 1)
    else:
        error_pattern_score = 70.0

    learning_stability = round(min(100, max(30,
        100 - sum(1 for nid, d in node_mastery.items() if d.get('error', 0) >= 3) * 8 + len(feedbacks) * 2
    )), 1)

    transfer_ability = round(min(100, max(20,
        profile.knowledge_mastery * 0.6 + error_pattern_score * 0.3 + 30
    )), 1)

    profile.knowledge_states = {
        str(nid): {
            'node_id': str(nid),
            'name': node_id_to_name.get(nid, f'知识点{nid}'),
            'mastery': d.get('mastery', 50),
            'error_count': d.get('error', 0),
            'correct_count': d.get('correct', 0),
        } for nid, d in node_mastery.items()
    }

    now = datetime.now()
    hour_count = [0] * 24
    weekday_count = [0] * 7
    for e in errs:
        if e.created_at:
            hour_count[e.created_at.hour] += 1
            weekday_count[e.created_at.weekday()] += 1
    for f in feedbacks:
        if f.created_at:
            hour_count[f.created_at.hour] += 1
            weekday_count[f.created_at.weekday()] += 1
    peak_hours = sorted(range(24), key=lambda h: -hour_count[h])[:3]
    peak_weekday = sorted(range(7), key=lambda w: -weekday_count[w])[0] if sum(weekday_count) else now.weekday()

    big_five = {
        'openness': round(min(100, max(30, transfer_ability + (10 if len(tasks) > 5 else 0))), 1),
        'conscientiousness': round(min(100, max(30, learning_stability + 5 if self_driven_score > 60 else 0)), 1),
        'extraversion': round(min(100, max(20, len(feedbacks) * 10 + 30)), 1),
        'agreeableness': round(min(100, max(40, profile.emotional_state - 10)), 1),
        'neuroticism': round(max(10, min(80, 100 - profile.emotional_state)), 1),
    }

    top_weak = []
    for nid, d in sorted(node_mastery.items(), key=lambda x: x[1]['error'], reverse=True):
        if d['error'] >= 1:
            top_weak.append({
                'node_id': str(nid),
                'name': node_id_to_name.get(nid, f'知识点{nid}'),
                'mastery': d.get('mastery', 50),
                'error_count': d['error'],
                'priority_score': round(d['error'] * (100 - d.get('mastery', 50)) / 10, 1),
            })
        if len(top_weak) >= 5:
            break

    profile._cache = {
        'error_distribution': error_dist,
        'self_driven_score': self_driven_score,
        'transfer_ability': transfer_ability,
        'error_pattern_score': error_pattern_score,
        'learning_stability': learning_stability,
        'response_speed': response_speed,
        'big_five': big_five,
        'top_weak': top_weak,
        'rhythm': {
            'peak_hours': peak_hours,
            'peak_weekday': peak_weekday,
            'hour_count': hour_count,
            'weekday_count': weekday_count,
            'hour_labels': [f'{h}:00' for h in range(24)],
            'weekday_labels': ['周一','周二','周三','周四','周五','周六','周日'],
        },
    }
    try:
        profile.knowledge_stability = learning_stability
    except Exception:
        pass
    db.commit()


def _serialize(profile: StudentProfile) -> dict:
    cache = getattr(profile, '_cache', None) or {}
    error_dist: Dict[str, int] = cache.get('error_distribution', {}) or {}
    self_driven_score = cache.get('self_driven_score', 50)
    transfer_ability = cache.get('transfer_ability', 40)
    error_pattern_score = cache.get('error_pattern_score', 70)
    learning_stability = cache.get('learning_stability', 50)
    response_speed = cache.get('response_speed', 50)
    knowledge_states = profile.knowledge_states or {}
    big_five = cache.get('big_five', {
        'openness': 50, 'conscientiousness': 50, 'extraversion': 40,
        'agreeableness': 60, 'neuroticism': 40,
    })
    top_weak = cache.get('top_weak', [])
    rhythm = cache.get('rhythm', {
        'peak_hours': [20, 19, 21], 'peak_weekday': 1,
        'hour_count': [0]*24, 'weekday_count': [0]*7,
        'hour_labels': [f'{h}:00' for h in range(24)],
        'weekday_labels': ['周一','周二','周三','周四','周五','周六','周日'],
    })

    radar = [
        {'name': '知识掌握', 'value': profile.knowledge_mastery or 50},
        {'name': '学习稳定', 'value': learning_stability},
        {'name': '反应速度', 'value': response_speed},
        {'name': '错因健康', 'value': error_pattern_score},
        {'name': '自主学习', 'value': self_driven_score},
        {'name': '迁移能力', 'value': transfer_ability},
        {'name': '情绪状态', 'value': profile.emotional_state or 70},
    ]

    error_dist_cn = {ERROR_LABEL_CN.get(k, k): v for k, v in error_dist.items()}

    diagnosis = None
    try:
        import sys
        sys.path.insert(0, '.')
        from utils.llm_client import invoke_llm
        prompt = (
            f'你是智学魔方AI画像师，基于以下数据给一名中学生写一份画像诊断书，中文Markdown 400字以内，\n'
            f'严格按四板块输出，每一板块用一行简短结论，不要多输出：\n'
            f'📊 综合评价 / 🔍 错因指纹 / 📈 近期趋势 / 💊 AI处方\n\n'
            f'【画像数据】\n'
            f'- 雷达:{json.dumps(radar, ensure_ascii=False)}\n'
            f'- 错因:{json.dumps(error_dist_cn, ensure_ascii=False)}\n'
            f'- 性格大五:{json.dumps(big_five, ensure_ascii=False)}\n'
            f'- 节律高峰小时:{rhythm.get("peak_hours")}, 高峰星期:{rhythm.get("weekday_labels", [""]*7)[rhythm.get("peak_weekday", 0)]}\n'
            f'- 薄弱点:{json.dumps([w["name"] for w in top_weak], ensure_ascii=False)}\n'
            f'- 学习目标:{profile.learning_goal or "未填写"}\n'
        )
        diagnosis = invoke_llm(prompt, system_message='你是资深教学诊断专家，15年中学辅导经验，用语温暖简洁，输出纯Markdown，不用解释。')
    except Exception as e:
        diagnosis = None

    composite_score = round(
        (profile.knowledge_mastery * 0.25 + learning_stability * 0.15 +
         response_speed * 0.10 + error_pattern_score * 0.15 +
         self_driven_score * 0.10 + transfer_ability * 0.10 +
         (profile.emotional_state or 70) * 0.15), 1)

    level_tier = 'S' if composite_score >= 85 else 'A' if composite_score >= 75 else 'B' if composite_score >= 65 else 'C' if composite_score >= 50 else 'D'

    return {
        'student_id': profile.student_id,
        'username': (profile.student and profile.student.username) or '同学',
        'grade': profile.grade or '',
        'education_level': profile.education_level or 'high_school',
        'subjects': profile.subjects or [],
        'cognitive_preference': profile.cognitive_preference or 'visual',
        'learning_goal': profile.learning_goal or '',
        'weak_points': profile.weak_points or [],
        'knowledge_mastery': profile.knowledge_mastery or 50,
        'learning_stability': learning_stability,
        'response_speed': response_speed,
        'error_pattern_score': error_pattern_score,
        'self_driven_score': self_driven_score,
        'transfer_ability': transfer_ability,
        'emotional_state': profile.emotional_state or 70,
        'composite_score': composite_score,
        'level_tier': level_tier,
        'radar': radar,
        'error_distribution': error_dist,
        'error_distribution_cn': error_dist_cn,
        'error_distribution_pct': {k: round(v / max(sum(error_dist.values()), 1) * 100, 1)
                                    for k, v in error_dist.items()},
        'error_type_labels': ERROR_LABEL_CN,
        'knowledge_states': knowledge_states,
        'big_five': big_five,
        'top_weak': top_weak,
        'rhythm': rhythm,
        'last_updated': profile.updated_at.isoformat() if profile.updated_at else None,
        'diagnosis': diagnosis,
    }


@router.get("/profile/{student_id}")
async def get_profile(student_id: str, db: Session = Depends(get_db)):
    profile = _ensure_profile(db, student_id)
    return {'status': 'success', 'profile': _serialize(profile)}


class ProfileUpdate(BaseModel):
    grade: Optional[str] = None
    subjects: Optional[List[str]] = None
    cognitive_preference: Optional[str] = None
    learning_goal: Optional[str] = None
    weak_points: Optional[List[str]] = None
    education_level: Optional[str] = None


@router.put("/profile/{student_id}")
async def update_profile(student_id: str, updates: ProfileUpdate, db: Session = Depends(get_db)):
    profile = _ensure_profile(db, student_id)
    data = updates.model_dump(exclude_none=True)
    for k, v in data.items():
        setattr(profile, k, v)
    db.commit()
    return {'status': 'success', 'profile': _serialize(profile)}


@router.get("/profile/{student_id}/trend")
async def get_trend(student_id: str, days: int = 30, db: Session = Depends(get_db)):
    sid = int(student_id) if str(student_id).isdigit() else 1
    since = datetime.now() - timedelta(days=days)
    errs = db.query(ErrorRecord).filter(
        ErrorRecord.student_id == sid, ErrorRecord.created_at >= since
    ).all()
    feedbacks = db.query(Feedback).filter(
        Feedback.student_id == sid, Feedback.created_at >= since
    ).all()
    daily: Dict[str, Dict[str, Any]] = {}
    for d_offset in range(days + 1):
        day = (datetime.now() - timedelta(days=days - d_offset)).strftime('%Y-%m-%d')
        daily[day] = {'date': day, 'errors': 0, 'mastery': None, 'emotion': None, 'feedback': 0, 'new_knowledge': 0}
    for e in errs:
        if not e.created_at: continue
        day = e.created_at.strftime('%Y-%m-%d')
        if day in daily:
            daily[day]['errors'] += 1
    for f in feedbacks:
        if not f.created_at: continue
        day = f.created_at.strftime('%Y-%m-%d')
        if day in daily:
            daily[day]['feedback'] += 1
            if f.rating is not None and f.rating >= 0:
                daily[day]['emotion'] = round(f.rating * 20, 0)
    values = list(daily.values())
    if values:
        total_err = sum(v['errors'] for v in values)
        for v in values:
            v['mastery'] = round(max(20, 100 - total_err * 5 + 40 - v['errors'] * 10), 0)
        roll_err_7 = [values[i:i+7] for i in range(len(values))]
        for i, seg in enumerate(roll_err_7):
            if len(seg) == 7:
                avg = sum(x['errors'] for x in seg) / 7
                for j, v in enumerate(seg):
                    v['moving_avg'] = round(avg, 1)
            else:
                seg[0]['moving_avg'] = round(seg[0]['errors'], 1)
    return {'status': 'success', 'trend': values}


@router.get("/profile/{student_id}/calendar")
async def get_calendar(student_id: str, days: int = 30, db: Session = Depends(get_db)):
    sid = int(student_id) if str(student_id).isdigit() else 1
    since = datetime.now() - timedelta(days=days)
    errs = db.query(ErrorRecord).filter(
        ErrorRecord.student_id == sid, ErrorRecord.created_at >= since
    ).all()
    feedbacks = db.query(Feedback).filter(
        Feedback.student_id == sid, Feedback.created_at >= since
    ).all()
    by_day: Dict[str, Dict[str, Any]] = {}
    for d_offset in range(days + 1):
        day = (datetime.now() - timedelta(days=days - d_offset)).strftime('%Y-%m-%d')
        by_day[day] = {'date': day, 'errors': 0, 'feedback': 0, 'intensity': 0,
                       'top_knowledge': [], 'top_etype': []}
    for e in errs:
        if not e.created_at: continue
        day = e.created_at.strftime('%Y-%m-%d')
        if day in by_day:
            by_day[day]['errors'] += 1
            k = ERROR_LABEL_CN.get(_error_type(e.error_type or ''), e.error_type or '未分类')
            et = _error_type(e.error_type or '')
            if k not in by_day[day]['top_knowledge']:
                by_day[day]['top_knowledge'].append(k)
            if et not in by_day[day]['top_etype']:
                by_day[day]['top_etype'].append(et)
    for f in feedbacks:
        if not f.created_at: continue
        day = f.created_at.strftime('%Y-%m-%d')
        if day in by_day:
            by_day[day]['feedback'] += 1
    max_possible = max(v['errors'] + v['feedback'] for v in by_day.values()) or 1
    for d, v in by_day.items():
        raw = v['errors'] + v['feedback']
        v['intensity'] = round(raw / max_possible, 2)
    return {'status': 'success', 'calendar': list(by_day.values())}


@router.get("/profile/{student_id}/error-tree")
async def get_error_tree(student_id: str, db: Session = Depends(get_db)):
    sid = int(student_id) if str(student_id).isdigit() else 1
    errs = db.query(ErrorRecord).filter(ErrorRecord.student_id == sid).order_by(
        ErrorRecord.created_at.desc()).limit(50).all()
    node_ids = list({e.knowledge_node_id for e in errs if e.knowledge_node_id})
    nid_to_name: Dict[int, str] = {}
    if node_ids:
        for nid, nm in db.query(KnowledgeNode.id, KnowledgeNode.name).filter(
                KnowledgeNode.id.in_(node_ids)).all():
            nid_to_name[nid] = nm

    tree_etype: Dict[str, List[Dict[str, Any]]] = {}
    tree_knowledge: Dict[str, List[Dict[str, Any]]] = {}
    for e in errs:
        etype = _error_type(e.error_type or '')
        etype_label = ERROR_LABEL_CN.get(etype, etype)
        q = (e.question or '')[:80]
        kname = nid_to_name.get(e.knowledge_node_id, None) if e.knowledge_node_id else None
        kdisplay = kname or e.error_type or (e.knowledge_node_id and f'知识点{e.knowledge_node_id}') or '未分类'
        card = {
            'id': e.id,
            'question': q,
            'user_answer': e.user_answer,
            'correct_answer': e.correct_answer,
            'error_type': e.error_type or '',
            'error_type_label': etype_label,
            'knowledge': kdisplay,
            'knowledge_node_id': e.knowledge_node_id,
            'created_at': e.created_at.isoformat() if e.created_at else None,
        }
        tree_etype.setdefault(etype_label, []).append(card)
        tree_knowledge.setdefault(kdisplay, []).append(card)
    etype_color = {
        '概念不清':'#ef4444','计算失误':'#f97316','审题不清':'#f59e0b',
        '迁移薄弱':'#8b5cf6','记忆遗忘':'#0ea5e9','方法不当':'#10b981',
        '公式遗忘':'#ec4899','逻辑跳步':'#6366f1',
    }
    return {
        'status': 'success',
        'by_error_type': tree_etype,
        'by_knowledge': tree_knowledge,
        'total_errors': len(errs),
        'error_type_color': etype_color,
    }


@router.get("/profile/{student_id}/diagnosis")
async def get_diagnosis(student_id: str, db: Session = Depends(get_db)):
    profile = _ensure_profile(db, student_id)
    data = _serialize(profile)
    return {'status': 'success', 'diagnosis': data['diagnosis']}


@router.get("/profile/snapshots/{student_id}")
async def get_snapshots(student_id: str):
    return {"status": "success", "snapshots": profile_engine.get_snapshots(student_id)}
