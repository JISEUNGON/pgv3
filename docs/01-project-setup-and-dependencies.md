### 01. 프로젝트 생성 및 의존성 설정

이 문서는 `pgv3` 폴더 안에 Python 기반 컨테이너 관리 시스템 v3 프로젝트를 새로 만들기 위한
**최초 셋업 절차**를 정의한다.

모든 단계는 위에서부터 순서대로 수행한다.

---

### 1. 루트 디렉터리 구조 결정

1. `pgv3` 폴더 자체를 Python 프로젝트 루트로 사용한다. (별도의 `container-management` 디렉터리를 만들지 않는다.)
   - **구조**
     - 루트: `pgv3/`
     - 소스: `pgv3/src/`
     - 문서: `pgv3/docs/` (선택)
2. 실제 디렉터리는 이미 존재하는 `pgv3` 폴더를 그대로 사용한다.

> 이후 문서들(02~09)은 모두 이 구조를 기준으로 경로를 기술한다. (pgv3 아래에 추가 하위 루트는 두지 않는다.)

---

### 2. Python 버전 및 가상환경 준비

1. Python 3.12가 설치되어 있는지 확인한다.
   - `python3 --version` 또는 `pyenv versions` 등을 사용.
2. 프로젝트 전용 가상환경을 만든다. (예시는 `venv` 기준, 다른 도구 사용 가능)
   - `python3.12 -m venv .venv` (루트: `pgv3/` 기준)
   - `source .venv/bin/activate` (macOS/zsh 기준)
3. 이 문서 상단에 실제로 사용한 Python 버전과 가상환경 생성 명령을 메모해 둔다.

---

### 3. `pyproject.toml` 생성 (Poetry 기준)

1. 프로젝트 루트(`pgv3/`)에서 Poetry 초기화를 수행한다.  
   (Poetry를 사용하지 않을 계획이라면, 이 섹션을 참고해서 `requirements.txt` 방식으로 변환하면 된다.)
   - `poetry init` 실행
   - 질문에는 다음 방향으로 응답한다.
     - 패키지 이름: `container-management`
     - 버전: `0.1.0`
     - 설명: `Container Management System V3 (FastAPI, Python)`
     - 저자, 라이선스 등은 상황에 맞게 입력
2. `pyproject.toml`의 Python 버전과 의존성을 아래와 같이 맞춘다.
   - `[tool.poetry.dependencies]`에 추가:
     - `python = "^3.12"`
     - `fastapi`
     - `uvicorn[standard]`
     - `pydantic`
     - `pydantic-settings`
     - `sqlalchemy`
     - `alembic`
     - `asyncpg`
     - `psycopg2-binary`
     - `aiomysql`
     - `pymysql`
     - `kubernetes`
     - `minio`
     - `pika`
     - `redis`
     - `httpx`
     - `python-jose[cryptography]`
     - `pyjwt`
     - `passlib[bcrypt]`
     - `aiofiles`
     - `python-dotenv`
     - `greenlet`
3. 개발용 의존성은 최소한으로 두고, 테스트 도구는 추가하지 않는다. (요청에 따라 테스트 코드는 제외)
   - `[tool.poetry.group.dev.dependencies]` (또는 기존 dev 섹션)에 필요 시 다음 정도만 추가 가능:
     - `ruff` 또는 `flake8` (코드 스타일 검사용, 선택)
     - `mypy` (정적 타입 검사, 선택)
   - 단, 테스트 프레임워크(`pytest`, `pytest-asyncio` 등)는 추가하지 않는다.

---

### 4. 기본 디렉터리/파일 생성

1. 프로젝트 루트(`pgv3/`)에서 다음 디렉터리를 생성한다.
   - `src/`
   - `docs/` (이미 이 문서들이 존재하므로, 실제로는 `pgv3` 쪽에만 둘 수도 있음. 코드용 docs가 필요하면 이 하위에 추가)
2. `src/` 하위에 패키지 루트를 만든다.
   - `src/` 바로 아래에 `__init__.py` (비워둬도 됨)를 생성.
3. 아직 세부 폴더(예: `api`, `core`, `db` 등)는 만들지 않는다.  
   - 세부 구조/`__init__.py`는 `02-folder-structure-and-config.md`를 진행하면서 생성한다.

---

### 5. `main.py` 엔트리포인트 스켈레톤 작성

1. 프로젝트 루트(`pgv3/`)에 `main.py` 파일을 만든다.
2. `main.py`의 초기 목표는 아래 두 가지이다.
   - (1) 개발 초기 단계에서는 **FastAPI 앱만 단독으로 실행**할 수 있도록 진입점을 제공
   - (2) 이후 단계에서 **멀티프로세스 ProcessManager**를 붙일 수 있는 구조를 열어두기
3. `main.py`에 다음과 같은 구조를 계획한다. (실제 코드는 나중에 구현해도 좋고, 지금 바로 스텁 형태로 작성해도 된다.)
   - `create_app()` 함수를 분리해 `src/api/app.py`의 FastAPI 인스턴스를 가져오도록 설계
   - `run_fastapi()` 함수: 개발 편의를 위한 단일 프로세스 FastAPI 실행
   - `run_all_processes()` 함수: ProcessManager를 이용해 FastAPI + Worker 프로세스를 올리는 함수 (초기에는 `pass` 또는 TODO)
   - `if __name__ == "__main__":` 블록에서, 개발 단계에서는 `run_fastapi()`만 호출하도록 해 둔다.
4. 이 문서에, 나중에 멀티프로세스 구조로 전환할 때 바꿀 위치(예: `run_fastapi` vs `run_all_processes`)를 메모해 둔다.

---

### 6. 의존성 설치 및 실행 방법 기록

1. Poetry 사용 시:
   - `poetry install`
   - `poetry run python main.py` (또는 멀티프로세스 적용 전에는 `poetry run uvicorn src.api.app:app --reload`)
2. Poetry를 사용하지 않고 venv + pip를 사용할 경우:
   - `pip install -r requirements.txt` (별도 작성 시)
   - `python main.py` 또는 `uvicorn src.api.app:app --reload`
3. 실제로 사용할 커맨드를 이 문서에 복사해 두고, 나중에 README 작성 시 그대로 가져다 쓸 수 있도록 한다.

---

### 7. 다음 단계로 넘어가기 전에 체크할 것

아래 항목을 모두 만족하면, `02-folder-structure-and-config.md` 문서로 넘어간다.

- [ ] `pgv3/` 디렉터리가 프로젝트 루트로 사용되고 있다. (별도 하위 루트 없음)
- [ ] Python 3.12 기반 가상환경(또는 Poetry 환경)이 준비되어 있다.
- [ ] `pyproject.toml`에 필수 의존성이 모두 추가되어 있다.
- [ ] `src/` 디렉터리와 `__init__.py`가 생성되어 있다.
- [ ] `main.py`가 존재하고, 최소한 FastAPI 앱을 실행할 수 있는 진입점 설계(또는 스텁)가 잡혀 있다.
- [ ] (테스트 관련 의존성/코드는 추가하지 않았다.)

