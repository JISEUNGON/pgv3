### 03. DB 설정, ORM 모델, 마이그레이션 설계

이 문서는 `pgv3` Python 프로젝트에서 사용할 **DB 연결, SQLAlchemy ORM 모델, Alembic 마이그레이션**을 구성하는 절차를 정의한다.

---

### 1. DB 베이스/타입 정의 (`src/db/base.py`)

1. `src/db/base.py` 파일을 생성한다.
2. SQLAlchemy 2.x 스타일의 Declarative Base를 설계한다.
   - `from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column`
   - `class Base(DeclarativeBase): pass`
3. 공통 타입/유틸 정의
   - UUID/GUID 타입 (예: `GUID(TypeDecorator)` 또는 `sqlalchemy.dialects.postgresql.UUID` 사용)
   - `created_at`, `updated_at` 등에 사용할 공통 Mixin (선택)
4. 이후 모든 엔티티는 이 `Base`를 상속받도록 한다.

---

### 2. 세션/엔진 구성 (`src/db/session.py`, `src/db/sync_session.py`)

1. `src/db/session.py` 파일을 생성한다.
2. AsyncSession 기반 세션 팩토리 설계
   - `create_async_engine()`로 엔진 생성
   - `async_sessionmaker()`로 `AsyncSession` 팩토리 생성
   - FastAPI 의존성으로 사용할 `async def get_db()` 생성:
     - `async with async_session() as session: yield session`
3. DB URL 구성 방식
   - `src/core/config.py`의 설정 객체에서 DSN을 가져와 엔진을 생성하는 구조로 설계.
   - 예: `db_url = settings.database.main.dsn`
4. 워커 등에서 사용할 동기 세션
   - `src/db/sync_session.py` 파일을 생성한다.
   - `create_engine()` + `sessionmaker()`를 이용해 SyncSession 팩토리를 만든다.
   - ThreadPool/Worker에서 블로킹 작업이 필요한 경우에만 사용하도록 설계.

---

### 3. Alembic 기본 설정 (`src/alembic/`, `src/alembic.ini`)

1. 프로젝트 루트에서 Alembic 초기화를 수행한다. (커맨드는 메모만 해두고 실제 실행은 준비가 되었을 때 진행)
   - `alembic init src/alembic`
2. 생성된 `alembic.ini`를 `src/alembic.ini` 또는 루트에 둘지 결정하고, 이 문서에 위치를 명시한다.
   - 권장: 프로젝트 루트에 `alembic.ini` 두고, env.py는 `src/alembic/env.py` 사용
3. `src/alembic/env.py`에서 `target_metadata`를 `src/models/entity`에 정의한 Base 메타데이터에 연결한다.
   - 예: `from src.db.base import Base` → `target_metadata = Base.metadata`
4. 마이그레이션 스크립트 저장 위치
   - `src/alembic/versions/` 디렉터리를 사용한다.

---

### 4. v2 SQL → v3 ORM 매핑 계획

1. pgv2의 SQL 마이그레이션 파일 위치 확인
   - `pgv2-origin/project/playground/target/classes/db/migration/*.sql`
2. 주요 테이블 우선순위 정의 (최소 목록)
   - `app_access_log` (접속 로그)
   - `file_node` 및 관련 테이블
   - `analysis_tool`, `analysis_tool_approval`
   - `analysis_tool_backup` (또는 유사 이름)
   - 기타 필요한 코드/메타 테이블 (예: 이미지 정보, 이미지 타입)
3. 각 테이블에 대해 다음 정보를 추출해 이 문서에 적어둔다.
   - 테이블명
   - 주요 컬럼명/타입/제약조건
   - 기본키/유니크/인덱스
   - 외래키 관계
4. 이 단계에서는 아직 Python 코드로 옮기지 않고, **매핑 표**만 이 문서에 먼저 정리하는 것을 목표로 한다.

---

### 5. 엔티티 파일 구조 설계 (`src/models/entity/`)

