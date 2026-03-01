from __future__ import annotations

import multiprocessing
from multiprocessing import Process
from typing import Dict

from src.utils.logging import get_logger

logger = get_logger(__name__)


class ProcessManager:
    """
    FastAPI / StateMachine / Monitoring 프로세스를 관리하는 간단한 매니저.
    현재는 최소 스켈레톤만 구현하며, 실제 비즈니스 로직은 이후 확장한다.
    """

    def __init__(self) -> None:
        self.children: Dict[str, Process] = {}

    def start_fastapi(self) -> None:
        from src.workers.fastapi_process import main as fastapi_main

        proc = multiprocessing.Process(target=fastapi_main, name="fastapi")
        proc.start()
        self.children["fastapi"] = proc
        logger.info("Started FastAPI process pid=%s", proc.pid)

    def start_statemachine_worker(self) -> None:
        from src.workers.statemachine_worker import main as sm_main

        proc = multiprocessing.Process(target=sm_main, name="statemachine")
        proc.start()
        self.children["statemachine"] = proc
        logger.info("Started StateMachine worker pid=%s", proc.pid)

    def start_monitoring_worker(self) -> None:
        from src.workers.monitoring_worker import main as mon_main

        proc = multiprocessing.Process(target=mon_main, name="monitoring")
        proc.start()
        self.children["monitoring"] = proc
        logger.info("Started Monitoring worker pid=%s", proc.pid)

    def start_all(self) -> None:
        self.start_fastapi()
        self.start_statemachine_worker()
        self.start_monitoring_worker()

    def stop(self, name: str) -> None:
        proc = self.children.get(name)
        if proc and proc.is_alive():
            proc.terminate()
            proc.join(timeout=5)
            logger.info("Stopped process %s pid=%s", name, proc.pid)

    def stop_all(self) -> None:
        for name in list(self.children.keys()):
            self.stop(name)

    def check_health(self) -> None:
        for name, proc in list(self.children.items()):
            if not proc.is_alive():
                logger.warning("Process %s pid=%s is not alive", name, proc.pid)

