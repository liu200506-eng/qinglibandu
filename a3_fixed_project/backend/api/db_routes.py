from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import datetime, json, random, time

from database import get_db
from models.database_models import (
    Subject, KnowledgeNode, Course, StudentProfile, Student,
    StudyPlan, LearningTask, ResourcePack, Feedback, ChatMessage,
    WorkflowRecord, ErrorRecord
)

router = APIRouter(prefix='/db', tags=['database'])


class SubjectRsp(BaseModel):
    id: int
    name: str
    description: str = ''
    icon: str = ''
    education_level: str = 'high_school'
    full_score: int = 100


@router.get('/subjects')
async def get_subjects(education_level: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Subject)
    if education_level:
        query = query.filter(Subject.education_level.in_([education_level, 'all']))
    rows = query.all()
    return {'status': 'success', 'subjects': [
        {
            'id': s.id, 'name': s.name, 'description': s.description or '',
            'icon': s.icon or '', 'education_level': s.education_level or 'high_school',
            'full_score': s.full_score or 100
        } for s in rows
    ]}


def _build_tree(nodes, parent_id=None):
    out = []
    for n in nodes:
        if n.parent_id == parent_id:
            c = _build_tree(nodes, n.id)
            out.append({
                'id': n.id, 'label': n.name, 'name': n.name,
                'description': n.description or '',
                'difficulty': n.difficulty or 0.5,
                'mastery': n.mastery or 0.0,
                'education_level': n.education_level or '',
                'grade': n.grade or '',
                'lecture_text': n.lecture_text or '',
                'exercises': json.loads(n.exercises_json) if n.exercises_json else [],
                'flash_cards': json.loads(n.flash_cards_json) if n.flash_cards_json else [],
                'children': c
            })
    return out


@router.get('/knowledge-tree/{subject_name}')
async def get_tree(subject_name: str, education_level: Optional[str] = None,
                   grade: Optional[str] = None, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.name == subject_name).first()
    if not subject:
        subject = db.query(Subject).filter(Subject.name.like(f'%{subject_name}%')).first()
    if not subject:
        return {'status': 'error', 'grades': []}
    q = db.query(KnowledgeNode).filter(KnowledgeNode.subject_id == subject.id)
    if education_level:
        q = q.filter(KnowledgeNode.education_level == education_level)
    if grade:
        q = q.filter(KnowledgeNode.grade == grade)
    rows = q.order_by(KnowledgeNode.id.asc()).all()
    tree = _build_tree(rows, None)
    return {'status': 'success', 'tree': tree}


@router.get('/grades/{subject_name}')
async def get_grades(subject_name: str, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.name == subject_name).first()
    if not subject:
        return {'status': 'error', 'grades': []}
    rows = db.query(KnowledgeNode).filter(KnowledgeNode.subject_id == subject.id).all()
    grades = sorted({(r.grade or '') for r in rows if r.grade})
    return {'status': 'success', 'grades': grades}


@router.get('/knowledge-node/{node_id}')
async def get_node(node_id: int, db: Session = Depends(get_db)):
    node = db.query(KnowledgeNode).filter(KnowledgeNode.id == node_id).first()
    if not node:
        return {'status': 'error', 'message': 'not found'}
    return {
        'status': 'success',
        'node': {
            'id': node.id, 'name': node.name, 'description': node.description or '',
            'lecture_text': node.lecture_text or '',
            'exercises': json.loads(node.exercises_json) if node.exercises_json else [],
            'flash_cards': json.loads(node.flash_cards_json) if node.flash_cards_json else [],
            'children_count': db.query(KnowledgeNode).filter(KnowledgeNode.parent_id == node.id).count()
        }
    }


def _build_video_templates(query: str) -> list:
    from urllib.parse import quote
    q = quote(query)
    return [
        {
            'source': 'bilibili',
            'source_label': '哔哩哔哩 B站',
            'title': f'{query} — 系统讲解合集',
            'teacher': 'B站热门名师',
            'description': 'B站最全的系统讲解合集，支持免费倍速播放',
            'difficulty': 'medium',
            'duration': 45,
            'view_count': random.randint(12000, 800000),
            'url': f'https://search.bilibili.com/all?keyword={q}&order=click&duration=1&tids_1=',
        },
        {
            'source': 'bilibili',
            'source_label': '哔哩哔哩 B站',
            'title': f'{query} — 刷题精讲',
            'teacher': '高考/竞赛名师',
            'description': '真题+模拟题逐题精讲，配套知识点回顾',
            'difficulty': 'hard',
            'duration': 30,
            'view_count': random.randint(5000, 300000),
            'url': f'https://search.bilibili.com/all?keyword={q}+真题+讲解&order=click',
        },
        {
            'source': 'bilibili',
            'source_label': '哔哩哔哩 B站',
            'title': f'{query} — 40分钟串讲',
            'teacher': '高中同步课老师',
            'description': '一节课串透本节所有概念、公式、题型',
            'difficulty': 'easy',
            'duration': 40,
            'view_count': random.randint(8000, 200000),
            'url': f'https://search.bilibili.com/all?keyword={q}+完整课程&order=click&duration=4',
        },
        {
            'source': 'icourse163',
            'source_label': '中国大学MOOC',
            'title': f'{query} — 名校公开课',
            'teacher': '清华/北大/复旦等名校',
            'description': '中国大学MOOC 收录的名校公开课，权威教材同步',
            'difficulty': 'medium',
            'duration': 50,
            'view_count': random.randint(3000, 120000),
            'url': f'https://www.icourse163.org/search.htm?search={q}',
        },
        {
            'source': 'qqvideo',
            'source_label': '腾讯视频教育',
            'title': f'{query} — 教育频道精选',
            'teacher': '腾讯视频教育专区',
            'description': '腾讯视频教育频道的热门讲解视频',
            'difficulty': 'medium',
            'duration': 40,
            'view_count': random.randint(5000, 200000),
            'url': f'https://v.qq.com/x/search/?q={q}&stag=0&srecommend=10&_adtest=0',
        },
        {
            'source': 'youku',
            'source_label': '优酷教育',
            'title': f'{query} — 精讲系列（优酷）',
            'teacher': '教育专区名师',
            'description': '优酷教育专区的精选系列课程',
            'difficulty': 'medium',
            'duration': 40,
            'view_count': random.randint(1500, 80000),
            'url': f'https://so.youku.com/search_video/q_{q}?search_key={q}',
        },
        {
            'source': 'khan',
            'source_label': '可汗学院 Khan',
            'title': f'{query} — Khan Academy 英文/中英双语',
            'teacher': 'Khan Academy',
            'description': '可汗学院国际化讲解，适合拓展思维，中英双语',
            'difficulty': 'medium',
            'duration': 25,
            'view_count': random.randint(3000, 150000),
            'url': f'https://www.khanacademy.org/search?page_search_query={q}',
        },
        {
            'source': 'toutiao',
            'source_label': '今日头条',
            'title': f'{query} — 短视频碎片化精讲',
            'teacher': '一线教师',
            'description': '5-10分钟一条，利用碎片时间查漏补缺',
            'difficulty': 'easy',
            'duration': 8,
            'view_count': random.randint(5000, 500000),
            'url': f'https://so.toutiao.com/search?keyword={q}&source=input',
        },
    ]


