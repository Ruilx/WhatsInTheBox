# 部署指南（Docker）

「箱子里面有什么 / WhatsInTheBox」前后端容器化部署。

- 后端：FastAPI + pymysql（uvicorn 多 worker），监听 8000。
- 前端：Vue3 构建产物，由 nginx:alpine 提供静态文件并反代 API，监听 80。
- 数据库：你已有的 MySQL docker 容器（与后端同 `app-net` 内网，caching_sha2_password 保持不变）。

## 1. 前置条件

- 已安装 Docker + docker compose。
- 数据库已建表并初始化管理员（见 §3）。
- MySQL 容器已生成 caching_sha2 RSA 公钥（官方 mysql 镜像首次启动会自动生成；
  若 `SHOW STATUS LIKE 'Caching_sha2_password_public_key'` 为空，需重启 MySQL 让其生成，
  否则客户端缓存未命中时会间歇性 1045，详见 §4）。

## 2. 一键启动

```bash
# 在仓库根目录
docker compose up -d --build
```

- 前端访问：http://<服务器IP>/ （容器映射 80:80）
- 后端 API：http://<服务器IP>/whatsinthebox/...（由 nginx 反代）

生产建议把前端 80 端口放到 nginx/反代之后并启用 HTTPS；后端不直接暴露。

### 使用你已有的 MySQL（推荐）

```bash
# 把已有 MySQL 容器加入 app-net 网络，使其在网内可被解析为 db
docker network connect app-net <你的mysql容器名>
# 若容器名不是 db，请在 docker-compose.yml 的 backend.environment 把 DB_HOST 改成该名称
docker compose up -d --build
```

### 使用 compose 自带 MySQL

取消 docker-compose.yml 中 `db` 服务的注释，并相应取消 backend 的 `depends_on: [db]`，
然后 `docker compose up -d --build`。首次启动后用 §3 步骤建表 + 初始化管理员。

## 3. 建表与初始化管理员

任选一种方式（都需要 rw 账号具备建表权限，即 `GRANT ALL PRIVILEGES ON whatsinthebox.*`）：

**方式 A：用 mysql CLI 导入 + 建管理员**

```bash
mysql -h<db-host> -P3306 -uwhatsinthebox_rw -p whatsinthebox < backend/sql/init_db.sql
# 管理员初始化（admin/admin123）可用 backend/seed.py，或手动插入：
#   password_hash = sha256(salt + 'admin123')，salt = 任意随机串
```

**方式 B：用后端 seed 脚本**（在后端容器内执行）

```bash
docker compose exec backend python seed.py            # 建表 + 建管理员
docker compose exec backend python seed.py --reset    # 重设管理员密码
```

## 4. caching_sha2_password 与连接稳定性

- 认证插件保持 `caching_sha2_password`（安全），**不降级**为 mysql_native_password。
- 后端 `app/core/db.py` 使用**标准 PyMySQL（≥1.1）**连接参数：
  - 开启 `DB_SSL`（默认 true）时走 SSL 通道，密码经加密链路传输；
  - 缓存未命中时，标准 PyMySQL 会自动向服务端请求 RSA 公钥（握手期 0x02 包）完成认证，
    **无需**在代码里显式传入 `get_server_public_key` / `server_public_key`。
  - `connect_with_retry` 对连接类错误（1045/2013/2003/2026）做指数退避重试；
    一轮耗尽后仍失败则调用 `mysql` CLI 预热缓存再重试一轮（生产容器无 mysql 客户端时自动跳过）。
- 前提：服务端 RSA 公钥已生成并加载（官方 mysql 镜像首次启动自动生成；见 §1）。
  若 `SHOW STATUS LIKE 'Caching_sha2_password_public_key'` 为空，重启 MySQL 让其生成即可根治。
  （注：`SHOW STATUS` 为空不代表握手拿不到公钥——CLI / 标准 pymysql 仍能经握手取得。）

## 7. 关于 MySQL 连接

> ⚠️ dev MySQL `10.25.0.201` 已退役，现用**公司测试库 `10.4.215.193:3306`**。后端 `db.py` 连接时不选库 + 全限定表名（`whatsinthebox.xxx`），`DB_SSL=false` 明文；新库 rw=`whatsinthebox_rw`/`whatsintheboxrwmysqlpassword`(ALL on `whatsinthebox.*`)。下文针对 10.25.0.201 的诊断结论已作废，仅作历史留档。

