"""
Google Sheets 전화번호 검색 API
채널톡에서 고객 전화번호를 받아 2개의 Google Sheets 문서에서 검색
1. 수도권 문서 검색
2. 못 찾으면 지방 문서 검색

열 구조:
A-접수날짜, B-요청날짜, C-처리날짜, D-기사명, E-고객명
F-상품명/증상, G-접수내용, H-휴대폰번호, I-전화번호

전화번호 조회: H열, I열
반환 데이터: F열(상품명,증상)
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# utils 모듈 경로 추가
sys.path.append(os.path.dirname(__file__))
from utils.sheets_common import (
    get_sheets_service,
    get_all_sheet_names,
    normalize_phone,
    compare_phone_numbers,
    batch_get_columns,
    get_row_data
)

# Google Sheets 문서 ID
SHEET_ID_CAPITAL = '1bADgRJlufpAoBGsDtyUWsHVAtmNe3ocYbcs9F3WnsCk'  # 수도권
SHEET_ID_PROVINCE = '1Gogj_ugZ5tnGi1vXZ6iCSzQd-fXy670JeOjKRk6x-sk'  # 지방


def search_phone_in_sheet(sheets_service, sheet_id, normalized_phone):
    """
    하나의 Google Sheets 문서에서 전화번호 검색

    Args:
        sheets_service: Google Sheets API 서비스
        sheet_id: 검색할 문서 ID
        normalized_phone: 정규화된 전화번호

    Returns:
        dict: 검색 결과 (found, sheet_name, row, action_date, product_list)
              찾지 못하면 found=False
    """
    # 모든 시트 이름 가져오기
    sheet_names = get_all_sheet_names(sheets_service, sheet_id)
    print(f"문서 {sheet_id[:10]}...: {len(sheet_names)}개 시트 검색 중")

    # 모든 시트의 H열(휴대폰번호), I열(전화번호) 데이터 한 번에 가져오기 (배치 읽기)
    all_data = batch_get_columns(sheets_service, sheet_id, sheet_names, ['H', 'I'])

    # 전화번호 검색
    for sheet_name in sheet_names:
        h_column = all_data[sheet_name].get('H', [])  # 휴대폰번호
        i_column = all_data[sheet_name].get('I', [])  # 전화번호

        # 각 행을 순회하며 H열 또는 I열에서 전화번호 찾기
        max_rows = max(len(h_column), len(i_column))

        for row_idx in range(max_rows):
            # H열 값 확인 (휴대폰번호)
            h_value = h_column[row_idx][0] if row_idx < len(h_column) and len(h_column[row_idx]) > 0 else ''
            # I열 값 확인 (전화번호)
            i_value = i_column[row_idx][0] if row_idx < len(i_column) and len(i_column[row_idx]) > 0 else ''

            # 전화번호 비교 (H열 또는 I열 중 하나라도 매칭되면 OK)
            if compare_phone_numbers(h_value, normalized_phone) or \
               compare_phone_numbers(i_value, normalized_phone):
                found_row = row_idx + 1  # 행 번호는 1부터 시작
                print(f"전화번호 찾음: 시트={sheet_name}, 행={found_row}")

                # 매칭된 행의 F열(상품명,증상) 값 가져오기
                row_data = get_row_data(sheets_service, sheet_id, sheet_name, found_row, ['F'])

                return {
                    'found': True,
                    'sheet_name': sheet_name,
                    'row': found_row,
                    'product_list': row_data.get('F', '')  # 상품명,증상
                }

    # 찾지 못함
    return {'found': False}


class handler(BaseHTTPRequestHandler):
    """Vercel Serverless Function Handler"""

    def _set_headers(self, status_code=200):
        """HTTP 응답 헤더 설정"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        """CORS preflight 요청 처리"""
        self._set_headers(200)

    def do_POST(self):
        """POST 요청 처리 - 전화번호로 고객 정보 검색 (2개 문서 순차 검색)"""
        try:
            # 요청 데이터 읽기
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                raise ValueError("요청 본문이 비어있습니다")

            body = self.rfile.read(content_length)
            request_data = json.loads(body.decode('utf-8'))

            # 필수 파라미터 확인
            phone_number = request_data.get('phone_number')

            if not phone_number:
                raise ValueError("phone_number가 필요합니다")

            # 전화번호 정규화
            normalized_phone = normalize_phone(phone_number)
            print(f"검색할 전화번호: {phone_number} → 정규화: {normalized_phone}")

            # Google Sheets 서비스 생성
            sheets_service = get_sheets_service()

            # 1. 수도권 문서 검색
            print("1단계: 수도권 문서 검색")
            result = search_phone_in_sheet(sheets_service, SHEET_ID_CAPITAL, normalized_phone)

            # 2. 수도권에서 못 찾으면 지방 문서 검색
            if not result['found']:
                print("2단계: 지방 문서 검색")
                result = search_phone_in_sheet(sheets_service, SHEET_ID_PROVINCE, normalized_phone)

            # 결과 반환
            if result['found']:
                print(f"결과: 시트={result['sheet_name']}, 행={result['row']}, 상품정보={result['product_list']}")

                self._set_headers(200)
                response = {
                    'status': 'success',
                    'found': True,
                    'sheet_name': result['sheet_name'],
                    'row': result['row'],
                    'product_list': result['product_list'],  # 상품명,증상 (F열)
                    'phone_normalized': normalized_phone
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

            else:
                # 두 문서 모두에서 찾지 못함
                print("결과: 전화번호를 찾을 수 없습니다")

                self._set_headers(200)
                response = {
                    'status': 'success',
                    'found': False,
                    'product_list': '',
                    'phone_normalized': normalized_phone,
                    'message': '일치하는 전화번호를 찾을 수 없습니다'
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

        except json.JSONDecodeError as e:
            # JSON 파싱 오류
            self._set_headers(400)
            error_response = {
                'status': 'error',
                'message': 'JSON 파싱 오류',
                'error': str(e)
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))

        except ValueError as e:
            # 요청 파라미터 오류
            self._set_headers(400)
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            # 기타 오류
            print(f"오류 발생: {type(e).__name__}: {str(e)}")
            self._set_headers(500)
            error_response = {
                'status': 'error',
                'message': '서버 오류가 발생했습니다',
                'error': str(e),
                'type': type(e).__name__
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
