### 08. K8s, MinIO, RabbitMQ, Redis 연동 설계

이 문서는 pgv3 컨테이너 관리 시스템에서 사용하는 **외부 인프라 연동 모듈**(Kubernetes, 오브젝트 스토리지, 메시징, 캐시)을 설계한다.

---

### 1. 공통 설계 원칙

1. 모든 외부 연동은 `src/tools/` 하위 모듈로 캡슐화한다.
2. 서비스/워커 레이어에서는 이 도구 모듈의 인터페이스만 의존하고, 구체 구현은 교체 가능하도록 만든다.
3. 설정 값은 `src/core/config.py`의 `AppSettings`를 통해 주입한다.

---

### 2. Kubernetes 연동 (`src/tools/k8s_client.py`)

1. `src/tools/k8s_client.py` 파일을 생성한다.
2. 의존 라이브러리
   - `kubernetes` Python 클라이언트 사용
3. 설정 주입
   - `KubernetesSettings` (namespace, inCluster, kubeconfigPath 등)를 생성자 인자로 받는다.
4. 주요 기능 설계
   - Pod/Deployment 생성
     - Analysis Tool를 실행하기 위한 Deployment/Pod spec 생성
     - 리소스 요청/제한(CPU/memory/GPU)을 설정 값과 요청 값에 맞게 조합
   - Pod/Deployment 삭제
   - 상태 조회
     - 툴 ID 또는 containerId 기준으로 Pod 상태 조회
   - 로그 조회 (선택)
5. 메서드 예시
   - `create_tool_pod(tool: AnalysisTool, resources: ResourceSpec) -> str`  (containerId 반환)
   - `delete_tool_pod(container_id: str) -> None`
   - `get_tool_status(container_id: str) -> ToolStatus`
6. 멀티 클러스터/네임스페이스 지원 여부가 필요하면, 해당 전략을 이 문서에 명시한다.

---

### 3. Container Management API 연동 (`src/tools/container_client.py`)

1. K8s 클라이언트와 분리하여, 상위 레벨의 “컨테이너 관리 API”를 담당하는 모듈을 설계한다.
2. 역할:
   - Analysis Tool 생성/삭제/재시작/설정 변경/백업 복원 등의 고수준 오퍼레이션 제공
3. 메서드 예시:
   - `create_tool_container(tool_info, resource_info) -> str`
   - `stop_tool_container(container_id: str) -> None`
   - `restart_tool_container(container_id: str) -> None`
   - `delete_tool_container(container_id: str) -> None`
   - `backup_tool_container(container_id: str, backup_options) -> str`
4. 내부에서 K8s 클라이언트/스토리지/기타 API를 조합할지, 또는 별도의 Container Management HTTP API를 호출할지 선택하고, 이 문서에 전략을 기록한다.

---

### 4. MinIO/오브젝트 스토리지 연동 (`src/tools/storage_client.py`)

1. `src/tools/storage_client.py` 파일을 생성한다.
2. 의존 라이브러리
   - `minio` Python 클라이언트 사용
3. 설정 주입
   - `StorageSettings` (endpoint, accessKey, secretKey, bucket 등)를 생성자 인자로 받는다.
4. 주요 기능
   - 파일 업로드
   - 파일 다운로드
   - 객체 메타데이터 조회
5. 메서드 예시
   - `upload_file(file_path: str, object_name: str, content_type: str | None = None) -> str`
   - `download_file(object_name: str, target_path: str) -> None`
   - `get_object_url(object_name: str, expire_seconds: int) -> str`
6. File Node/Analysis Tool 파일 연동에서 이 클라이언트를 사용해 데이터 이동을 구현하도록 설계한다.

---

### 5. RabbitMQ/메시징 연동 (`src/tools/messaging.py`)

1. `src/tools/messaging.py` 파일을 생성한다.
2. 의존 라이브러리
   - `pika` 사용
3. 설정 주입
   - `MessagingSettings` (host, port, username, password, vhost, queue 이름 등)
