### 02. 폴더 구조 및 설정 시스템 구현

이 문서는 `pgv3` 파이썬 프로젝트의 **폴더 구조**와
`application.yaml` 기반 설정 로딩 방식을 실제로 만들어 가는 절차를 정의한다.

---

### 1. 폴더 구조 생성 (src 하위)

`pgv3/src/` 기준으로 아래 디렉터리를 생성한다.

1. 필수 디렉터리 생성
   - `src/api/`
   - `src/core/`
   - `src/db/`
   - `src/dto/`
     - `src/dto/request/`
     - `src/dto/response/`
   - `src/exceptions/`
   - `src/middleware/`
   - `src/models/`
     - `src/models/entity/`
   - `src/security/`
   - `src/services/`
   - `src/tools/`
   - `src/utils/`
   - `src/workers/`
     - `src/workers/actions/`
2. 각 디렉터리에 `__init__.py` 생성
   - 모든 상위 디렉터리 및 서브 디렉터리에 빈 `__init__.py` 파일을 생성해 모듈 인식이 되도록 한다.
   - 생성해야 할 예:  
     - `src/__init__.py`  
     - `src/api/__init__.py`  
     - `src/core/__init__.py`  
     - …  
     - `src/workers/actions/__init__.py`

---

### 2. 설정 파일 설계 및 `application.yaml` 초안 작성

1. 프로젝트 루트(`pgv3/`)에 `application.yaml` 을 만든다.
2. `pgv3/spec.md`의 4) 설정(Configuration) 방식을 참고하여, 다음과 같은 상위 블록을 정의한다.
   - `database:` (RDB 관련)
     - `main:` (기본 DB)
       - `engine: postgresql` 또는 `mariadb` (환경에 따라)
       - `host: ...`
       - `port: ...`
       - `username: ...`
       - `password: ...`
       - `database: ...`
   - `storage:` (MinIO/오브젝트 스토리지)
     - `endpoint: ...`
     - `accessKey: ...`
     - `secretKey: ...`
     - `bucket: ...`
   - `messaging:` (RabbitMQ)
     - `host: ...`
     - `port: ...`
     - `username: ...`
     - `password: ...`
     - `vhost: ...`
   - `redis:`
     - `host: ...`
     - `port: ...`
     - `db: 0`
   - `security:`
     - `jwtSecretKey: ...`
     - `jwtAlgorithm: HS256`
     - `accessTokenExpireMinutes: 60`
     - 기타 세션/토큰 관련 옵션
   - `kubernetes:`
     - `namespace: ...`
     - `inCluster: true|false`
     - `kubeconfigPath: ...` (필요 시)
   - `nodes:` (클러스터 노드 리소스 정보)
     - 리스트 형태로 각 노드의 CPU/memory/gpu/capacity 등을 나열
   - `analysisTool:` (분석 도구 관련 설정)
     - `defaultCpu`, `defaultGpu`, `defaultMemory`, `defaultCapacity`
     - `maxExpireDuration: "6M"` 등
   - `logging:` (선택) 로깅 레벨/포맷 등
3. 이 단계에서는 실제 비밀번호/토큰 값 대신 **플레이스홀더**나 개발용 샘플 값을만 넣는다.
   - 예: `password: "CHANGE_ME_DEV_ONLY"`
4. 민감정보 정책
   - `.env` 파일 또는 운영 환경 변수로 실제 민감정보를 관리하고,
   - `application.yaml`에는 기본 구조/기본값/플레이스홀더만 둔다.

---

### 3. 설정 로더 설계 (`src/core/config.py`)

1. `src/core/config.py` 파일을 생성한다.
2. `pydantic-settings`를 기반으로 설정 클래스를 설계한다.
   - 상위 설정 클래스 예시:
     - `class AppSettings(BaseSettings):`
       - `database: DatabaseSettings`
       - `storage: StorageSettings`
       - `messaging: MessagingSettings`
       - `redis: RedisSettings`
       - `security: SecuritySettings`
       - `kubernetes: KubernetesSettings`
       - `nodes: list[NodeSettings]`
       - `analysis_tool: AnalysisToolSettings`
   - 각 하위 Settings 클래스는 `BaseModel` or `BaseSettings` 를 사용해 필드/타입을 정의한다.
