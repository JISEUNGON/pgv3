### 07. 멀티프로세스, 이벤트 큐, 워커 설계

이 문서는 pgv3 컨테이너 관리 시스템의 **멀티프로세스 아키텍처, 이벤트 큐, 워커 프로세스 구조**를 정의한다.

---

### 1. 전체 프로세스 구조 개요

1. 프로세스 종류
   - FastAPI Process
     - HTTP API 처리
   - StateMachine Worker
     - 이벤트 큐 소비 + 컨테이너 작업 실행 (ThreadPool 기반 병렬 처리)
   - Monitoring Worker
     - K8s Pod/컨테이너 상태 모니터링 및 DB 업데이트
2. 진입점
   - `main.py`
     - DB 마이그레이션 실행
     - RabbitMQ/MinIO/PVC 등 외부 리소스 초기화
     - `ProcessManager`로 위 프로세스들을 기동/모니터링

---

### 2. ProcessManager 설계 (`src/core/process_manager.py`)

1. `src/core/process_manager.py` 파일을 생성한다.
2. `ProcessManager` 클래스 설계
   - 필드:
     - `children: dict[str, subprocess.Popen | multiprocessing.Process]` (또는 유사 구조)
   - 주요 메서드:
     - `start_all()`: FastAPI/StateMachine/Monitoring 프로세스를 모두 시작
     - `start_fastapi()`
     - `start_statemachine_worker()`
     - `start_monitoring_worker()`
     - `stop(name: str)`
     - `stop_all()`
     - `check_health()`: 각 프로세스의 상태를 확인하고, 비정상 종료 시 재기동 또는 알림
3. 프로세스 시작 방식 결정
   - Python `multiprocessing` 모듈 vs `subprocess` vs `uvicorn` 프로세스 직접 실행 중 어떤 방식을 쓸지 선택하고 문서에 기록.
   - 예: StateMachine/Monitoring은 `multiprocessing.Process`로, FastAPI는 `uvicorn` 서브프로세스로.
4. 로그/에러 처리 정책
   - 각 자식 프로세스의 stdout/stderr를 어떻게 수집할지 (파일로그, 표준로그 등) 간단히 메모.

---

### 3. Event Queue 설계 (`src/core/event_queue.py`)

1. `src/core/event_queue.py` 파일을 생성한다.
2. 이벤트 타입 정의
   - Enum 예: `class EventType(str, Enum): CREATE = "CREATE"; STOP = "STOP"; DELETE = "DELETE"; BACKUP = "BACKUP"; ...`
3. 이벤트 페이로드 모델
   - Pydantic 모델 예: `class EventPayload(BaseModel): event_type: EventType; tool_id: int; user_id: str; ...`
4. 큐 인터페이스 설계
   - `class EventQueue(Protocol):`
     - `def publish(self, event: EventPayload) -> None: ...`
     - `def consume(self, handler: Callable[[EventPayload], None]) -> None: ...`
   - 실제 구현은 RabbitMQ/Redis 중 하나를 선택하여 `src/tools/messaging.py`에 두고, 여기서는 추상화만 다룬다.
5. StateMachine/Monitoring Worker에서 이 인터페이스를 사용하도록 설계한다.

---

### 4. FastAPI 프로세스 워커 (`src/workers/fastapi_process.py`)

1. `src/workers/fastapi_process.py` 파일을 생성한다.
2. 역할:
   - 단일 프로세스에서 FastAPI 앱을 실행
   - 실질적으로는 `uvicorn.run("src.api.app:app", ...)` 호출
3. main 진입점 구조:
   - `def main():`
     - 설정 로딩 (필요 시)
     - `uvicorn.run(...)`
   - `if __name__ == "__main__": main()`
4. `ProcessManager.start_fastapi()`에서 이 모듈을 서브프로세스로 실행하도록 설계.

---

### 5. StateMachine Worker (`src/workers/statemachine_worker.py`)

1. `src/workers/statemachine_worker.py` 파일을 생성한다.
2. 역할:
   - Event Queue를 구독하고, 들어온 이벤트를 ThreadPool에 분배하여 처리
