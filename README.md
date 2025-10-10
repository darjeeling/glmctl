# glmctl

macOS용 GLM Coding Plan 을 Claude Code 에서 사용하기 위한 격리 환경 유틸리티

## 개요

`glmctl`은 [Claude Code](https://docs.claude.com/claude-code)를 Docker 컨테이너 내에서 실행하여 격리된 개발 환경을 제공합니다. GLM API를 사용하여 Claude Code 를 저렴하게 활용이 가능하며 평소에 무서웠던 `--dangerously-skip-permissions` 를 사용해봅시다.

2025년 10월 현재 [GLM Coding Lite](https://z.ai/subscribe?ic=QUOROVB4GK) - (레퍼럴링크포함) 를 이용할때 Claude Pro 플랜의 5배 정도 사용량을 기준으로 첫 결제 할인 및 레퍼럴포함 1년 선결제시에 *1년*에 32.4 USD 정도입니다. 

## 주요 기능

- 🐳 Docker 기반 격리 환경
- 🔒 호스트 시스템과 분리된 안전한 코딩 환경
- 🚀 Claude Code CLI 사전 설치
- 🛠️ 필수 개발 도구 포함 (Git, Node.js, Python, Rust, Docker CLI 등)
- 📦 간편한 설치 및 업데이트

## 필수 요구사항

- **macOS** (현재 macOS 전용)
- **Docker 환경**: 다음 중 하나 설치 필요
  - [OrbStack](https://orbstack.dev/) (권장)
  - [Docker Desktop](https://www.docker.com/products/docker-desktop)

## 설치

1. 저장소 클론:
```bash
git clone <repository-url>
cd glmctl
```

2. 설치 스크립트 실행:
```bash
./install.sh
```

설치 과정에서 다음 작업이 수행됩니다:
- Docker 환경 확인
- `~/.glmenv` 디렉토리 생성
- 환경 설정 파일 생성 (`~/.glmenv/env`)
- Docker 이미지 빌드
- `glm-code` 명령어를 `~/.local/bin`에 링크

3. PATH 설정 (필요한 경우):

설치 후 `~/.local/bin`이 PATH에 없다면, 쉘 설정 파일에 다음 라인을 추가하세요:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

- **bash**: `~/.bashrc` 또는 `~/.bash_profile`
- **zsh**: `~/.zshrc`

4. 환경 설정:

`~/.glmenv/env` 파일을 편집하여 GLM API 키와 모델을 설정하세요:

```bash
nano ~/.glmenv/env
```

주요 설정 항목:
- `ANTHROPIC_BASE_URL`: GLM API 엔드포인트
- `ANTHROPIC_AUTH_TOKEN`: GLM API 키
- `ANTHROPIC_DEFAULT_HAIKU_MODEL`: Haiku 모델 이름
- `ANTHROPIC_DEFAULT_SONNET_MODEL`: Sonnet 모델 이름
- `ANTHROPIC_DEFAULT_OPUS_MODEL`: Opus 모델 이름
- `IS_SANDBOX` : docker 에서 root 로 사용하기 위한 설정값

## 사용 방법

코딩하려는 프로젝트 디렉토리로 이동한 후 `glm-code` 명령어를 실행하세요:

```bash
cd /path/to/your/project
glm-code
```

### 작업 환경

- **현재 디렉토리**: `/workspace/<디렉토리명>`에 자동으로 마운트됩니다
- **Claude 설정**: `~/.glmenv/claude`에 저장됩니다
- **Git 설정**: 호스트의 `~/.gitconfig`를 공유합니다
- **Docker 소켓**: Docker-in-Docker를 위해 마운트됩니다

예시:
```bash
# 호스트에서
cd ~/myproject
glm-code

# 컨테이너 내에서는 /workspace/myproject 경로에서 작업
```

컨테이너 내에서 Claude Code를 실행하거나 일반 bash 명령어를 사용할 수 있습니다:

```bash
# Claude Code 실행
claude

# 또는 일반적인 개발 작업
git status
npm install
python script.py
```

종료하려면 `exit`를 입력하거나 `Ctrl+D`를 누르세요.

## 업데이트

Claude Code CLI 및 Docker 이미지 내 패키지를 최신 버전으로 업데이트하려면:

```bash
cd glmctl
./update.sh
```

이 명령은 Docker 이미지를 재빌드하여 모든 도구를 최신 버전으로 업데이트합니다.

## 포함된 도구

Docker 이미지에는 다음 도구들이 사전 설치되어 있습니다:

- **Claude Code CLI**: AI 코딩 어시스턴트
- **Node.js 22.x** (nvm)
- **Python 3** + pip + venv
- **Rust** (rustup + cargo)
- **uv**: 빠른 Python 패키지 설치 도구
- **Git** + GitHub CLI (gh) + git-delta
- **Docker CLI**: Docker-in-Docker 지원
- **기타**: tmux, vim, nano, jq, fzf 등

## 문제 해결

### Docker가 실행되지 않음

```
❌ Error: Docker is not running.
```

**해결 방법**: OrbStack 또는 Docker Desktop을 실행하세요.

### PATH에 glm-code가 없음

```
command not found: glm-code
```

**해결 방법**:
1. `~/.local/bin`이 PATH에 있는지 확인
2. 없다면 쉘 설정 파일에 다음 추가:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```
3. 새 터미널을 열거나 `source ~/.zshrc` (또는 `~/.bashrc`) 실행

### 환경 변수가 로드되지 않음

```
❌ Error: Configuration file not found
```

**해결 방법**:
1. `~/.glmenv/env` 파일이 존재하는지 확인
2. 없다면 `./install.sh`를 다시 실행

## 디렉토리 구조

```
~/.glmenv/
├── env          # 환경 변수 설정 파일 (API 키 등)
└── claude/      # Claude Code 설정 및 데이터
```

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 참고 링크

- [GLM Coding Lite](https://z.ai/subscribe?ic=QUOROVB4GK)
- [Claude Code 문서](https://docs.claude.com/claude-code)
- [OrbStack](https://orbstack.dev/)
