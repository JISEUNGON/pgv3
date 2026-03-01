### 10. pgv2 Spring Boot API → Python(FastAPI) 전체 포팅 계획

이 문서는 `@pgv2-origin/project/playground` Spring Boot 프로젝트에 구현된 API들을  
`pgv3` Python(FastAPI) 기반으로 **동일한 URL/context-path**로 포팅하기 위한 정리 문서이다.

- **목표**
  - HTTP 경로, HTTP 메서드, 요청/응답 구조를 최대한 유지하면서 Python으로 재구현
  - 비즈니스 로직은 `SERVICE_LAYER_API_LOGIC.md`의 동작을 기준으로 서비스 레이어에 구현
  - 컨텍스트 패스는 pgv2와 동일하게 유지  
    - `/v1/...`, `/api/...`, `/service/...` 경로 유지 (별도 `/pgv3` prefix 없음)

---

### 1. 포팅 원칙

1. **경로/메서드 보존**
   - Spring Boot 컨트롤러에서 사용하던 `@RequestMapping` 경로와 HTTP 메서드를 그대로 사용
   - 예: `POST /v1/app-access/add` → FastAPI에서도 `POST /v1/app-access/add`
2. **응답 포맷 보존**
   - 성공/실패 응답은 `ApiResponse` 포맷 사용
   - 성공: `{"result":"1","errorCode":null,"errorMessage":null,"data":...}`
   - 실패: `{"result":"0","errorCode":"<ExceptionClassName>","errorMessage":"<message>","data":null}`
3. **레이어 분리**
   - 컨트롤러 역할 → FastAPI 라우터 (`src/api/endpoints/*.py`)
   - 서비스 로직 → Python 서비스 (`src/services/*.py`)
   - DB/엔티티 → SQLAlchemy 엔티티 (`src/models/entity/*.py`)
4. **인증/세션**
   - pgv2에서 세션/토큰을 사용하던 API는 `get_current_user` 의존성으로 동일하게 보호

---

### 2. 도메인별 API 목록 (pgv2 → pgv3 그대로 포팅)

#### 2.1. App Access Log API

- **라우터 파일 (v3)**: `src/api/endpoints/app_access.py`
- **서비스 (v3)**: `src/services/app_access_service.py`

**엔드포인트**

- `POST /v1/app-access/add`
- `GET /v1/app-access`
- `GET /v1/app-access/list`

---

#### 2.2. File Node API

- **라우터 파일 (v3)**: `src/api/endpoints/file_node.py`
- **서비스 (v3)**: `src/services/file_node_service.py`

**엔드포인트**

- `GET /v1/file-node`
- `POST /v1/file-node/{id}/rename`
- `POST /v1/file-node/exist-name`
- `POST /v1/file-node/exist-name/multi`
- `POST /v1/file-node/api/update/file-object`

---

#### 2.3. ACL API

- **라우터 파일 (v3)**: `src/api/endpoints/acl.py`
- **서비스 (v3)**: `src/services/acl_service.py`

**엔드포인트**

- `GET /v1/acl`
- `GET /v1/acl/file-node/{contentsId}`
- `GET /v1/acl/analysis-tool/{contentsId}`
- `POST /v1/acl/file-node/{contentsId}/update`
- `POST /v1/acl/analysis-tool/{contentsId}/update`
- `POST /v1/acl/file-node/update-multi`
- `POST /v1/acl/analysis-tool/update-multi`

---

#### 2.4. Analysis Tool API

- **라우터 파일 (v3)**: `src/api/endpoints/analysis_tool.py`
- **서비스 (v3)**: `src/services/analysis_tool_service.py`, `src/services/backup_service.py`

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

---

#### 2.5. Graphio API

- **라우터 파일 (v3)**: `src/api/endpoints/graphio.py`
- **서비스 (v3)**: `src/services/graphio_service.py`

**엔드포인트**

- `GET /v1/graphio/url`
- `POST /v1/graphio/app/list`

---

#### 2.6. Common API

- **라우터 파일 (v3)**: `src/api/endpoints/common.py`
- **서비스 (v3)**: `src/services/common_service.py`

**엔드포인트**

- `GET /v1/common/session/user`
- `GET /v1/common/config`
- `POST /v1/common/token`

---

#### 2.7. IRIS API

- **라우터 파일 (v3)**: `src/api/endpoints/iris.py`
- **서비스 (v3)**: `src/services/iris_service.py`

**엔드포인트**

- `GET /api/status`
- `GET /api/route`
- `POST /api/event`
- `GET /api/heartbeat`

---

#### 2.8. Time API

- **라우터 파일 (v3)**: `src/api/endpoints/time.py`
- **서비스 (v3)**: `src/services/time_service.py`

**엔드포인트**

- `GET /service/time/servertime`
- `GET /service/time/timeoffset`

---

### 3. 실제 포팅 작업 순서 (이 파일 기준)

1. **엔드포인트 스켈레톤 생성**
   - 위 도메인별 목록을 기준으로 FastAPI 라우터 함수 시그니처만 먼저 만든다.
2. **DTO 작성**
   - pgv2 요청/응답 VO/DTO를 보고 Pydantic 모델로 변환 (`src/dto/request/*`, `src/dto/response/*`)
3. **서비스 메서드 구현**
   - `SERVICE_LAYER_API_LOGIC.md` 로직을 그대로 Python 서비스 메서드로 옮긴다.
4. **연동/DB 연결**
   - 각 서비스에서 DB/외부 시스템(`tools`) 호출을 연결한다.
5. **예외/응답 통합**
   - 모든 엔드포인트 응답이 `ApiResponse` 포맷을 사용하도록 정리한다.