def _build_lecture_prompt(subject_name: str, level_label: str, name: str) -> tuple[str, str]:
    is_english = '英语' in subject_name or 'English' in subject_name
    is_writing = any(k in name for k in ['写作', '读后续写', '概要', '应用文'])
    is_reading = any(k in name for k in ['阅读', '完形', '七选五', '推断'])
    is_grammar = any(k in name for k in ['语法', '时态', '语态', '非谓语', '从句', '句法', '特殊句式'])
    is_vocab = any(k in name for k in ['词汇', '单词', '词性', '构词'])

    if is_english:
        if is_grammar:
            template = (
                f'请撰写「{level_label}{subject_name}」中《{name}》的超详细讲解，面向高中高考/大学四六级备考学生。\n'
                f'严格返回 Markdown，结构必须包含以下 6 大模块（每部分至少 80 字）：\n'
                f'# {name} 核心知识点\n'
                f'## 一、概念总览\n（一句话定义 + 核心作用 + 高考占分比例 / 考频等级）\n'
                f'## 二、核心规则\n（逐条列出 5~8 条最关键的语法规则，每条配一句英文例句+中文翻译）\n'
                f'## 三、常见标志词\n（列出在阅读/完型中出现的提示词，如 however / therefore / although 等）\n'
                f'## 四、真题例句\n（选取 3 道历年高考真题或四级真题，标出考点并翻译整句）\n'
                f'## 五、易错题精讲\n（3 道学生最容易错的单选题 A/B/C/D，含答案+解析）\n'
                f'## 六、记忆口诀\n（自编 2~3 句顺口溜帮助记忆，同时给出 5 个高频考点关键词）\n'
                f'要求：中英双语例句对照，禁止空话，每部分必须有具体内容。'
            )
        elif is_writing:
            template = (
                f'请撰写「{level_label}{subject_name}」中《{name}》的超详细讲解，面向高中高考/大学四六级写作备考。\n'
                f'严格返回 Markdown，结构必须包含以下 6 大模块（每部分至少 80 字）：\n'
                f'# {name} 写作指导\n'
                f'## 一、评分标准\n（高考/官方评分五档或四档，每档描述）\n'
                f'## 二、万能开头/结尾句\n（给 10 句高分句型，中英对照）\n'
                f'## 三、三段式模板\n（引入段/主体段/结论段模板，含连接词）\n'
                f'## 四、高分替换词\n（low -> high 替换词表，如 important -> vital, many -> a multitude of 等 15 组）\n'
                f'## 五、范文一篇\n（完整英文范文 150~200 词 + 中文译文）\n'
                f'## 六、避坑清单\n（5 个常见扣分点：时态一致、主谓一致、标点、字数、结构）\n'
                f'要求：全部实用，不要空话，句型可直接套用。'
            )
        elif is_reading:
            template = (
                f'请撰写「{level_label}{subject_name}」中《{name}》的超详细讲解。\n'
                f'严格返回 Markdown，结构必须包含以下 6 大模块（每部分至少 80 字）：\n'
                f'# {name} 解题指南\n'
                f'## 一、题型介绍\n（占分比例、考察能力、常见题源）\n'
                f'## 二、解题三步法\n（step-by-step 操作流程：题干定位 -> 原文检索 -> 选项比对）\n'
                f'## 三、干扰选项套路\n（常见陷阱：偷换概念/扩大范围/因果倒置/绝对化表述，各举一例）\n'
                f'## 四、真题实战\n（选取 1 段高考真题原文 + 2 道题目 + 解析）\n'
                f'## 五、高频逻辑关系词\n（转折/因果/递进/让步各 5 个，中英对照）\n'
                f'## 六、计时策略\n（建议用时 + 涂卡提醒）\n'
                f'要求：可操作、可直接套用到实战，不要空泛理论。'
            )
        elif is_vocab or name == '词汇':
            template = (
                f'请撰写「{level_label}{subject_name}」中《{name}》的超详细讲解。\n'
                f'严格返回 Markdown，结构必须包含以下 6 大模块：\n'
                f'# {name} 核心词汇\n'
                f'## 一、高频词汇 30\n（每个单词给：音标 + 词性 + 中文释义 + 高考真题例句）\n'
                f'## 二、词根词缀\n（常见前缀 re-/pre-/dis-/un- 等 10 个 + 后缀 -tion/-able/-ment 等 10 个，配例词）\n'
                f'## 三、同义词辨析\n（易混淆词 5 组：affect vs effect 等，每组对比+例句）\n'
                f'## 四、一词多义\n（高考最常考的 10 个一词多义词，如 run/mind/light/figure）\n'
                f'## 五、搭配短语\n（动词短语 / 介词短语 / 固定搭配共 20 个，中英对照）\n'
                f'## 六、记忆方法\n（谐音记忆、词根记忆、故事记忆法各举一例）\n'
                f'要求：每个词条必须带真实例句，不要只列单词。'
            )
        else:
            template = (
                f'请撰写「{level_label}{subject_name}」中《{name}》的超详细讲解，面向高中高考/大学四六级。\n'
                f'严格返回 Markdown，结构必须包含以下 6 大模块（每部分至少 80 字）：\n'
                f'# {name} 核心知识点\n'
                f'## 一、概念总览\n（定义 + 考试占分 + 考频）\n'
                f'## 二、核心技巧/规则\n（逐条列出 5~8 条核心点，每条配英文例句+翻译）\n'
                f'## 三、真题实战\n（1 段真题材料 + 2 道题目 + 解析）\n'
                f'## 四、易错题精讲\n（3 道最容易错的单选题 + 答案 + 解析）\n'
                f'## 五、高分表达/句型\n（可直接套用的 10 个加分表达，中英对照）\n'
                f'## 六、避坑清单\n（5 个最常见扣分点）\n'
                f'要求：全部中英双语对照，实用、具体、可套用。'
            )
        system = f'你是{level_label}{subject_name}金牌讲师，深谙高考/四六级出题规律，讲解实战导向，中英文交替，例句必带中文翻译。'
    else:
        template = (
            f'请撰写「{level_label}{subject_name}」中《{name}》这个核心知识点的完整讲解。\n'
            f'严格返回 Markdown，结构必须包含以下 6 个部分（每部分至少 80 字）：\n'
            f'# {name} 核心知识点\n'
            f'## 一、定义/概念\n（通俗解释+关键术语）\n'
            f'## 二、公式卡片\n（LaTeX 公式，用 \\(...\\) 或 \\[...\\] 格式展示 3~6 个核心公式）\n'
            f'## 三、性质/定理\n（列出 3~5 条核心性质或定理）\n'
            f'## 四、题型清单\n（列出 4~6 种常考题型）\n'
            f'## 五、解题步骤\n（通用解题流程，分点列出）\n'
            f'## 六、易错点\n（列出 3~5 个常见误区+反例）\n'
            f'注意：全部用中文，公式用 LaTeX，不要出现任何"以下是..."之类的废话，直接开始正文。'
        )
        system = f'你是{level_label}教育名师，擅长{subject_name}的知识点讲解，直接输出Markdown正文，不要任何开场白。'
    return template, system