4. 기능 설계
   - 큐 생성/보장
   - 이벤트 퍼블리시
   - 이벤트 소비 (consume)
5. 인터페이스
   - `class RabbitMQClient:`
     - `def publish(self, queue: str, message: dict) -> None: ...`
     - `def consume(self, queue: str, handler: Callable[[dict], None]) -> None: ...`
6. `src/core/event_queue.py`의 `EventQueue` 추상화와 연결
   - `RabbitMQEventQueue(EventQueue)` 구현체를 만들고, 내부에서 `RabbitMQClient`를 사용하도록 설계한다.

---

### 6. Redis/캐시 연동 (`src/tools/cache.py`)

1. `src/tools/cache.py` 파일을 생성한다.
2. 의존 라이브러리
   - `redis` Python 클라이언트 사용
3. 설정 주입
   - `RedisSettings` (host, port, db 등)
4. 주요 사용 용도
   - 세션/토큰 저장
   - 임시 상태/락 정보 저장 (예: 중복 요청 방지)
5. 메서드 예시
   - `set(key: str, value: str, expire_seconds: int | None = None)`
   - `get(key: str) -> str | None`
   - `delete(key: str) -> None`

---

### 7. Graphio/Meta ACL/기타 HTTP 연동 (`src/tools/graphio_client.py`, `src/tools/meta_acl_client.py`, `src/tools/http_client.py`)

1. Graphio 클라이언트
   - `src/tools/graphio_client.py`
   - `httpx`를 이용해 Graphio API 호출
   - Access Token 처리, 기본 URL 설정 등
2. Meta ACL 클라이언트
   - `src/tools/meta_acl_client.py`
   - ACL 조회/업데이트용 HTTP API 래퍼
3. 공통 HTTP 클라이언트 (선택)
   - `src/tools/http_client.py`
   - `httpx.AsyncClient` 또는 `httpx.Client`를 감싼 헬퍼

---

### 8. 설정(`application.yaml`)과의 연결

1. 각 도구 모듈은 `src/core/config.py`의 설정 객체를 입력으로 받아 초기화한다.
   - 예:
     - `settings = get_settings()`
     - `k8s_client = KubernetesClient(settings.kubernetes)`
     - `storage_client = StorageClient(settings.storage)`
2. 서비스/워커/ProcessManager에서 이들 클라이언트를 생성하는 위치를 결정해 이 문서에 메모한다.
   - 예:
     - ProcessManager 생성 시 공통 클라이언트를 만들어 워커 프로세스에 전달
     - 또는 각 프로세스 안에서 `get_settings()`를 호출해 직접 클라이언트 생성

---

### 9. 에러/재시도 정책 요약

1. K8s/Container 실패
   - 재시도 횟수/간격을 설정 값으로 둘지 여부 결정
2. MinIO 업로드/다운로드 실패
   - 네트워크/권한 오류 시 어떻게 처리할지 (예: 로그 + 예외 전파)
3. RabbitMQ 연결 끊김
   - 연결 재시도 루프를 둘지, 애플리케이션을 종료할지 정책을 문서에 정의
4. Redis 장애
   - 세션/캐시 미사용 상태에서 동작 가능한지, 아니면 강제 에러로 처리할지 결정

---

### 10. 다음 단계로 넘어가기 전에 체크할 것

아래 항목을 모두 만족하면, `09-auth-security-and-common-api.md` 문서로 넘어간다.

- [ ] `src/tools/k8s_client.py`에 K8s 연동용 클래스와 주요 메서드가 설계되어 있다.
- [ ] `src/tools/container_client.py`에 컨테이너 관리용 고수준 API가 설계되어 있다.
- [ ] `src/tools/storage_client.py`, `src/tools/messaging.py`, `src/tools/cache.py`의 역할과 인터페이스가 정의되어 있다.
- [ ] Graphio/Meta ACL/HTTP 클라이언트 모듈 구조와 역할이 정리되어 있다.
- [ ] 각 클라이언트가 `application.yaml`의 설정과 어떻게 연결되는지 설계되어 있다.

