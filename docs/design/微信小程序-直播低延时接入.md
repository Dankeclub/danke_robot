
本文档描述当前推荐方案：不改现有 `docker-compose.yml`，由 Nginx 在公网 `443` 端口统一接入 HTTPS，然后按路径把请求分发到不同服务：

- `/live` 走 ZLMediaKit 视频服务，给微信小程序提供 HTTP-FLV 拉流。
- `/llm`、`/ws`、`/backend` 走后端服务。
- go2rtc/ffmpeg 负责本地 USB 摄像头和麦克风采集编码，并推流到 ZLMediaKit。

核心目标是：满足微信小程序 HTTPS 要求，同时尽量降低直播延迟，并把证书、域名、端口、后端接口统一收敛到 Nginx 管理。

## 1. 最终链路

```text
USB 摄像头 + 麦克风
  -> go2rtc/ffmpeg 低延时编码
  -> RTMP 推流到 ZLMediaKit:25402
  -> ZLMediaKit 输出 HTTP-FLV:25400/live/{stream}.live.flv
  -> Nginx 443 HTTPS 反向代理
  -> 微信小程序 live-player 拉流
```

对外只暴露一个 HTTPS 入口：

```text
https://your-domain.com/live/cam1.live.flv
https://your-domain.com/backend/xxx
https://your-domain.com/llm/xxx
wss://your-domain.com/ws/xxx
```

内部仍然使用你当前 Docker 端口：

```text
ZLMediaKit HTTP: 127.0.0.1:25400
ZLMediaKit HTTPS: 127.0.0.1:25401，可保留但不作为小程序主入口
ZLMediaKit RTMP: 127.0.0.1:25402
ZLMediaKit RTSP: 127.0.0.1:25403
```

## 2. 为什么要这样做

### 2.1 小程序要求 HTTPS，统一走 443 最稳

微信小程序正式环境要求网络请求使用合法 HTTPS 域名。虽然小程序可以配置多个合法域名，也可以访问带端口的 HTTPS 地址，但生产环境不建议让小程序直接访问多个非标准端口，例如 `:25401`、`:8443`。

统一走 `443` 的好处：

- 微信后台域名配置更简单。
- 证书只需要在 Nginx 维护一份。
- 后端接口、WebSocket、直播拉流都使用同一套公网入口。
- 后续更换后端端口或容器网络时，小程序端 URL 不需要变。
- 避免用户网络、代理、防火墙对非标准 HTTPS 端口的兼容问题。

### 2.2 HTTPS 放 Nginx，比放 ZLMediaKit 更容易维护

ZLMediaKit 支持 HTTPS，但视频服务本身最重要的是转封装和流媒体分发。证书签发、续期、域名路由、多后端反代、WebSocket 升级这些工作更适合交给 Nginx。

让 Nginx 终止 TLS 的好处：

- 证书续期流程成熟，例如 acme.sh、Certbot。
- 可以按路径区分多个服务。
- 可以统一添加安全头、访问日志、限流、鉴权。
- ZLMediaKit 只专注提供内网 HTTP-FLV。

### 2.3 Nginx 对视频服务的压力主要是带宽，不是计算

HTTP-FLV 是长连接传输。Nginx 不转码，只做 HTTPS 解密和 TCP 转发，所以 CPU 压力通常可控。真正要关注的是公网出口带宽。

粗略估算：

```text
总带宽 = 单路码率 x 在线观看人数
```

例如：

```text
2 Mbps x 50 人 = 100 Mbps
2 Mbps x 100 人 = 200 Mbps
4 Mbps x 100 人 = 400 Mbps
```

所以如果观众数量上来，最先吃紧的通常是服务器公网带宽，而不是 Nginx 本身。

### 2.4 下行选择 HTTP-FLV，是兼容性和低延迟的平衡点

微信小程序 `live-player` 对直播拉流最适合的协议是 HTTP-FLV 或 RTMP。HLS 兼容性也好，但切片机制会天然带来更高延迟，常见是数秒到十几秒。

本方案选择 HTTP-FLV：

- 小程序原生 `live-player` 支持。
- ZLMediaKit 原生支持。
- 通过 HTTPS 反代后满足小程序要求。
- 相比 HLS 延迟更低。
- 相比 WebRTC 部署简单，兼容性更稳。

## 3. Nginx 路由配置

以下示例假设：

- 域名：`your-domain.com`
- ZLMediaKit HTTP 端口：`127.0.0.1:25400`
- 后端服务端口示例：
  - `/backend` -> `127.0.0.1:18080`
  - `/llm` -> `127.0.0.1:18081`
  - `/ws` -> `127.0.0.1:18082`

请把域名、证书路径和后端端口替换成你的实际值。

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

