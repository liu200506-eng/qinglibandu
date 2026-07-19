# DHCP

## DHCP概述

DHCP（Dynamic Host Configuration Protocol）是一种自动分配IP地址的协议。

### DHCP的作用

1. **自动分配IP地址**：无需手动配置
2. **统一管理**：集中管理IP地址分配
3. **减少错误**：避免IP地址冲突

### DHCP工作过程（四步握手）

1. **DHCP Discover**：客户端广播发送发现请求
2. **DHCP Offer**：服务器发送IP地址提议
3. **DHCP Request**：客户端请求使用该IP地址
4. **DHCP Acknowledge**：服务器确认分配

### DHCP消息类型

| 类型 | 用途 |
|------|------|
| Discover | 发现可用的DHCP服务器 |
| Offer | 提供IP地址 |
| Request | 请求IP地址 |
| Acknowledge | 确认分配 |
| Release | 释放IP地址 |
| Decline | 拒绝IP地址 |

## DHCP分配方式

1. **自动分配**：永久分配一个IP地址
2. **动态分配**：在租约期内分配IP地址，到期后收回
3. **手动分配**：管理员指定IP地址，由DHCP服务器分配

### DHCP租约

- **租约期限**：IP地址的使用期限
- **续租**：客户端在租约到期前请求续租
- **释放**：客户端主动释放IP地址

## DHCP选项

DHCP可以分配除IP地址外的其他配置信息：

| 选项 | 用途 |
|------|------|
| 子网掩码 | 网络掩码 |
| 默认网关 | 默认路由 |
| DNS服务器 | DNS地址 |
| 域名 | 主机域名 |
| MTU | 最大传输单元 |

## DHCP中继

当DHCP客户端和服务器不在同一网段时，需要DHCP中继代理。

### DHCP中继工作原理

1. 客户端发送DHCP Discover（广播）
2. 中继代理接收并转发给DHCP服务器（单播）
3. 服务器发送DHCP Offer给中继代理
4. 中继代理转发给客户端（广播）

## 总结

DHCP简化了网络配置管理，是现代网络中不可或缺的协议。