3. `YamlConfigSettingsSource` 구현 계획
   - `pydantic-settings`의 커스텀 소스를 사용해 `application.yaml`을 읽어오는 클래스를 만든다.
   - 구현 흐름:
     1. `Path("application.yaml")` 기준으로 파일을 연다.
     2. `yaml.safe_load`로 dict로 변환한다.
     3. 이 dict를 `AppSettings`에 주입하는 커스텀 소스를 정의한다.
   - 실제 코드는 나중에 작성해도 되지만, 인터페이스/함수 이름을 미리 문서에 적어둔다.
     - 예: `def load_settings() -> AppSettings: ...`
4. `get_settings()` 헬퍼 함수 설계
   - 모듈 레벨에서 Lazy Singleton 패턴으로 동작하게 한다.
   - 예:
     - `_settings: AppSettings | None = None`
     - `def get_settings() -> AppSettings: ...`
   - FastAPI 의존성 (`Depends(get_settings)`) 또는 일반 모듈에서 공통 사용.

---

### 4. 노드 리소스에서 총 리소스 계산 로직 설계

`pgv3/spec.md`에 언급된 것처럼, `nodes` 정보를 기반으로 클러스터 전체 리소스를 계산하는 로직을 설계한다.

1. `AppSettings` 또는 별도 유틸에 다음 함수를 설계한다.
   - `def calc_total_resources(nodes: list[NodeSettings]) -> ClusterResources:`
2. `ClusterResources` 모델을 정의한다.
   - 필드 예:
     - `total_cpu_milli: int`
     - `total_memory_bytes: int`
     - `total_gpu: int`
     - `total_capacity: int` (스토리지 용량 등)
3. 계산 규칙을 문서로 명시한다.
   - CPU: 각 노드의 CPU core 또는 milli-core 값을 모두 합산
   - Memory: 각 노드 메모리를 bytes 단위로 변환 후 합산
   - GPU: 단순 합산
   - Capacity: 단순 합산 또는 설정된 단위 기준 합산
4. 이 계산 결과를 설정 객체에 캐시해두기 위한 필드를 정의한다.
   - 예: `AppSettings.cluster_resources: ClusterResources`  
   - 또는 `get_cluster_resources()` 헬퍼 함수 제공

---

### 5. 환경별 설정 전략 정리

1. 최소 구성으로는 단일 `application.yaml`만 사용하고, 환경별 차이는 `.env` 또는 환경변수로 처리한다.
2. 만약 환경별 파일을 분리하고 싶다면, 아래 전략 중 하나를 선택해 이 문서에 고정한다.
   - 전략 A: `APP_ENV` 값에 따라 `application-{env}.yaml`을 추가로 로딩하고, 기본 설정과 병합
   - 전략 B: `application.yaml` 한 개만 사용하고, 환경 차이는 모두 환경변수로 오버라이드
3. 선택한 전략을 명시하고, 이후 코드에서 어떻게 읽어올지 개략적인 의사코드를 적어둔다.

---

### 6. 설정 사용 패턴 예시 메모

나중에 구현할 때 참고하기 위해, 아래와 같은 사용 예를 이 문서에 남겨둔다.

1. FastAPI 라우터에서 설정 사용 예:
   - `from src.core.config import get_settings`
   - `settings = get_settings()`
   - `db_url = settings.database.main.dsn`
2. 서비스 레이어에서 리소스 한도 확인 예:
   - `resources = get_settings().cluster_resources`
   - `if requested_cpu > resources.total_cpu_milli: raise ...`

---

### 7. 다음 단계로 넘어가기 전에 체크할 것

아래 항목을 모두 만족하면, `03-db-and-migrations.md` 문서로 넘어간다.

- [ ] `src/` 하위에 `api/core/db/dto/exceptions/middleware/models/security/services/tools/utils/workers` 디렉터리가 생성되어 있다.
- [ ] 각 디렉터리에 `__init__.py`가 생성되어 있다.
- [ ] 프로젝트 루트에 `application.yaml`이 존재하고, 기본 블록(database, storage, messaging, redis, security, kubernetes, nodes, analysisTool 등)이 정의되어 있다.
- [ ] `src/core/config.py`에 설정 클래스/로더에 대한 스켈레톤(또는 설계 주석)이 작성되었다.
- [ ] 노드 리소스 기반 총 리소스 계산 규칙이 문서에 정리되었다.

