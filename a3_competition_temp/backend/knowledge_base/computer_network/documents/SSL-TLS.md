# SSL/TLS

## SSL/TLS概述

SSL（Secure Sockets Layer）和TLS（Transport Layer Security）是用于在网络上提供安全通信的协议。

### SSL/TLS的作用

1. **加密传输**：使用对称加密保护数据传输
2. **身份认证**：通过数字证书验证服务器（和客户端）身份
3. **数据完整性**：使用MAC防止数据篡改

### SSL与TLS的关系

- SSL是早期版本（SSL 1.0/2.0/3.0）
- TLS是SSL的升级版本（TLS 1.0/1.1/1.2/1.3）
- TLS 1.0 = SSL 3.1，TLS向后兼容SSL

## SSL/TLS握手过程

### TLS 1.2握手

1. **ClientHello**：客户端发送支持的加密套件和随机数
2. **ServerHello**：服务器选择加密套件和发送随机数
3. **Certificate**：服务器发送数字证书
4. **ServerKeyExchange**：服务器发送密钥交换信息
5. **ServerHelloDone**：服务器完成问候
6. **ClientKeyExchange**：客户端发送密钥交换信息
7. **ChangeCipherSpec**：客户端通知开始使用新密钥
8. **Finished**：客户端发送握手完成消息
9. **ChangeCipherSpec**：服务器通知开始使用新密钥
10. **Finished**：服务器发送握手完成消息

### TLS 1.3优化

TLS 1.3简化了握手过程，只需1-RTT：

- 删除了不安全的加密套件
- 合并了多个消息
- 支持0-RTT（恢复连接时）

## SSL/TLS加密套件

加密套件包含：

1. **密钥交换算法**：RSA、DH、ECDH
2. **对称加密算法**：AES、ChaCha20
3. **哈希算法**：SHA-256、SHA-384

### 常见加密套件

- **TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384**
- **TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384**
- **TLS_CHACHA20_POLY1305_SHA256**

## SSL/TLS应用

### HTTPS

HTTPS = HTTP + SSL/TLS，用于安全的Web通信。

### FTPS

FTPS = FTP + SSL/TLS，用于安全的文件传输。

### IMAPS

IMAPS = IMAP + SSL/TLS，用于安全的邮件接收。

### VPN

IPsec VPN和SSL VPN都使用SSL/TLS进行加密。

## SSL/TLS漏洞

### 历史漏洞

- **Heartbleed**：OpenSSL漏洞，泄露内存数据
- **POODLE**：SSL 3.0漏洞，降级攻击
- **BEAST**：TLS 1.0漏洞，CBC模式攻击

### 防护措施

- 使用最新版本的TLS（TLS 1.2或1.3）
- 禁用SSL和旧版TLS
- 使用强加密套件

## 总结

SSL/TLS是网络安全的基础，通过加密、认证和完整性保护提供安全的通信。
