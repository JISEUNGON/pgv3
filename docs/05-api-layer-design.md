### 05. API 레이어(FastAPI 엔드포인트) 설계

이 문서는 pgv2 `playground`의 REST API를 pgv3 FastAPI 기반으로 옮기기 위해,
**엔드포인트 구조, 라우터 파일 구분, DTO 매핑**을 정의한다.

---

### 1. FastAPI 앱 기본 구성 (`src/api/app.py`)

1. `src/api/app.py` 파일을 생성한다.
2. FastAPI 인스턴스 생성 설계
   - `app = FastAPI(title="Container Management V3", version="0.1.0")`
3. 공통 prefix 정책
   - **중요**: 기존 pgv2 playground와 동일한 context-path를 유지한다.
   - 즉, 별도의 `/pgv3` prefix 없이, 기존 엔드포인트 그대로 사용한다.
     - 예: `/v1/app-access/add`, `/v1/file-node`, `/api/status`, `/service/time/servertime` 등
4. 아래 항목을 이 문서에 메모한 뒤, 실제 구현 시 해당 위치에서 코드를 작성한다.
   - 라우터들을 import 후 `app.include_router(router)` 또는 필요한 최소 prefix만 사용 (예: `prefix="/v1"` 등, v2와 동일하게)
   - 공통 예외 핸들러 등록
   - 미들웨어/이벤트 핸들러(on_startup/on_shutdown) 등록

---

### 2. 라우터 모듈 구조 정의 (`src/api/endpoints/`)

1. `src/api/endpoints/` 디렉터리를 사용하여 API 그룹별 파일을 나눈다.
2. 최소 파일 목록을 다음과 같이 정의한다.
   - `analysis_tool.py`
   - `image_type.py`
   - `file_node.py`
   - `acl.py`
   - `app_access.py`
   - `graphio.py`
   - `common.py`
   - `iris.py`
   - `time.py`
3. 각 파일에서 다음 요소를 갖도록 설계한다.
   - `router = APIRouter(prefix="/...", tags=["..."])`
   - 의존 서비스 (예: `AnalysisToolService`) 주입 방식
   - 공통 응답 데코레이터(`@common_response`) 적용 여부

---

### 3. pgv2 → pgv3 엔드포인트 매핑 (요약표)

아래는 `SERVICE_LAYER_API_LOGIC.md` 기준으로 각 그룹별 주요 엔드포인트를
pgv3에서 어떤 라우터 파일/경로로 둘지 정리한 것이다.

#### 3.1. App Access Log API (`app_access.py`)

- `POST /v1/app-access/add`
  - 목적: 접속 로그 추가
  - v3 경로: **기존과 동일** `POST /v1/app-access/add`
  - 서비스 메서드: `AppAccessService.add_access_log`
- `GET /v1/app-access`
  - 목적: 목록 + 카운트 조회
  - v3 경로: **기존과 동일** `GET /v1/app-access`
  - 서비스 메서드: `AppAccessService.get_list_and_count`
- `GET /v1/app-access/list`
  - 목적: 목록만 조회
  - v3 경로: **기존과 동일** `GET /v1/app-access/list`
  - 서비스 메서드: `AppAccessService.get_list`

#### 3.2. File Node API (`file_node.py`)

- `GET /v1/file-node`
  - 목적: 파일 노드 목록 + 카운트
  - v3 경로: **기존과 동일** `GET /v1/file-node`
  - 서비스: `FileNodeService.get_file_node_list_with_count`
- `POST /v1/file-node/{id}/rename`
  - 목적: 파일 노드 이름 변경
  - v3 경로: **기존과 동일** `POST /v1/file-node/{id}/rename`
- `POST /v1/file-node/exist-name`
  - 목적: 파일명 중복 체크
  - v3 경로: **기존과 동일** `POST /v1/file-node/exist-name`
