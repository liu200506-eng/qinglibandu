# -*- coding: utf-8 -*-
"""
批量预填充知识点讲义和题目
运行方式: python batch_fill_knowledge.py
"""
import sys
import os
import json
import time

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from database import SessionLocal
from models.database_models import KnowledgeNode, Subject
from utils.llm_client import get_llm

db = SessionLocal()
llm = get_llm()


def log(msg):
    print(msg, flush=True)

def generate_lecture(node_name, description, education_level):
    """生成精美排版的讲义"""
    level_desc = "高中" if education_level == "high_school" else "大学"
    prompt = f"""请为以下知识点生成一篇精美排版的讲义：

知识点名称：{node_name}
知识点描述：{description}
教育级别：{level_desc}

要求：
1. 使用Markdown格式，包含标题、目录、表格、代码块等
2. 结构清晰：概念定义 → 基本原理 → 典型例题 → 常见错误 → 总结
3. 包含高考/考研重点标注（如：★★★高考高频考点）
4. 例题要有详细解答步骤
5. 常见错误要举例说明
6. 适合学生自学，语言通俗易懂
7. 适当使用emoji增加可读性

讲义内容："""
    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        log(f"  [Error] Lecture failed: {e}")
        return ""


def generate_exercises(node_name, description, education_level, num=8):
    """生成高考/考研重点题目，从简到难排序"""
    level_desc = "高中" if education_level == "high_school" else "大学"
    prompt = f"""请为以下知识点生成{num}道练习题：

知识点名称：{node_name}
知识点描述：{description}
教育级别：{level_desc}

要求：
1. 题目类型：包含选择题、填空题、解答题
2. 难度梯度：前2道基础题 → 中间4道中档题 → 后2道提高题/高考真题
3. 标注每道题的难度和来源（如：基础题/中档题/高考真题/考研真题）
4. 每道题包含：题目、正确答案、详细解析
5. 优先选取：
   - 高考真题（近5年全国卷、省市卷）
   - 考研真题（统考专业课真题）
   - 经典模拟题
6. 答案解析要详细，包含解题思路

JSON格式：
[
  {{
    "type": "choice|fill|解答",
    "difficulty": "基础|中档|提高",
    "source": "来源标注",
    "question": "题目内容",
    "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],  // 选择题必填
    "answer": "正确答案",
    "explanation": "详细解析，包含解题思路和步骤"
  }}
]

练习题JSON："""
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        # 尝试提取JSON
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            content = content[start:end]
        elif "```" in content:
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])
        return json.loads(content)
    except Exception as e:
        log(f"  [Error] Exercises failed: {e}")
        return []


def fill_node(node):
    """填充单个知识点"""
    name = node.name
    desc = node.description or ""
    level = node.education_level or "high_school"

    log(f"  Processing: {name}")

    # 生成讲义
    if not node.lecture_text:
        lecture = generate_lecture(name, desc, level)
        node.lecture_text = lecture
        log(f"   Lecture ({len(lecture)} chars) OK")
    else:
        log(f"   Lecture exists, skip")

    # 生成题目
    if not node.exercises_json:
        exercises = generate_exercises(name, desc, level, num=8)
        if exercises:
            node.exercises_json = json.dumps(exercises, ensure_ascii=False)
            log(f"   Exercises ({len(exercises)} items) OK")
        else:
            log(f"   Exercises failed")
    else:
        log(f"   Exercises exist, skip")

    db.commit()
    time.sleep(0.3)


def main():
    log("=" * 60)
    log("Batch Fill Knowledge Content")
    log("=" * 60)

    # 获取所有叶子知识点
    nodes = db.query(KnowledgeNode).filter(
        KnowledgeNode.parent_id != None
    ).all()

    log(f"Total: {len(nodes)} nodes\n")

    success = 0
    skip = 0
    error = 0

    for i, node in enumerate(nodes):
        log(f"[{i+1}/{len(nodes)}]")
        try:
            has_lecture = bool(node.lecture_text and len(node.lecture_text) > 100)
            has_exercises = bool(node.exercises_json and len(node.exercises_json) > 10)

            if has_lecture and has_exercises:
                log(f"  Skip (exists): {node.name}")
                skip += 1
                continue

            fill_node(node)
            success += 1

        except Exception as e:
            log(f"  [Error] {e}")
            error += 1

        time.sleep(0.2)

    log("\n" + "=" * 60)
    log(f"Done! Success: {success}, Skip: {skip}, Error: {error}")
    log("=" * 60)

    db.close()


if __name__ == "__main__":
    main()
