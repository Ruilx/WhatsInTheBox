"""
启动入口：uvicorn 多 worker（单实例部署，dev-plan v4 §1.3 / R1 / R10）。
- 开发：python run.py --reload  （单 worker，自动重载）
- 生产：python run.py           （多 worker）
"""
import argparse
import uvicorn
from app.core import config


def main() -> None:
    parser = argparse.ArgumentParser(description="WhatsInTheBox 后端启动")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    parser.add_argument("--port", type=int, default=8004, help="监听端口（与 frontend/vite.config.ts 的 dev 代理目标 127.0.0.1:8004 对齐）")
    parser.add_argument("--reload", action="store_true", help="开发模式（自动重载，单 worker）")
    parser.add_argument("--workers", type=int, default=4, help="生产 worker 数")
    args = parser.parse_args()

    if args.reload:
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=True,
        )
    else:
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            workers=args.workers,
        )


if __name__ == "__main__":
    main()
