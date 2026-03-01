### 00. 개요 및 v2 → v3 매핑 설계

이 문서는 `pgv2-origin/project/playground` (Spring Boot 기반)에서 제공하던 기능을
`pgv3` 파이썬 프로젝트(FastAPI 기반 컨테이너 관리 시스템 v3)로 옮기기 위한 **전체 그림과 매핑 표**를 정의한다.

실제 코드를 작성하기 전에, 이 문서를 먼저 읽고 아래 순서대로 체크하면서
다른 `01~09` 문서를 진행하면 된다.

---

### 1. 프로젝트 목표 정리

1. pgv2 `playground`가 제공하는 API 그룹을 모두 나열한다.
   - App Access Log
   - File Node
   - ACL
   - Analysis Tool (메타/목록/상세/승인/백업/미리보기/파일연동)
   - Graphio
   - Common
   - IRIS
   - Time
2. `pgv3/spec.md`를 기준으로, pgv3가 가져야 할 공통 인프라/아키텍처를 요약한다.
   - 언어/런타임: Python 3.12
   - 웹 프레임워크: FastAPI
   - ASGI 서버: Uvicorn
   - ORM/DB: SQLAlchemy 2.x + Alembic, PostgreSQL/MariaDB 지원
   - 외부 연동: Kubernetes, MinIO, RabbitMQ, Redis, HTTPX, 인증 관련 라이브러리 등
   - 아키텍처: 멀티프로세스 + 이벤트 기반 (FastAPI 프로세스, StateMachine Worker, Monitoring Worker)
3. 최종 목표를 다음과 같이 문장으로 기록한다.
   - “pgv2 playground의 주요 API와 비즈니스 로직을 유지하면서, pgv3에서 정의된 컨테이너 관리 아키텍처와 폴더 구조, 설정 방식을 따르는 Python 프로젝트를 만든다.”

---

### 2. 레이어/폴더 구조 개념 잡기

아래 레이어를 기준으로, 각 레이어가 어떤 책임을 가지는지 명확히 적어둔다.

1. **API 레이어 (`src/api`)**
   - FastAPI 앱/라우터 정의
   - 요청/응답 DTO와 HTTP 세부 사항 (path, query, body, status code 등)
   - 인증/세션 의존성 주입
2. **서비스 레이어 (`src/services`)**
   - 비즈니스 로직의 중심
   - 트랜잭션, 검증, 상태 전이, 외부 시스템 호출 orchestration
3. **DTO 레이어 (`src/dto`)**
   - 요청/응답용 Pydantic 모델
   - v2에서 사용하던 필드명을 최대한 유지하되, Python/PGV3 스타일에 맞게 필요한 부분만 조정
4. **모델/ORM 레이어 (`src/models`)**
   - SQLAlchemy 엔티티 (테이블 구조, 관계)
   - Alembic 마이그레이션 메타데이터와 연결
5. **DB/세션 레이어 (`src/db`)**
   - AsyncSession/SyncSession 팩토리
   - DB 연결 문자열 구성
6. **코어/워커 레이어 (`src/core`, `src/workers`)**
   - 설정 로더, 이벤트 큐, 프로세스 매니저
   - FastAPI/StateMachine/Monitoring 프로세스 진입점
7. **도구/외부 연동 레이어 (`src/tools`)**
   - K8s, MinIO, RabbitMQ, Redis, Graphio, Meta ACL 등 클라이언트/헬퍼
8. **보안/세션/미들웨어 (`src/security`, `src/middleware`)**
   - JWT/세션 관리
   - 인증 미들웨어/의존성
9. **공통 응답/예외/유틸 (`src/dto/response`, `src/exceptions`, `src/utils`)**
   - `ApiResponse` 포맷
   - 공통 예외 계층, 에러 핸들러

이 항목은 개념 정리용이며, 실제 디렉터리/파일 생성은 `02-folder-structure-and-config.md`에서 구체적으로 수행한다.

---

### 3. v2 서비스 → v3 서비스/엔드포인트 매핑 표 작성

아래 표를 실제로 문서에 채워 넣는다. (처음에는 대략적으로 채우고, 구현을 진행하면서 보완 가능)