1. 아래와 같은 파일 목록을 만든다.
   - `src/models/entity/app_access_log.py`
   - `src/models/entity/file_node.py`
   - `src/models/entity/analysis_tool.py`
   - `src/models/entity/analysis_tool_approval.py`
   - `src/models/entity/analysis_tool_backup.py`
   - `src/models/entity/image_info.py`
   - `src/models/entity/image_type.py`
   - (필요 시 추가 테이블 별도 파일)
2. 각 파일에 대해 클래스 이름을 정한다. (CamelCase, 단수형)
   - 예:
     - `class AppAccessLog(Base):`
     - `class FileNode(Base):`
     - `class AnalysisTool(Base):`
3. 필드 정의 스타일
   - SQLAlchemy 2.x typed ORM 스타일을 따른다.
   - 예:
     - `id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)`
     - `name: Mapped[str] = mapped_column(String(255))`
4. 관계 설정
   - `relationship()`을 이용해 연관된 엔티티 간 관계를 명시한다.
   - 예: `AnalysisTool` ↔ `AnalysisToolApproval`, `AnalysisTool` ↔ `AnalysisToolBackup`

---

### 6. 초기 마이그레이션 생성 플로우 설계

1. 모든 엔티티가 대략 정의된 후, Alembic 자동생성 기능을 사용해 초기 마이그레이션을 만든다.
   - 커맨드 (메모):  
     - `alembic revision --autogenerate -m "init schema"`
2. 자동 생성된 마이그레이션 스크립트를 검토할 때 확인해야 할 항목을 이 문서에 적어둔다.
   - 테이블명/컬럼명/타입이 v2 SQL과 일치하는지
   - PK/FK/UNIQUE/INDEX 제약조건이 올바른지
   - nullable/기본값 등이 스펙과 맞는지
3. 검토 후, 실제 DB에 마이그레이션을 적용하는 커맨드 메모
   - `alembic upgrade head`
4. `main.py`에서 마이그레이션 실행 위치 설계
   - `main.py` 또는 별도 모듈(예: `src/db/migration_runner.py`)에서
     - 앱 시작 전에 `alembic upgrade head` 또는 동등한 함수를 호출하는 위치를 이 문서에 메모.

---

### 7. 도메인별 쿼리 패턴 메모

서비스 레이어에서 자주 사용할 쿼리 패턴을 미리 정리해 둔다.

1. App Access Log
   - 조건/정렬/페이징을 지원하는 `get_list_and_count` 쿼리 패턴
   - 정렬 키(`key,ASC|DESC`)를 컬럼으로 매핑하는 규칙 (v2와 동일하게 설계)
2. File Node
   - ACL + 검색조건 + 페이징 조합 쿼리
   - 이름 중복 체크, rename, multi rename 쿼리 패턴
3. Analysis Tool
   - 상태값별 목록/카운트 쿼리
   - Approval/Backup과 조인한 상세 조회 쿼리
4. 각 패턴에 대해 “어떤 칼럼 기준으로 인덱스를 만드는 것이 좋은지” 메모해 둔다.

---

### 8. 다음 단계로 넘어가기 전에 체크할 것

아래 항목을 모두 만족하면, `04-common-components-and-exceptions.md` 문서로 넘어간다.

- [ ] `src/db/base.py`에 SQLAlchemy Base 및 공통 타입/Mixin 설계가 되어 있다.
- [ ] `src/db/session.py`에 AsyncSession 팩토리와 `get_db()` 의존성 설계가 되어 있다.
- [ ] `src/db/sync_session.py`에 SyncSession 팩토리 설계가 되어 있다.
- [ ] Alembic 초기화 전략과 `target_metadata` 연결 방법이 명확히 정리되어 있다.
- [ ] v2 SQL 마이그레이션 파일을 기반으로 주요 테이블 목록과 스키마 요약이 이 문서에 정리되어 있다.
- [ ] `src/models/entity/` 하위에 어떤 엔티티 파일을 만들지, 파일/클래스 이름이 정의되어 있다.

