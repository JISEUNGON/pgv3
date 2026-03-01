### Container Management System V3 — 프로젝트 개요

최종 업데이트: 2026-02-27

이 문서는 현재 개발되어 있는 `container-management` 프로젝트의 **프레임워크/라이브러리(의존성), 아키텍처, 폴더/레이어 구조, 설정 방식**을 빠르게 파악할 수 있도록 정리한 문서입니다.

---

### 1) 프레임워크 / 런타임

- **언어/런타임**: Python 3.12 (`pyproject.toml`)
- **웹 프레임워크**: FastAPI (`fastapi`)
- **ASGI 서버**: Uvicorn (`uvicorn[standard]`)
- **모델/검증**: Pydantic v2 (`pydantic`, `pydantic-settings`)
- **ORM/DB**: SQLAlchemy 2.x (`sqlalchemy`), Alembic (`alembic`)
  - **PostgreSQL**: `asyncpg`, `psycopg2-binary`
  - **MariaDB/MySQL**: `aiomysql`, `pymysql`

---

### 2) 주요 외부 연동 / 인프라 컴포넌트

`pyproject.toml` 기준.

- **Kubernetes**: `kubernetes`
- **오브젝트 스토리지(MinIO)**: `minio`
- **메시징(RabbitMQ 연동)**: `pika`
- **Redis**: `redis`
- **HTTP 클라이언트**: `httpx`
- **보안/인증 관련**: `python-jose[cryptography]`, `pyjwt`, `passlib[bcrypt]`
- **기타**: `aiofiles`, `python-dotenv`, `greenlet`

---

### 3) 아키텍처 요약 (Event-driven + 멀티프로세스)

README에 기술된 바와 같이 **순수 Python 멀티프로세스 기반 Event-driven 아키텍처**를 사용합니다.

- **진입점**: `main.py`
  - DB 마이그레이션 실행
  - RabbitMQ/MinIO/PVC 초기화 실행
  - `ProcessManager`로 자식 프로세스들을 기동/모니터링
- **프로세스 구성(대표)**:
  - **FastAPI Process**: HTTP API 처리
  - **StateMachine Worker**: 이벤트 큐 소비 + 컨테이너 작업 실행(ThreadPool 기반 병렬 처리)
  - **Monitoring Worker**: (설정에 따라) Pod 상태 모니터링 및 DB 업데이트

---

### 4) 설정(Configuration) 방식

- **메인 설정 파일**: `application.yaml`
  - DB, MinIO, RabbitMQ, 보안 토큰 이름, K8s(namespace/ssl), 노드 리소스, 옵션, 분석도구 설정 등 포함
- **설정 로더**: `src/core/config.py`
  - `pydantic-settings` 커스텀 소스(`YamlConfigSettingsSource`)로 `application.yaml`을 계층형으로 로딩
  - `nodes` 정보를 기반으로 클러스터 총 리소스(`K8S_TOTAL_*`)를 계산

---

### 5) API 구조

- **FastAPI 앱**: `src/api/app.py`
  - 라우터는 `/pgv3/v1` prefix로 등록
  - 주요 라우터:
    - `src/api/endpoints/analysis_tool.py`
    - `src/api/endpoints/image_type.py`
    - `src/api/endpoints/file_node.py`
    - `src/api/endpoints/acl.py`
    - `src/api/endpoints/app_access.py`
    - `src/api/endpoints/custom.py`
- **공통 응답 래핑**: `src/utils/common_response.py`
  - `@common_response` 데코레이터로 응답을 `ApiResponse`로 감쌈
  - 현재 정책(프로젝트 대화 기반):
    - 성공: `{"result":"1","errorCode":null,"errorMessage":null,"data":...}`
    - 예외: `{"result":"0","errorCode":"<ExceptionClassName>","errorMessage":"<message>","data":null}`
- **인증**:
  - `src/middleware/auth.py`의 `get_current_user`를 통해 세션/JWT 기반 사용자 정보 로딩
  - 세션 매니저: `src/security/session_manager.py`

---

### 6) 서비스 레이어 / DTO / 모델(ORM)

- **DTO (Pydantic)**: `src/dto/`
  - `src/dto/request/`: 요청 모델
  - `src/dto/response/`: 응답 모델 (`ApiResponse` 포함)
- **서비스 레이어**: `src/services/`
  - 예: `analysis_tool_service.py`, `container_service.py`, `resource_service.py`, `backup_service.py`
  - 원칙적으로 **비즈니스 로직은 서비스 레이어에 위치**하고 API 레이어는 호출만 담당
- **ORM 엔티티**: `src/models/entity/`
  - `containers`, `alloc_resources`, `image_info`, `image_type` 등
  - Pyright 타입 호환을 위해 주요 엔티티는 **SQLAlchemy 2.0 typed ORM(`Mapped[]/mapped_column`) 스타일**로 정리됨
- **DB 세션/베이스**: `src/db/`
  - `src/db/base.py`: `DeclarativeBase`, `GUID(TypeDecorator)` 등
  - `src/db/session.py`: AsyncSession 주입 (FastAPI DI)
  - `src/db/sync_session.py`: Worker에서 사용할 수 있는 동기 세션

---

### 7) 마이그레이션

- Alembic 기반
  - `src/alembic/`, `src/alembic.ini`
  - `src/migration/` 및 `src/db/migration/` 하위에 DB별(예: postgresql/mariadb) 마이그레이션 유틸 존재
- `main.py` 실행 시 `migration.migrator.run_migrations()`가 먼저 수행됨

---

### 8) 워커 / 작업 실행 구조

- `src/workers/`
  - `fastapi_process.py`: FastAPI 프로세스 실행
  - `statemachine_worker.py`: 이벤트 소비 + ThreadPool 실행
  - `monitoring_worker.py`: 모니터링(옵션)
  - `workers/actions/`: create/stop/delete 등 작업 단위 액션들
- `src/core/`
  - `event_queue.py`, `process_manager.py` 등 멀티프로세스 구성요소

---

### 9) 폴더 구조(요약)

프로젝트 루트 기준 핵심 디렉토리.

```text
container-management/
├── main.py
├── pyproject.toml
├── application.yaml
├── docs/
├── src/
│   ├── api/                # FastAPI app + endpoints + deps
│   ├── core/               # config, process manager, event queue 등
│   ├── db/                 # Base, session, migration helpers
│   ├── dto/                # Pydantic request/response models
│   ├── exceptions/         # BaseCustomException + error codes + 도메인 예외
│   ├── middleware/         # auth, decorators 등
│   ├── models/             # SQLAlchemy entities
│   ├── security/           # session manager 등 인증/세션
│   ├── services/           # 비즈니스 로직
│   ├── tools/              # k8s/storage 등 도구성 모듈
│   ├── utils/              # common_response 등 공통 유틸
│   └── workers/            # 멀티프로세스 워커 및 액션
└── tests/
```

---

### 10) 개발/실행 참고

- **의존성 설치(권장)**:

```bash
poetry install
```

- **실행**:

```bash
python main.py
```

- **API 문서(UI)**:
  - FastAPI Swagger: `GET /docs`
  - OpenAPI JSON: `GET /openapi.json`

---

### 11) 관련 문서

- `README.md`: 아키텍처/개요/실행 안내
- `docs/api-spec-python.md`: API 스펙 문서(상세)
- `application.yaml`: 운영/개발 환경 설정(민감정보 포함 가능 — 공유/커밋 주의)

