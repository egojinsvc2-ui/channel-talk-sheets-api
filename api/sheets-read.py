"""
Google Sheets Read API
채널톡에서 요청을 받아 Google Sheets의 데이터를 읽어 반환하는 Vercel Serverless Function
"""

from http.server import BaseHTTPRequestHandler
import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Google Sheets API 설정
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


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
        """POST 요청 처리 - Google Sheets 데이터 읽기"""
        try:
            # 요청 데이터 읽기
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                raise ValueError("요청 본문이 비어있습니다")

            body = self.rfile.read(content_length)
            request_data = json.loads(body.decode('utf-8'))

            # 필수 파라미터 확인
            sheet_id = request_data.get('sheet_id')
            sheet_name = request_data.get('sheet_name')
            range_notation = request_data.get('range', 'A:Z')  # 기본값: A부터 Z열까지

            if not sheet_id:
                raise ValueError("sheet_id가 필요합니다")
            if not sheet_name:
                raise ValueError("sheet_name이 필요합니다")

            # Service Account 인증
            service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
            if not service_account_json:
                raise ValueError("환경 변수 GOOGLE_SERVICE_ACCOUNT_JSON이 설정되지 않았습니다")

            service_account_info = json.loads(service_account_json)
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info, scopes=SCOPES
            )

            # Google Sheets API 클라이언트 생성
            sheets_service = build('sheets', 'v4', credentials=credentials)

            # 시트 데이터 읽기
            full_range = f'{sheet_name}!{range_notation}'
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=full_range
            ).execute()

            values = result.get('values', [])

            # 검색 조건이 있는 경우 필터링
            search = request_data.get('search')
            filtered_results = []

            if search and values:
                search_column = search.get('column', 'A')  # 검색할 컬럼 (A, B, C 등)
                search_value = search.get('value', '')  # 검색할 값

                # 컬럼 문자를 인덱스로 변환 (A=0, B=1, C=2, ...)
                column_index = ord(search_column.upper()) - ord('A')

                # 데이터 필터링 (첫 행은 헤더로 가정하고 건너뜀)
                for idx, row in enumerate(values[1:], start=2):  # start=2는 실제 시트의 행 번호
                    if column_index < len(row) and str(row[column_index]) == str(search_value):
                        filtered_results.append({
                            'row': idx,
                            'data': row
                        })

                # 성공 응답 (검색 결과)
                self._set_headers(200)
                response = {
                    'status': 'success',
                    'message': f'{len(filtered_results)}개의 결과를 찾았습니다',
                    'search': search,
                    'total_rows': len(values),
                    'filtered_count': len(filtered_results),
                    'results': filtered_results
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

            else:
                # 검색 조건이 없으면 전체 데이터 반환
                self._set_headers(200)
                response = {
                    'status': 'success',
                    'message': f'{len(values)}개의 행을 읽었습니다',
                    'total_rows': len(values),
                    'range': full_range,
                    'data': values
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
            self._set_headers(500)
            error_response = {
                'status': 'error',
                'message': '서버 오류가 발생했습니다',
                'error': str(e),
                'type': type(e).__name__
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