def _build_exercises_prompt(subject_name: str, level_label: str, name: str) -> str:
    is_english = '英语' in subject_name or 'English' in subject_name
    if is_english:
        return (
            f'请为「{level_label}{subject_name}」中的《{name}》知识点生成 8 道精选英语习题（单选/填空/完形各类型混合）。\n'
            f'严格返回 JSON 数组，不要返回 markdown、不要代码块、不要解释，只返回纯 JSON 数组。\n'
            f'每个元素字段：\n'
            f'- question: 完整英文题目文字\n'
            f'- options: 4 个选项英文字符串数组 A/B/C/D\n'
            f'- answer: 正确选项字母或答案英文短语\n'
            f'- explanation: 详细中文解析，点明考点、关键提示词、干扰项陷阱\n'
            f'- difficulty: "easy" | "medium" | "hard"\n'
            f'要求：题目全英文，解析全中文，覆盖三种难度，符合{level_label}{subject_name}高考/四六级真实命题风格。'
        )
    return (
        f'请为「{level_label}{subject_name}」中的《{name}》知识点生成 5 道精选习题。\n'
        f'严格返回 JSON 数组，不要返回 markdown、不要代码块、不要解释，只返回纯 JSON 数组。\n'
        f'每个元素字段：\n'
        f'- question: 题目文字（含 LaTeX 公式用 $ 或 $$ 包裹）\n'
        f'- options: 4 个选项字符串数组 A/B/C/D（单选题），或空数组（填空/解答题）\n'
        f'- answer: 正确答案字符串\n'
        f'- explanation: 详细解析\n'
        f'- difficulty: "easy" | "medium" | "hard"\n'
        f'确保覆盖 easy/medium/hard 三种难度，题目符合{level_label}{subject_name}考试要求。'
    )


def _build_flash_prompt(subject_name: str, level_label: str, name: str) -> str:
    is_english = '英语' in subject_name or 'English' in subject_name
    if is_english:
        return (
            f'请为「{level_label}{subject_name}」中的《{name}》知识点生成 12 张英语记忆闪卡（front 英文关键词，back 中文解释/例句）。\n'
            f'严格返回 JSON 数组，不要返回 markdown、不要代码块、不要解释，只返回纯 JSON 数组。\n'
            f'每个元素字段：\n'
            f'- front: 英文问题/单词/术语（简短，≤15 词）\n'
            f'- back: 中文解释 + 1 个英文例句（含中文翻译）\n'
            f'覆盖面：核心概念、高频词、句型、干扰点、搭配等全方位。'
        )
    return (
        f'请为「{level_label}{subject_name}」中的《{name}》知识点生成 8 张记忆闪卡。\n'
        f'严格返回 JSON 数组，不要返回 markdown、不要代码块、不要解释，只返回纯 JSON 数组。\n'
        f'每个元素字段：\n'
        f'- front: 问题/关键词（15字以内）\n'
        f'- back: 答案/解释（30字以内，可含简单 LaTeX）\n'
        f'覆盖面：定义、公式、性质、反例、易错点等各方面。'
    )


