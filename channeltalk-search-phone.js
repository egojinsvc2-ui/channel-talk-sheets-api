// 채널톡 코드 노드 - 전화번호로 고객 정보 검색
// 수도권/지방 문서 자동 검색
// 아래 코드를 채널톡 코드 노드에 복사해서 사용하세요
//
// 열 구조:
// A-접수날짜, B-요청날짜, C-처리날짜, D-기사명, E-고객명
// F-상품명/증상, G-접수내용, H-휴대폰번호, I-전화번호
//
// 전화번호 조회: H열, I열
// 반환 데이터: F열(상품명,증상) → product_list

const axios = require('axios');

// API 설정
const API_URL = 'https://channel-talk-sheets-api.vercel.app/api/sheets-search-phone';

// 고객 전화번호 가져오기
const phoneNumber = context.user.profile?.mobileNumber;

if (!phoneNumber) {
  console.log('[경고] 전화번호가 없습니다');
  memory.put('product_list', '');
  memory.put('sheet_name', '');
  memory.save();
  return;
}

console.log(`[검색] 전화번호: ${phoneNumber}`);

// API 호출 (수도권 -> 지방 순차 검색)
try {
  const response = await axios.post(
    API_URL,
    {
      phone_number: phoneNumber
    },
    {
      timeout: 30000
    }
  );

  console.log('[성공] API 응답:', JSON.stringify(response.data));

  if (response.data.found) {
    // 전화번호를 찾은 경우
    const productList = response.data.product_list || '';
    const sheetName = response.data.sheet_name || '';

    memory.put('product_list', productList);
    memory.put('sheet_name', sheetName);

    console.log('[성공] 고객 정보 찾음!');
    console.log(`   시트: ${sheetName}`);
    console.log(`   행: ${response.data.row}`);
    console.log(`   상품정보: ${productList}`);
  } else {
    // 전화번호를 찾지 못한 경우
    memory.put('product_list', '');
    memory.put('sheet_name', '');

    console.log('[실패] 고객 정보를 찾을 수 없습니다');
  }

  memory.save();

} catch (error) {
  console.log('[오류] API 호출 실패:', error.message);

  if (error.response) {
    console.log('   상태 코드:', error.response.status);
    console.log('   오류 내용:', JSON.stringify(error.response.data));
  }

  memory.put('product_list', '');
  memory.put('sheet_name', '');
  memory.save();
}
