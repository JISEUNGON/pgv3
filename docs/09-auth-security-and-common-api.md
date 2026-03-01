### 09. 인증/보안 및 Common API 설계

이 문서는 pgv3 프로젝트의 **인증/세션, ACL/권한, Common/IRIS/Time API**를 묶어서 설계한다.

---

### 1. JWT/세션 모델 설계 (`src/security/session_manager.py`)

1. 사용자 정보 모델 정의
   - `class UserInfo(BaseModel):`
     - `id: str`
     - `name: str`
     - `groups: list[str]`
     - `is_admin: bool`
     - 필요 시 추가 필드 (이메일, 조직 등)
2. 세션 저장 방식 결정
   - Redis 기반 세션 토큰 vs JWT 자체 보관 중 선택
   - 혼합 전략(Access Token은 JWT, 세션/상태는 Redis) 필요 여부를 결정
3. `SessionManager` 인터페이스 설계
   - `def create_session(self, user: UserInfo) -> str: ...`
   - `def get_user(self, session_id_or_token: str) -> UserInfo | None: ...`
   - `def invalidate_session(self, session_id_or_token: str) -> None: ...`
4. Redis를 사용할 경우, 키 규칙/만료시간 정책을 이 문서에 정리한다.

---

### 2. JWT 토큰 처리 (`src/security/jwt_utils.py` 등)

1. `src/security/jwt_utils.py` 파일을 생성한다.
2. `python-jose` 또는 `pyjwt`를 이용해 JWT 생성/검증 함수를 설계한다.
   - 입력:
     - 사용자 정보 / 클레임
     - 만료 시간
   - 출력:
     - JWT 문자열
3. 설정 (`AppSettings.security`)와 연결
   - `jwtSecretKey`, `jwtAlgorithm`, `accessTokenExpireMinutes`를 사용
4. 토큰 구조
   - `sub` (사용자 ID), `name`, `groups`, `is_admin`, `exp` 등

---

### 3. 인증 의존성 및 권한 체크 (`src/middleware/auth.py`)

1. `get_current_user` 설계
   - HTTP Request에서 다음 순서로 인증 정보를 추출:
     1. Authorization 헤더 (Bearer 토큰)
     2. 특정 쿠키 (예: `SESSIONID`)
   - JWT면 `jwt_utils`로 검증, 세션 토큰이면 `SessionManager`로 조회
   - 유효하지 않으면 인증 예외 발생 (`AuthenticationException`)
2. 권한 체크 패턴
   - 예: `def require_admin(user: UserInfo = Depends(get_current_user))`
   - 특정 그룹/역할이 필요한 API를 위한 데코레이터/의존성 설계
3. Common/IRIS/Time/Analysis Tool/ACL/File Node API가 각각 어떤 권한을 요구하는지 간략히 표로 정리한다.

---

### 4. ACL/권한 모델 정리 (서비스 레이어와의 연결)

1. ACL 데이터 구조
   - 사용자/그룹/Everyone 세 가지 축으로 권한을 정의
   - 권한 타입 (예: READ/WRITE/OWNER 등) 명세
2. `AclService`와의 연계
   - `FileNode`/`AnalysisTool`/`Backup` 조회/수정/삭제 시, 다음 순서로 권한을 체크:
     1. 시스템 관리자 여부 (`user.is_admin`)
     2. 소유자 여부
     3. 공개 리소스 여부
     4. ACL에서 허용된 사용자/그룹 여부
3. 권한 체크의 위치
   - API 레이어에서 할지, 서비스 레이어에서 할지 이 문서에서 정책을 정한다.
   - 권장: 서비스 레이어에서 도메인 로직과 함께 처리 (API 레이어는 호출/전달 역할)

---

### 5. Common API 설계 (`src/api/endpoints/common.py`, `src/services/common_service.py`)

#### 5.1. `GET /v1/common/session/user`

1. 목적: 세션 사용자 기본 프로필/권한 정보 반환
2. 처리 흐름:
   - `get_current_user` 의존성으로 현재 사용자 정보 조회
   - `CommonService.get_session_user` 호출
   - 필요한 필드만 맵 또는 DTO로 구성 후 반환

