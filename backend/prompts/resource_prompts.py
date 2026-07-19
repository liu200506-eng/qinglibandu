EXERCISE_GENERATION_PROMPT = """你是一位出题专家。请针对以下知识点生成练习题。

知识点：{knowledge_points}
学生水平：{level}
错因侧重：{error_focus}

请生成{count}道题目，包含：
- 简单题：{easy_count}道
- 中等题：{medium_count}道
- 难题：{hard_count}道

每题包含：
- question: 题目内容
- options: 选项（选择题）
- answer: 正确答案
- difficulty: easy/medium/hard
- knowledge_point: 对应知识点
- solution: 详细解题过程
- common_mistakes: 常见错误及原因

请输出JSON数组格式。"""


MIND_MAP_PROMPT = """请为以下知识点生成思维导图结构。

知识点列表：{topics}

思维导图应包含：
- 根节点：主题名称
- 一级分支：主要概念
- 二级分支：关键知识点
- 三级分支：具体内容或例子

请输出JSON格式的思维导图数据。"""


FLASH_CARD_PROMPT = """请为以下知识点生成记忆卡片。

知识点：{topics}
学生水平：{level}

每张卡片包含：
- front: 正面问题
- back: 背面答案
- difficulty: 难度（easy/medium/hard）
- tags: 相关标签

请生成{count}张卡片，输出JSON数组格式。"""