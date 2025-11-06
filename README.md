# Channel Talk + Google Sheets API

채널톡(Channel Talk)에서 Google Sheets를 읽고 쓸 수 있는 REST API 서버입니다.
Vercel Serverless Functions로 배포되어 사용됩니다.

## 🚀 API 엔드포인트

### 1. 전화번호로 고객 정보 검색 ⭐ (주요 기능)
**POST** `/api/sheets-search-phone`

채널톡에서 고객의 전화번호를 받아 Google Sheets의 모든 시트에서 검색합니다.
- G열 또는 H열에서 전화번호 검색
- 매칭된 행의 C열(일정), F열(접수내용) 값 반환
- API 호출 최소화 (배치 읽기 사용)
 
**요청 예시:**
```json
{
  "sheet_id": "1bADgRJlufpAoBGsDtyUWsHVAtmNe3ocYbcs9F3WnsCk",
  "phone_number": "+82 10-5217-0838"
}
```

**응답 예시 (찾았을 때):**
```json
{
  "status": "success",
  "found": true,
  "sheet_name": "접수현황",
  "row": 15,
  "action_date": "2025-11-10",
  "product_list": "제품A, 제품B",
  "phone_normalized": "010-5217-0838"
}
```

**응답 예시 (못 찾았을 때):**
```json
{
  "status": "success",
  "found": false,
  "action_date": "",
  "product_list": "",
  "phone_normalized": "010-5217-0838",
  "message": "일치하는 전화번호를 찾을 수 없습니다"
}
```

**전화번호 자동 변환:**
- `+82 10-5217-0838` → `010-5217-0838`
- `+82 010-5217-0838` → `010-5217-0838`
- `+8210-5217-0838` → `010-5217-0838`

### 2. 시트에 데이터 쓰기
**POST** `/api/sheets-write`

Google Sheets에 새 행을 추가합니다.

**요청 예시:**
```json
{
  "sheet_id": "1ABC...xyz",
  "sheet_name": "문의내역",
  "data": {
    "name": "홍길동",
    "message": "문의 내용입니다",
    "timestamp": "2025-11-04T15:30:00"
  }
}
```

**응답 예시:**
```json
{
  "status": "success",
  "message": "데이터가 성공적으로 저장되었습니다",
  "updated_range": "문의내역!A10:C10",
  "updated_rows": 1,
  "updated_cells": 3
}
```

### 2. 시트에서 데이터 읽기
**POST** `/api/sheets-read`

Google Sheets의 데이터를 읽어옵니다.

**요청 예시 (전체 데이터):**
```json
{
  "sheet_id": "1ABC...xyz",
  "sheet_name": "문의내역",
  "range": "A:C"
}
```

**요청 예시 (검색):**
```json
{
  "sheet_id": "1ABC...xyz",
  "sheet_name": "문의내역",
  "range": "A:C",
  "search": {
    "column": "A",
    "value": "홍길동"
  }
}
```

**응답 예시:**
```json
{
  "status": "success",
  "message": "2개의 결과를 찾았습니다",
  "total_rows": 50,
  "filtered_count": 2,
  "results": [
    {
      "row": 5,
      "data": ["홍길동", "문의 내용 1", "2025-11-04"]
    },
    {
      "row": 15,
      "data": ["홍길동", "문의 내용 2", "2025-11-05"]
    }
  ]
}
```

## 📦 설치 및 배포

### 1. 로컬 설정 (선택사항)

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. GitHub 저장소 생성

```bash
# Git 초기화
cd channel-talk-sheets-api
git init
git add .
git commit -m "Initial commit: Channel Talk Google Sheets API"

# GitHub 저장소에 푸시
git remote add origin https://github.com/YOUR_USERNAME/channel-talk-sheets-api.git
git branch -M main
git push -u origin main
```

### 3. Vercel 배포

1. **Vercel 웹사이트 접속**: https://vercel.com
2. **New Project** 클릭
3. GitHub 저장소 연결: `channel-talk-sheets-api`
4. **Environment Variables** 설정:
   - Key: `GOOGLE_SERVICE_ACCOUNT_JSON`
   - Value: Service Account JSON 파일의 **전체 내용**을 붙여넣기
5. **Deploy** 클릭

### 4. Google Sheets 권한 부여

1. Google Sheets 열기
2. 우측 상단 **공유** 버튼 클릭
3. 다음 이메일 추가: `channeltalk@field-work-analyzer.iam.gserviceaccount.com`
4. 권한: **편집자** 선택
5. **완료** 클릭

## 🔐 환경 변수

### GOOGLE_SERVICE_ACCOUNT_JSON

Service Account JSON 파일의 전체 내용입니다.

**Vercel 설정 방법:**
1. Vercel 프로젝트 → Settings → Environment Variables
2. Name: `GOOGLE_SERVICE_ACCOUNT_JSON`
3. Value: JSON 파일 내용 전체 복사해서 붙여넣기
4. Save

**JSON 파일 위치:** `C:\Users\고동현\Downloads\field-work-analyzer-01029068e93a.json`

## 📝 채널톡 코드 노드 사용 예시

### 전화번호로 고객 정보 검색 ⭐

채널톡에서 고객 전화번호로 Google Sheets를 검색하여 `action_date`, `product_list` 메모리 변수에 저장합니다.

**완전한 코드는 `channel-talk-code-node-search-phone.js` 파일 참조**