def _generate_node_content(node: KnowledgeNode, subject_name: str = '') -> dict:
    from utils.llm_client import invoke_llm
    name = node.name or '知识点'
    if not subject_name and node.subject_id:
        try:
            from database import SessionLocal
            _s = SessionLocal()
            try:
                _s2 = _s.query(Subject).filter(Subject.id == node.subject_id).first()
                if _s2:
                    subject_name = _s2.name or ''
            finally:
                _s.close()
        except Exception:
            pass
    edu_level = node.education_level or 'high_school'
    level_label = '高中' if edu_level == 'high_school' else '大学'

    lecture_prompt, lecture_system = _build_lecture_prompt(subject_name, level_label, name)
    exercises_prompt = _build_exercises_prompt(subject_name, level_label, name)
    flash_prompt = _build_flash_prompt(subject_name, level_label, name)

    result = {'lecture_text': '', 'exercises': [], 'flash_cards': []}
    try:
        lecture_text = invoke_llm(lecture_prompt, system_message=lecture_system)
        lecture_text = lecture_text.strip()
        if not lecture_text.startswith('#'):
            lecture_text = f'# {name} 核心知识点\n\n' + lecture_text
        result['lecture_text'] = lecture_text
    except Exception as e:
        result['lecture_text'] = f'# {name} 核心知识点\n\n（AI生成失败：{e}）'
    for key, prompt, sys in [
        ('exercises', exercises_prompt, '你是出题专家，只返回纯JSON数组，不要任何解释或代码块标记。'),
        ('flash_cards', flash_prompt, '你是闪卡专家，只返回纯JSON数组，不要任何解释或代码块标记。'),
    ]:
        try:
            out = invoke_llm(prompt, system_message=sys)
            out = out.strip()
            if out.startswith('```'):
                out = out.strip('`')
                if 'json' in out[:20].lower():
                    out = out[out.find('['):]
            start = out.find('[')
            if start >= 0:
                out = out[start:]
            end = out.rfind(']')
            if end >= 0:
                out = out[:end + 1]
            parsed = json.loads(out)
            if isinstance(parsed, list):
                result[key] = parsed
        except Exception:
            pass
    return result


def _guess_study_path(name: str, lecture_text: str, exercises: list, flash_cards: list) -> list:
    path = []
    ex_n = len(exercises or [])
    fl_n = len(flash_cards or [])
    path.append({'step': 1, 'title': '概念速记', 'desc': '阅读《' + name + '》核心概念 · 约 3 分钟', 'section': '一、概念'})
    if '公式' in lecture_text or '公式' in name or 'LaTeX' in lecture_text:
        path.append({'step': 2, 'title': '公式卡片', 'desc': '掌握关键公式/定理 · 约 4 分钟', 'section': '二、公式'})
        path.append({'step': 3, 'title': '题型清单', 'desc': '了解常见出题方式 · 约 3 分钟', 'section': '三、题型'})
    else:
        path.append({'step': 2, 'title': '核心原理', 'desc': '理解关键机制/规则 · 约 4 分钟', 'section': '二、核心'})
        path.append({'step': 3, 'title': '真题精讲', 'desc': '看真题怎么考 · 约 3 分钟', 'section': '三、真题'})
    path.append({'step': 4, 'title': '练习题库', 'desc': str(ex_n) + ' 道精选题（含 408 真题风格）· 约 ' + str(max(5, ex_n * 3)) + ' 分钟', 'section': '练习'})
    if fl_n > 0:
        path.append({'step': 5, 'title': '记忆闪卡', 'desc': str(fl_n) + ' 张闪卡反复记 · 约 5 分钟', 'section': '闪卡'})
    return path


def _guess_sections(text: str) -> list:
    if not text:
        return []
    heads = [('一、', '概念速记'), ('二、', '核心原理'), ('三、', '真题精讲'), ('四、', '练习'), ('五、', '闪卡'), ('六、', '拓展')]
    out = []
    for (k, t) in heads:
        if k in text:
            out.append({'title': t, 'desc': '重点章节：' + k + '...', 'section': k, 'icon': '📘'})
    return out


@router.get('/videos')
async def get_videos(subject: str = None, knowledge: str = None,
                     education_level: str = None, grade: str = None,
                     node_id: int = None, limit: int = 8,
                     db: Session = Depends(get_db)):
    packs = []
    query_parts = []
    node_name = None
    node_obj = None
    is_generating = False
    source_label = 'template'
    study_path = []
    has_preset = False
    if node_id:
        node_obj = db.query(KnowledgeNode).filter(KnowledgeNode.id == node_id).first()
        if node_obj:
            node_name = node_obj.name
            exercises = []
            flash_cards = []
            try:
                exercises = json.loads(node_obj.exercises_json) if node_obj.exercises_json else []
            except Exception:
                exercises = []
            try:
                flash_cards = json.loads(node_obj.flash_cards_json) if node_obj.flash_cards_json else []
            except Exception:
                flash_cards = []
            lecture = node_obj.lecture_text or ''
            has_preset = bool(lecture.strip()) and bool(exercises)
            if has_preset:
                source_label = 'cache'
                study_path = _guess_study_path(node_name, lecture, exercises, flash_cards)
            else:
                if not lecture or len(lecture.strip()) < 20:
                    try:
                        generated = _generate_node_content(node_obj)
                        node_obj.lecture_text = generated['lecture_text']
                        node_obj.exercises_json = json.dumps(generated['exercises'], ensure_ascii=False) if generated['exercises'] else None
                        node_obj.flash_cards_json = json.dumps(generated['flash_cards'], ensure_ascii=False) if generated['flash_cards'] else None
                        db.commit()
                        db.refresh(node_obj)
                        lecture = node_obj.lecture_text or ''
                        exercises = json.loads(node_obj.exercises_json) if node_obj.exercises_json else []
                        flash_cards = json.loads(node_obj.flash_cards_json) if node_obj.flash_cards_json else []
                        source_label = 'ai'
                        is_generating = True
                        study_path = _guess_study_path(node_name, lecture, exercises, flash_cards)
                    except Exception as e:
                        lecture = node_obj.lecture_text or f'# {node_name}\n\n（生成失败：{e}）'
                        db.commit()
                        study_path = _guess_study_path(node_name, lecture, exercises, flash_cards)
                else:
                    study_path = _guess_study_path(node_name, lecture, exercises, flash_cards)
            packs = [{
                'lecture_text': lecture,
                'exercises': exercises,
                'flash_cards': flash_cards,
                'knowledge': node_name,
            }]
    if subject:
        query_parts.append(subject)
    if node_name:
        query_parts.append(node_name)
    elif knowledge:
        query_parts.append(knowledge)
    base = ' '.join(query_parts) if query_parts else '高中数学'
    videos = _build_video_templates(base)[:limit]
    if not has_preset:
        try:
            from utils.llm_client import invoke_llm
            llm_prompt = (
                f'请为「{base}」这个高中/大学学习主题，推荐 3 个最适合的网课/UP主/系列课。\n'
                f'严格返回 JSON 数组，每个元素包含字段：title, teacher, description, difficulty (easy/medium/hard), '
                f'duration (分钟整数)。不要返回任何 markdown、解释或代码块，只返回纯 JSON 数组。'
            )
            llm_out = invoke_llm(llm_prompt, system_message='你是教育资源推荐专家，只返回纯JSON。')
            llm_out = llm_out.strip()
            if llm_out.startswith('```'):
                llm_out = llm_out.strip('`')
                if 'json' in llm_out[:20].lower():
                    llm_out = llm_out[llm_out.find('['):]
            llm_out = llm_out[llm_out.find('['):]
            data = json.loads(llm_out)
            if isinstance(data, list) and data:
                from urllib.parse import quote
                q = quote(base)
                platform_pool = [
                    ('bilibili', '哔哩哔哩 B站', f'https://search.bilibili.com/all?keyword={q}&order=click&duration=1&tids_1='),
                    ('icourse163', '中国大学MOOC', f'https://www.icourse163.org/search.htm?search={q}'),
                    ('qqvideo', '腾讯视频教育', f'https://v.qq.com/x/search/?q={q}&stag=0&srecommend=10&_adtest=0'),
                    ('khan', '可汗学院', f'https://www.khanacademy.org/search?page_search_query={q}'),
                    ('toutiao', '今日头条', f'https://so.toutiao.com/search?keyword={q}&source=input'),
                ]
                extras = []
                for i, item in enumerate(data[:3]):
                    src, label, url = platform_pool[i % len(platform_pool)]
                    extras.append({
                        'source': src,
                        'source_label': label,
                        'title': item.get('title', f'{base} 精讲'),
                        'teacher': item.get('teacher', '名师'),
                        'description': item.get('description', '推荐课程'),
                        'difficulty': item.get('difficulty', 'medium'),
                        'duration': int(item.get('duration', 40) or 40),
                        'view_count': random.randint(2000, 500000),
                        'url': url,
                    })
                videos = (extras + [v for v in videos if v['source'] == 'bilibili'])[:limit]
                source_label = 'ai' if source_label != 'cache' else source_label
        except Exception:
            pass
    platforms = sorted({(v['source'], v.get('source_label', v['source'])) for v in videos}, key=lambda x: x[0])
    return {
        'status': 'success',
        'videos': videos,
        'platforms': [{'source': s, 'label': lbl} for s, lbl in platforms],
        'content_source': source_label,
        'study_path': study_path,
        'resource_pack': packs[0] if packs else None,
        'is_generating': is_generating,
    }