- `POST /v1/file-node/exist-name/multi`
  - 목적: 다건 파일명 중복 처리/새 이름 생성
  - v3 경로: **기존과 동일** `POST /v1/file-node/exist-name/multi`
- `POST /v1/file-node/api/update/file-object`
  - 목적: file object 메타 정보 갱신
  - v3 경로: **기존과 동일** `POST /v1/file-node/api/update/file-object`

#### 3.3. ACL API (`acl.py`)

- `GET /v1/acl`
  - 목적: ACL 편집을 위한 사용자/그룹 목록 조회
- `GET /v1/acl/file-node/{contentsId}`
- `GET /v1/acl/analysis-tool/{contentsId}`
  - 목적: 파일 노드/분석툴 ACL 조회
- `POST /v1/acl/file-node/{contentsId}/update`
- `POST /v1/acl/analysis-tool/{contentsId}/update`
  - 목적: 단건 ACL 업데이트
- `POST /v1/acl/file-node/update-multi`
- `POST /v1/acl/analysis-tool/update-multi`
  - 목적: 다건 ACL 업데이트

#### 3.4. Analysis Tool API (`analysis_tool.py`)

**메타/목록/조회**

- `GET /v1/analysis-tool/meta/create-info`
- `GET /v1/analysis-tool/meta/resource`
- `GET /v1/analysis-tool/meta/image`
- `GET /v1/analysis-tool`
- `GET /v1/analysis-tool/list`
- `GET /v1/analysis-tool/list/waiting`
- `GET /v1/analysis-tool/{id}/detail`
- `GET /v1/analysis-tool/{id}/detail/approval`

**생성/수정/상태변경**

- `POST /v1/analysis-tool/exist-name`
- `POST /v1/analysis-tool/create`
- `POST /v1/analysis-tool/{id}/reapplication`
- `POST /v1/analysis-tool/{id}/change-application-info`
- `POST /v1/analysis-tool/{id}/update/expire-date`
- `POST /v1/analysis-tool/{id}/update/remove`
- `POST /v1/analysis-tool/{id}/cancel`
- `POST /v1/analysis-tool/{id}/stop`
- `POST /v1/analysis-tool/{id}/tool-restart`
- `POST /v1/analysis-tool/{id}/delete`

**관리자 승인**

- `GET /v1/analysis-tool/management/status`
- `POST /v1/analysis-tool/management/{id}/approve/create`
- `POST /v1/analysis-tool/management/{id}/approve/resource`
- `POST /v1/analysis-tool/management/{id}/approve/expire-date`

**미리보기/파일 연동/백업**

- `GET /v1/analysis-tool-preview/{id}/tool-url`
- `POST /v1/analysis-tool-preview/{id}/update/access-date`
- `POST /v1/analysis-tool-preview/{id}/file/list`
- `POST /v1/analysis-tool-preview/{id}/file/import`
- `POST /v1/analysis-tool-preview/{id}/file/export`
- `GET /v1/analysis-tool/backup/list`
- `GET /v1/analysis-tool/{id}/backup/status`
- `POST /v1/analysis-tool/backup/exist-name`
- `POST /v1/analysis-tool/{id}/backup`
- `POST /v1/analysis-tool/backup/{backupId}/update`
- `POST /v1/analysis-tool/backup/{backupId}/delete`

각 엔드포인트는 `src/services/analysis_tool_service.py` 및 `src/services/backup_service.py` 메서드와 1:1 또는 명확한 매핑을 갖도록 설계한다.

#### 3.5. Graphio API (`graphio.py`)

- `GET /v1/graphio/url`
- `POST /v1/graphio/app/list`

#### 3.6. Common/IRIS/Time API (`common.py`, `iris.py`, `time.py`)

- Common
  - `GET /v1/common/session/user`
  - `GET /v1/common/config`
  - `POST /v1/common/token`
