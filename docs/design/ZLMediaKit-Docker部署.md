# ZLMediaKit Docker 部署配置记录

> 服务器：`88bill99.top`（SSH 端口 `30000`，用户 `ljf`）  
> 部署日期：2026-06-09  
> 安装目录：`~/server/zlmediakit/`

---

## 1. 环境检查

部署前确认服务器已安装 Docker 与 Docker Compose：

```bash
docker --version
docker compose version
```

本机环境（部署时）：

- Ubuntu，内核 5.15
- Docker 29.4.3
- Docker Compose v5.1.3
- 用户 `ljf` 已在 `docker` 组，可直接运行容器命令

---

## 2. 创建目录与 Docker Compose

```bash
mkdir -p ~/server/zlmediakit/{conf,log,www}
cd ~/server/zlmediakit
```

创建 `docker-compose.yml`：

```yaml
services:
  zlmediakit:
    image: zlmediakit/zlmediakit:master_py
    container_name: zlmediakit
    restart: unless-stopped
    ports:
      - "25400:80"          # HTTP (Web管理 / API / HTTP-FLV / HLS)
      - "25401:443"         # HTTPS
      - "25402:1935"        # RTMP
      - "25403:554"         # RTSP
      - "25404:10000"       # RTP TCP
      - "25404:10000/udp"   # RTP UDP
      - "25405:8000/udp"    # RTSP UDP / WebRTC
      - "25406:9000/udp"    # SRT
    volumes:
      - ./conf:/opt/media/conf
      - ./log:/opt/media/log
      - ./www:/opt/media/www
```

说明：

- 选用 `master_py` 镜像，内置 **pymkui** Web 管理界面
- 宿主机端口统一映射到 **25400–25406**（落在 25400–25450 区间）
- 443 已被 nginx 占用，HTTPS 映射到宿主机 **25401**

---

## 3. 启动服务

```bash
cd ~/server/zlmediakit
docker compose pull
docker compose up -d
```

验证容器状态：

```bash
docker ps --filter name=zlmediakit
docker logs zlmediakit --tail 30
curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:25400/
```

---

## 4. 端口映射一览

| 宿主机端口 | 容器端口 | 协议 | 用途 |
|-----------|---------|------|------|
| 25400 | 80 | TCP | HTTP（Web 管理 / API / HTTP-FLV / HLS） |
| 25401 | 443 | TCP | HTTPS |
| 25402 | 1935 | TCP | RTMP 推流/拉流 |
| 25403 | 554 | TCP | RTSP |
| 25404 | 10000 | TCP + UDP | RTP |
| 25405 | 8000 | UDP | RTSP UDP / WebRTC |
| 25406 | 9000 | UDP | SRT |

---

## 5. 访问地址

| 服务 | 地址 |
|------|------|
| Web 管理界面 | http://88bill99.top:25400/ |
| 登录页 | http://88bill99.top:25400/login.html |
| RTMP 推流示例 | `rtmp://88bill99.top:25402/live/流名` |
| RTSP 示例 | `rtsp://88bill99.top:25403/live/流名` |

登录密钥位于配置文件 `~/server/zlmediakit/conf/config.ini` 中的 `secret=` 字段（首次启动时自动生成，请自行查看，勿泄露）。

---

## 6. 关键配置修改

首次启动后，ZLMediaKit 会在 `./conf/config.ini` 生成默认配置。需手动调整以下项：

### 6.1 放开公网 HTTP 访问（必做）

**问题现象**：浏览器访问显示 `Your ip is not allowed to access the service.`

**原因**：`[http]` 段默认 `allow_ip_range` 仅允许内网 IP。

**修改**：编辑 `~/server/zlmediakit/conf/config.ini`：

```ini
[http]
allow_ip_range=
```

置空表示不限制 IP，允许公网访问 HTTP API 与文件索引。

### 6.2 启用 pymkui Web 管理界面

首次挂载空配置目录时，Python 插件与前端路径可能未正确写入，需补充：

```ini
[http]
rootPath=/opt/media/bin/pymkui/frontend

[python]
plugin=mk_plugin
```

### 6.3 应用配置

```bash
cd ~/server/zlmediakit
docker compose restart
```

验证：

```bash
curl -s -o /dev/null -w 'login HTTP %{http_code}\n' http://127.0.0.1:25400/login.html
```

期望返回 `HTTP 200`。

---

## 7. 数据持久化

| 宿主机路径 | 容器路径 | 说明 |
|-----------|---------|------|
| `~/server/zlmediakit/conf/` | `/opt/media/conf` | 配置文件 |
| `~/server/zlmediakit/log/` | `/opt/media/log` | 日志 |
| `~/server/zlmediakit/www/` | `/opt/media/www` | 媒体文件 |

重启或重建容器后，上述数据保留。

---

## 8. 常用运维命令

```bash
cd ~/server/zlmediakit

# 查看状态
docker compose ps

# 查看日志（实时）
docker logs -f zlmediakit

# 重启
docker compose restart

# 停止
docker compose down

# 更新镜像并重启
docker compose pull && docker compose up -d
```

---

## 9. 防火墙 / 安全组

服务器本机未启用 ufw，Docker 已监听 `0.0.0.0`。

若公网无法访问，请在**云厂商安全组**中放行：

- **25400–25406** TCP
- **25404–25406** UDP

---

## 10. 安全建议

1. **修改 API 密钥**：登录后在管理界面修改，或直接编辑 `config.ini` 中的 `secret=` 并重启容器。
2. **限制管理入口**：生产环境建议通过 Nginx 反向代理，并加 IP 白名单或 Basic Auth，而不是长期对公网完全开放。
3. **按需恢复 IP 白名单**：若只需特定 IP 访问 HTTP API，可在 `allow_ip_range` 中填写 CIDR 或 IP 段，例如：

   ```ini
   allow_ip_range=1.2.3.4,10.0.0.0-10.255.255.255
   ```

---

## 11. 故障排查

| 现象 | 可能原因 | 处理 |
|------|---------|------|
| `Your ip is not allowed to access the service` | HTTP IP 白名单限制 | 清空 `[http] allow_ip_range=` 并重启 |
| 访问 25400 超时 | 安全组未放行 | 在云控制台开放 25400–25406 |
| 只看到文件列表，无登录页 | pymkui 未启用 | 配置 `rootPath` 与 `[python] plugin=mk_plugin` |
| 容器反复重启 | 端口冲突 | `docker compose down`，检查端口占用后重新 `up -d` |
| API 返回 `Please login first` | 未带 secret 参数 | 在请求中携带 `config.ini` 里的 `secret` 值 |

---

## 12. 参考链接

- [ZLMediaKit GitHub](https://github.com/ZLMediaKit/ZLMediaKit)
- [Docker 镜像 zlmediakit/zlmediakit](https://hub.docker.com/r/zlmediakit/zlmediakit)
- [配置文件说明](https://docs.zlmediakit.com/guide/media_server/config_file.html)
- [pymkui 管理界面](https://github.com/ZLMediaKit/pymkui)
