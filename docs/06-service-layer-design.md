### 06. 서비스 레이어 및 비즈니스 로직 설계

이 문서는 `SERVICE_LAYER_API_LOGIC.md`를 기반으로,
각 도메인별 **서비스 클래스/메서드/비즈니스 규칙**을 pgv3 Python 서비스 레이어에서 어떻게 구현할지 정의한다.

---

### 1. 서비스 모듈 구조 (`src/services/`)

1. 다음 파일을 생성할 계획을 세운다.
   - `src/services/app_access_service.py`
   - `src/services/file_node_service.py`
   - `src/services/acl_service.py`
   - `src/services/analysis_tool_service.py`
   - `src/services/backup_service.py`
   - `src/services/graphio_service.py`
   - `src/services/common_service.py`
   - `src/services/iris_service.py`
   - `src/services/time_service.py`
2. 각 서비스 파일 안에는 하나의 주요 서비스 클래스를 둔다.
   - 예: `class AppAccessService:`, `class FileNodeService:`, ...
3. 서비스 클래스의 초기화 패턴
   - DB 세션(AsyncSession)을 메서드 인자로 받거나, DI 컨테이너/팩토리를 이용해 주입
   - 외부 연동 클라이언트(`tools` 모듈들)를 생성자 인자로 받도록 설계 (테스트/교체 용이)

---

### 2. App Access Log 서비스 (`AppAccessService`)

파일: `src/services/app_access_service.py`

1. `add_access_log` 메서드 설계
   - 입력:
     - 요청 DTO (`AppAccessAddRequest`)
     - 세션 사용자 정보 (`UserInfo | None`)
   - 처리 단계:
     1. `appCode` 유효성 검사 (`AppCode.find` 역할을 하는 유틸/enum 준비)
     2. 요청 DTO → `AppAccessLog` 엔티티 변환
     3. 세션 사용자 정보가 있으면 `userId/group` 반영, 없으면 `UNKNOWN` 값 사용
     4. `accessDate` 미입력 시 현재 시각으로 보정
     5. DB에 저장 후 커밋
   - 출력:
     - 성공 시: 저장된 로그의 식별자 또는 단순 성공 표시
2. `get_list_and_count` 메서드 설계
   - 입력:
     - 검색 조건, 페이징 정보, 정렬 파라미터(`key,ASC|DESC`)
   - 처리 단계:
     1. 정렬 파라미터를 `PageRequest` 유사 구조로 변환
     2. 조건/페이징을 적용해 목록 조회
     3. 전체 건수 조회
   - 출력:
     - `(items: list[AppAccessRow], total: int)`
3. `get_list` 메서드 설계
   - `get_list_and_count`에서 카운트만 제외한 버전으로 설계

---

### 3. File Node 서비스 (`FileNodeService`)

파일: `src/services/file_node_service.py`

1. `get_file_node_list_with_count`
   - 입력:
     - 검색/정렬/페이징 조건
     - 세션 사용자
   - 처리 단계:
     1. 정렬 키를 DB 컬럼명으로 매핑
        - `type -> fileType`
        - `name -> fileNm`
        - `createDate -> crtDt`
        - 등, v2와 동일한 매핑표를 이 문서에 기록
     2. 세션 사용자 기준 ACL 접근 가능한 파일노드 ID 목록 조회
     3. `shared/existAcl` 조건에 따라:
        - 전체 ACL 대상 조회 OR 현재 사용자 접근 ACL 조회
     4. ACL + 검색조건 + 페이징 기준으로 목록/카운트 조회
2. `rename_file_node`
   - 입력: 파일노드 ID, 새 이름, 세션 사용자
   - 처리 단계:
     1. 이름 공백/유효성 체크 후 trim
     2. 대상 파일노드 조회 (없으면 False 반환)
     3. 권한 체크 (필요 시)
     4. 이름 변경 후 저장
3. `get_exist_file_node_name`
   - 입력: 이름, 파일노드 ID(선택), 세션 사용자
   - 처리 단계:
     1. 수정 요청인 경우, 자신의 ID는 제외하고 중복 검사
     2. 신규 생성인 경우 전체에 대해 중복 검사
     3. 에러 상황(세션 없음 등)은 `true` (존재함)으로 취급
