"""
Google Sheets Write API
채널톡에서 데이터를 받아 Google Sheets에 쓰는 Vercel Serverless Function
"""

from http.server import BaseHTTPRequestHandler
import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

# Google Sheets API 설정
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


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
        """POST 요청 처리 - Google Sheets에 데이터 쓰기"""
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
            data = request_data.get('data')

            if not sheet_id:
                raise ValueError("sheet_id가 필요합니다")
            if not sheet_name:
                raise ValueError("sheet_name이 필요합니다")
            if not data:
                raise ValueError("data가 필요합니다")

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

            # 데이터를 행으로 변환
            # data는 딕셔너리 형태로 들어오므로 리스트로 변환
            row_values = [
                data.get('name', ''),
                data.get('message', ''),
                data.get('timestamp', datetime.now().isoformat())
            ]

            # 추가 필드가 있으면 포함
            for key, value in data.items():
                if key not in ['name', 'message', 'timestamp']:
                    row_values.append(str(value))

            values = [row_values]
            body_data = {'values': values}

            # 시트에 데이터 추가 (맨 마지막 행에 추가)
            result = sheets_service.spreadsheets().values().append(
                spreadsheetId=sheet_id,
                range=f'{sheet_name}!A:Z',  # A부터 Z열까지 사용 가능
                valueInputOption='USER_ENTERED',  # 사용자 입력 형식 (날짜, 숫자 자동 변환)
                insertDataOption='INSERT_ROWS',
                body=body_data
            ).execute()

            # 성공 응답
            self._set_headers(200)
            response = {
                'status': 'success',
                'message': '데이터가 성공적으로 저장되었습니다',
                'updated_range': result.get('updates', {}).get('updatedRange', ''),
                'updated_rows': result.get('updates', {}).get('updatedRows', 0),
                'updated_cells': result.get('updates', {}).get('updatedCells', 0)
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
