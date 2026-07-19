# Socket编程

## Socket概述

Socket（套接字）是网络通信的编程接口，用于在不同主机之间传输数据。

### Socket类型

1. **流式套接字（SOCK_STREAM）**：基于TCP，提供可靠的字节流传输
2. **数据报套接字（SOCK_DGRAM）**：基于UDP，提供不可靠的数据包传输
3. **原始套接字（SOCK_RAW）**：直接访问网络层，用于特殊用途

## TCP Socket编程

### 服务器端流程

1. **创建Socket**：socket()
2. **绑定地址**：bind()
3. **监听连接**：listen()
4. **接受连接**：accept()
5. **数据传输**：recv()/send()
6. **关闭连接**：close()

### 客户端流程

1. **创建Socket**：socket()
2. **连接服务器**：connect()
3. **数据传输**：send()/recv()
4. **关闭连接**：close()

### TCP Socket示例（Python）

```python
# 服务器端
import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('localhost', 8080))
server.listen(5)

client, addr = server.accept()
data = client.recv(1024)
print(f"收到: {data.decode()}")
client.send(b"Hello from server")
client.close()
server.close()
```

```python
# 客户端
import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 8080))
client.send(b"Hello from client")
data = client.recv(1024)
print(f"收到: {data.decode()}")
client.close()
```

## UDP Socket编程

### UDP特点

- 无连接，无需建立连接
- 不可靠，不保证数据到达
- 速度快，开销小

### UDP编程流程

1. **创建Socket**：socket()
2. **绑定地址**（可选）：bind()
3. **数据传输**：sendto()/recvfrom()
4. **关闭Socket**：close()

### UDP Socket示例（Python）

```python
# 服务器端
import socket

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(('localhost', 8080))

data, addr = server.recvfrom(1024)
print(f"收到来自{addr}的消息: {data.decode()}")
server.sendto(b"Hello from server", addr)
server.close()
```

```python
# 客户端
import socket

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.sendto(b"Hello from client", ('localhost', 8080))
data, addr = client.recvfrom(1024)
print(f"收到来自{addr}的消息: {data.decode()}")
client.close()
```

## Socket选项

常用的Socket选项：

- **SO_REUSEADDR**：允许重用地址
- **SO_TIMEOUT**：设置超时时间
- **SO_SNDBUF/SO_RCVBUF**：设置发送/接收缓冲区大小

## 总结

Socket编程是网络编程的基础，掌握TCP和UDP的Socket编程是开发网络应用的必备技能。