_generate_running = False
_generate_progress = {'done': 0, 'total': 0, 'last_id': 0, 'errors': [], 'start_time': None}


@router.post('/generate/all')
async def generate_all(
    req: Request = None,
    education_level: str = None,
    subject_name: str = None,
    min_len: int = 20,
    db: Session = Depends(get_db),
):
    global _generate_running, _generate_progress
    if req is not None:
        try:
            payload = await req.json()
            if isinstance(payload, dict):
                education_level = payload.get('education_level', education_level)
                subject_name = payload.get('subject_name', subject_name)
                min_len = int(payload.get('min_len', min_len))
        except Exception:
            pass
    if _generate_running:
        return {'status': 'already_running', 'progress': _generate_progress}
    q = db.query(KnowledgeNode)
    if education_level:
        q = q.filter(KnowledgeNode.education_level == education_level)
    if subject_name:
        subj = db.query(Subject).filter(Subject.name.like(f'%{subject_name}%')).first()
        if subj:
            q = q.filter(KnowledgeNode.subject_id == subj.id)
    all_nodes = q.order_by(KnowledgeNode.id.asc()).all()
    nodes = [n for n in all_nodes if not n.lecture_text or len(n.lecture_text.strip()) < min_len]
    total = len(nodes)
    if total == 0:
        return {'status': 'nothing_to_generate', 'progress': {'done': 0, 'total': 0}}
    _generate_running = True
    _generate_progress = {'done': 0, 'total': total, 'last_id': 0, 'errors': [], 'start_time': time.time()}

    def _run():
        import concurrent.futures
        from database import SessionLocal

        def _do(node):
            try:
                generated = _generate_node_content(node)
                node.lecture_text = generated['lecture_text']
                node.exercises_json = json.dumps(generated['exercises'], ensure_ascii=False) if generated['exercises'] else None
                node.flash_cards_json = json.dumps(generated['flash_cards'], ensure_ascii=False) if generated['flash_cards'] else None
                s = SessionLocal()
                try:
                    n2 = s.query(KnowledgeNode).filter(KnowledgeNode.id == node.id).first()
                    if n2:
                        n2.lecture_text = node.lecture_text
                        n2.exercises_json = node.exercises_json
                        n2.flash_cards_json = node.flash_cards_json
                        s.commit()
                finally:
                    s.close()
                return node.id, None
            except Exception as e:
                return node.id, {'node_id': node.id, 'name': node.name, 'error': str(e)[:200]}

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(_do, n): n for n in nodes}
            for f in concurrent.futures.as_completed(futures):
                nid, err = f.result()
                _generate_progress['done'] += 1
                _generate_progress['last_id'] = nid
                if err:
                    _generate_progress['errors'].append(err)
        global _generate_running
        _generate_running = False

    import threading
    threading.Thread(target=_run, daemon=True).start()
    return {'status': 'started', 'total': total}
    return {'status': 'started', 'total': total}


@router.get('/generate/progress')
async def generate_progress():
    return {
        'running': _generate_running,
        'progress': _generate_progress,
        'eta_sec': int((_generate_progress['total'] - _generate_progress['done']) * 6) if _generate_progress['start_time'] and _generate_progress['done'] > 0 else None,
    }


