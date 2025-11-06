// 채널톡 코드 노드 - 전화번호로 고객 정보 검색
// 수도권/지방 문서 자동 검색
// 아래 코드를 채널톡 코드 노드에 복사해서 사용하세요

const axios = require('axios');

// API 설정
const API_URL = 'https://channel-talk-sheets-api.vercel.app/api/sheets-search-phone';

// 고객 전화번호 가져오기
const phoneNumber = context.user.profile?.mobileNumber;

if (!phoneNumber) {
  console.log('[경고] 전화번호가 없습니다');
  memory.put('action_date', '');
  memory.put('product_list', '');
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
    const actionDate = response.data.action_date || '';
    const productList = response.data.product_list || '';

    memory.put('action_date', actionDate);
    memory.put('product_list', productList);

    console.log('[성공] 고객 정보 찾음!');
    console.log(`   시트: ${response.data.sheet_name}`);
    console.log(`   행: ${response.data.row}`);
    console.log(`   일정: ${actionDate}`);
    console.log(`   접수내용: ${productList}`);
  } else {
    // 전화번호를 찾지 못한 경우
    memory.put('action_date', '');
    memory.put('product_list', '');

    console.log('[실패] 고객 정보를 찾을 수 없습니다');
  }

  memory.save();

} catch (error) {
  console.log('[오류] API 호출 실패:', error.message);

  if (error.response) {
    console.log('   상태 코드:', error.response.status);
    console.log('   오류 내용:', JSON.stringify(error.response.data));
  }

  memory.put('action_date', '');
  memory.put('product_list', '');
  memory.save();
}