> ⚠️ 诊断已更新（2026-08-13 复测，覆盖旧版结论）：早前观察到「只有原生 `mysql` CLI 能连、所有 Python 驱动 1045」，
> 现**已证伪**——复测时原生 CLI 与所有 Python 驱动**同样**返回
> `1045 Access denied for 'whatinthebox_rw'@'10.25.0.24'`（SSL / 明文均如此）。
> 说明这不是「代理只放行 CLI 握手」，而是**该 rw 账号的凭证 / 授权当前不匹配**：
> `.env` 中的密码 `whatsintheboxrwmysqlpassword` 无法从客户端 IP `10.25.0.24` 通过认证
> （密码不符，或账号 host 白名单不含 `10.25.0.24`，或账号被改 / 重建过）。
> 这与后端代码无关（db.py 为标准 PyMySQL 写法），属服务端账号 / 密码治理范畴。

现象（复测）：
- `mysql -h10.25.0.201 -P3306 -uwhatsinthebox_rw -pwhatsintheboxrwmysqlpassword -e "SELECT 1"`
  → `ERROR 1045 (28000): Access denied for user 'whatinthebox_rw'@'10.25.0.24'`。
- 同一账号、同一密码，Python 驱动（pymysql / mysql-connector-python / mysqlclient）`connect()` 同样 `1045`。
- 两者失败**完全一致** → 不是驱动差异，是凭证 / 授权问题。
- 网络可达（能拿到 MySQL 协议层 1045，而非超时 / 拒绝连接），故非网络或防火墙问题。

修复（任选其一，需有该库管理员权限）：
1. **重设 rw 密码与 .env 一致**（最快）：
   ```sql
   -- 若账号已存在（host 可能是 '%' 或具体 IP）：
   ALTER USER 'whatsinthebox_rw'@'%'
     IDENTIFIED WITH caching_sha2_password BY 'whatsintheboxrwmysqlpassword';
   GRANT ALL PRIVILEGES ON whatsinthebox.* TO 'whatsinthebox_rw'@'%';
   FLUSH PRIVILEGES;
   -- 若不存在则先建：CREATE USER 'whatsinthebox_rw'@'%'
   --   IDENTIFIED WITH caching_sha2_password BY 'whatsintheboxrwmysqlpassword';
   ```
2. **或告诉我当前真实密码**：把 `backend/.env` 的 `DB_PASSWORD` 改成实际值即可
   （账号 host 白名单需含 `10.25.0.24` 或 `%`）。
3. 确认账号存在且 host 覆盖客户端 IP：
   ```sql
   SELECT user, host, plugin FROM mysql.user WHERE user='whatsinthebox_rw';
   ```

对部署的影响与建议：
- 凭证修好后，后端代码**无需任何改动**即可连上（db.py 为标准 PyMySQL 写法）。
- 本地 `pip` 镜像另发**被篡改的 PyMySQL 轮子**（伪装成 `1.4.6`），叠加干扰本地排障；
  但 1045 与轮子无关（CLI 也 1045）。**验证请走 Docker**：`docker compose up -d --build` 后
  在 backend 容器内 `pip install -r requirements-dev.txt && pytest`（容器内为官方 PyMySQL + 标准 MySQL）。
- 本机未安装 Docker，无法在本地跑实时冒烟 / pytest，需 Docker 或干净环境验证。

## 5. 环境变量

见 `backend/.env.example`。关键项：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| DB_HOST | 数据库主机（Docker 内网填服务名 db） | db |
| DB_USER / DB_PASSWORD | rw 账号 | - |
| DB_NAME | 库名 | whatsinthebox |
| DB_SSL | 是否 SSL 连接（本地 dev 用 false 明文；连接时不选库+库限定表名的方式不依赖 TLS） | true |
| GLOBAL_PREFIX | 活动 URL 保留前缀 | _wb |
| API_PREFIX | 后端路由前缀 | /whatsinthebox |
| SESSION_EXPIRE_HOURS | 会话有效期(小时) | 4 |
| CORS_ORIGINS | 允许的前端源(逗号分隔) | http://localhost |
| ADMIN_USER / ADMIN_PASS | 初始化管理员 | admin / admin123 |

## 6. 常见排错

- **后端起不来 / 1045**：检查 DB_HOST 是否指向同网络 MySQL、rw 密码是否正确、服务端 RSA 公钥是否已生成（§4）。
- **前端白屏 / API 404**：确认 nginx 反代 `/whatsinthebox` 与 `/uploads` 到 backend:8000；
  前端 `VITE_API_BASE` 默认 `/whatsinthebox`（相对路径，无需改）。
- **上传文件 404**：确认后端 `UPLOAD_DIR` 已挂载/可写，且 nginx `/uploads` 反代到位。
- **CORS 报错**：把前端正式域名加入后端 `CORS_ORIGINS`（同网反代下通常同源，不会触发）。
