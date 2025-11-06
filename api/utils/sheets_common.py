"""
Google Sheets 공통 기능 모듈
- 인증
- 데이터 읽기/쓰기 공통 함수
- 전화번호 변환 등 유틸리티 함수
"""

import json
import os
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build


# Google Sheets API 스코프
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly'
]


def get_sheets_service():
    """
    Google Sheets API 서비스 객체 생성
    환경 변수에서 Service Account 정보를 읽어 인증
    """
    # Base64 인코딩된 환경 변수 먼저 시도
    service_account_base64 = os.environ.get('GOOGLE_SERVICE_ACCOUNT_BASE64')
    if service_account_base64:
        # Base64 디코딩
        service_account_json = base64.b64decode(service_account_base64).decode('utf-8')
    else:
        # 기존 JSON 환경 변수 시도
        service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
        if not service_account_json:
            raise ValueError("환경 변수 GOOGLE_SERVICE_ACCOUNT_BASE64 또는 GOOGLE_SERVICE_ACCOUNT_JSON이 설정되지 않았습니다")

    service_account_info = json.loads(service_account_json)
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info, scopes=SCOPES
    )

    return build('sheets', 'v4', credentials=credentials)


def get_all_sheet_names(sheets_service, spreadsheet_id):
    """
    스프레드시트의 모든 시트(탭) 이름 가져오기

    Args:
        sheets_service: Google Sheets API 서비스 객체
        spreadsheet_id: 스프레드시트 ID

    Returns:
        list: 시트 이름 리스트
    """
    spreadsheet = sheets_service.spreadsheets().get(
        spreadsheetId=spreadsheet_id
    ).execute()

    sheets = spreadsheet.get('sheets', [])
    return [sheet['properties']['title'] for sheet in sheets]


def normalize_phone(phone):
    """
    전화번호를 한국 표준 형식으로 변환

    변환 예시:
    - +82 10-5217-0838 → 010-5217-0838
    - +82 010-5217-0838 → 010-5217-0838
    - +8210-5217-0838 → 010-5217-0838
    - +821052170838 → 010-5217-0838
    - 01052170838 → 010-5217-0838

    Args:
        phone (str): 원본 전화번호

    Returns:
        str: 정규화된 전화번호 (010-xxxx-xxxx 형식)
    """
    if not phone:
        return ""

    # 공백, 하이픈 제거
    phone = str(phone).strip().replace(" ", "").replace("-", "")

    # +82로 시작하면 0으로 변경
    if phone.startswith("+82"):
        phone = "0" + phone[3:]
    elif phone.startswith("82") and len(phone) >= 10:
        phone = "0" + phone[2:]

    # 11자리 숫자인 경우 010-xxxx-xxxx 형태로 변경
    if len(phone) == 11 and phone.startswith("0"):
        return f"{phone[0:3]}-{phone[3:7]}-{phone[7:11]}"

    # 10자리 숫자인 경우 (지역번호) 0xx-xxx-xxxx 또는 0xx-xxxx-xxxx
    if len(phone) == 10 and phone.startswith("0"):
        # 서울 02 등 지역번호
        if phone.startswith("02"):
            return f"{phone[0:2]}-{phone[2:6]}-{phone[6:10]}"
        else:
            return f"{phone[0:3]}-{phone[3:6]}-{phone[6:10]}"

    # 형식이 맞지 않으면 원본 반환
    return phone


def compare_phone_numbers(phone1, phone2):
    """
    두 전화번호가 같은지 비교
    정규화 후 비교하여 형식이 달라도 같은 번호면 True 반환

    Args:
        phone1 (str): 첫 번째 전화번호
        phone2 (str): 두 번째 전화번호

    Returns:
        bool: 같으면 True, 다르면 False
    """
    normalized1 = normalize_phone(phone1)
    normalized2 = normalize_phone(phone2)

    return normalized1 == normalized2


def batch_get_columns(sheets_service, spreadsheet_id, sheet_names, columns):
    """
    여러 시트의 특정 컬럼들을 한 번에 가져오기 (배치 읽기)
    API 호출 최소화

    Args:
        sheets_service: Google Sheets API 서비스 객체
        spreadsheet_id: 스프레드시트 ID
        sheet_names (list): 시트 이름 리스트
        columns (list): 컬럼 리스트 (예: ['G', 'H'])

    Returns:
        dict: {
            'sheet_name': {
                'G': [[값1], [값2], ...],
                'H': [[값1], [값2], ...]
            }
        }
    """
    # 범위 생성 (예: "시트1!G:G", "시트1!H:H", "시트2!G:G", ...)
    ranges = []
    for sheet_name in sheet_names:
        for column in columns:
            ranges.append(f"'{sheet_name}'!{column}:{column}")

    # 배치 읽기 실행
    result = sheets_service.spreadsheets().values().batchGet(
        spreadsheetId=spreadsheet_id,
        ranges=ranges
    ).execute()

    value_ranges = result.get('valueRanges', [])

    # 결과 정리
    data = {}
    idx = 0
    for sheet_name in sheet_names:
        data[sheet_name] = {}
        for column in columns:
            if idx < len(value_ranges):
                data[sheet_name][column] = value_ranges[idx].get('values', [])
            else:
                data[sheet_name][column] = []
            idx += 1

    return data


def get_row_data(sheets_service, spreadsheet_id, sheet_name, row_number, columns):
    """
    특정 시트의 특정 행에서 여러 컬럼 값 가져오기

    Args:
        sheets_service: Google Sheets API 서비스 객체
        spreadsheet_id: 스프레드시트 ID
        sheet_name: 시트 이름
        row_number: 행 번호 (1부터 시작)
        columns (list): 컬럼 리스트 (예: ['C', 'F'])

    Returns:
        dict: {'C': '값1', 'F': '값2'}
    """
    # 범위 생성 (예: "시트1!C5:F5")
    start_col = min(columns)
    end_col = max(columns)
    range_notation = f"'{sheet_name}'!{start_col}{row_number}:{end_col}{row_number}"

    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_notation
    ).execute()

    values = result.get('values', [[]])[0] if result.get('values') else []

    # 컬럼 인덱스 계산 (A=0, B=1, C=2, ...)
    def col_to_index(col):
        return ord(col.upper()) - ord('A')

    start_index = col_to_index(start_col)

    # 결과 딕셔너리 생성
    result_dict = {}
    for col in columns:
        col_index = col_to_index(col) - start_index
        if col_index < len(values):
            result_dict[col] = values[col_index]
        else:
            result_dict[col] = ''

    return result_dict