@router.get('/generate/regen/{node_id}')
async def regen_one(node_id: int, db: Session = Depends(get_db)):
    node = db.query(KnowledgeNode).filter(KnowledgeNode.id == node_id).first()
    if not node:
        return {'status': 'not_found'}
    try:
        generated = _generate_node_content(node)
        node.lecture_text = generated['lecture_text']
        node.exercises_json = json.dumps(generated['exercises'], ensure_ascii=False) if generated['exercises'] else None
        node.flash_cards_json = json.dumps(generated['flash_cards'], ensure_ascii=False) if generated['flash_cards'] else None
        db.commit()
        db.refresh(node)
        return {'status': 'success', 'lecture_len': len(node.lecture_text or ''),
                'exercises': len(generated['exercises']), 'flash_cards': len(generated['flash_cards'])}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


@router.put('/knowledge-node/{node_id}/mastery')
async def update_mastery(node_id: int, mastery: float, db: Session = Depends(get_db)):
    node = db.query(KnowledgeNode).filter(KnowledgeNode.id == node_id).first()
    if node:
        node.mastery = mastery
        db.commit()
    return {'status': 'success'}


@router.get('/node/{node_id}/exercises')
async def get_node_exercises(node_id: int, db: Session = Depends(get_db)):
    node = db.query(KnowledgeNode).filter(KnowledgeNode.id == node_id).first()
    if not node:
        return {'status': 'error', 'exercises': []}
    ex = []
    if node.exercises_json:
        try:
            ex = json.loads(node.exercises_json) if isinstance(node.exercises_json, str) else node.exercises_json
        except Exception:
            ex = []
    fc = []
    if node.flash_cards_json:
        try:
            fc = json.loads(node.flash_cards_json) if isinstance(node.flash_cards_json, str) else node.flash_cards_json
        except Exception:
            fc = []
    return {
        'status': 'success',
        'node_id': node.id,
        'node_name': node.name,
        'lecture_text': node.lecture_text or '',
        'exercises': ex,
        'flash_cards': fc,
    }


@router.get('/quiz/{subject_name}')
async def get_quiz(subject_name: str, education_level: Optional[str] = None,
                  source_node_id: Optional[int] = None, count: int = 10,
                  db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.name == subject_name).first()
    if not subject:
        subject = db.query(Subject).filter(Subject.name.like(f'%{subject_name}%')).first()
    if not subject:
        return {'status': 'error', 'quiz': [], 'subject': subject_name}

    exs = []

    def _collect(nodes):
        for n in nodes:
            if n.exercises_json:
                try:
                    arr = json.loads(n.exercises_json) if isinstance(n.exercises_json, str) else n.exercises_json
                    for e in arr:
                        if isinstance(e, dict) and e.get('question'):
                            exs.append({
                                'question': e.get('question', ''),
                                'options': e.get('options', []) or [],
                                'answer': e.get('answer', 0),
                                'explanation': e.get('explanation', ''),
                                'difficulty': e.get('difficulty', 'medium'),
                                'source_node': n.name,
                                'source_node_id': n.id,
                            })
                except Exception:
                    pass
            if n.children:
                _collect(n.children)

    if source_node_id:
        node = db.query(KnowledgeNode).filter(KnowledgeNode.id == source_node_id).first()
        if node:
            rows = [node]
            children = db.query(KnowledgeNode).filter(KnowledgeNode.parent_id == node.id).all()
            rows.extend(children)
            _collect(rows)
            rows2 = db.query(KnowledgeNode).filter(
                KnowledgeNode.parent_id.in_([r.id for r in children])
            ).all()
            _collect(rows2)
    else:
        q = db.query(KnowledgeNode).filter(KnowledgeNode.subject_id == subject.id)
        if education_level:
            q = q.filter(KnowledgeNode.education_level == education_level)
        rows = q.all()
        _collect(rows)

    if not exs:
        return {'status': 'success', 'quiz': [], 'subject': subject.name,
                'message': '该科目暂无存题库，可先选中知识点后在右侧点击「✨ 为当前节点生成讲解+习题」'}

    random.seed((subject_name or '') + str(source_node_id or 0))
    random.shuffle(exs)
    exs = exs[:max(3, min(count, len(exs)))]

    for i, e in enumerate(exs):
        opts = e['options']
        if isinstance(e['answer'], str) and opts:
            for j, o in enumerate(opts):
                if isinstance(o, str):
                    plain = o.lstrip('ABCD.。、 ').strip()
                    if o.startswith(e['answer'] + '.') or o.startswith(e['answer'] + '、'):
                        e['answer'] = j
                        break
                elif isinstance(o, dict):
                    if str(o.get('label', '')).upper() == str(e['answer']).upper():
                        e['answer'] = j
                        break

    return {'status': 'success', 'subject': subject.name, 'quiz': exs}


@router.get('/profile/{student_id}')
async def get_profile(student_id: int, db: Session = Depends(get_db)):
    p = db.query(StudentProfile).filter(StudentProfile.student_id == student_id).first()
    if not p:
        return {'status': 'error', 'message': 'no profile'}
    return {
        'status': 'success',
        'profile': {
            'education_level': p.education_level or 'high_school',
            'grade': p.grade or '',
            'subjects': json.loads(p.subjects) if p.subjects else [],
            'cognitive_preference': p.cognitive_preference or 'visual',
            'weak_points': json.loads(p.weak_points) if p.weak_points else [],
            'knowledge_mastery': p.knowledge_mastery or 0,
            'knowledge_states': json.loads(p.knowledge_states) if p.knowledge_states else {},
        }
    }