- IRIS
  - `GET /api/status`
  - `GET /api/route`
  - `POST /api/event`
  - `GET /api/heartbeat`
- Time
  - `GET /service/time/servertime`
  - `GET /service/time/timeoffset`

---

### 4. 요청/응답 DTO 매핑 설계

1. 각 엔드포인트에 대한 Request/Response 모델을 `src/dto/request/`, `src/dto/response/` 하위에 분리한다.
2. 파일 구조 예시:
   - `src/dto/request/app_access.py`
   - `src/dto/response/app_access.py`
   - `src/dto/request/file_node.py`
   - `src/dto/response/file_node.py`
   - `...` (도메인별 동일 패턴)
3. v2에서 사용하던 필드명을 기준으로, Pydantic 모델 필드를 정의한다.
   - 가능하면 필드명은 유지하되, Python 스타일에 맞게 snake_case로만 바꿀지 여부를 이 문서에서 결정한다.
   - 클라이언트와의 호환성이 중요하면 JSON 필드는 기존 이름을 유지하고, Pydantic `alias` 기능을 사용할 수 있다.
4. 각 엔드포인트별로 사용할 Request/Response 모델 이름을 표로 정리한다.
   - 예:
     - `POST /v1/app-access/add`  
       - Request: `AppAccessAddRequest`  
       - Response: `AppAccessAddResponse | ApiResponse[list[AppAccessRow]]` 등 구체화

---

### 5. 공통 패턴/규칙 정리

1. 공통 prefix 규칙
   - **v3에서도 pgv2 playground와 동일한 context-path/엔드포인트를 유지한다.**
   - 즉, 별도의 `/pgv3` prefix를 추가하지 않는다.
   - 예:
     - `/v1/...` 그대로 사용
     - `/api/...` 그대로 사용
     - `/service/...` 그대로 사용
2. HTTP 메서드 규칙
   - 조회: `GET`
   - 생성/수정/삭제/상태변경: `POST` (v2 규칙 유지)
3. 응답 포맷
   - 외부로 노출되는 API는 기본적으로 `ApiResponse` 포맷을 사용한다.
   - 일부 내부/헬스 체크 API는 순수한 JSON을 사용할 수 있으나, 문서에 예외를 명시한다.
4. 인증 필수 여부
   - 인증이 필수인 API와, 익명 접근 가능한 API를 이 문서에서 미리 구분한다.
   - 예:
     - `GET /api/status` → 인증 불필요
     - Analysis Tool / File Node / ACL → 인증 필수

---

### 6. 실제 구현 시 흐름 예시

1. `src/api/endpoints/app_access.py`에서:
   - `@router.post("/app-access/add")`
   - Request DTO → Service 인자 변환
   - `service.add_access_log(...)` 호출
   - 반환값을 `ApiResponse`로 감싸서 반환 (`@common_response` 또는 수동)
2. `src/api/app.py`에서:
   - `from src.api.endpoints import app_access, file_node, ...`
   - `app.include_router(app_access.router)`  (또는 v2와 동일한 최소 prefix만 사용)

이 흐름을 다른 도메인에도 동일하게 적용한다.

---

### 7. 다음 단계로 넘어가기 전에 체크할 것

아래 항목을 모두 만족하면, `06-service-layer-design.md` 문서로 넘어간다.

- [ ] `src/api/app.py`에서 FastAPI 인스턴스 생성/라우터 포함 구조가 설계되어 있다.
- [ ] `src/api/endpoints/` 하위에 도메인별 파일 이름과 prefix/tag 구조가 명확히 정리되어 있다.
- [ ] pgv2의 모든 주요 엔드포인트가 v3의 URL/라우터 파일로 매핑되어 있다.
- [ ] 각 엔드포인트별 Request/Response DTO 파일 위치와 모델 이름이 정의되어 있다.
- [ ] 공통 prefix/HTTP 메서드/응답 포맷/인증 정책이 문서로 정리되어 있다.

