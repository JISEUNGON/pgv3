from __future__ import annotations

import uvicorn

from src.api.app import create_app
from src.core.process_manager import ProcessManager


def run_fastapi() -> None:
    """
    개발 초기 단계: FastAPI 단일 프로세스 실행 진입점.
    멀티프로세스 구조가 준비되기 전까지는 이 함수를 사용한다.
    """

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)


def run_all_processes() -> None:
    """
    07-workers-and-event-system.md 를 따라
    ProcessManager 를 이용해 FastAPI + Worker 프로세스를 모두 올리는 진입점.
    """
    manager = ProcessManager()
    manager.start_all()


if __name__ == "__main__":
    # 현재는 개발 편의를 위해 FastAPI 단일 프로세스만 실행한다.
    run_fastapi()

