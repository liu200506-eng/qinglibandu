# -*- coding: utf-8 -*-
import sys
import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from sqlalchemy import create_engine, func, Column, Integer, String, Text, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func as _f
# 不导入 main 模块，使用独立数据库连接

engine = create_engine(
    f"sqlite:///{BACKEND_DIR}/database/qingli.db",
    echo=False,
    connect_args={"check_same_thread": False},
)

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    description = Column(Text, default="")
    icon = Column(String(50), default="")
    education_level = Column(String(20), default="high_school")
    full_score = Column(Integer, default=100)
    created_at = Column(DateTime, server_default=_f.now())


class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    subject_id = Column(Integer, nullable=False)
    parent_id = Column(Integer, nullable=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    difficulty = Column(Float, default=0.5)
    mastery = Column(Float, default=0.0)
    education_level = Column(String(20), default="high_school")
    grade = Column(String(20), default=None)
    created_at = Column(DateTime, server_default=_f.now())
    lecture_text = Column(Text, default=None)
    exercises_json = Column(Text, default=None)
    flash_cards_json = Column(Text, default=None)
    ai_generated_at = Column(DateTime, default=None)


def add_subject_if_not_exists(db, name, desc, icon, level, score):
    existing = db.query(Subject).filter(Subject.name == name).first()
    if existing:
        print(f"  已存在: {name}")
        return existing
    s = Subject(name=name, description=desc, icon=icon, education_level=level, full_score=score)
    db.add(s)
    db.flush()
    print(f"  新增: {name}")
    return s


def add_node_if_not_exists(db, subject_id, parent_id, name, desc="", difficulty=0.5,
                           education_level="high_school", grade=None):
    existing = db.query(KnowledgeNode).filter(
        KnowledgeNode.subject_id == subject_id,
        KnowledgeNode.parent_id == parent_id,
        KnowledgeNode.name == name
    ).first()
    if existing:
        return existing
    n = KnowledgeNode(
        subject_id=subject_id, parent_id=parent_id, name=name, description=desc,
        difficulty=difficulty, education_level=education_level, grade=grade,
    )
    db.add(n)
    db.flush()
    return n


def build_tree(db, subject_id, grade, chapters, level="high_school"):
    res = {}
    for ch_name, leaves in chapters:
        ch = add_node_if_not_exists(db, subject_id, None, ch_name, ch_name, 0.5, level, grade)
        res[ch_name] = {}
        for l_name, l_desc, diff in leaves:
            leaf = add_node_if_not_exists(db, subject_id, ch.id, l_name, l_desc, diff, level, grade)
            res[ch_name][l_name] = leaf.id
    return res


def fill_node_content(db, node_id, lecture, exercises, flash_cards):
    node = db.query(KnowledgeNode).filter(KnowledgeNode.id == node_id).first()
    if not node:
        return False
    import json as _j
    node.lecture_text = lecture
    node.exercises_json = _j.dumps(exercises, ensure_ascii=False)
    node.flash_cards_json = _j.dumps(flash_cards, ensure_ascii=False)
    node.ai_generated_at = _f.now()
    return True


def main():
    db = SessionLocal()
    try:
        UNIVERSITY_SUBJECTS = [
            ("计算机网络", "计算机网络", "🌐", "university", 100),
            ("数据结构", "数据结构(C语言版)", "🌳", "university", 100),
            ("操作系统", "操作系统导论", "🖥️", "university", 100),
            ("计算机组成", "计算机组成原理", "🔧", "university", 100),
            ("数据库原理", "数据库系统概论", "🗄️", "university", 100),
        ]

        UNIVERSITY_TREES = {
            "计算机网络": [
                ("网络概述", [("OSI/RM、TCP/IP", "七层、四层模型", 0.7)]),
                ("物理层与数据链路层", [
                    ("物理层", "带宽、奈奎斯特定理、香农公式", 0.7),
                    ("数据链路层", "帧、CRC检错、滑动窗口", 0.8),
                    ("以太网", "CSMA/CD、100BASE-T", 0.75),
                ]),
                ("网络层", [
                    ("IP协议", "IPv4地址、子网划分、CIDR", 0.85),
                    ("ICMP", "ping、traceroute原理", 0.75),
                    ("路由协议", "RIP OSPF BGP", 0.85),
                ]),
                ("运输层", [
                    ("TCP", "三次握手四次挥手、滑动窗口、拥塞控制", 0.9),
                    ("UDP", "特点、校验和、应用", 0.7),
                ]),
                ("应用层", [
                    ("HTTP", "方法、状态码、Cookie/SESSION/JWT、HTTPS", 0.85),
                    ("DNS", "递归迭代、记录类型", 0.8),
                    ("FTP/SMTP/POP3", "", 0.7),
                ]),
                ("网络安全", [("加密与认证", "对称AES 非对称RSA、摘要HMAC", 0.8)]),
            ],
            "数据结构": [
                ("线性表", [("顺序表", "动态数组、操作", 0.7), ("链表", "单链表、双链表", 0.7)]),
                ("栈和队列", [("栈", "括号匹配、表达式求值", 0.7), ("队列", "循环队列", 0.7)]),
                ("树和二叉树", [("二叉树", "遍历、线索化", 0.8), ("二叉搜索树", "BST", 0.75)]),
                ("图", [("图的存储", "邻接矩阵、邻接表", 0.7), ("图的遍历", "DFS、BFS", 0.75)]),
                ("查找", [("二分查找", "二分查找", 0.65), ("哈希表", "散列函数、冲突处理", 0.75)]),
                ("排序", [("快速排序", "分治", 0.75), ("归并排序", "稳定排序", 0.7)]),
            ],
            "操作系统": [
                ("进程与线程", [("进程概念", "PCB 状态转换", 0.7), ("进程调度", "FCFS SJF RR", 0.75)]),
                ("内存管理", [("分页与分段", "分页、分段、段页式", 0.75), ("虚拟内存", "页面置换", 0.85)]),
                ("文件系统", [("文件与目录", "FAT/索引节点", 0.7), ("磁盘调度", "SCAN C-SCAN", 0.7)]),
            ],
            "计算机组成": [
                ("数制与编码", [("定点数", "原码反码补码移码", 0.7), ("浮点数", "IEEE 754", 0.8)]),
                ("CPU", [("ALU与CU", "算术逻辑、控制单元", 0.7), ("寄存器", "用户可见寄存器、控制寄存器", 0.7), ("指令系统", "指令格式、寻址方式", 0.75)]),
                ("存储系统", [("主存", "DRAM SRAM", 0.7), ("Cache", "直接、全相联、组相联映射", 0.85)]),
                ("总线与I/O", [("总线", "仲裁", 0.7), ("I/O系统", "程序查询、程序中断、DMA、通道", 0.8)]),
            ],
            "数据库原理": [
                ("概述", [("三级模式", "外模式/模式/内模式", 0.6)]),
                ("关系模型", [("关系代数", "σ π × ∪ ÷", 0.7), ("SQL", "SELECT 连接 子查询 聚合 窗口", 0.8), ("规范化", "1NF~4NF BC范式", 0.8)]),
                ("事务与并发", [("事务ACID", "四大特性", 0.75), ("并发控制", "封锁协议、死锁、可串行化", 0.85)]),
                ("恢复与安全", [("备份与恢复", "日志 撤销重做", 0.75), ("安全", "用户权限、GRANT", 0.7)]),
                ("数据库设计", [("ER模型", "实体关系图", 0.75)]),
            ],
        }

        print("=== 初始化科目 ===")
        uni_ids = {}
        for name, desc, icon, level, score in UNIVERSITY_SUBJECTS:
            s = add_subject_if_not_exists(db, name, desc, icon, level, score)
            uni_ids[name] = s.id

        print("\n=== 初始化知识点树 ===")
        for name, chapters in UNIVERSITY_TREES.items():
            sid = uni_ids.get(name)
            if sid:
                print(f"  {name}:")
                build_tree(db, sid, None, chapters, "university")

        print("\n=== 填充知识点内容 ===")
        def find_node(db_, sid_, name_):
            return db_.query(KnowledgeNode).filter(
                KnowledgeNode.subject_id == sid_, KnowledgeNode.name == name_
            ).first()

        def lecture_text(label, items):
            lines = [f"# {label}"]
            for k, v in items:
                lines.append(f"- {k}: {v}")
            lines.append("")
            return "\n".join(lines)

        def exercises(label, questions):
            return [
                {"question": q, "options": opts, "answer": a, "difficulty": d, "explanation": e, "knowledge_point": label}
                for (q, opts, a, d, e) in questions
            ]

        def flash(label, pairs):
            return [{"front": f"{label}: {k}", "back": v, "difficulty": "基础"} for k, v in pairs]

        net_sid = uni_ids.get("计算机网络")
        if net_sid:
            HTTP_LECTURE = lecture_text("HTTP 核心知识点", [
                ("默认端口", "HTTP=80 HTTPS=443"),
                ("有无状态", "HTTP 无状态，靠 Cookie/Session/JWT 维持状态"),
                ("默认连接", "HTTP/1.0 非持久；HTTP/1.1 默认 Keep-Alive"),
                ("RFC 关键方法", "GET 幂等安全；POST 不幂等；PUT 幂等；DELETE 幂等"),
                ("缓存", "强缓存 Cache-Control；协商缓存 ETag/Last-Modified → 304"),
                ("HTTPS", "HTTP + TLS/SSL；TLS 默认 443"),
                ("跨域", "简单请求直接发；否则先发 OPTIONS 预检"),
            ])
            HTTP_EX = exercises("HTTP", [
                ("HTTPS 默认端口是？", ["A. 80", "B. 8080", "C. 443", "D. 8443"], "C", "easy", "HTTPS 默认 443。"),
                ("HTTP/1.1 默认连接方式是？", ["A. 短连接", "B. 长连接(Keep-Alive)", "C. 随机", "D. 管道化"], "B", "easy", "HTTP/1.1 默认 Keep-Alive 长连接。"),
                ("304 状态码表示？", ["A. 永久重定向", "B. 临时重定向", "C. 协商缓存命中", "D. 资源不存在"], "C", "easy", "304 Not Modified 表示资源未修改。"),
                ("下列哪个方法不幂等？", ["A. GET", "B. PUT", "C. POST", "D. DELETE"], "C", "medium", "POST 不幂等，重复调用可能创建多个资源。"),
            ])
            HTTP_FL = flash("HTTP", [
                ("默认端口", "HTTP 80, HTTPS 443"),
                ("有无状态", "无状态；Cookie/Session/JWT 维持状态"),
                ("HTTP/1.0 vs 1.1", "1.0 非持久；1.1 默认 Keep-Alive"),
                ("状态码", "2成功 3重定向 4客户端错 5服务器错"),
                ("幂等方法", "GET PUT DELETE HEAD OPTIONS"),
            ])

            TCP_LECTURE = lecture_text("TCP 核心知识点", [
                ("三次握手", "SYN → SYN+ACK → ACK"),
                ("四次挥手", "FIN→ACK→FIN→ACK；TIME_WAIT = 2MSL(约 1~2 分钟)"),
                ("首部大小", "TCP 最小 20B；UDP 固定 8B"),
                ("MSS 公式", "MSS = MTU - IP头(20) - TCP头(20)；以太网 MSS = 1460"),
                ("可靠传输", "滑动窗口、累计确认、超时重传、快速重传(3个重复ACK)"),
                ("拥塞控制", "慢启动→拥塞避免→快重传→快恢复"),
                ("吞吐公式", "吞吐 ≈ cwnd/RTT"),
            ])
            TCP_EX = exercises("TCP", [
                ("TCP 三次握手第三次 ACK 能否携带数据？", ["A. 绝对不能", "B. 能(RFC 793)", "C. 只能1字节", "D. 看端口"], "B", "easy", "RFC 793 允许第三次 ACK 携带数据。"),
                ("TCP 首部最小长度？", ["A. 8B", "B. 12B", "C. 20B", "D. 32B"], "C", "easy", "TCP 最小 20B。"),
                ("MSS=？（以太网环境）", ["A. 1500", "B. 1480", "C. 1460", "D. 1400"], "C", "easy", "MSS = 1500-20-20=1460。"),
                ("TIME_WAIT 时长大约？", ["A. 10秒", "B. 1~2分钟(2MSL)", "C. 1小时", "D. 永远"], "B", "medium", "2MSL，MSL 约 30s~1min。"),
                ("拥塞控制慢启动阶段 cwnd 增长方式？", ["A. 线性+1", "B. 指数×2(每RTT)", "C. 恒定", "D. 随机"], "B", "medium", "慢启动指数增长。"),
            ])
            TCP_FL = flash("TCP", [
                ("三次握手", "SYN → SYN+ACK → ACK"),
                ("四次挥手", "FIN→ACK→FIN→ACK; TIME_WAIT=2MSL"),
                ("首部大小", "TCP 最小 20B; UDP 固定 8B"),
                ("MSS", "MSS=MTU-IP头-TCP头; 以太网 1460"),
                ("可靠传输", "滑动窗口 累计确认 超时重传"),
                ("拥塞控制", "慢启动→拥塞避免→快重传→快恢复"),
            ])

            nodes = [
                ("HTTP", HTTP_LECTURE, HTTP_EX, HTTP_FL),
                ("TCP", TCP_LECTURE, TCP_EX, TCP_FL),
            ]

            for name_, lecture_, ex_, fl_ in nodes:
                node = find_node(db, net_sid, name_)
                if node:
                    if fill_node_content(db, node.id, lecture_, ex_, fl_):
                        print(f"  [OK] 填充: {name_}")
                    else:
                        print(f"  [FAIL] 未找到: {name_}")

        db.commit()
        n_s = db.query(Subject).count()
        n_k = db.query(KnowledgeNode).count()
        n_content = db.query(KnowledgeNode).filter(KnowledgeNode.lecture_text != None).count()
        print(f"\n[DONE] 种子完成：科目 {n_s} 个，知识点 {n_k} 个，已填充内容 {n_content} 个")

        subs = db.query(Subject).order_by(Subject.id).all()
        for s in subs:
            n = db.query(KnowledgeNode).filter(KnowledgeNode.subject_id == s.id).count()
            nc = db.query(KnowledgeNode).filter(KnowledgeNode.subject_id == s.id, KnowledgeNode.lecture_text != None).count()
            print(f"  [{s.id:>2}] {s.education_level:<12} | {s.name} ({n} 节点, {nc} 有内容)")

    finally:
        db.close()


if __name__ == "__main__":
    main()
