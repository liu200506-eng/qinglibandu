import os
import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

from database import SessionLocal
from models.database_models import Subject, KnowledgeNode

db = SessionLocal()

knowledge_base_dir = Path(__file__).parent / 'knowledge_base' / 'computer_network'
question_bank = json.loads((knowledge_base_dir / 'question_bank.json').read_text(encoding='utf-8'))

subject = db.query(Subject).filter(Subject.name == '计算机网络').first()
if not subject:
    print('未找到计算机网络科目')
    db.close()
    sys.exit(1)

questions_by_kp = {}
for q in question_bank.get('questions', []):
    kp_id = q.get('knowledge_point_id', '')
    if kp_id not in questions_by_kp:
        questions_by_kp[kp_id] = []
    questions_by_kp[kp_id].append(q)

default_exercises = {
    '网络基础': [
        {
            'question': '计算机网络的主要功能是什么？',
            'options': ['A. 数据传输和资源共享', 'B. 文字处理', 'C. 图形绘制', 'D. 音频播放'],
            'answer': 'A',
            'explanation': '计算机网络的主要功能包括数据传输、资源共享、分布式处理等。',
            'difficulty': 0.3
        },
        {
            'question': '网络按覆盖范围可分为哪几类？',
            'options': ['A. 局域网、城域网、广域网', 'B. 有线网、无线网', 'C. 互联网、内联网', 'D. 公用网、专用网'],
            'answer': 'A',
            'explanation': '按覆盖范围，网络可分为局域网（LAN）、城域网（MAN）和广域网（WAN）。',
            'difficulty': 0.3
        }
    ],
    '物理层与数据链路层': [
        {
            'question': '物理层的主要功能是什么？',
            'options': ['A. 传输比特流', 'B. 路由选择', 'C. 端到端可靠传输', 'D. 数据加密'],
            'answer': 'A',
            'explanation': '物理层负责在物理介质上传输原始比特流。',
            'difficulty': 0.3
        },
        {
            'question': '数据链路层使用什么作为传输单元？',
            'options': ['A. 帧', 'B. 数据包', 'C. 段', 'D. 比特'],
            'answer': 'A',
            'explanation': '数据链路层的传输单元是帧。',
            'difficulty': 0.4
        }
    ],
    '网络层': [
        {
            'question': '网络层的主要功能是什么？',
            'options': ['A. 路由选择和转发', 'B. 帧的传输', 'C. 端到端可靠传输', 'D. 应用程序接口'],
            'answer': 'A',
            'explanation': '网络层负责数据包的路由选择和转发。',
            'difficulty': 0.4
        },
        {
            'question': 'IP地址的主要作用是什么？',
            'options': ['A. 标识网络中的主机', 'B. 加密数据', 'C. 压缩数据', 'D. 纠错'],
            'answer': 'A',
            'explanation': 'IP地址用于在网络中唯一标识主机。',
            'difficulty': 0.3
        }
    ],
    '传输层': [
        {
            'question': '传输层提供什么类型的服务？',
            'options': ['A. 端到端通信', 'B. 物理传输', 'C. 路由选择', 'D. 数据加密'],
            'answer': 'A',
            'explanation': '传输层为应用程序提供端到端的通信服务。',
            'difficulty': 0.4
        },
        {
            'question': 'TCP和UDP的主要区别是什么？',
            'options': ['A. TCP可靠，UDP不可靠', 'B. TCP快，UDP慢', 'C. TCP简单，UDP复杂', 'D. TCP面向报文，UDP面向字节流'],
            'answer': 'A',
            'explanation': 'TCP提供可靠传输，UDP提供不可靠传输但速度更快。',
            'difficulty': 0.4
        }
    ],
    '应用层': [
        {
            'question': 'HTTP协议工作在哪个层次？',
            'options': ['A. 应用层', 'B. 传输层', 'C. 网络层', 'D. 数据链路层'],
            'answer': 'A',
            'explanation': 'HTTP是应用层协议，用于Web通信。',
            'difficulty': 0.3
        },
        {
            'question': 'DNS的作用是什么？',
            'options': ['A. 域名到IP地址的解析', 'B. 文件传输', 'C. 邮件发送', 'D. 远程登录'],
            'answer': 'A',
            'explanation': 'DNS（域名系统）负责将域名转换为IP地址。',
            'difficulty': 0.3
        }
    ],
    '网络安全': [
        {
            'question': '加密算法的主要目的是什么？',
            'options': ['A. 保护数据机密性', 'B. 提高传输速度', 'C. 压缩数据', 'D. 纠错'],
            'answer': 'A',
            'explanation': '加密算法通过将明文转换为密文来保护数据的机密性。',
            'difficulty': 0.4
        },
        {
            'question': '防火墙的主要作用是什么？',
            'options': ['A. 控制网络访问', 'B. 加速数据传输', 'C. 数据压缩', 'D. 数据备份'],
            'answer': 'A',
            'explanation': '防火墙用于控制进出网络的流量，保护网络安全。',
            'difficulty': 0.3
        }
    ],
    '以太网与MAC地址': [
        {
            'question': 'MAC地址的长度是多少？',
            'options': ['A. 48位', 'B. 32位', 'C. 128位', 'D. 64位'],
            'answer': 'A',
            'explanation': 'MAC地址由48位二进制数组成，通常表示为十六进制形式。',
            'difficulty': 0.3
        },
        {
            'question': 'CSMA/CD的中文含义是什么？',
            'options': ['A. 载波监听多路访问/冲突检测', 'B. 码分多址', 'C. 时分多址', 'D. 频分多址'],
            'answer': 'A',
            'explanation': 'CSMA/CD是以太网的介质访问控制方法。',
            'difficulty': 0.4
        }
    ],
    'UDP协议': [
        {
            'question': 'UDP的主要特点是什么？',
            'options': ['A. 无连接、不可靠', 'B. 面向连接、可靠', 'C. 无连接、可靠', 'D. 面向连接、不可靠'],
            'answer': 'A',
            'explanation': 'UDP是无连接的、不可靠的传输协议。',
            'difficulty': 0.3
        },
        {
            'question': 'UDP适合用于什么场景？',
            'options': ['A. 实时视频通话', 'B. 文件传输', 'C. 数据库访问', 'D. 邮件发送'],
            'answer': 'A',
            'explanation': 'UDP适合对实时性要求高的场景，如视频通话、在线游戏。',
            'difficulty': 0.4
        }
    ],
    'TCP三次握手': [
        {
            'question': 'TCP三次握手的目的是什么？',
            'options': ['A. 确认双方通信能力并同步序列号', 'B. 加密数据', 'C. 压缩数据', 'D. 路由选择'],
            'answer': 'A',
            'explanation': '三次握手用于确认双方的发送和接收能力，并同步初始序列号。',
            'difficulty': 0.5
        },
        {
            'question': '第一次握手发送的报文包含什么标志位？',
            'options': ['A. SYN', 'B. ACK', 'C. FIN', 'D. SYN+ACK'],
            'answer': 'A',
            'explanation': '第一次握手时客户端发送SYN报文。',
            'difficulty': 0.4
        }
    ],
    'TCP四次挥手': [
        {
            'question': '为什么TCP释放连接需要四次挥手？',
            'options': ['A. 全双工需要分别释放两个方向', 'B. 提高安全性', 'C. 加快速度', 'D. 减少数据量'],
            'answer': 'A',
            'explanation': 'TCP是全双工协议，双方需要分别释放各自的发送通道。',
            'difficulty': 0.5
        },
        {
            'question': 'TIME_WAIT状态的作用是什么？',
            'options': ['A. 确保最后一个ACK到达并等待旧报文段消失', 'B. 加密数据', 'C. 压缩数据', 'D. 路由选择'],
            'answer': 'A',
            'explanation': 'TIME_WAIT状态等待2MSL时间，确保网络中所有旧的报文段都已消失。',
            'difficulty': 0.6
        }
    ],
    'TCP流量控制': [
        {
            'question': 'TCP流量控制的目的是什么？',
            'options': ['A. 防止接收方缓冲区溢出', 'B. 防止网络拥塞', 'C. 加密数据', 'D. 压缩数据'],
            'answer': 'A',
            'explanation': '流量控制用于防止发送方过快地发送数据，导致接收方缓冲区溢出。',
            'difficulty': 0.4
        },
        {
            'question': '流量控制使用什么机制实现？',
            'options': ['A. 滑动窗口', 'B. 拥塞窗口', 'C. 三次握手', 'D. 四次挥手'],
            'answer': 'A',
            'explanation': 'TCP使用滑动窗口机制实现流量控制。',
            'difficulty': 0.4
        }
    ],
    'TCP拥塞控制': [
        {
            'question': 'TCP拥塞控制的目的是什么？',
            'options': ['A. 防止网络拥塞', 'B. 防止接收方缓冲区溢出', 'C. 加密数据', 'D. 压缩数据'],
            'answer': 'A',
            'explanation': '拥塞控制用于防止网络因过多数据而导致拥塞。',
            'difficulty': 0.5
        },
        {
            'question': '慢启动阶段cwnd如何增长？',
            'options': ['A. 指数增长', 'B. 线性增长', 'C. 固定不变', 'D. 随机增长'],
            'answer': 'A',
            'explanation': '慢启动阶段，cwnd每收到一个ACK就翻倍，呈指数增长。',
            'difficulty': 0.5
        }
    ],
    '数据封装与解封装': [
        {
            'question': '数据在OSI七层模型中如何传输？',
            'options': ['A. 从上到下封装，从下到上解封装', 'B. 从下到上封装，从上到下解封装', 'C. 只封装不解封装', 'D. 只解封装不封装'],
            'answer': 'A',
            'explanation': '数据在发送端从上到下逐层封装，在接收端从下到上逐层解封装。',
            'difficulty': 0.4
        },
        {
            'question': '传输层的PDU称为什么？',
            'options': ['A. 段(Segment)', 'B. 帧(Frame)', 'C. 数据包(Packet)', 'D. 比特(Bit)'],
            'answer': 'A',
            'explanation': '传输层的协议数据单元称为段(Segment)。',
            'difficulty': 0.4
        }
    ],
    '路由算法': [
        {
            'question': '距离向量算法的特点是什么？',
            'options': ['A. 每个路由器只知道到邻居的距离', 'B. 每个路由器知道整个网络拓扑', 'C. 计算复杂度高', 'D. 收敛速度快'],
            'answer': 'A',
            'explanation': '距离向量算法中，每个路由器只知道到直接邻居的距离。',
            'difficulty': 0.5
        },
        {
            'question': '链路状态算法基于什么算法？',
            'options': ['A. Dijkstra算法', 'B. Bellman-Ford算法', 'C. 二分查找', 'D. 冒泡排序'],
            'answer': 'A',
            'explanation': '链路状态算法使用Dijkstra算法计算最短路径。',
            'difficulty': 0.5
        }
    ],
    'ICMP与ping': [
        {
            'question': 'ICMP协议的主要作用是什么？',
            'options': ['A. 传递控制消息和错误报告', 'B. 数据加密', 'C. 文件传输', 'D. 邮件发送'],
            'answer': 'A',
            'explanation': 'ICMP用于在IP主机和路由器之间传递控制消息和错误报告。',
            'difficulty': 0.4
        },
        {
            'question': 'ping命令基于什么协议？',
            'options': ['A. ICMP', 'B. TCP', 'C. UDP', 'D. HTTP'],
            'answer': 'A',
            'explanation': 'ping命令使用ICMP回显请求和回显应答报文。',
            'difficulty': 0.3
        }
    ],
    'NAT与VPN': [
        {
            'question': 'NAT的主要作用是什么？',
            'options': ['A. 节省IP地址', 'B. 数据加密', 'C. 提高传输速度', 'D. 数据压缩'],
            'answer': 'A',
            'explanation': 'NAT通过将私有IP地址转换为公有IP地址，节省了IP地址资源。',
            'difficulty': 0.4
        },
        {
            'question': 'VPN的主要作用是什么？',
            'options': ['A. 通过公共网络建立安全连接', 'B. 提高传输速度', 'C. 数据压缩', 'D. 纠错'],
            'answer': 'A',
            'explanation': 'VPN通过公共网络建立安全的私有连接。',
            'difficulty': 0.4
        }
    ],
    'DHCP': [
        {
            'question': 'DHCP的主要作用是什么？',
            'options': ['A. 自动分配IP地址', 'B. 数据加密', 'C. 文件传输', 'D. 邮件发送'],
            'answer': 'A',
            'explanation': 'DHCP用于自动分配IP地址和其他网络配置。',
            'difficulty': 0.3
        },
        {
            'question': 'DHCP租约的作用是什么？',
            'options': ['A. 规定IP地址的使用期限', 'B. 加密数据', 'C. 压缩数据', 'D. 纠错'],
            'answer': 'A',
            'explanation': 'DHCP租约规定了IP地址的使用期限，到期后需要续租或释放。',
            'difficulty': 0.4
        }
    ],
    'FTP与邮件协议': [
        {
            'question': 'FTP使用几个TCP连接？',
            'options': ['A. 2个（控制连接和数据连接）', 'B. 1个', 'C. 3个', 'D. 4个'],
            'answer': 'A',
            'explanation': 'FTP使用两个TCP连接：一个用于控制命令，一个用于数据传输。',
            'difficulty': 0.4
        },
        {
            'question': 'SMTP协议用于什么？',
            'options': ['A. 发送邮件', 'B. 接收邮件', 'C. 文件传输', 'D. 域名解析'],
            'answer': 'A',
            'explanation': 'SMTP（简单邮件传输协议）用于发送电子邮件。',
            'difficulty': 0.3
        }
    ],
    'Socket编程': [
        {
            'question': 'Socket是什么？',
            'options': ['A. 网络通信的编程接口', 'B. 一种硬件设备', 'C. 数据格式', 'D. 协议名称'],
            'answer': 'A',
            'explanation': 'Socket是网络通信的编程接口，用于在不同主机之间传输数据。',
            'difficulty': 0.4
        },
        {
            'question': 'TCP Socket编程中服务器端需要调用哪些函数？',
            'options': ['A. socket, bind, listen, accept', 'B. socket, connect', 'C. only socket', 'D. socket, send'],
            'answer': 'A',
            'explanation': 'TCP服务器端需要依次调用socket、bind、listen、accept函数。',
            'difficulty': 0.5
        }
    ],
    '加密算法': [
        {
            'question': '对称加密和非对称加密的主要区别是什么？',
            'options': ['A. 对称加密使用相同密钥，非对称加密使用不同密钥', 'B. 对称加密速度慢，非对称加密速度快', 'C. 对称加密不安全，非对称加密安全', 'D. 对称加密复杂，非对称加密简单'],
            'answer': 'A',
            'explanation': '对称加密使用相同的密钥进行加密和解密，非对称加密使用公钥和私钥对。',
            'difficulty': 0.5
        },
        {
            'question': 'AES是哪种类型的加密算法？',
            'options': ['A. 对称加密', 'B. 非对称加密', 'C. 哈希函数', 'D. 数字签名'],
            'answer': 'A',
            'explanation': 'AES（高级加密标准）是对称加密算法。',
            'difficulty': 0.4
        }
    ],
    '数字签名与证书': [
        {
            'question': '数字签名的主要作用是什么？',
            'options': ['A. 验证数据真实性和完整性', 'B. 加密数据', 'C. 压缩数据', 'D. 纠错'],
            'answer': 'A',
            'explanation': '数字签名用于验证数据的真实性和完整性，以及提供不可否认性。',
            'difficulty': 0.5
        },
        {
            'question': '数字证书由谁颁发？',
            'options': ['A. CA（证书颁发机构）', 'B. 用户自己', 'C. 浏览器', 'D. 操作系统'],
            'answer': 'A',
            'explanation': '数字证书由CA（证书颁发机构）颁发，用于证明公钥所有者的身份。',
            'difficulty': 0.4
        }
    ],
    'SSL/TLS': [
        {
            'question': 'SSL/TLS的主要作用是什么？',
            'options': ['A. 提供安全通信', 'B. 提高传输速度', 'C. 压缩数据', 'D. 纠错'],
            'answer': 'A',
            'explanation': 'SSL/TLS用于在网络上提供加密、认证和完整性保护的安全通信。',
            'difficulty': 0.4
        },
        {
            'question': 'HTTPS使用什么端口？',
            'options': ['A. 443', 'B. 80', 'C. 21', 'D. 25'],
            'answer': 'A',
            'explanation': 'HTTPS使用443端口，HTTP使用80端口。',
            'difficulty': 0.3
        }
    ],
    '防火墙与IDS': [
        {
            'question': '防火墙的主要作用是什么？',
            'options': ['A. 控制网络访问', 'B. 检测入侵行为', 'C. 阻止攻击', 'D. 数据加密'],
            'answer': 'A',
            'explanation': '防火墙用于控制进出网络的流量，实施访问控制策略。',
            'difficulty': 0.4
        },
        {
            'question': 'IDS和IPS的主要区别是什么？',
            'options': ['A. IDS被动检测，IPS主动阻止', 'B. IDS主动阻止，IPS被动检测', 'C. IDS快，IPS慢', 'D. IDS简单，IPS复杂'],
            'answer': 'A',
            'explanation': 'IDS（入侵检测系统）被动检测入侵行为并告警，IPS（入侵防御系统）主动阻止攻击。',
            'difficulty': 0.5
        }
    ],
    'RIP与OSPF': [
        {
            'question': 'RIP使用什么作为度量标准？',
            'options': ['A. 跳数', 'B. 带宽', 'C. 延迟', 'D. 可靠性'],
            'answer': 'A',
            'explanation': 'RIP使用跳数作为度量标准，最大跳数为15。',
            'difficulty': 0.4
        },
        {
            'question': 'OSPF使用什么作为度量标准？',
            'options': ['A. 带宽', 'B. 跳数', 'C. 延迟', 'D. 可靠性'],
            'answer': 'A',
            'explanation': 'OSPF使用带宽作为度量标准，选择带宽最高的路径。',
            'difficulty': 0.4
        }
    ],
    '快速重传': [
        {
            'question': '快速重传的触发条件是什么？',
            'options': ['A. 收到3个重复ACK', 'B. 定时器超时', 'C. 收到1个重复ACK', 'D. 收到2个重复ACK'],
            'answer': 'A',
            'explanation': '当发送方收到3个重复的ACK时，立即重传丢失的段。',
            'difficulty': 0.5
        },
        {
            'question': '快速重传相比超时重传有什么优势？',
            'options': ['A. 减少延迟', 'B. 提高安全性', 'C. 增加数据量', 'D. 减少带宽消耗'],
            'answer': 'A',
            'explanation': '快速重传无需等待超时，能够更快地恢复丢失的数据，减少延迟。',
            'difficulty': 0.5
        }
    ],
    '快速恢复': [
        {
            'question': '快速恢复阶段cwnd如何调整？',
            'options': ['A. 设置为ssthresh+3', 'B. 重置为1', 'C. 设置为ssthresh', 'D. 设置为原来的一半'],
            'answer': 'A',
            'explanation': '快速恢复阶段，cwnd设置为ssthresh+3，然后线性增长。',
            'difficulty': 0.6
        },
        {
            'question': '快速恢复与慢启动相比有什么优势？',
            'options': ['A. 更快恢复发送速率', 'B. 更安全', 'C. 更简单', 'D. 更节省带宽'],
            'answer': 'A',
            'explanation': '快速恢复避免退回到慢启动，能够更快地恢复到原来的发送速率。',
            'difficulty': 0.5
        }
    ]
}

