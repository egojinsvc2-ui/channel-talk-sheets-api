// 채널톡 코드 노드 - 전화번호 검색 테스트 버전
// 테스트용: 010-3850-7656으로 고정 검색

const axios = require('axios');

// API 설정
const API_URL = 'https://channel-talk-sheets-api.vercel.app/api/sheets-search-phone';
const SHEET_ID = '1bADgRJlufpAoBGsDtyUWsHVAtmNe3ocYbcs9F3WnsCk';

// 테스트용 전화번호 (하드코딩)
const phoneNumber = '010-3850-7656';

console.log(`📞 [테스트] 검색할 전화번호: ${phoneNumber}`);

// API 호출
try {
  const response = await axios.post(
    API_URL,
    {
      sheet_id: SHEET_ID,
      phone_number: phoneNumber
    },
    {
      timeout: 30000
    }
  );

  console.log('✅ API 응답:', JSON.stringify(response.data));

  if (response.data.found) {
    // 전화번호를 찾은 경우
    const actionDate = response.data.action_date || '';
    const productList = response.data.product_list || '';

    memory.put('action_date', actionDate);
    memory.put('product_list', productList);

    console.log(`✅ 고객 정보 찾음!`);
    console.log(`   시트: ${response.data.sheet_name}`);
    console.log(`   행: ${response.data.row}`);
    console.log(`   일정: ${actionDate}`);
    console.log(`   접수내용: ${productList}`);
  } else {
    // 전화번호를 찾지 못한 경우
    memory.put('action_date', '');
    memory.put('product_list', '');

    console.log('❌ 고객 정보를 찾을 수 없습니다');
    console.log(`   검색한 번호: ${response.data.phone_normalized}`);
  }

  memory.save();

} catch (error) {
  console.log('❌ API 호출 실패:', error.message);

  if (error.response) {
    console.log('   상태 코드:', error.response.status);
    console.log('   오류 내용:', JSON.stringify(error.response.data));
  } else if (error.request) {
    console.log('   네트워크 오류 또는 타임아웃');
  }

  memory.put('action_date', '');
  memory.put('product_list', '');
  memory.save();
}