4. `get_map_file_node_new_name_multi`
   - 입력: 파일명 리스트
   - 처리 단계:
     1. 각 이름에 대해 중복 여부 조회
     2. 중복 시 `name (n)` 규칙으로 재귀 보정
   - 출력: `{원래이름: 새이름}` 맵
5. `update_file_object`
   - 입력: `fileId`, `ready`, 기타 메타필드
   - 처리 단계:
     1. 필수값 검증
     2. 대상 파일노드 조회
     3. fileObjectId/fileName/fileSize/sensitive/expireDate 갱신

---

### 4. ACL 서비스 (`AclService`)

파일: `src/services/acl_service.py`

1. `get_list_without_acl`
   - Meta 서비스에서 사용자/그룹 라이트 목록 조회
   - 현재 세션 사용자는 사용자 후보에서 제외
   - ACL 편집 UI 구조(`user/group -> isEveryone, acl, list`)로 가공
2. `get_acl_list`
   - 입력: contentsId, 타입(file-node/analysis-tool), 세션 사용자
   - 처리 단계:
     1. 현재 ACL, 사용자/그룹 원본 목록 조회 (Meta ACL API)
     2. ACL 항목을 USER/GROUP + EVERYONE 여부로 분리
     3. 이미 ACL에 들어간 대상은 선택 후보 목록에서 제외
3. `set_acl_list`
   - 단건/다건 둘 다 처리할 수 있도록 설계
   - Meta ACL 업데이트 API 호출 전, contentId를 리스트 형식(`content.ids`)으로 변환

Meta ACL API 호출은 `src/tools/meta_acl_client.py` 같은 모듈로 분리하여 의존하도록 설계한다.

---

### 5. Analysis Tool 서비스 (`AnalysisToolService`, `BackupService`)

파일:
- `src/services/analysis_tool_service.py`
- `src/services/backup_service.py`

#### 5.1. 상태/리소스 관련 공통 규칙 메모

1. 상태 전이 축:
   - 신청(Approval 기반 상태 전이)
   - 리소스 쿼터 검증
   - Container Management API 오케스트레이션
   - ACL/소유자 기반 권한 제어
2. 상태값/Approval 타입/리소스 조합 표를 이 문서에 작성해 둔다.

#### 5.2. 주요 메서드 설계 (요약)

1. `check_exist_name`
   - 세션 사용자 기준 이름 중복 체크
   - 관리자 요청에서 ID가 있으면 해당 툴 소유자 기준으로 검사
2. `create_tool`
   - 신청 리소스 사전 검증
     - 전체 쿼터 vs (현재 사용량 + 요청량)
   - CPU 이미지 선택 시 GPU를 강제로 0 처리
   - Approval(`APPLICATION`, `NONE`) 먼저 저장
   - Tool을 `APPLICATION` 상태로 생성, Approval FK 연결
3. `reapplication_tool`
   - 대상 툴 제외한 리소스 검증
   - Approval(`REAPPLICATION`) 신규 생성 후 연결
   - 이름/설명은 승인 없이 즉시 반영
4. `change_application_info`
   - 기존 approval 존재 필수
   - approval 타입별 업데이트 범위 분기:
     - `APPLICATION/REAPPLICATION`: 리소스 + 만료 + limit 갱신
     - `EXPIRE`: 만료 + limit만 갱신
   - `APPLICATION` 상태에서는 툴 엔티티 본문도 동기화
   - 이름/설명은 즉시 반영
5. `update_tool_expire_date`
   - Approval(`EXPIRE`, `NONE`) 생성 및 툴에 연결
   - 이름/설명 변경 요청이 있으면 즉시 반영
6. `update_tool_remove`
   - containerId 검증
   - Container delete API 호출 성공 시 툴 상태를 `PROCESS`로 변경
   - 실제 최종 삭제는 콜백 처리에서 담당 (Monitoring/StateMachine 측)
7. `cancel_application`
   - approval 없는 경우 에러
   - 신청 상태 + 재신청 취소인 경우:
     - approval 타입을 `APPLICATION`로 되돌리고 `REJECT`
   - 그 외:
     - approval 삭제 또는 링크 해제
   - 상태값이 APPLICATION 취소이면 툴 레코드 자체 삭제 가능
