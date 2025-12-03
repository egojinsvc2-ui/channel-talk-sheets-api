/**
 * 채널톡 코드 노드 - 전화번호로 고객 정보 검색
 *
 * 열 구조:
 * A-접수날짜, B-요청날짜, C-처리날짜, D-기사명, E-고객명
 * F-상품명/증상, G-접수내용, H-휴대폰번호, I-전화번호
 *
 * 기능:
 * 1. 고객의 전화번호를 가져옴 (context.user.profile.mobileNumber)
 * 2. Google Sheets의 모든 시트에서 전화번호 검색 (H열, I열)
 * 3. 찾으면: F열 → product_info 메모리에 저장
 * 4. 못 찾으면: 빈 값으로 설정
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

  // ===== 1. 고객 전화번호 가져오기 =====
  const phoneNumber = context.user.profile?.mobileNumber;

  if (!phoneNumber) {
    console.log('[경고] 전화번호가 없습니다');
    memory.put('product_info', '');
    memory.save();
    return;
  }

  console.log(`[검색] 전화번호: ${phoneNumber}`);

  // ===== 2. API 호출하여 전화번호 검색 =====
  try {
    const response = await axios.post(
      API_URL,
      {
        phone_number: phoneNumber
      },
      {
        timeout: 30000  // 30초 타임아웃
      }
    );

    console.log('[성공] API 응답:', JSON.stringify(response.data));

    // ===== 3. 결과 처리 =====
    if (response.data.found) {
      // 전화번호를 찾은 경우
      const productInfo = response.data.product_info || '';

      memory.put('product_info', productInfo);

      console.log('[성공] 고객 정보 찾음!');
      console.log(`   시트: ${response.data.sheet_name}`);
      console.log(`   행: ${response.data.row}`);
      console.log(`   상품정보: ${productInfo}`);

    } else {
      // 전화번호를 찾지 못한 경우
      memory.put('product_info', '');

      console.log('[실패] 고객 정보를 찾을 수 없습니다');
      console.log(`   검색한 번호: ${response.data.phone_normalized}`);
    }

    memory.save();

  } catch (error) {
    // ===== 4. 오류 처리 =====
    console.log('[오류] API 호출 실패:', error.message);

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
    memory.put('product_info', '');
    memory.save();
  }
};
