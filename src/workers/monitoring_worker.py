from __future__ import annotations

import time

from src.utils.logging import configure_root_logger, get_logger

logger = get_logger(__name__)


def main() -> None:
    configure_root_logger()
    logger.info("Monitoring worker started")

    while True:
        # TODO: K8s/Container 상태 조회 및 DB 업데이트, 필요시 이벤트 발행
        time.sleep(5)


if __name__ == "__main__":
    main()