8. `stop_tool`, `restart_tool`, `delete_tool`
   - Container stop/restart/delete API 호출
   - 호출 후 툴 상태를 적절히 갱신

#### 5.3. 관리자 승인 관련 메서드

1. `get_management_status`
   - 전체/사용 리소스 조회 후 사용률(%) 계산
   - CPU milli-core → core 단위 보정
2. `approve_create`, `approve_resource`, `approve_expire_date`
   - 승인 시:
     - 리소스/만료/limit 갱신
     - Container create/restart/setting API 호출
     - 성공 시 approval 제거/상태 갱신
   - 거부 시:
     - approval 상태를 `REJECT`로 변경

#### 5.4. 백업 관련 메서드 (`BackupService`)

1. `get_backup_list`
2. `get_backup_status`
3. `check_backup_exist_name`
4. `backup_tool`
5. `update_backup`
6. `delete_backup`

각 메서드는 권한 정책(시스템 관리자/공개 백업/백업 생성자/툴 소유자/툴 ACL 사용자)을 적용해 조회/수정/삭제 권한을 결정하고,
Container Management 백업 API와 연동한다.

---

### 6. Graphio/공통/IRIS/Time 서비스

#### 6.1. Graphio (`GraphioService`)

파일: `src/services/graphio_service.py`

1. `get_url`
   - 설정값에서 Graphio URL 반환
2. `get_app_list`
   - 요청 컨텍스트에서 Graphio access token 추출
   - Authorization Bearer 헤더로 Graphio API 호출

#### 6.2. Common (`CommonService`)

파일: `src/services/common_service.py`

1. `get_session_user`
   - 세션 사용자 기본 프로필/권한 정보를 맵으로 구성
2. `get_config`
   - 파일 업로드 제한(`maxFileSize`, `maxRequestSize`) 파싱
   - 공통/파일노드/분석툴 옵션 설정 묶음 반환
3. `create_token`
   - 입력 자격증명 기반 토큰 발급

#### 6.3. IRIS (`IrisService`)

파일: `src/services/iris_service.py`

1. `status`
   - 서비스 상태 고정값 반환
2. `get_route`
   - locale 지정 시 단일 route 파일 로딩
   - 미지정 시 전체 locale route 파일 로딩 후 묶어서 반환
3. `event`
   - 현재는 고정 문자열 `success` 반환
4. `heartbeat`
   - 세션 사용자 없으면 종료
   - Brick token 검증/갱신 후 세션 사용자 토큰 갱신

#### 6.4. Time (`TimeService`)

파일: `src/services/time_service.py`

1. `get_server_time`
   - 현재 시각을 지정 포맷 문자열로 반환
2. `get_time_offset`
   - 클라이언트 전달 시각과 서버 시각의 offset 계산
   - 구현상 millis 단위 비교(초/분/시 차이는 반영되지 않음)를 유지할지 개선할지 결정

---

### 7. 외부 연동 추상화 (`src/tools/` 연계)

1. 서비스 내부에서 직접 HTTP/K8s/Storage를 호출하지 않고, `src/tools/` 모듈을 거치도록 설계한다.
2. 예:
   - `ContainerClient` (컨테이너 생성/삭제/재시작 등)
   - `StorageClient` (파일 업로드/다운로드)
   - `MetaAclClient` (ACL 조회/업데이트)
   - `GraphioClient` (Graphio API)
3. 서비스 클래스 생성자에서 이러한 클라이언트를 인자로 받아 저장하고, 메서드 내부에서는 이 인스턴스를 사용한다.

---

### 8. 다음 단계로 넘어가기 전에 체크할 것

아래 항목을 모두 만족하면, `07-workers-and-event-system.md` 문서로 넘어간다.

- [ ] `src/services/` 하위에 필요 서비스 파일 이름과 클래스 이름이 모두 정의되어 있다.
- [ ] 각 서비스별 주요 메서드(입력/출력/내부 처리 순서)가 이 문서에 구체적으로 정리되어 있다.
- [ ] Analysis Tool/Approval/Backup 관련 상태/리소스/승인 로직 흐름이 이해 가능한 수준으로 정리되어 있다.
- [ ] 외부 시스템 호출은 `src/tools/` 모듈을 통해 이루어지도록 설계되어 있다.

