# pyBTC 블록체인 프로젝트 - 상세 설명서

## 📌 프로젝트 소개

이 프로젝트는 **Python**과 **Flask**로 구현한 **분산형 블록체인 네트워크**입니다. 가상 암호화폐 **pyBTC**를 발행·이체할 수 있는 개인 블록체인 시스템이며, 다음 기능을 제공합니다:

- **멀티 노드 블록체인 네트워크** (P2P 노드 간 동기화)
- **작업증명(PoW) 기반 채굴** 및 블록 생성
- **지갑 서버** - pyBTC 발송/수신 및 잔액 조회
- **블록 스캔 서버** - 블록체인 전체 조회

---

## 🏗️ 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        pyBTC BlockChain Network                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│   │   Node 1     │◄──►│   Node 2     │◄──►│   Node 3     │   (포트 5000, 5001, 5002)
│   │  (thread1)   │    │  (thread2)   │    │  (thread3)   │              │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘              │
│          │                   │                   │                       │
│          └───────────────────┼───────────────────┘                       │
│                              │                                           │
│                    블록체인 API (chain, transactions, mine)              │
│                              │                                           │
│          ┌───────────────────┼───────────────────┐                       │
│          │                   │                   │                       │
│   ┌──────▼───────┐    ┌──────▼───────┐    ┌──────▼───────┐              │
│   │ WalletServer │    │ BlockScan    │    │  main.py     │              │
│   │  (포트 8081) │    │ Server       │    │  (실행 스크립트)             │
│   │  - 로그인     │    │  (포트 8080) │    │  - 노드 등록  │              │
│   │  - 전송/잔액  │    │  - 블록 조회  │    │  - 채굴 시작  │              │
│   └──────────────┘    └──────────────┘    └──────────────┘              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 프로젝트 구조

```
BlockChainProjects/
├── main.py                    # 실행 진입점 (노드 등록 + 채굴 시작)
├── Nodes/
│   ├── BlockChainClass.py     # 블록체인 핵심 로직 (POW, 검증, 동기화)
│   ├── node.py                # Flask 노드 서버 클래스
│   ├── thread1.py             # Node1 실행 (127.0.0.1:5000)
│   ├── thread2.py             # Node2 실행 (127.0.0.1:5001)
│   └── thread3.py             # Node3 실행 (127.0.0.1:5002)
├── WalletServer/
│   ├── WalletServer.py        # 지갑 웹 서버
│   ├── login.html             # 로그인 화면
│   └── wallet.html            # 지갑 화면 (잔액, 전송)
├── BlockScanServer/
│   ├── BlockScanServer.py     # 블록체인 조회 서버
│   └── BlockScanFront.html    # 블록 조회 화면
├── templates/                 # 기타 템플릿
├── README.md                  # 포트 정리
└── README2.md                 # 이 문서 (상세 설명서)
```

---

## 🔌 포트 구성

| 서비스 | 포트 | 설명 |
|--------|------|------|
| Node 1 | 5000 | 블록체인 노드 1 (주 노드, 지갑/메인 연결 대상) |
| Node 2 | 5001 | 블록체인 노드 2 |
| Node 3 | 5002 | 블록체인 노드 3 |
| BlockScan Server | 8080 | 블록체인 조회 웹 UI |
| Wallet Server | 8081 | 지갑 로그인·전송 웹 UI |

---

## 🔧 핵심 컴포넌트 상세

### 1. `BlockChainClass.py` - 블록체인 핵심

- **Blockchain 클래스**: 블록 생성, 거래, 노드 등록, 동기화
- **해시**: `SHA-256`로 블록·nonce 해싱
- **작업증명(PoW)**: nonce 4자리가 `"0000"`으로 시작하도록 난수 탐색
- **충돌 해결**: 더 긴 유효한 체인으로 교체 (`resolve_conflict`)

**주요 메서드:**
- `hash(block)` - 블록 해시 생성
- `pow(last_proof, stop_event)` - 채굴 (중단 신호 지원)
- `new_transaction()` - 거래 풀에 추가
- `new_block()` - 새 블록 생성
- `valid_chain()` - 체인 유효성 검증
- `resolve_conflict()` - 다른 노드와 비교 후 긴 체인으로 교체

---

### 2. `node.py` - 블록체인 노드 서버

Flask 기반 HTTP API를 제공하는 블록체인 노드입니다.

