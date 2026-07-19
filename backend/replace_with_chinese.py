import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
from database import SessionLocal
from models.database_models import Subject, KnowledgeNode

DOCUMENTS_DIR = os.path.join(os.path.dirname(__file__), 'knowledge_base', 'computer_network', 'documents')

NAME_MAPPINGS = {
    'OSI七层模型': 'OSI七层模型.md',
    'TCP_IP四层模型': 'TCP_IP四层模型.md',
    '数据封装与解封装': '数据封装与解封装.md',
    '物理层设备': '物理层设备.md',
    '以太网与MAC地址': '以太网与MAC地址.md',
    '交换机工作原理': '交换机工作原理.md',
    'IP地址与子网划分': 'IP地址与子网划分.md',
    'ARP协议': 'ARP协议.md',
    'ICMP与ping': 'ICMP与ping.md',
    'RIP与OSPF': 'RIP与OSPF.md',
    '路由算法': '路由算法.md',
    'NAT与VPN': 'NAT与VPN.md',
    'TCP协议详解': 'TCP协议详解.md',
    'UDP协议详解': 'UDP协议详解.md',
    'TCP和UDP的区别': 'TCP和UDP的区别.md',
    'TCP三次握手': 'TCP三次握手.md',
    'TCP四次挥手': 'TCP四次挥手.md',
    'TCP可靠传输': 'TCP可靠传输.md',
    '流量控制': '流量控制.md',
    '拥塞控制': '拥塞控制.md',
    '慢启动': '慢启动.md',
    '拥塞避免': '拥塞避免.md',
    '快速重传': '快速重传.md',
    '快速恢复': '快速恢复.md',
    '域名系统': 'DNS域名系统.md',
    'HTTP与HTTPS': 'HTTP与HTTPS.md',
    'FTP与邮件协议': 'FTP与邮件协议.md',
    'DHCP': 'DHCP.md',
    'Socket编程': 'Socket编程.md',
    '输入URL到页面显示全过程': '输入URL到页面显示全过程.md',
    '加密算法': '加密算法.md',
    '数字签名与证书': '数字签名与证书.md',
    'SSL-TLS': 'SSL-TLS.md',
    '防火墙与IDS': '防火墙与IDS.md',
}

def load_md_content(file_name):
    file_path = os.path.join(DOCUMENTS_DIR, file_name)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def replace_content():
    db = SessionLocal()
    
    subject = db.query(Subject).filter(Subject.name == '计算机网络').first()
    if not subject:
        print("❌ 未找到计算机网络课程")
        db.close()
        return
    
    nodes = db.query(KnowledgeNode).filter(
        KnowledgeNode.subject_id == subject.id,
        KnowledgeNode.parent_id != None
    ).all()
    
    replaced_count = 0
    skipped_count = 0
    
    for node in nodes:
        md_file = NAME_MAPPINGS.get(node.name)
        if md_file:
            content = load_md_content(md_file)
            if content:
                original_length = len(node.lecture_text or '')
                node.lecture_text = content
                replaced_count += 1
                print(f"✅ 替换: {node.name} ({original_length} → {len(content)} chars)")
            else:
                print(f"⚠ 文件不存在: {md_file}")
                skipped_count += 1
        else:
            skipped_count += 1
    
    db.commit()
    db.close()
    
    print(f"\n替换完成!")
    print(f"  已替换: {replaced_count}")
    print(f"  跳过(无匹配): {skipped_count}")

if __name__ == '__main__':
    replace_content()
