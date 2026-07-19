import logging
from typing import List, Dict
from utils.web_search import search_and_collect, bing_search
from utils.llm_client import invoke_llm

logger = logging.getLogger(__name__)

_SUBJECT_KEYWORDS = {
    '数学': ['数学', 'math', '公式', '方程', '函数', '几何', '代数', '微积分', '概率', '统计'],
    '物理': ['物理', 'physics', '力学', '电磁', '光学', '热学', '量子', '牛顿', '定律'],
    '化学': ['化学', 'chemistry', '反应', '元素', '分子', '原子', '有机', '无机', '方程式'],
    '英语': ['英语', 'english', '语法', '单词', '词汇', '时态', '从句', '阅读', '写作', '完形'],
    '语文': ['语文', '文言文', '诗歌', '作文', '阅读', '拼音', '组词', '成语', '修辞'],
    '历史': ['历史', '朝代', '事件', '人物', '近代史', '古代史', '时间线'],
    '地理': ['地理', '地形', '气候', '经纬度', '洋流', '板块', '地图'],
    '生物': ['生物', '细胞', '基因', '进化', '生态', '遗传', 'DNA', '蛋白质'],
    '政治': ['政治', '经济', '哲学', '法律', '国家', '制度'],
    '编程': ['编程', '代码', 'python', 'java', 'c++', 'javascript', '算法', '数据结构', '程序', 'async', 'await', '函数', '循环', '数组', '递归'],
    '计算机网络': ['网络', 'tcp', 'udp', 'ip', 'http', 'https', 'dns', '路由', '交换机', '协议', '拥塞控制', '流量控制', '三次握手', '四次挥手', 'osi', '子网', 'mac', 'arp'],
}


def detect_subject(text: str) -> str:
    t = text.lower()
    scores: Dict[str, int] = {}
    for subject, kws in _SUBJECT_KEYWORDS.items():
        s = 0
        for kw in kws:
            if kw.lower() in t:
                s += 1
        if s:
            scores[subject] = s
    if not scores:
        return '通用'
    return max(scores, key=scores.get)


def expand_queries(raw: str) -> List[str]:
    variants = [raw]
    stripped = raw.strip().rstrip('。？?!！.,')
    if stripped != raw:
        variants.append(stripped)

    subject = detect_subject(raw)
    if subject != '通用':
        variants.append(f'{subject} {stripped}')

    explicit = [
        f'{stripped} 是什么意思' if not any(k in stripped for k in ['是什么', '是什么意思', '定义']) else stripped,
        f'{stripped} 讲解',
        f'{stripped} 详解',
    ]
    for v in explicit:
        if v not in variants and len(v) < 80:
            variants.append(v)
    return variants[:4]


def rank_by_relevance(candidates: List[Dict], original_question: str) -> List[Dict]:
    q_terms = set(re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{2,}', original_question.lower()))
    scored = []
    for c in candidates:
        score = 0
        blob = f"{c.get('title','')} {c.get('snippet','')} {c.get('content','')[:200]}".lower()
        for term in q_terms:
            if term in blob:
                score += 2 if term in c.get('title','').lower() else 1
        if 'zhihu.com' in c.get('url',''):
            score += 1
        if 'baike.baidu.com' in c.get('url','') or 'wikipedia' in c.get('url',''):
            score += 1
        if score == 0:
            score = 1
        scored.append((score, c))
    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored]


import re


class SearchAgent:

    def __init__(self):
        self._cache: Dict[str, List[Dict]] = {}

    def gather(self, question: str, max_sources: int = 3) -> List[Dict]:
        if question in self._cache:
            return self._cache[question]

        queries = expand_queries(question)
        logger.info('SearchAgent: expanded queries=%s', queries)

        all_found: List[Dict] = []
        seen_urls = set()
        for q in queries:
            try:
                results = search_and_collect(q, max_sources=max(2, max_sources - 1))
            except Exception as e:
                logger.warning('SearchAgent search failed for %s: %s', q, e)
                continue
            for r in results:
                if r['url'] in seen_urls:
                    continue
                seen_urls.add(r['url'])
                all_found.append(r)
            if len(all_found) >= max_sources:
                break

        if not all_found:
            try:
                plain = bing_search(question, max_results=max_sources)
                for r in plain:
                    if r['url'] in seen_urls:
                        continue
                    seen_urls.add(r['url'])
                    all_found.append(r)
            except Exception as e:
                logger.warning('SearchAgent fallback failed: %s', e)

        ranked = rank_by_relevance(all_found, question)[:max_sources]
        self._cache[question] = ranked
        return ranked

    def build_enhanced_prompt(self, question: str, sources: List[Dict], level_desc: str = '高中水平学生') -> str:
        if not sources:
            return (f"请结合你的知识，面向{level_desc}，清晰、准确、通俗地讲解下面这个问题。"
                    f"\n问题：{question}")

        src_texts = []
        for i, s in enumerate(sources, 1):
            title = s.get('title', '').strip()
            url = s.get('url', '')
            snippet = s.get('snippet', '').strip()
            content = s.get('content', '').strip()
            blob = content if content else snippet
            if blob:
                src_texts.append(f"[来源{i}]《{title}》({url})\n{blob[:2000]}")

        src_block = '\n\n'.join(src_texts)

        return f"""你是一名经验丰富、讲课通俗易懂的{level_desc}辅导老师。

学生现在的问题：「{question}」

你通过联网检索到了一些参考资料：
---
{src_block}
---

请结合以上检索资料 + 你自身的知识，面向{level_desc}，写出一份清晰、准确的讲解，结构如下：

1. 用一句话先给结论（学生一看就明白"原来是什么意思"）
2. 核心概念/定义（用自己的话转述检索内容，不要大段复制）
3. 关键点拆解（分 1-2-3，给公式/规则就解释每一项）
4. 一个小例子/生活类比帮助理解
5. 常见误区/易混点提醒

要求：
- 口语化、不要堆砌术语
- 中文，Markdown 排版
- 结尾一行小字标注：「(内容综合网络资料整理，来源：{', '.join('《'+s.get('title','')+'》' for s in sources[:3])})」
- 如果检索资料互相矛盾，以权威来源优先，并在结尾简单说明

不要输出"我在网上查到…"，直接按老师讲题的口吻回答。"""

    def decide_needs_search(self, question: str, weak_points_text: str = '') -> bool:
        if not question or len(question.strip()) < 2:
            return False
        broad_words = ['是什么', '什么是', '定义', '原理', '怎么用', '区别', '比较', '发展历程',
                       '最新', '最新进展', '例子', '案例', '例题', '公式']
        if any(b in question for b in broad_words):
            return True
        if weak_points_text and any(w in question for w in weak_points_text.split(',')[:5]):
            return False
        return True


search_agent = SearchAgent()