@router.post('/error-records')
async def create_error_record(payload: dict, db: Session = Depends(get_db)):
    rec = ErrorRecord(
        student_id=int(payload.get('student_id', 1)),
        question=payload.get('question', '') or '',
        user_answer=payload.get('user_answer', '') or '',
        correct_answer=payload.get('correct_answer', '') or '',
        error_type=payload.get('knowledge_point', '') or '',
        explanation=payload.get('explanation', '') or '',
        knowledge_node_id=payload.get('knowledge_node_id'),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {'status': 'success', 'id': rec.id}


@router.get('/error-records/{student_id}')
async def list_error_records(student_id: int, db: Session = Depends(get_db)):
    rows = (db.query(ErrorRecord).filter(ErrorRecord.student_id == student_id)
            .order_by(ErrorRecord.id.desc()).limit(200).all())
    out = []
    for r in rows:
        node_name = ''
        if r.knowledge_node_id:
            node = db.query(KnowledgeNode).filter(KnowledgeNode.id == r.knowledge_node_id).first()
            if node: node_name = node.name
        out.append({
            'id': r.id,
            'question': r.question,
            'user_answer': r.user_answer,
            'correct_answer': r.correct_answer,
            'knowledge_point': node_name or r.error_type or '',
            'explanation': r.explanation,
            'created_at': r.created_at.isoformat() if r.created_at else '',
        })
    return {'status': 'success', 'items': out}


@router.delete('/error-records/{record_id}')
async def delete_error_record(record_id: int, db: Session = Depends(get_db)):
    rec = db.query(ErrorRecord).filter(ErrorRecord.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail='record not found')
    db.delete(rec); db.commit()
    return {'status': 'success'}


@router.delete('/error-records/clear/{student_id}')
async def clear_error_records(student_id: int, db: Session = Depends(get_db)):
    db.query(ErrorRecord).filter(ErrorRecord.student_id == student_id).delete()
    db.commit()
    return {'status': 'success', 'cleared': True}


from fastapi.responses import StreamingResponse
import json as json_module


@router.get('/knowledge/{node_id}/stream')
async def generate_knowledge_stream(
    node_id: int,
    db: Session = Depends(get_db)
):
    async def generate():
        try:
            node_obj = db.query(KnowledgeNode).filter(KnowledgeNode.id == node_id).first()
            if not node_obj:
                yield "data: " + json_module.dumps({'status': 'error', 'message': '知识点不存在'}) + "\n\n"
                return
            
            yield "data: " + json_module.dumps({'status': 'starting', 'node_name': node_obj.name, 'message': f'开始生成：{node_obj.name}'}) + "\n\n"
            
            name = node_obj.name or '知识点'
            subject_name = ''
            if node_obj.subject_id:
                subj = db.query(Subject).filter(Subject.id == node_obj.subject_id).first()
                if subj:
                    subject_name = subj.name or ''
            edu_level = node_obj.education_level or 'high_school'
            level_label = '高中' if edu_level == 'high_school' else '大学'
            
            yield "data: " + json_module.dumps({'status': 'generating', 'step': 'lecture', 'message': '正在生成讲义...'}) + "\n\n"
            
            from utils.llm_client import stream_llm
            lecture_prompt, lecture_system = _build_lecture_prompt(subject_name, level_label, name)
            
            lecture_text = ''
            for chunk in stream_llm(lecture_prompt, system_message=lecture_system):
                lecture_text += chunk
                yield "data: " + json_module.dumps({'status': 'streaming', 'step': 'lecture', 'content': chunk, 'total_length': len(lecture_text)}) + "\n\n"
            
            lecture_text = lecture_text.strip()
            if not lecture_text.startswith('#'):
                lecture_text = f'# {name} 核心知识点\n\n' + lecture_text
            
            yield "data: " + json_module.dumps({'status': 'completed', 'step': 'lecture', 'message': '讲义生成完成'}) + "\n\n"
            
            yield "data: " + json_module.dumps({'status': 'generating', 'step': 'exercises', 'message': '正在生成习题...'}) + "\n\n"
            
            exercises_prompt = _build_exercises_prompt(subject_name, level_label, name)
            exercises_raw = ''
            for chunk in stream_llm(exercises_prompt, system_message='你是出题专家，只返回纯JSON数组，不要任何解释或代码块标记。'):
                exercises_raw += chunk
                yield "data: " + json_module.dumps({'status': 'streaming', 'step': 'exercises', 'content': chunk, 'total_length': len(exercises_raw)}) + "\n\n"
            
            exercises = []
            try:
                out = exercises_raw.strip()
                if out.startswith('```'):
                    out = out.strip('`')
                    if 'json' in out[:20].lower():
                        out = out[out.find('['):]
                start = out.find('[')
                if start >= 0:
                    out = out[start:]
                end = out.rfind(']')
                if end >= 0:
                    out = out[:end + 1]
                parsed = json_module.loads(out)
                if isinstance(parsed, list):
                    exercises = parsed
            except Exception:
                pass
            
            yield "data: " + json_module.dumps({'status': 'completed', 'step': 'exercises', 'count': len(exercises), 'message': f'习题生成完成（{len(exercises)}道）'}) + "\n\n"
            
            yield "data: " + json_module.dumps({'status': 'generating', 'step': 'flash_cards', 'message': '正在生成闪卡...'}) + "\n\n"
            
            flash_prompt = _build_flash_prompt(subject_name, level_label, name)
            flash_raw = ''
            for chunk in stream_llm(flash_prompt, system_message='你是闪卡专家，只返回纯JSON数组，不要任何解释或代码块标记。'):
                flash_raw += chunk
                yield "data: " + json_module.dumps({'status': 'streaming', 'step': 'flash_cards', 'content': chunk, 'total_length': len(flash_raw)}) + "\n\n"
            
            flash_cards = []
            try:
                out = flash_raw.strip()
                if out.startswith('```'):
                    out = out.strip('`')
                    if 'json' in out[:20].lower():
                        out = out[out.find('['):]
                start = out.find('[')
                if start >= 0:
                    out = out[start:]
                end = out.rfind(']')
                if end >= 0:
                    out = out[:end + 1]
                parsed = json_module.loads(out)
                if isinstance(parsed, list):
                    flash_cards = parsed
            except Exception:
                pass
            
            yield "data: " + json_module.dumps({'status': 'completed', 'step': 'flash_cards', 'count': len(flash_cards), 'message': f'闪卡生成完成（{len(flash_cards)}张）'}) + "\n\n"
            
            node_obj.lecture_text = lecture_text
            node_obj.exercises_json = json_module.dumps(exercises, ensure_ascii=False) if exercises else None
            node_obj.flash_cards_json = json_module.dumps(flash_cards, ensure_ascii=False) if flash_cards else None
            node_obj.ai_generated_at = datetime.datetime.now()
            db.commit()
            
            yield "data: " + json_module.dumps({
                'status': 'finished',
                'node_name': node_obj.name,
                'lecture_length': len(lecture_text),
                'exercises_count': len(exercises),
                'flash_cards_count': len(flash_cards),
                'message': '生成完成！'
            }) + "\n\n"
        
        except Exception as e:
            yield "data: " + json_module.dumps({'status': 'error', 'message': f'生成失败: {str(e)[:150]}'}) + "\n\n"
    
    return StreamingResponse(generate(), media_type='text/event-stream')


@router.get('/fill-knowledge/stream')
async def fill_knowledge_stream(
    subject_id: Optional[int] = None,
    limit: Optional[int] = None,
    db: Session = Depends(get_db)
):
    async def generate():
        try:
            query = db.query(KnowledgeNode)
            if subject_id:
                query = query.filter(KnowledgeNode.subject_id == subject_id)
            
            nodes_to_fill = []
            for node in query.all():
                has_lecture = bool(node.lecture_text and len(node.lecture_text.strip()) > 100)
                has_exercises = bool(node.exercises_json and len(node.exercises_json) > 10)
                has_flash = bool(node.flash_cards_json and len(node.flash_cards_json) > 10)
                if not (has_lecture and has_exercises and has_flash):
                    nodes_to_fill.append(node)
            
            if limit:
                nodes_to_fill = nodes_to_fill[:limit]
            
            total = len(nodes_to_fill)
            completed = 0
            skipped = 0
            failed = 0
            
            yield "data: " + json_module.dumps({'status': 'starting', 'total': total, 'message': f'开始填充 {total} 个知识点'}) + "\n\n"
            
            for node in nodes_to_fill:
                has_lecture = bool(node.lecture_text and len(node.lecture_text.strip()) > 100)
                has_exercises = bool(node.exercises_json and len(node.exercises_json) > 10)
                has_flash = bool(node.flash_cards_json and len(node.flash_cards_json) > 10)
                
                if has_lecture and has_exercises and has_flash:
                    skipped += 1
                    yield "data: " + json_module.dumps({
                        'status': 'skip',
                        'current': completed + skipped + failed,
                        'total': total,
                        'node_name': node.name,
                        'message': f'跳过：{node.name}（已有完整内容）'
                    }) + "\n\n"
                    continue
                
                yield "data: " + json_module.dumps({
                    'status': 'processing',
                    'current': completed + skipped + failed,
                    'total': total,
                    'node_name': node.name,
                    'message': f'正在生成：{node.name}'
                }) + "\n\n"
                
                try:
                    generated = _generate_node_content(node)
                    node.lecture_text = generated['lecture_text']
                    node.exercises_json = json_module.dumps(generated['exercises'], ensure_ascii=False) if generated['exercises'] else None
                    node.flash_cards_json = json_module.dumps(generated['flash_cards'], ensure_ascii=False) if generated['flash_cards'] else None
                    node.ai_generated_at = datetime.datetime.now()
                    db.commit()
                    
                    completed += 1
                    yield "data: " + json_module.dumps({
                        'status': 'completed',
                        'current': completed + skipped + failed,
                        'total': total,
                        'node_name': node.name,
                        'completed': completed,
                        'skipped': skipped,
                        'failed': failed,
                        'progress': round((completed + skipped + failed) / total * 100, 1),
                        'message': f'完成：{node.name}'
                    }) + "\n\n"
                except Exception as e:
                    failed += 1
                    yield "data: " + json_module.dumps({
                        'status': 'error',
                        'current': completed + skipped + failed,
                        'total': total,
                        'node_name': node.name,
                        'completed': completed,
                        'skipped': skipped,
                        'failed': failed,
                        'progress': round((completed + skipped + failed) / total * 100, 1),
                        'message': f'失败：{node.name} - {str(e)[:100]}'
                    }) + "\n\n"
            
            yield "data: " + json_module.dumps({
                'status': 'finished',
                'total': total,
                'completed': completed,
                'skipped': skipped,
                'failed': failed,
                'progress': 100.0,
                'message': f'填充完成！成功: {completed}, 跳过: {skipped}, 失败: {failed}'
            }) + "\n\n"
        
        except Exception as e:
            yield "data: " + json_module.dumps({'status': 'error', 'message': f'系统错误: {str(e)}'}) + "\n\n"
    
    return StreamingResponse(generate(), media_type='text/event-stream')


@router.get('/sync-knowledge-to-rag')
async def sync_knowledge_to_rag(db: Session = Depends(get_db), request: Request = None):
    try:
        from rag.engine import RAGEngine
        
        rag_engine = None
        if request:
            rag_engine = getattr(request.app.state, 'rag_engine', None)
        
        if not rag_engine:
            rag_engine = RAGEngine()
        
        nodes_query = db.query(KnowledgeNode, Subject).join(Subject, KnowledgeNode.subject_id == Subject.id)
        nodes = nodes_query.all()
        
        nodes_data = []
        for node, subject in nodes:
            has_content = bool(node.lecture_text and len(node.lecture_text.strip()) > 50)
            if has_content:
                nodes_data.append({
                    'id': node.id,
                    'subject_id': node.subject_id,
                    'subject_name': subject.name,
                    'name': node.name,
                    'lecture_text': node.lecture_text,
                    'exercises_json': node.exercises_json,
                    'flash_cards_json': node.flash_cards_json,
                })
        
        if not nodes_data:
            return {'status': 'error', 'message': '没有找到有内容的知识点'}
        
        result = rag_engine.ingest_knowledge_nodes(nodes_data)
        
        stats = rag_engine.get_stats()
        
        return {
            'status': 'success',
            'total_nodes_found': len(nodes),
            'nodes_with_content': len(nodes_data),
            'total_upserted': result.get('total_upserted', 0),
            'errors': result.get('errors', []),
            'qdrant_stats': stats,
            'message': f'成功将 {len(nodes_data)} 个知识点同步到RAG知识库，共插入 {result.get("total_upserted", 0)} 条向量'
        }
    
    except Exception as e:
        return {'status': 'error', 'message': f'同步失败: {str(e)}'}