#### 5.2. `GET /v1/common/config`

1. 목적: 업로드 제한/공통 옵션/파일노드/분석툴 옵션 반환
2. 처리 흐름:
   - `AppSettings`에서 maxFileSize, maxRequestSize, 옵션 블록 읽기
   - 실제 사용 가능한 한계치를 계산 (예: MB/GB 단위 변환)
   - 응답 DTO로 묶어 반환

#### 5.3. `POST /v1/common/token`

1. 목적: 사용자 자격증명을 받아 토큰 발급
2. 처리 흐름:
   - 입력 DTO: ID/비밀번호 등
   - 인증 절차:
     - 내부 사용자 DB/외부 인증 서버 등과 연계 (구체 구현은 나중에)
   - 성공 시:
     - JWT 생성 또는 세션 생성
     - 토큰 문자열 반환

---

### 6. IRIS API 설계 (`src/api/endpoints/iris.py`, `src/services/iris_service.py`)

#### 6.1. `GET /api/status`

1. 목적: 서비스 상태 체크
2. 처리:
   - 고정값 `{"status": true}` 또는 유사 JSON 반환

#### 6.2. `GET /api/route`

1. 목적: 라우팅 정보 제공
2. 처리:
   - locale 지정 시: `route_{locale}.yml` 1개 로드
   - 미지정 시: 설정된 모든 locale 파일 로드 후 합쳐서 반환
3. 어디서 파일을 로드할지 (프로젝트 내 파일 vs 외부 설정) 결정 후 이 문서에 경로를 메모.

#### 6.3. `POST /api/event`

1. 목적: 현재는 단순 응답 (비즈니스 로직 없음)
2. 처리:
   - 고정 문자열 `success` 반환

#### 6.4. `GET /api/heartbeat`

1. 목적: 세션/토큰 갱신
2. 처리:
   - 세션 사용자 없으면 에러
   - Brick token 검증/갱신 후, 세션/토큰 갱신
3. Brick token 관련 로직은 별도 유틸/클라이언트로 분리할지 여부를 정한다.

---

### 7. Time API 설계 (`src/api/endpoints/time.py`, `src/services/time_service.py`)

#### 7.1. `GET /service/time/servertime`

1. 목적: 서버 현재 시각 제공
2. 처리:
   - 현재 시각을 `yyyy-MM-dd HH:mm:ss` 포맷 문자열로 변환

#### 7.2. `GET /service/time/timeoffset`

1. 목적: 클라이언트 시각과 서버 시각 차이 계산
2. 처리:
   - 요청 파라미터로 클라이언트 시각 수신
   - 서버 현재 시각과 비교하여 offset 계산
   - 구현상 millis 기준이라 초/분/시 차이는 반영되지 않는다는 제약을 유지할지, 보완할지 결정

---

### 8. 보안 관점 체크리스트 (요약)

1. 모든 민감한 설정 값은 `.env` 또는 환경변수로 관리하고, `application.yaml`에는 직접 넣지 않는다.
2. JWT 서명 키는 운영 환경에서 별도로 관리하며, Git에 노출되지 않도록 한다.
3. 세션/토큰 만료 시간, 비밀번호/토큰 재발급 정책 등을 간단히 문서에 적어둔다.
4. 관리자/일반 사용자/게스트 구분 및 각 역할의 권한 범위를 요약해 둔다.

---

### 9. 다음 단계 (구현)로 넘어가기 전에 체크할 것

- [ ] `src/security/session_manager.py`에 UserInfo/SessionManager 설계가 구체화되어 있다.
- [ ] `src/security/jwt_utils.py`에 JWT 생성/검증 로직 설계와 설정 연결이 정의되어 있다.
- [ ] `src/middleware/auth.py`에 인증 의존성 및 권한 체크 패턴이 정리되어 있다.
- [ ] ACL/권한 모델과 서비스 레이어에서의 권한 체크 위치가 명확히 정의되어 있다.
- [ ] Common/IRIS/Time API의 엔드포인트/처리 흐름이 이 문서에 요약되어 있다.

