### 04. 공통 응답, 예외, 미들웨어 설계

이 문서는 pgv3 프로젝트의 **공통 응답 포맷, 예외 계층, 인증 관련 미들웨어/의존성**을 설계하기 위한 단계별 작업을 정의한다.

---

### 1. 공통 응답 DTO 설계 (`src/dto/response/api_response.py`)

1. `src/dto/response/api_response.py` 파일을 생성한다.
2. `ApiResponse` Pydantic 모델 설계
   - 필드:
     - `result: str`  (`"1"`: 성공, `"0"`: 실패)
     - `errorCode: str | None`
     - `errorMessage: str | None`
     - `data: Any | None`
   - `Config` (또는 `model_config`)에서 JSON 직렬화 옵션을 기본값으로 두되, 특별한 변환이 필요하면 메모.
3. 성공/실패 예시를 이 문서에 명시한다.
   - 성공:
     - `{"result": "1", "errorCode": null, "errorMessage": null, "data": {...}}`
   - 예외:
     - `{"result": "0", "errorCode": "SomeException", "errorMessage": "설명...", "data": null}`

---

### 2. 공통 응답 유틸/데코레이터 설계 (`src/utils/common_response.py`)

1. `src/utils/common_response.py` 파일을 생성한다.
2. FastAPI 엔드포인트에 적용할 데코레이터/헬퍼를 설계한다.
   - `def success(data: Any) -> ApiResponse`
     - `return ApiResponse(result="1", errorCode=None, errorMessage=None, data=data)`
   - `def failure(error_code: str, message: str) -> ApiResponse`
     - `return ApiResponse(result="0", errorCode=error_code, errorMessage=message, data=None)`
3. 엔드포인트에서 자연스럽게 쓸 수 있는 데코레이터 설계
   - 예: `@common_response`
   - 내부 동작:
     - 원래 엔드포인트 함수가 반환하는 값을 받아 `success()`로 감싼다.
     - 이미 `ApiResponse` 타입이면 그대로 통과시키는 정책 여부를 문서에 결정해 둔다.
4. 공통 응답을 강제할 것인지, 선택적으로 사용할 것인지 정책을 정해 메모한다.
   - 예: 외부 공개 API는 반드시 `ApiResponse` 포맷 사용, 내부/관리용 API는 선택

---

### 3. 예외 계층 설계 (`src/exceptions/`)

1. `src/exceptions/base.py` 파일을 생성한다.
2. `BaseCustomException` 클래스 설계
   - 필드:
     - `error_code: str`
     - `message: str`
     - `http_status: int` (FastAPI/Starlette용)
   - Python 예외 상속:
     - `class BaseCustomException(Exception): ...`
3. 도메인별 예외 클래스를 정의할 파일을 구분한다.
   - `src/exceptions/analysis_tool_exceptions.py`
   - `src/exceptions/file_node_exceptions.py`
   - `src/exceptions/acl_exceptions.py`
   - `src/exceptions/app_access_exceptions.py`
   - 기타 필요에 따라 추가
4. 각 도메인 예외 클래스 설계 예시
   - `class AnalysisToolNotFound(BaseCustomException):`
     - `error_code = "AnalysisToolNotFound"`
     - `http_status = 404`
   - 실제 구현 시에는 `__init__`에서 메시지를 받거나 기본 메시지를 설정하도록 설계.

---

### 4. 예외 → 공통 응답 변환 핸들러 설계

1. FastAPI 앱 레벨에서 사용할 예외 핸들러를 설계한다.
   - 위치: `src/api/app.py` 또는 별도 모듈에서 정의 후 `app`에 등록
2. `BaseCustomException`에 대한 핸들러
   - `from fastapi import Request`
   - `from fastapi.responses import JSONResponse`
   - 예외를 받아 `ApiResponse(result="0", errorCode=exc.error_code, errorMessage=exc.message, data=None)`로 변환
   - HTTP 상태 코드는 `exc.http_status` 사용
3. 알 수 없는 예외(Exception)에 대한 핸들러
   - `errorCode = exc.__class__.__name__`
   - `errorMessage = str(exc)` (운영 환경에서는 노출을 제한할 수도 있음)
   - 상태코드: 500
4. 이 핸들러들을 FastAPI 앱에서 등록하는 위치/코드를 이 문서에 메모해 둔다.

---

### 5. 인증/세션 관련 미들웨어 및 의존성 설계

#### 5.1. 세션/사용자 모델 설계 (`src/security/session_manager.py`)

1. `src/security/session_manager.py` 파일을 생성한다.
2. 세션에 저장할 사용자 정보 모델 정의
   - Pydantic 모델 또는 dataclass 사용
   - 필드 예:
     - `user_id: str`
     - `user_name: str`
     - `groups: list[str]`
     - `is_admin: bool`
3. 세션 관리 인터페이스 설계
   - `class SessionManager:`
     - `def get_current_user(self, token_or_session) -> UserInfo | None: ...`
     - `def create_session(self, user_info: UserInfo) -> str: ...`
     - `def invalidate_session(self, session_id: str) -> None: ...`
   - 실제 구현에서 Redis 또는 다른 저장소를 사용할 수 있도록 내부 구현은 이후에 채운다.

#### 5.2. 인증 의존성 설계 (`src/middleware/auth.py`)

1. `src/middleware/auth.py` 파일을 생성한다.
2. FastAPI용 의존성 함수 설계
   - `async def get_current_user(...) -> UserInfo:`
     - HTTP 요청 헤더/Cookie에서 세션 또는 토큰 정보를 읽는다.
     - `SessionManager`를 이용해 사용자 정보를 로딩한다.
     - 사용자 정보가 없으면 인증 오류 예외(`AuthenticationException`)를 발생시킨다.
3. 역할/권한 체크용 데코레이터/의존성도 설계할 수 있다.
   - 예: `def require_admin(user: UserInfo = Depends(get_current_user))`

---

### 6. 공통 로깅/트레이싱 (선택)

1. 공통 로깅 유틸 위치 결정
   - 예: `src/utils/logging.py`
2. API 레벨에서 요청/응답 로깅, 주요 서비스 레벨에서 비즈니스 이벤트 로깅을 어떻게 남길지 간략히 메모한다.
3. 나중에 실제 구현 시 어떤 로거 이름을 쓸지, 어떤 구조로 Json 로그를 남길지 설계할 수 있다.

---

### 7. 다음 단계로 넘어가기 전에 체크할 것

아래 항목을 모두 만족하면, `05-api-layer-design.md` 문서로 넘어간다.

- [ ] `src/dto/response/api_response.py`에 `ApiResponse` 모델 설계가 되어 있다.
- [ ] `src/utils/common_response.py`에 성공/실패 응답 헬퍼 및 데코레이터 설계가 되어 있다.
- [ ] `src/exceptions/base.py` 및 도메인별 예외 파일 구조/클래스 설계가 정의되어 있다.
- [ ] FastAPI 예외 핸들러에서 공통 응답 포맷으로 변환하는 흐름이 정리되어 있다.
- [ ] `src/security/session_manager.py`에 세션/사용자 모델 및 인터페이스 설계가 되어 있다.
- [ ] `src/middleware/auth.py`에 `get_current_user` 및 권한 체크 패턴이 설계되어 있다.

