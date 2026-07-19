"""Idempotent bootstrap for the single competition showcase course."""
from pathlib import Path
from sqlalchemy.orm import Session

from models.database_models import Subject, KnowledgeNode


PRIMARY_SUBJECT = "计算机网络"

COURSE_TREE = {
    "第1章 网络体系结构": ["OSI七层模型", "TCP_IP四层模型", "数据封装与解封装"],
    "第2章 物理层与数据链路层": ["物理层设备", "以太网与MAC地址", "交换机工作原理"],
    "第3章 网络层": ["IP地址与子网划分", "ARP协议", "ICMP与ping", "RIP与OSPF", "路由算法", "NAT与VPN"],
    "第4章 传输层": ["TCP协议详解", "UDP协议详解", "TCP和UDP的区别", "TCP三次握手", "TCP四次挥手", "TCP可靠传输", "流量控制"],
    "第5章 TCP拥塞控制": ["拥塞控制", "慢启动", "拥塞避免", "快速重传", "快速恢复"],
    "第6章 应用层": ["DNS域名系统", "HTTP与HTTPS", "FTP与邮件协议", "DHCP", "Socket编程", "输入URL到页面显示全过程"],
    "第7章 网络安全": ["加密算法", "数字签名与证书", "SSL-TLS", "防火墙与IDS"],
}


def _document_text(name: str) -> str:
    base = Path(__file__).resolve().parents[1] / "knowledge_base" / "computer_network" / "documents"
    path = base / f"{name}.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def ensure_primary_course(db: Session) -> dict:
    """Create missing nodes and fill empty lectures from reviewed local documents."""
    subject = db.query(Subject).filter(Subject.name == PRIMARY_SUBJECT).first()
    if not subject:
        subject = Subject(
            name=PRIMARY_SUBJECT,
            course_code="computer_network",
            description="面向高校计算机类专业的计算机网络核心示范课程",
            icon="🌐",
            education_level="university",
            full_score=100,
            publish_status="demo_only",
        )
        db.add(subject)
        db.flush()

    created = 0
    filled = 0
    for chapter_index, (chapter_name, point_names) in enumerate(COURSE_TREE.items(), 1):
        chapter_code = f"cn.chapter.{chapter_index}"
        chapter = db.query(KnowledgeNode).filter(
            KnowledgeNode.subject_id == subject.id,
            KnowledgeNode.node_code == chapter_code,
        ).first()
        if not chapter:
            chapter = KnowledgeNode(
                subject_id=subject.id,
                parent_id=None,
                node_code=chapter_code,
                name=chapter_name,
                description=chapter_name,
                education_level="university",
                grade="计算机",
                difficulty=0.5,
            )
            db.add(chapter)
            db.flush()
            created += 1

        for point_index, point_name in enumerate(point_names, 1):
            node_code = f"{chapter_code}.{point_index}"
            node = db.query(KnowledgeNode).filter(
                KnowledgeNode.subject_id == subject.id,
                KnowledgeNode.node_code == node_code,
            ).first()
            if not node:
                node = db.query(KnowledgeNode).filter(
                    KnowledgeNode.subject_id == subject.id,
                    KnowledgeNode.name == point_name,
                ).first()
            lecture = _document_text(point_name)
            if not node:
                node = KnowledgeNode(
                    subject_id=subject.id,
                    parent_id=chapter.id,
                    node_code=node_code,
                    name=point_name,
                    description=f"{point_name}核心概念、工作原理与常见考点",
                    education_level="university",
                    grade="计算机",
                    difficulty=0.65,
                    lecture_text=lecture or f"# {point_name}\n\n该知识点内容待补充。",
                )
                db.add(node)
                created += 1
            else:
                if node.parent_id is None:
                    node.parent_id = chapter.id
                if (not node.lecture_text or len(node.lecture_text.strip()) < 20) and lecture:
                    node.lecture_text = lecture
                    filled += 1

    db.commit()
    return {"subject": PRIMARY_SUBJECT, "created": created, "filled": filled}
