# YTM Backend API

YouTube Music Downloader 백엔드 서버 - FastAPI 기반 REST API

## 📋 목차

- [개요](#개요)
- [기능](#기능)
- [기술 스택](#기술-스택)
- [프로젝트 구조](#프로젝트-구조)
- [설치 및 실행](#설치-및-실행)
- [API 문서](#api-문서)
- [비즈니스 모델](#비즈니스-모델)
- [배포](#배포)
- [환경 변수](#환경-변수)

---

## 개요

YTM Backend는 YouTube 영상을 고품질 MP3로 변환하여 다운로드할 수 있는 REST API 서버입니다.
Flutter 앱(ytm-app)의 백엔드로 사용되며, 사용자 인증, 구독 관리, 다운로드 처리를 담당합니다.

### 왜 서버가 필요한가?

1. **iOS 지원**: iOS에서는 직접 다운로드가 불가능하여 서버 기반 처리 필수
2. **YouTube 차단 우회**: 서버 IP를 통한 안정적인 접근
3. **사용량 제어**: Free/Pro 사용자 구분 및 일일 제한 관리
4. **결제 처리**: Stripe 웹훅을 통한 구독 관리

---

## 기능

### 핵심 기능

| 기능 | 설명 |
|------|------|
| 🔐 **사용자 인증** | JWT 기반 회원가입/로그인 |
| 🔍 **YouTube 검색** | 키워드로 영상 검색 |
| 📋 **영상 정보** | 제목, 아티스트, 썸네일, 길이 조회 |
| ⬇️ **다운로드** | MP3 변환 및 다운로드 (128/320kbps) |
| 📁 **플레이리스트** | 플레이리스트 전체 조회 |
| 💳 **구독 관리** | Stripe 결제 및 웹훅 처리 |

### 사용자 등급별 기능

| 기능 | Free | Pro ($4.99/월) | Ultra ($9.99/월) |
|------|:----:|:----:|:----:|
| 일일 다운로드 | 3개 | 무제한 | 무제한 |
| 음질 | 128kbps | 320kbps | 320kbps |
| 광고 | 있음 | 없음 | 없음 |
| 플레이리스트 | ❌ | ✅ | ✅ |
| 우선 처리 | ❌ | ❌ | ✅ |

---

## 기술 스택

```
Backend Framework : FastAPI 0.109.0
Database          : PostgreSQL 15 + SQLAlchemy 2.0
Cache             : Redis 7
Auth              : JWT (python-jose)
YouTube           : yt-dlp
Audio Processing  : FFmpeg
Payments          : Stripe
Container         : Docker + Docker Compose
```

---

## 프로젝트 구조

```
ytm-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 앱 진입점
│   │
│   ├── core/                   # 핵심 설정
│   │   ├── __init__.py
│   │   ├── config.py           # 환경 변수 설정
│   │   ├── database.py         # DB 연결 (AsyncSession)
│   │   └── security.py         # JWT 인증, 비밀번호 해싱
│   │
│   ├── models/                 # SQLAlchemy 모델
│   │   ├── __init__.py
│   │   ├── user.py             # User, SubscriptionTier
│   │   └── download.py         # Download, DownloadStatus
│   │
│   ├── services/               # 비즈니스 로직
│   │   ├── __init__.py
│   │   └── youtube_service.py  # yt-dlp 래퍼
│   │
│   └── api/                    # API 라우터
│       ├── __init__.py
│       ├── auth.py             # 회원가입, 로그인, 토큰
│       ├── videos.py           # 검색, 정보 조회
│       ├── downloads.py        # 다운로드 요청/관리
│       └── webhooks.py         # Stripe 웹훅
│
├── tests/                      # 테스트 코드
├── test_server.py              # 경량 테스트 서버
├── requirements.txt            # Python 의존성
├── Dockerfile                  # Docker 이미지
├── docker-compose.yml          # 개발 환경
├── .env.example                # 환경 변수 템플릿
└── README.md
```

---

## 설치 및 실행

### 방법 1: Docker (권장)

```bash
# 1. 저장소 클론
git clone https://github.com/shinjadong/ytm-backend.git
cd ytm-backend

# 2. 환경 변수 설정
cp .env.example .env
nano .env  # SECRET_KEY 등 수정

# 3. Docker Compose 실행
docker-compose up -d

# 4. 상태 확인
curl http://localhost:8000/health
```

### 방법 2: 로컬 실행

```bash
# 1. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. PostgreSQL, Redis 실행 (별도 설치 필요)
# 4. 환경 변수 설정
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/ytm"
export SECRET_KEY="your-secret-key"

# 5. 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 방법 3: 경량 테스트 서버 (Termux 등)

```bash
# 의존성 없이 바로 실행 가능 (yt-dlp만 필요)
python test_server.py
```

---

## API 문서

### 인증 (Authentication)

#### 회원가입
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "username": "myusername"
}
```

**응답:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### 로그인
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

#### 내 정보 조회
```http
GET /api/auth/me
Authorization: Bearer {access_token}
```

**응답:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "myusername",
  "subscription_tier": "free",
  "is_pro": false,
  "daily_downloads": 2,
  "daily_limit": 3
}
```

---

### 영상 (Videos)

#### 영상 정보 조회
```http
GET /api/videos/info?url=https://youtu.be/PsO6ZnUZI0g
```

**응답:**
```json
{
  "id": "PsO6ZnUZI0g",
  "title": "Kanye West - Stronger",
  "artist": "Kanye West",
  "thumbnail": "https://i.ytimg.com/vi/PsO6ZnUZI0g/maxresdefault.jpg",
  "duration": 266
}
```

#### 검색
```http
GET /api/videos/search?q=kanye+west&limit=10
```

**응답:**
```json
{
  "videos": [
    {
      "id": "PsO6ZnUZI0g",
      "title": "Kanye West - Stronger",
      "artist": "Kanye West",
      "duration": 266
    }
  ],
  "query": "kanye west",
  "count": 10
}
```

#### 플레이리스트 조회
```http
GET /api/videos/playlist?url=https://youtube.com/playlist?list=PLxxxxx
```

---

### 다운로드 (Downloads)

#### 다운로드 요청
```http
POST /api/downloads
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "video_id": "PsO6ZnUZI0g"
}
```

**응답:**
```json
{
  "id": 123,
  "video_id": "PsO6ZnUZI0g",
  "title": "Kanye West - Stronger",
  "artist": "Kanye West",
  "status": "pending",
  "quality": "128",
  "download_url": null,
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### 다운로드 상태 확인
```http
GET /api/downloads/123
Authorization: Bearer {access_token}
```

**상태값:**
- `pending`: 대기 중
- `processing`: 변환 중
- `completed`: 완료
- `failed`: 실패

#### 파일 다운로드
```http
GET /api/downloads/123/file
Authorization: Bearer {access_token}
```

---

## 비즈니스 모델

### 수익 구조

```
┌─────────────────────────────────────────────────────┐
│                    월간 예상 수익                     │
├─────────────────────────────────────────────────────┤
│  MAU 10,000명 기준                                   │
│                                                      │
│  Free (85%):  8,500명 × 광고     = $500/월          │
│  Pro (12%):   1,200명 × $4.99    = $5,988/월        │
│  Ultra (3%):    300명 × $9.99    = $2,997/월        │
│  ─────────────────────────────────────────────       │
│  총 매출:                          $9,485/월         │
│  서버 비용:                        -$100/월          │
│  결제 수수료 (10%):                -$900/월          │
│  ─────────────────────────────────────────────       │
│  순이익:                           $8,485/월         │
│                                   (약 1,100만원)     │
└─────────────────────────────────────────────────────┘
```

### 결제 시스템

- **Paddle**: 해외 결제, 세금 처리 자동화 (수수료 5-10%)
- **Stripe**: 직접 연동 (수수료 2.9%)
- **암호화폐**: USDT/USDC (수수료 1%)

---

## 배포

### 권장 서버: Hetzner Cloud

| 플랜 | 사양 | 가격 |
|------|------|------|
| CX11 | 1 vCPU, 2GB RAM | €3.29/월 |
| CX21 | 2 vCPU, 4GB RAM | €5.39/월 |
| CX31 | 2 vCPU, 8GB RAM | €9.29/월 |

### 배포 스크립트

```bash
# 서버 접속
ssh root@your-server-ip

# Docker 설치
curl -fsSL https://get.docker.com | sh

# 저장소 클론
git clone https://github.com/shinjadong/ytm-backend.git
cd ytm-backend

# 환경 변수 설정
cp .env.example .env
nano .env

# 실행
docker-compose up -d

# Nginx 리버스 프록시 설정 (선택)
apt install nginx certbot python3-certbot-nginx
```

### Nginx 설정

```nginx
server {
    listen 80;
    server_name api.yourapp.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 환경 변수

| 변수 | 설명 | 기본값 | 필수 |
|------|------|--------|:----:|
| `SECRET_KEY` | JWT 서명 키 | - | ✅ |
| `DATABASE_URL` | PostgreSQL 연결 URL | - | ✅ |
| `REDIS_URL` | Redis 연결 URL | localhost:6379 | |
| `STRIPE_SECRET_KEY` | Stripe API 키 | - | |
| `STRIPE_WEBHOOK_SECRET` | Stripe 웹훅 시크릿 | - | |
| `FREE_DAILY_LIMIT` | 무료 사용자 일일 제한 | 3 | |
| `FREE_QUALITY` | 무료 사용자 음질 | 128 | |
| `PRO_QUALITY` | Pro 사용자 음질 | 320 | |
| `DOWNLOAD_PATH` | 파일 저장 경로 | /tmp/ytm-downloads | |
| `MAX_FILE_AGE_HOURS` | 파일 보관 시간 | 24 | |

---

## 라이선스

Proprietary - All rights reserved

---

## 관련 저장소

- **Frontend (Flutter)**: [ytm-app](https://github.com/shinjadong/ytm-app)
- **Shell Script**: [ytm](https://github.com/shinjadong/ytm)