1. **서비스/컨트롤러 매핑 (예시)**  
   - App Access Log
     - v2: `AppAccessLogService`, 관련 Controller
     - v3 서비스: `src/services/app_access_service.py`
     - v3 엔드포인트: `src/api/endpoints/app_access.py`
   - File Node
     - v2: `FileNodeService`
     - v3 서비스: `src/services/file_node_service.py`
     - v3 엔드포인트: `src/api/endpoints/file_node.py`
   - ACL
     - v2: `AclService`
     - v3 서비스: `src/services/acl_service.py`
     - v3 엔드포인트: `src/api/endpoints/acl.py`
   - Analysis Tool
     - v2: `AnalysisToolService` (+ Approval/Backup 관련)
     - v3 서비스: `src/services/analysis_tool_service.py`, `src/services/backup_service.py`
     - v3 엔드포인트: `src/api/endpoints/analysis_tool.py`
   - Graphio
     - v2: `GraphioWebService`, `GraphioService`
     - v3 서비스: `src/services/graphio_service.py`
     - v3 엔드포인트: `src/api/endpoints/graphio.py`
   - Common/IRIS/Time
     - v2: `CommonController`, `IRISService`, `TimeService` 등
     - v3 서비스: `src/services/common_service.py`, `src/services/iris_service.py`, `src/services/time_service.py`
     - v3 엔드포인트: `src/api/endpoints/common.py`, `src/api/endpoints/iris.py`, `src/api/endpoints/time.py`

2. **엔티티/테이블 매핑 (예시)**  
   각 도메인에서 사용되는 핵심 테이블을 SQLAlchemy 엔티티로 옮길 계획을 기록한다.
   - App Access Log
     - v2 테이블: `app_access_log` (가정, 실제 이름은 v2 SQL 확인 후 수정)
     - v3 엔티티: `src/models/entity/app_access_log.py` 내 `AppAccessLog`
   - File Node
     - v2 테이블: `file_node` 계열
     - v3 엔티티: `src/models/entity/file_node.py` 내 `FileNode`
   - Analysis Tool
     - v2 테이블: `analysis_tool`, `analysis_tool_approval`, `analysis_tool_backup` 등
     - v3 엔티티: 각각 별도 파일에 정의

3. **외부 시스템 매핑 (예시)**  
   v2에서 직접 사용하던 컴포넌트/클라이언트를 pgv3의 `tools` 레이어로 옮기는 계획을 작성한다.
   - Meta ACL API → `src/tools/meta_acl_client.py`
   - Container Management API → `src/tools/container_client.py`
   - Graphio API → `src/tools/graphio_client.py`
   - 파일 저장소 → `src/tools/storage_client.py`

---

### 4. 작업 순서 상위 타임라인 확정

아래 순서를 문서에 그대로 적고, 실제 구현 시 체크박스 형태로 사용한다.

1. **[ ] 1단계 – 프로젝트 뼈대/의존성/폴더 구조**
   - `01-project-setup-and-dependencies.md`
   - `02-folder-structure-and-config.md`
2. **[ ] 2단계 – 설정/환경 구성**
   - `02-folder-structure-and-config.md`
3. **[ ] 3단계 – DB/ORM/마이그레이션**
   - `03-db-and-migrations.md`
4. **[ ] 4단계 – 공통 컴포넌트/예외/응답 래퍼**
   - `04-common-components-and-exceptions.md`
5. **[ ] 5단계 – API/서비스 도메인별 구현**
   - `05-api-layer-design.md`
   - `06-service-layer-design.md`
6. **[ ] 6단계 – 워커/이벤트/컨테이너 연동**
   - `07-workers-and-event-system.md`
   - `08-integration-k8s-storage-messaging.md`
7. **[ ] 7단계 – 인증/ACL/공통 API 마무리**
   - `09-auth-security-and-common-api.md`

테스트 코드는 이 계획에서 제외하며, 이후 필요 시 별도 문서/작업으로 다룬다.

---

### 5. 이후 문서 사용 방법

1. 이 `00` 문서를 먼저 읽고, v2 → v3 매핑이 이해되면 다음으로 넘어간다.
2. `01` 문서부터 순서대로 진행하되, 도중에 구조를 바꿔야 할 경우 이 `00` 문서의 매핑 표/타임라인을 먼저 수정한다.
3. 실제 구현 중에 발견한 제약/결정 사항(예: 필드명 변경, API 경로 조정)은
   - 해당 도메인 문서(05~09)와
   - 여기 `00` 문서의 매핑 표
   두 곳에 함께 기록해, 전체 일관성을 유지한다.

