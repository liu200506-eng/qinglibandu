# 知识库统一JSON Schema

## 目录结构

每门课程必须具有以下文件结构：

```
knowledge_base/{course_code}/
├── course.json              # 课程基本信息
├── knowledge_tree.json      # 知识点树结构
├── dependencies.json        # 知识点依赖关系
├── error_patterns.json      # 常见错误模式
├── question_bank.json       # 题库
├── resources.json           # 学习资源索引
└── documents/               # Markdown讲义文档
    ├── {knowledge_point_name}.md
    └── ...
```

## 1. course.json

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| course_id | string | 是 | 课程唯一标识 |
| course_name | string | 是 | 课程名称（中文） |
| course_name_en | string | 否 | 课程名称（英文） |
| description | string | 是 | 课程描述 |
| education_level | string | 是 | 教育级别：high_school/university |
| total_hours | integer | 是 | 总学时 |
| credits | integer | 是 | 学分 |
| target_students | string | 是 | 目标学生 |
| prerequisites | array | 否 | 先修课程列表 |
| course_objectives | array | 是 | 课程目标列表 |
| textbooks | array | 是 | 教材信息列表 |
| reference_materials | array | 否 | 参考资料列表 |
| status | string | 否 | 状态：draft/review/published |
| version | string | 否 | 版本号 |
| last_updated | string | 否 | 最后更新时间 |

## 2. knowledge_tree.json

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| course_id | string | 是 | 课程唯一标识 |
| version | string | 是 | 版本号 |
| description | string | 否 | 描述 |
| roots | array | 是 | 知识点根节点列表 |

### 知识点节点结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 知识点唯一标识（格式：{course_code}_{number}） |
| name | string | 是 | 知识点名称 |
| description | string | 是 | 知识点描述 |
| difficulty | number | 是 | 难度系数（0~1） |
| mastery_threshold | number | 否 | 掌握阈值（默认0.7） |
| learning_hours | number | 否 | 建议学习时长（小时） |
| education_level | string | 否 | 教育级别 |
| keywords | array | 否 | 关键词列表 |
| prerequisites | array | 否 | 先修知识点ID列表 |
| children | array | 否 | 子知识点列表 |

## 3. dependencies.json

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| course_id | string | 是 | 课程唯一标识 |
| version | string | 是 | 版本号 |
| description | string | 否 | 描述 |
| dependencies | array | 是 | 依赖关系列表 |

### 依赖关系结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| source_id | string | 是 | 源知识点ID |
| target_id | string | 是 | 目标知识点ID |
| dependency_type | string | 是 | 依赖类型：prerequisite/corequisite/recommended |
| weight | number | 否 | 依赖权重（0~1） |
| description | string | 否 | 依赖描述 |

## 4. error_patterns.json

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| course_id | string | 是 | 课程唯一标识 |
| version | string | 是 | 版本号 |
| description | string | 否 | 描述 |
| error_patterns | array | 是 | 错误模式列表 |

### 错误模式结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pattern_id | string | 是 | 错误模式唯一标识 |
| knowledge_point_id | string | 是 | 关联知识点ID |
| pattern_name | string | 是 | 错误模式名称 |
| pattern_description | string | 是 | 错误模式描述 |
| common_cause | string | 是 | 常见原因 |
| remediation_strategy | string | 是 | 补救策略 |
| difficulty_level | number | 是 | 难度系数（0~1） |
| examples | array | 否 | 错误示例列表 |

## 5. question_bank.json

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| course_id | string | 是 | 课程唯一标识 |
| description | string | 否 | 描述 |
| questions | array | 是 | 题目列表 |

### 题目结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question_id | string | 是 | 题目唯一标识 |
| knowledge_point_id | string | 是 | 关联知识点ID |
| knowledge_point_name | string | 是 | 关联知识点名称 |
| question_type | string | 是 | 题目类型：single_choice/multiple_choice/judgment/calculation/essay |
| difficulty | number | 是 | 难度系数（0~1） |
| score | number | 是 | 分值 |
| question | string | 是 | 题目内容 |
| options | array | 否 | 选项列表（选择题必填） |
| answer | string | 是 | 正确答案 |
| analysis | string | 是 | 答案解析 |
| reference | array | 是 | 来源参考 |
| source | string | 否 | 题目来源：textbook/exam/practice |
| created_at | string | 否 | 创建时间 |

## 6. resources.json

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| course_id | string | 是 | 课程唯一标识 |
| description | string | 否 | 描述 |
| resources | array | 是 | 资源列表 |

### 资源结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| resource_id | string | 是 | 资源唯一标识 |
| knowledge_point_id | string | 是 | 关联知识点ID |
| knowledge_point_name | string | 是 | 关联知识点名称 |
| resource_type | string | 是 | 资源类型：video/lecture/practice/code/simulation |
| title | string | 是 | 资源标题 |
| description | string | 否 | 资源描述 |
| format | string | 否 | 资源格式：markdown/video/python/html |
| source | string | 是 | 资源来源：textbook/bilibili/courseware/interactive |
| url | string | 否 | 资源链接（视频资源必填） |
| reference | string | 是 | 来源参考 |
| difficulty | number | 是 | 难度系数（0~1） |
| approved | boolean | 否 | 是否审核通过（默认false） |
| approval_status | string | 否 | 审核状态：pending/approved/rejected |

## 7. documents/

| 文件命名规则 | 说明 |
|-------------|------|
| {knowledge_point_name}.md | 知识点讲义文档 |

### Markdown文档规范

- 编码：UTF-8
- 标题：# 知识点名称
- 结构：概述、核心概念、示例、练习题、总结
- 来源标注：在文档末尾标注来源教材和章节

## 校验规则

### 文件完整性检查

- 缺少任何必需文件时，导入脚本应直接提示并终止
- 检查顺序：course.json → knowledge_tree.json → dependencies.json → error_patterns.json → question_bank.json → resources.json → documents/

### 数据校验规则

1. **知识点ID唯一性**：同一课程内知识点ID不能重复
2. **父知识点存在性**：子知识点的parent_id必须对应存在的知识点
3. **先修知识点存在性**：prerequisites列表中的ID必须对应存在的知识点
4. **循环依赖检测**：不能出现A→B→A的循环依赖
5. **题目绑定检查**：题目必须绑定到存在的知识点
6. **答案非空检查**：题目答案不能为空
7. **资源链接有效性**：视频资源必须有有效URL
8. **文档数量一致性**：documents/中的文档数量应与knowledge_tree中的叶子节点数量一致
9. **难度范围检查**：难度系数必须在0~1范围内
10. **掌握阈值检查**：掌握阈值必须在0~1范围内，且大于难度系数

### 幂等导入规则

- 使用course_code + knowledge_node_code作为唯一约束
- 已存在的数据更新
- 新数据插入
- 删除的数据标记失效（is_active=false）
- 不产生重复知识点

### 事务规则

- 每门课程作为一个独立事务
- 任何一项导入失败，整门课程回滚
- 避免数据库出现半成品状态