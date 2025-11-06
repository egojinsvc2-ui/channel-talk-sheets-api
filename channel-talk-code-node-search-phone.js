/**
 * 채널톡 코드 노드 - 전화번호로 고객 정보 검색
 *
 * 기능:
 * 1. 고객의 전화번호를 가져옴 (context.user.profile.mobileNumber)
 * 2. Google Sheets의 모든 시트에서 전화번호 검색 (G열, H열)
 * 3. 찾으면: C열 → action_date, F열 → product_list 메모리에 저장
 * 4. 못 찾으면: 두 변수를 빈 값으로 설정
 *
 * 사용 방법:
 * 1. 채널톡 플로우에서 "코드" 노드 추가
 * 2. 아래 코드의 handler 함수 내부 로직만 복사해서 붙여넣기
 * 3. YOUR_PROJECT_URL을 실제 Vercel 배포 URL로 변경
 */

export const handler = async (memory, context) => {
  const axios = require('axios');

  // ===== 설정 =====
  const API_URL = 'https://YOUR_PROJECT_URL.vercel.app/api/sheets-search-phone';
  const SHEET_ID = '1bADgRJlufpAoBGsDtyUWsHVAtmNe3ocYbcs9F3WnsCk';

  // ===== 1. 고객 전화번호 가져오기 =====
  const phoneNumber = context.user.profile?.mobileNumber;

  if (!phoneNumber) {
    console.log('⚠️ 전화번호가 없습니다');
    memory.put('action_date', '');
    memory.put('product_list', '');
    memory.save();
    return;
  }

  console.log(`📞 검색할 전화번호: ${phoneNumber}`);

  // ===== 2. API 호출하여 전화번호 검색 =====
  try {
    const response = await axios.post(
      API_URL,
      {
        sheet_id: SHEET_ID,
        phone_number: phoneNumber
      },
      {
        timeout: 30000  // 30초 타임아웃
      }
    );

    console.log('✅ API 응답 받음:', JSON.stringify(response.data));

    // ===== 3. 결과 처리 =====
    if (response.data.found) {
      // 전화번호를 찾은 경우
      const actionDate = response.data.action_date || '';
      const productList = response.data.product_list || '';

      memory.put('action_date', actionDate);
      memory.put('product_list', productList);

      console.log(`✅ 고객 정보 찾음!`);
      console.log(`   시트: ${response.data.sheet_name}`);
      console.log(`   행: ${response.data.row}`);
      console.log(`   일정(action_date): ${actionDate}`);
      console.log(`   접수내용(product_list): ${productList}`);

    } else {
      // 전화번호를 찾지 못한 경우
      memory.put('action_date', '');
      memory.put('product_list', '');

      console.log('❌ 고객 정보를 찾을 수 없습니다');
      console.log(`   검색한 번호: ${response.data.phone_normalized}`);
    }

    memory.save();

  } catch (error) {
    // ===== 4. 오류 처리 =====
    console.log('❌ API 호출 실패:', error.message);

    if (error.response) {
      // API에서 오류 응답을 받은 경우
      console.log('   상태 코드:', error.response.status);
      console.log('   오류 내용:', JSON.stringify(error.response.data));
    } else if (error.request) {
      // 요청은 보냈지만 응답을 받지 못한 경우
      console.log('   네트워크 오류 또는 타임아웃');
    } else {
      // 요청 설정 중 오류 발생
      console.log('   요청 설정 오류');
    }

    // 오류 발생 시 빈 값으로 설정
    memory.put('action_date', '');
    memory.put('product_list', '');
    memory.save();
  }
};
