# 路由器自动验证 Checklist 与 URL

## 自动检查结果

- [x] 安装 `miniupnpc`
- [x] 发现 UPnP 设备: `http://192.168.0.1:1900/igd.xml` — TP-Link EC225-G5
- [x] UPnP 可发现，但 `upnpc -s` 返回 `No valid UPNP Internet Gateway Device found`
- [ ] UPnP 自动映射未成功
- [x] UPnP 设备链接: `http://192.168.0.1:1900/ipc`
- [ ] NAT-PMP (natpmpc): 不可用，未安装
 
- [x] 检查绑定地址: `127.0.0.1:50051/50052` 均有监听
- [x] 外部地址: `175.100.46.19`
- [x] localhost 监听: `0.0.0.0:50051/50052`

## 自动测试 command

```bash
set -euo pipefail
upnpc -s || true
upnpc -l || true
```

## 手动验证步骤（由于 UPnP 未连接）

1. 打开路由器管理界面: `http://192.168.0.1`
2. 查找 “转发规则 / 虚拟服务器 / NAT” 项目
3. 添加两条 TCP 转发规则：
   - 外部端口: `50051`，内部 IP: 本机，内部端口: `50051`
   - 外部端口: `50052`，内部 IP: 本机，内部端口: `50052`
4. 保存后执行下方验证 URL

## 公网验证 URL / 命令

```bash
# local TCP
nc -vz 127.0.0.1 50051
nc -vz 127.0.0.1 50052

# seed peers sample
nc -vz 3.225.222.79 50051
nc -vz 52.40.84.2 50051
nc -vz 54.148.150.96 50051
nc -vz 18.224.119.93 50051
nc -vz 3.17.174.249 50051

# 浏览器验证
http://175.100.46.19:50051
http://175.100.46.19:50052
```

## todo

- [ ] UPnP 映射 50051, 50052
- [ ] 执行公网节点握手验证