```javascript
export const handler = async (memory, context) => {
  const axios = require('axios');

  const phoneNumber = context.user.profile?.mobileNumber;

  if (!phoneNumber) {
    console.log('전화번호가 없습니다');
    memory.put('action_date', '');
    memory.put('product_list', '');
    memory.save();
    return;
  }

  try {
    const response = await axios.post(
      'https://YOUR_PROJECT.vercel.app/api/sheets-search-phone',
      {
        sheet_id: '1bADgRJlufpAoBGsDtyUWsHVAtmNe3ocYbcs9F3WnsCk',
        phone_number: phoneNumber
      }
    );

    if (response.data.found) {
      memory.put('action_date', response.data.action_date || '');
      memory.put('product_list', response.data.product_list || '');
      console.log('고객 정보 찾음:', response.data);
    } else {
      memory.put('action_date', '');
      memory.put('product_list', '');
      console.log('고객 정보 없음');
    }

    memory.save();

  } catch (error) {
    console.log('검색 실패:', error.message);
    memory.put('action_date', '');
    memory.put('product_list', '');
    memory.save();
  }
};
```

### 시트에 데이터 쓰기

```javascript
export const handler = async (memory, context) => {
  const axios = require('axios');

  try {
    const response = await axios.post(
      'https://YOUR_PROJECT.vercel.app/api/sheets-write',
      {
        sheet_id: '1ABC...xyz',
        sheet_name: '문의내역',
        data: {
          name: context.user.name,
          message: memory.get('user_inquiry'),
          timestamp: new Date().toISOString()
        }
      }
    );

    console.log('저장 성공:', response.data);
    memory.put('save_status', 'success');
    memory.save();

  } catch (error) {
    console.log('저장 실패:', error.message);
    memory.put('save_status', 'failed');
    memory.put('error', error.message);
    memory.save();
  }
};
```

### 시트에서 데이터 읽기

```javascript
export const handler = async (memory, context) => {
  const axios = require('axios');

  try {
    const response = await axios.post(
      'https://YOUR_PROJECT.vercel.app/api/sheets-read',
      {
        sheet_id: '1ABC...xyz',
        sheet_name: '문의내역',
        range: 'A:C',
        search: {
          column: 'A',
          value: context.user.name
        }
      }
    );

    console.log('조회 결과:', response.data);
    memory.put('user_history', response.data.results);
    memory.save();

  } catch (error) {
    console.log('조회 실패:', error.message);
    memory.put('read_status', 'failed');
    memory.save();
  }
};
```

## 🛠️ 프로젝트 구조

```
channel-talk-sheets-api/
├── api/
│   ├── sheets-search-phone.py        # ⭐ 전화번호 검색 API (주요)
│   ├── sheets-write.py               # 시트 쓰기 API
│   ├── sheets-read.py                # 시트 읽기 API
│   └── utils/
│       └── sheets_common.py          # 공통 모듈 (인증, 전화번호 변환 등)
├── channel-talk-code-node-search-phone.js  # 채널톡 코드 노드 예제
├── requirements.txt                  # Python 패키지
├── vercel.json                       # Vercel 설정
├── .gitignore                        # Git 제외 파일
└── README.md                         # 이 문서
```

## 🎯 주요 기능 흐름

### 전화번호 검색 프로세스

```
채널톡
  ↓ context.user.profile.mobileNumber
  ↓ (예: +82 10-5217-0838)
  ↓
Vercel API (/api/sheets-search-phone)
  ↓
전화번호 정규화 (010-5217-0838)
  ↓
Google Sheets 전체 시트 검색
  - 배치 읽기로 API 호출 최소화
  - G열, H열에서 전화번호 찾기
  ↓
매칭된 행 찾음?
  ├─ Yes → C열(action_date), F열(product_list) 반환
  └─ No  → 빈 값 반환
  ↓
채널톡 메모리 변수 업데이트
  - memory.put('action_date', ...)
  - memory.put('product_list', ...)
```

## 📌 주의사항

### 보안
- ⚠️ Service Account JSON 파일을 **절대 Git에 커밋하지 마세요**
- ⚠️ `.gitignore`에 `*.json` 추가됨 (vercel.json 제외)
- ✅ Vercel 환경 변수로만 사용

### Google Sheets API
- Service Account 이메일에 시트 편집 권한 필요
- 시트 ID는 Google Sheets URL에서 확인:
  ```
  https://docs.google.com/spreadsheets/d/1ABC...xyz/edit
                                        ^^^^^^^^^^^
                                        이 부분이 sheet_id
  ```

### 채널톡 코드 노드 제약사항
- JavaScript만 사용 가능
- axios 라이브러리 사용 필수
- 실행 시간 최대 60초

## 🐛 트러블슈팅

### API 호출 시 403 오류
→ Service Account에 시트 편집 권한이 없음. 시트 공유 설정 확인.

### API 호출 시 500 오류
→ Vercel 환경 변수 `GOOGLE_SERVICE_ACCOUNT_JSON` 확인. JSON 형식이 올바른지 점검.

### 채널톡에서 CORS 오류
→ API 코드에 CORS 헤더가 이미 설정되어 있음. Vercel 재배포 필요.

## 📞 문의

문제가 발생하면 Vercel 프로젝트의 Logs를 확인하세요.

## 📄 라이선스

MIT License