3. 설계 단계:
   - 이벤트 루프:
     - `while True:`
       - 큐에서 메시지를 하나 읽어온다.
       - 적절한 액션 핸들러로 디스패치한다.
   - ThreadPool:
     - Python `concurrent.futures.ThreadPoolExecutor` 또는 `asyncio` 기반 병렬 처리 중 선택
   - 액션 디스패처:
     - `src/workers/actions/` 하위 모듈에 정의된 함수/클래스를 호출
4. 초기 액션 종류:
   - `create_container`
   - `stop_container`
   - `delete_container`
   - `backup_container`
   - 등, Analysis Tool 관련 작업
5. 예외 처리 전략:
   - 액션 수행 실패 시 로그 기록 및 재시도 전략 여부를 이 문서에 메모.

---

### 6. Monitoring Worker (`src/workers/monitoring_worker.py`)

1. `src/workers/monitoring_worker.py` 파일을 생성한다.
2. 역할:
   - 주기적으로 K8s/Container 상태를 조회하고 DB 상태/툴 상태를 갱신
3. 설계 단계:
   - 루프:
     - `while True:`
       - 모든(또는 일부) Analysis Tool에 대한 컨테이너 상태 조회
       - 상태 변화가 있는 경우 DB/엔티티 업데이트
       - 일정 주기(`sleep` 또는 스케줄러)로 반복
   - K8s/컨테이너 조회는 `src/tools/k8s_client.py` 또는 `src/tools/container_client.py`를 사용
4. 상태 변화에 따른 이벤트 발행 여부:
   - 예: 상태가 특정 값으로 변할 때 추가 작업이 필요하면 Event Queue에 새 이벤트를 발행하도록 설계할 수 있다.

---

### 7. 액션 모듈 설계 (`src/workers/actions/`)

1. 다음 파일을 계획한다.
   - `src/workers/actions/create.py`
   - `src/workers/actions/stop.py`
   - `src/workers/actions/delete.py`
   - `src/workers/actions/backup.py`
   - 필요 시 `update_resource.py`, `expire.py` 등
2. 각 파일에는 해당 작업을 담당하는 함수/클래스를 정의한다.
   - 예:
     - `def handle_create(event: EventPayload, container_client: ContainerClient, db: Session): ...`
3. StateMachine Worker는 이벤트 타입에 따라 적절한 액션 함수를 선택해 실행한다.

---

### 8. main.py와의 연결 플로우

1. `main.py`에서의 실행 순서는 다음과 같이 정의한다.
   1. 설정 로딩 (`get_settings()`)
   2. DB 마이그레이션 실행 (`run_migrations()` 또는 Alembic 호출)
   3. 외부 리소스 초기화 (RabbitMQ/MinIO/PVC 등)
   4. `ProcessManager` 인스턴스 생성
   5. `ProcessManager.start_all()` 호출
2. 개발 초기 단계에서는
   - 멀티프로세스가 불안정할 수 있으므로, `run_fastapi()`만 실행하는 모드와
   - 풀 모드를 선택할 수 있는 플래그/환경변수를 둘지 여부를 이 문서에서 결정한다.

---

### 9. 장애/에러 처리 전략 (요약)

1. 자식 프로세스 비정상 종료 시
   - `ProcessManager.check_health()`에서 감지
   - 재기동 시도 횟수/간격을 제한하는 정책 정의
2. Event Queue 연결 장애
   - 일정 횟수 재시도 후, 로그를 남기고 워커를 안전하게 종료 혹은 대기 상태로 유지
3. K8s/Container API 호출 실패
   - 재시도 로직 또는 에러 이벤트 발행 여부를 설계

---

### 10. 다음 단계로 넘어가기 전에 체크할 것

아래 항목을 모두 만족하면, `08-integration-k8s-storage-messaging.md` 문서로 넘어간다.

- [ ] `src/core/process_manager.py`에 ProcessManager 클래스 구조와 메서드 목록이 설계되어 있다.
- [ ] `src/core/event_queue.py`에 이벤트 타입/페이로드/큐 인터페이스가 정의되어 있다.
- [ ] `src/workers/fastapi_process.py`, `statemachine_worker.py`, `monitoring_worker.py`의 역할/루프 구조가 정리되어 있다.
- [ ] `src/workers/actions/` 하위에 액션별 파일/함수 구조가 정의되어 있다.
- [ ] `main.py`에서 설정 로딩 → 마이그레이션 → 외부 리소스 초기화 → ProcessManager 시작 순서가 명확히 정의되어 있다.

