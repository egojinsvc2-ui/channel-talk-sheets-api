"""
Google Sheets API 로컬 테스트
전화번호 검색 기능 테스트
"""

import sys
import os

# api 폴더를 Python path에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from utils.sheets_common import (
    get_sheets_service,
    get_all_sheet_names,
    normalize_phone,
    compare_phone_numbers,
    batch_get_columns,
    get_row_data
)

# 환경 변수 설정 (로컬 테스트용)
service_account_file = r'C:\Users\고동현\Downloads\field-work-analyzer-01029068e93a.json'

# JSON 파일 읽기
import json
with open(service_account_file, 'r', encoding='utf-8') as f:
    service_account_json = json.load(f)

# 환경 변수로 설정
os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'] = json.dumps(service_account_json)

# 테스트 설정
SHEET_ID = '1bADgRJlufpAoBGsDtyUWsHVAtmNe3ocYbcs9F3WnsCk'
TEST_PHONE = '010-3850-7656'

print("=" * 80)
print("Google Sheets API 테스트 시작")
print("=" * 80)

try:
    # 1. Google Sheets 서비스 생성
    print("\n[1단계] Google Sheets 서비스 생성...")
    sheets_service = get_sheets_service()
    print("✅ 성공: Google Sheets 서비스 생성 완료")

    # 2. 모든 시트 이름 가져오기
    print("\n[2단계] 모든 시트 이름 가져오기...")
    sheet_names = get_all_sheet_names(sheets_service, SHEET_ID)
    print(f"✅ 성공: {len(sheet_names)}개 시트 발견")
    print(f"   시트 목록 (처음 10개): {sheet_names[:10]}")

    # 3. 전화번호 정규화 테스트
    print(f"\n[3단계] 전화번호 정규화 테스트...")
    normalized = normalize_phone(TEST_PHONE)
    print(f"   원본: {TEST_PHONE}")
    print(f"   정규화: {normalized}")

    # 4. 전화번호 검색
    print(f"\n[4단계] 전화번호 검색 중...")
    print(f"   검색 대상: G열, H열")
    print(f"   검색 시트 수: {len(sheet_names)}")

    # 배치 읽기
    print(f"\n   배치 읽기 실행 중... (시간이 걸릴 수 있습니다)")
    all_data = batch_get_columns(sheets_service, SHEET_ID, sheet_names, ['G', 'H'])
    print(f"✅ 성공: 데이터 읽기 완료")

    # 전화번호 검색
    found = False
    found_sheet = None
    found_row = None
    found_g_value = None
    found_h_value = None

    for sheet_name in sheet_names:
        g_column = all_data[sheet_name].get('G', [])
        h_column = all_data[sheet_name].get('H', [])

        max_rows = max(len(g_column), len(h_column))

        for row_idx in range(max_rows):
            g_value = g_column[row_idx][0] if row_idx < len(g_column) and len(g_column[row_idx]) > 0 else ''
            h_value = h_column[row_idx][0] if row_idx < len(h_column) and len(h_column[row_idx]) > 0 else ''

            if compare_phone_numbers(g_value, normalized) or compare_phone_numbers(h_value, normalized):
                found = True
                found_sheet = sheet_name
                found_row = row_idx + 1
                found_g_value = g_value
                found_h_value = h_value
                break

        if found:
            break

    if found:
        print(f"\n✅ 전화번호 찾음!")
        print(f"   시트: {found_sheet}")
        print(f"   행: {found_row}")
        print(f"   G열 값: {found_g_value}")
        print(f"   H열 값: {found_h_value}")

        # 5. C열, F열 값 가져오기
        print(f"\n[5단계] 해당 행의 C열, F열 값 가져오기...")
        row_data = get_row_data(sheets_service, SHEET_ID, found_sheet, found_row, ['C', 'F'])

        action_date = row_data.get('C', '')
        product_list = row_data.get('F', '')

        print(f"✅ 성공!")
        print(f"   C열 (action_date): {action_date}")
        print(f"   F열 (product_list): {product_list}")

    else:
        print(f"\n❌ 전화번호를 찾을 수 없습니다")
        print(f"   검색한 번호: {normalized}")

except Exception as e:
    print(f"\n❌ 오류 발생: {type(e).__name__}")
    print(f"   메시지: {str(e)}")
    import traceback
    print(f"\n상세 오류:")
    traceback.print_exc()

print("\n" + "=" * 80)
print("테스트 종료")
print("=" * 80)