server {
    listen 80;
    server_name your-domain.com;

    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate     /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;

    client_max_body_size 100m;

    # 直播 HTTP-FLV。关键点：关闭代理缓冲，避免 Nginx 为了吞吐牺牲延迟。
    location /live/ {
        proxy_pass http://127.0.0.1:25400/live/;
        proxy_http_version 1.1;

        proxy_buffering off;
        proxy_request_buffering off;
        proxy_cache off;
        gzip off;

        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    # 普通后端接口。
    location /backend/ {
        proxy_pass http://127.0.0.1:18080/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    # LLM 接口。若是流式响应，必须关闭 buffering，否则前端会感觉响应被攒包。
    location /llm/ {
        proxy_pass http://127.0.0.1:18081/;
        proxy_http_version 1.1;

        proxy_buffering off;
        proxy_request_buffering off;

        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    # WebSocket。
    location /ws/ {
        proxy_pass http://127.0.0.1:18082/;
        proxy_http_version 1.1;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;

        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

如果后端服务需要保留路径前缀，例如后端实际也希望收到 `/backend/xxx`，则把：

```nginx
proxy_pass http://127.0.0.1:18080/;
```

改成：

```nginx
proxy_pass http://127.0.0.1:18080;
```

区别是：

- `proxy_pass http://127.0.0.1:18080/;` 会去掉 `/backend/` 前缀。
- `proxy_pass http://127.0.0.1:18080;` 会保留完整路径。

## 4. ZLMediaKit 使用方式

你当前 Docker 映射可以保持不动：

```yaml
services:
  zlmediakit:
    image: zlmediakit/zlmediakit:master_py
    container_name: zlmediakit
    restart: unless-stopped
    ports:
      - "25400:80"
      - "25401:443"
      - "25402:1935"
      - "25403:554"
      - "25404:10000"
      - "25404:10000/udp"
      - "25405:8000/udp"
      - "25406:9000/udp"
    volumes:
      - ./conf:/opt/media/conf
      - ./log:/opt/media/log
      - ./www:/opt/media/www
```

go2rtc/ffmpeg 推流到：

```text
rtmp://127.0.0.1:25402/live/cam1
```

ZLMediaKit 内部 HTTP-FLV 地址：

```text
http://127.0.0.1:25400/live/cam1.live.flv
```

小程序最终访问：

```text
https://your-domain.com/live/cam1.live.flv
```

建议 ZLMediaKit 不直接暴露管理 API 到公网。如果确实要暴露 `/index/api/`，建议加鉴权、IP 白名单或只放在内网。

## 5. go2rtc/ffmpeg 低延时编码原则

上行延迟通常不是 RTMP 一个因素决定的，更多来自采集缓冲、编码缓冲、GOP、B 帧、音频缓冲和网络拥塞。低延时优先级如下：

### 5.1 关闭 B 帧

B 帧需要参考未来帧，编码器和解码器都会增加等待。直播低延时场景应关闭：

```text
bframes=0
```

### 5.2 GOP 控制在 0.5 到 1 秒

GOP 越长，关键帧间隔越大。观众首帧、断线重连、追帧都会更慢。

建议：

```text
25 fps -> keyint=25，约 1 秒 GOP
30 fps -> keyint=30，约 1 秒 GOP
```

如果追求更低首帧，可尝试：

```text
25 fps -> keyint=12 或 15，约 0.5 秒 GOP
30 fps -> keyint=15，约 0.5 秒 GOP
```

代价是码率会稍微变高。

### 5.3 x264 使用 ultrafast + zerolatency

```text
preset=ultrafast
tune=zerolatency
```

含义：

- `ultrafast` 降低编码复杂度，减少编码耗时。
- `zerolatency` 关闭或减少编码器内部缓冲，适合实时直播。

画质不是最优，但实时性最好。摄像头监控、操作查看、远程状态查看通常更适合这个取舍。

### 5.4 固定 fps

建议固定为：

```text
15 / 20 / 25 / 30 fps
```

不要让摄像头或编码链路输出不稳定帧率。帧率抖动会让播放器缓冲策略更保守。

### 5.5 音频使用 AAC，降低音频缓冲

RTMP/HTTP-FLV 链路里，AAC 是兼容性最稳的选择：

```text
AAC
44100 Hz 或 48000 Hz
64k 到 128k
```

如果只是语音或环境音，`64k` 通常够用。

## 6. ffmpeg 推流模板

下面是低延时参数模板。设备名需要按你的系统实际调整。

```bash
ffmpeg \
  -fflags nobuffer \
  -flags low_delay \
  -thread_queue_size 512 \
  -f v4l2 -framerate 25 -video_size 1280x720 -i /dev/video0 \
  -thread_queue_size 512 \
  -f alsa -i default \
  -c:v libx264 \
  -preset ultrafast \
  -tune zerolatency \
  -x264-params bframes=0:keyint=25:min-keyint=25:scenecut=0 \
  -pix_fmt yuv420p \
  -r 25 \
  -g 25 \
  -b:v 2000k \
  -maxrate 2000k \
  -bufsize 1000k \
  -c:a aac \
  -ar 44100 \
  -b:a 64k \
  -f flv \
  rtmp://127.0.0.1:25402/live/cam1
```

如果 CPU 吃紧，优先降低分辨率或帧率：

```text
1280x720 25fps -> 960x540 20fps
```

如果画面卡顿但 CPU 不高，优先检查网络、USB 摄像头输出格式和麦克风采集缓冲。

## 7. go2rtc 配置思路

go2rtc 的定位是把摄像头、麦克风、RTSP、WebRTC、RTMP 等源做聚合和转发。你的目标是让它最终向 ZLMediaKit 输出一个低延时 RTMP 流。

配置思想：

```yaml
streams:
  cam1:
    - ffmpeg:device?video=/dev/video0&audio=default#video=h264#audio=aac
```

实际部署时，重点不是照抄这一段，而是确认最终 ffmpeg 参数满足：

```text
B 帧关闭
GOP 0.5 到 1 秒
x264 ultrafast + zerolatency
fps 固定
音频 AAC
```

如果 go2rtc 的内置模板不方便精确控制参数，可以直接用外部 ffmpeg 推 RTMP 到 ZLMediaKit。这样调参最清楚，也最容易定位延迟来源。

## 8. 微信小程序 live-player 配置

小程序使用 HTTP-FLV：

```xml
<live-player
  src="https://your-domain.com/live/cam1.live.flv"
  mode="live"
  autoplay
  muted="{{false}}"
  min-cache="1"
  max-cache="2"
  object-fit="contain"
/>
```

低延时优先尝试：

```text
min-cache=0.5
max-cache=1
```

如果播放容易卡顿，调成：

```text
min-cache=1
max-cache=2
```

如果网络更差，调成：

```text
min-cache=1
max-cache=3
```

原则：

- 缓冲越小，延迟越低，但越容易卡。
- 缓冲越大，播放越稳，但延迟越高。
- 先保证不卡，再逐步压低延迟。

## 9. 小程序后台域名配置

建议只配置标准 HTTPS 域名：

```text
request 合法域名: https://your-domain.com
socket 合法域名:  wss://your-domain.com
```

如果你把直播和 API 分成两个子域名：

```text
https://live.your-domain.com
https://api.your-domain.com
```

也可以，但每个域名都需要：

- 在微信公众平台配置合法域名。
- 使用公网可信 CA 证书。
- 证书域名匹配。
- 证书链完整。
- 使用 HTTPS/WSS。

不建议让小程序访问：

```text
https://your-domain.com:25401
https://your-domain.com:18080
```

原因是非标准端口更容易遇到白名单、网络策略、证书和审核问题。

## 10. 延迟排查顺序

如果最终延迟大，按下面顺序查，不要一开始就怀疑 Nginx。

### 10.1 先测 ZLMediaKit 内网地址

在服务器本机测试：

```bash
ffplay -fflags nobuffer -flags low_delay http://127.0.0.1:25400/live/cam1.live.flv
```

如果本机已经慢，问题在上行采集、编码或 ZLMediaKit。

### 10.2 再测 Nginx HTTPS 地址

```bash
ffplay -fflags nobuffer -flags low_delay https://your-domain.com/live/cam1.live.flv
```

如果本机快、HTTPS 慢，检查：

- Nginx 是否关闭 `proxy_buffering`。
- Nginx 和 ZLMediaKit 是否在同一台机器。
- 公网带宽是否不足。
- 客户端网络是否不稳定。

### 10.3 再测小程序

如果 ffplay 快，小程序慢，检查：

- `live-player` 是否使用 HTTP-FLV URL。
- `min-cache` 和 `max-cache` 是否过大。
- 真机网络是否稳定。
- 是否误用了 HLS/m3u8。

### 10.4 检查编码参数

重点确认：

```text
B 帧是否为 0
GOP 是否 0.5 到 1 秒
fps 是否固定
是否使用 zerolatency
音频是否 AAC
码率是否超过上行或下行带宽
```

## 11. 推荐默认值

第一版建议用这组参数上线测试：

```text
分辨率: 1280x720
帧率: 25 fps
视频码率: 1500k 到 2500k
GOP: 25
B 帧: 0
编码: H.264 baseline/main
音频: AAC 44100 Hz 64k
小程序 min-cache: 1
小程序 max-cache: 2
下行协议: HTTPS HTTP-FLV
公网入口: Nginx 443
```

如果延迟优先级更高：

```text
GOP 降到 0.5 秒
min-cache=0.5
max-cache=1
码率保持稳定，不要过高
```

如果稳定性优先级更高：

```text
min-cache=1
max-cache=3
码率降低 20% 到 30%
GOP 保持 1 秒
```

## 12. 一句话总结

这个方案的核心是：用 Nginx 统一解决 HTTPS、证书、域名和路径分发；用 ZLMediaKit 专注做流媒体协议转换和 HTTP-FLV 输出；用 go2rtc/ffmpeg 从源头减少编码缓冲；小程序端使用 HTTP-FLV，在兼容性和低延迟之间取得最稳的平衡。
