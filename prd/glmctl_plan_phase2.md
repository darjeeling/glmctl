# GLMCTL: GLM Coding Plan 실행 환경 유틸리티

## 📘 개요

**GLMCTL (GLM Control)** 은 GLM 코딩 플랜(Generative Language Model Coding Plan)을  
격리된 **Docker 기반 환경**에서 손쉽게 실행하고 관리할 수 있도록 지원하는 CLI 유틸리티입니다.  

이 도구는 개발자들이 로컬 환경 설정에 구애받지 않고,  
AI 기반 코딩 워크플로우를 **표준화된 컨테이너 환경에서 재현 가능하게 실행**하는 것을 목표로 합니다.

---

## 🧱 프로젝트 목표

| 목표 | 설명 |
|------|------|
| **재현 가능한 실행 환경** | 동일한 GLM 코딩 플랜을 어떤 시스템에서도 동일하게 실행 |
| **격리된 환경 구성** | Docker를 활용해 외부 의존성을 차단하고 안전한 테스트 수행 |
| **CLI 중심의 간결한 사용성** | 명확한 명령 체계와 자동완성 지원 |
| **확장 가능한 구조** | Plugin 기반 아키텍처로 환경, 이미지, 실행 로직 확장 가능 |

---

## ⚙️ 시스템 아키텍처

```
+--------------------------+
|        glmctl CLI        |
+-----------+--------------+
            |
            v
+--------------------------+
|   Command Parser (Click) |
+--------------------------+
            |
            v
+--------------------------+
| Docker Control Layer     |
|  - Image Build/Run       |
|  - Container Management  |
+--------------------------+
            |
            v
+--------------------------+
|  GLM Plan Executor       |
|  - plan.yaml Parser      |
|  - Validation & Runtime  |
+--------------------------+
```

---

## 🧩 주요 기능

### 1. **환경 초기화**
```bash
glmctl init --image glm:latest
```
- 기본 도커 이미지와 캐시 설정 초기화  
- `.glmctl/config.yaml` 생성  

### 2. **GLM 코딩 플랜 실행**
```bash
glmctl plan run plan.yaml
glmctl plan validate plan.yaml
glmctl plan inspect plan.yaml
```
- `run`: 플랜 파일을 컨테이너 내에서 실행  
- `validate`: YAML 형식, 의존성, 스크립트 검증  
- `inspect`: 실행 단계 미리보기  

### 3. **격리 환경 관리**
```bash
glmctl env create myenv
glmctl env exec myenv bash
glmctl env stop myenv
glmctl env list
glmctl env remove myenv
```
- 환경 생성/실행/중지/삭제 및 목록 조회  
- 내부 명령 실행 (`exec`) 지원  

### 4. **환경 설정 관리**
```bash
glmctl config get
glmctl config set default_image glm:latest
glmctl config unset default_image
```
- 사용자 전역 설정 관리  
- `~/.glmctl/config.yaml` 기반  

### 5. **유틸리티 명령**
```bash
glmctl logs myenv
glmctl clean --all
glmctl version
```
- 실행 로그 조회  
- 캐시 및 중간 컨테이너 정리  
- 버전 및 환경 정보 확인  

---

## 🔧 기술 스택

| 구성 요소 | 기술 | 설명 |
|-------------|-------|------|
| CLI Framework | `click` | Python 기반 명령 파서 |
| Docker Control | `docker-py` | 컨테이너 제어 라이브러리 |
| Config 관리 | `pyyaml`, `appdirs` | 설정파일 관리 |
| Plan Schema | `jsonschema` | 플랜 YAML 구조 검증 |
| 로깅 | `rich` | 컬러 출력 및 구조화 로그 |
| 테스트 | `pytest` | CLI 및 실행 로직 테스트 |

---

## 📂 디렉토리 구조 (예시)

```
glmctl/
 ├── cli/
 │    ├── __init__.py
 │    ├── main.py
 │    ├── plan.py
 │    ├── env.py
 │    └── config.py
 ├── core/
 │    ├── docker_manager.py
 │    ├── plan_executor.py
 │    └── config_loader.py
 ├── tests/
 │    └── test_plan_execution.py
 ├── setup.py
 └── README.md
```

---

## 🧠 사용 예시

```bash
# 1. 초기 설정
glmctl init --image glm:latest

# 2. 플랜 실행
glmctl plan run plan.yaml

# 3. 환경 접근
glmctl env exec myenv bash

# 4. 로그 확인
glmctl logs myenv
```

---

## 🧩 향후 확장 계획

| 기능 | 내용 |
|------|------|
| **Plugin System** | `~/.glmctl/plugins` 폴더를 통한 확장 기능 로드 |
| **GPU/TPU 지원** | `--device cuda` 옵션으로 GPU 환경 활성화 |
| **Remote Runner** | SSH 기반 원격 Docker 호스트 실행 지원 |
| **Web Dashboard** | 실행 상태를 모니터링하는 웹 UI 추가 |

---

## 📜 라이선스 및 기여 가이드

- 라이선스: **Apache 2.0**
- 기여 가이드: `CONTRIBUTING.md`  
- 이슈 및 토론은 GitHub Discussions을 통해 관리 예정

---

## 🪶 작성자

**배권한 (KwonHan Bae)**  
Python Software Foundation Director / PyCon Korea Organizer  
25년 경력 SRE / Python Engineer