nodes = db.query(KnowledgeNode).filter(KnowledgeNode.subject_id == subject.id).all()

updated_count = 0
for node in nodes:
    if node.exercises_json:
        continue
    
    node_kp_id = node.id
    if node_kp_id in questions_by_kp:
        exercises = []
        for q in questions_by_kp[node_kp_id]:
            options = [opt.get('text', '') for opt in q.get('options', [])]
            exercises.append({
                'question': q.get('question', ''),
                'options': options,
                'answer': q.get('answer', ''),
                'explanation': q.get('analysis', ''),
                'difficulty': q.get('difficulty', 0.5)
            })
        if exercises:
            node.exercises_json = json.dumps(exercises, ensure_ascii=False)
            updated_count += 1
            continue
    
    if node.name in default_exercises:
        node.exercises_json = json.dumps(default_exercises[node.name], ensure_ascii=False)
        updated_count += 1
        continue
    
    if node.name == '网络基础':
        node.exercises_json = json.dumps(default_exercises['网络基础'], ensure_ascii=False)
        updated_count += 1
    elif node.name == '物理层与数据链路层':
        node.exercises_json = json.dumps(default_exercises['物理层与数据链路层'], ensure_ascii=False)
        updated_count += 1
    elif node.name == '网络层':
        node.exercises_json = json.dumps(default_exercises['网络层'], ensure_ascii=False)
        updated_count += 1
    elif node.name == '传输层':
        node.exercises_json = json.dumps(default_exercises['传输层'], ensure_ascii=False)
        updated_count += 1
    elif node.name == '应用层':
        node.exercises_json = json.dumps(default_exercises['应用层'], ensure_ascii=False)
        updated_count += 1
    elif node.name == '网络安全':
        node.exercises_json = json.dumps(default_exercises['网络安全'], ensure_ascii=False)
        updated_count += 1

db.commit()
print(f'已为 {updated_count} 个知识点添加习题')

total_with_exercises = db.query(KnowledgeNode).filter(
    KnowledgeNode.subject_id == subject.id,
    KnowledgeNode.exercises_json.isnot(None)
).count()
print(f'总共有 {total_with_exercises}/{len(nodes)} 个知识点有习题')

db.close()
