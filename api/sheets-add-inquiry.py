"""
Google Sheets 문의인입 추가 API
채널톡에서 고객 정보를 받아 '문의인입' 시트의 마지막 행에 추가
A열: name
B열: mobile_number
C열: action_date (기존일정)
D열: change_date (변경원하는 일정)
E열: request
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# utils 모듈 경로 추가
sys.path.append(os.path.dirname(__file__))
from utils.sheets_common import get_sheets_service

# Google Sheets 문서 ID (수도권)
SHEET_ID = '1bADgRJlufpAoBGsDtyUWsHVAtmNe3ocYbcs9F3WnsCk'
INQUIRY_SHEET_NAME = '문의인입'


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
        """POST 요청 처리 - 문의인입 시트에 데이터 추가"""
        try:
            # 요청 데이터 읽기
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                raise ValueError("요청 본문이 비어있습니다")

            body = self.rfile.read(content_length)
            request_data = json.loads(body.decode('utf-8'))

            # 파라미터 가져오기 (없으면 빈 문자열)
            name = request_data.get('name', '')
            mobile_number = request_data.get('mobile_number', '')
            action_date = request_data.get('action_date', '')
            change_date = request_data.get('change_date', '')
            request_text = request_data.get('request', '')

            print(f"문의인입 추가: name={name}, mobile={mobile_number}, action_date={action_date}, change_date={change_date}")

            # Google Sheets 서비스 생성
            sheets_service = get_sheets_service()

            # 현재 마지막 행 찾기
            # A열 전체를 읽어서 데이터가 있는 마지막 행 찾기
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=SHEET_ID,
                range=f"'{INQUIRY_SHEET_NAME}'!A:A"
            ).execute()

            values = result.get('values', [])
            last_row = len(values)  # 마지막 데이터 행
            next_row = last_row + 1  # 다음 행 (새 데이터를 추가할 행)

            print(f"현재 마지막 행: {last_row}, 추가할 행: {next_row}")

            # A부터 E열까지 데이터 준비
            row_data = [[name, mobile_number, action_date, change_date, request_text]]

            # 한 번에 A~E열에 데이터 쓰기
            range_notation = f"'{INQUIRY_SHEET_NAME}'!A{next_row}:E{next_row}"

            sheets_service.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=range_notation,
                valueInputOption='RAW',
                body={'values': row_data}
            ).execute()

            print(f"성공: {next_row}행에 데이터 추가 완료")

            # 성공 응답
            self._set_headers(200)
            response = {
                'status': 'success',
                'message': '문의인입 추가 완료',
                'row': next_row,
                'data': {
                    'name': name,
                    'mobile_number': mobile_number,
                    'action_date': action_date,
                    'change_date': change_date,
                    'request': request_text
                }
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