**API 엔드포인트:**

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 체인 정보 요약 (chain, length, nodes 등) |
| GET | `/chain` | 전체 블록체인 조회 |
| POST | `/nodes/register` | 새 노드 등록 (양방향 등록 + 기존 노드 전파) |
| POST | `/transactions/new` | 새 거래 등록 |
| GET | `/mine` | 채굴 시작 (별도 스레드에서 지속 채굴) |
| POST | `/nodes/resolve` | 새 블록 전파 수신 시 체인 동기화 |

**동작 요약:**
- 채굴 시 다른 노드에 `POST /nodes/resolve`로 새 블록 전파
- 자신보다 긴 체인을 가진 노드가 있으면 로컬 체인 교체
- 채굴 중 다른 노드가 먼저 채굴하면 `stop_mining` 이벤트로 중단 후 재시도

---

### 3. `WalletServer.py` - 지갑 서버

- **포트 8081**에서 Flask 앱 실행
- **기능**: 로그인(지갑 ID 검증), 잔액 조회, pyBTC 전송
- **로그인**: Node 1(`127.0.0.1:5000`)의 `/chain`에서 거래 내역 조회 후 잔액 계산
- **전송**: `/transactions/new` API로 거래 등록

**화면:**
- `login.html`: 지갑 ID 입력 후 로그인
- `wallet.html`: 잔액 표시 + 수신자 주소·금액 입력 후 전송

---

### 4. `BlockScanServer.py` - 블록 조회 서버

- **포트 8080**에서 실행
- **기능**: 블록체인 전체를 테이블로 표시
- **데이터 소스**: Node 2(`127.0.0.1:5001`)의 `/chain` (포트는 변경 가능)
- **화면**: `BlockScanFront.html` - timestamp, previous_hash, nonce, transactions 표시

---

### 5. `main.py` - 실행 스크립트

실행 순서:
1. `RequestRegister('5000', '5001')` - Node 1 ↔ Node 2 서로 등록
2. 잠시 대기 (`time.sleep`)
3. `RequestMineStart(port)` - Node 1, Node 2에서 채굴 시작

> ⚠️ **주의**: `main.py`는 노드가 이미 실행 중이라야 합니다. 노드, 지갑, 블록스캔은 각각 별도 터미널에서 실행해야 합니다.

---

## 🚀 실행 방법

### 1. 의존성 설치

```bash
pip install flask requests pandas
```

### 2. 노드 실행 (각각 별도 터미널)

```bash
# 터미널 1 - Node 1
cd Nodes
python thread1.py

# 터미널 2 - Node 2
cd Nodes
python thread2.py

# (선택) 터미널 3 - Node 3
python thread3.py
```

### 3. 노드 등록 및 채굴 시작

```bash
# 터미널 4
python main.py
```

### 4. 지갑 서버 실행

```bash
cd WalletServer
python WalletServer.py
```

### 5. 블록 스캔 서버 실행

```bash
cd BlockScanServer
python BlockScanServer.py
```

### 6. 웹 접속

- 지갑: http://127.0.0.1:8081
- 블록 조회: http://127.0.0.1:8080

---

## 💡 사용 흐름 예시

1. **채굴**: `main.py` 실행 → 각 노드가 채굴 시작 → 블록 생성 시 보상(pyBTC) 지급
2. **거래**: 지갑 페이지에서 로그인 → 수신자와 금액 입력 후 전송 → 다음 블록에 거래 포함
3. **조회**: BlockScan 페이지에서 생성된 블록과 거래 내역 확인

---

## 🔐 기술적 특징

- **P2P 노드 동기화**: 새 노드 등록 시 양방향 등록 + 기존 노드에 전파
- **채굴 경쟁 처리**: 한 노드가 블록을 먼저 채굴하면 다른 노드에 전파하고, 경쟁 중인 노드는 채굴 중단 후 긴 체인으로 동기화
- **체인 검증**: `previous_hash` 체인 및 PoW(nonce 해시 `"0000"`) 검증
- **지갑 잔액**: `received - sent`로 계산 (블록체인 전체 거래에서 집계)

---

## 📝 기타

- **pyBTC**: 이 프로젝트에서 사용하는 가상 화폐 단위
- **제네시스 블록**: `BlockChain` 초기화 시 `previous_hash=1`, `proof=100`으로 자동 생성
- **채굴 보상**: 블록 생성 시 `master` → 해당 노드로 0.1 pyBTC 지급
