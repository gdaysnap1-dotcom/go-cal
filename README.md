# GO CAL

한국어 개인용 Pokémon GO 이벤트 캘린더. React + TypeScript + Vite, Tailwind CSS, FullCalendar, Python 표준 라이브러리 수집기와 정적 JSON을 사용합니다. 서버 DB가 없으며 즐겨찾기·관심 포켓몬·개인 점수는 기기의 localStorage에만 저장됩니다.

## 실행

Node 22 이상, pnpm 11, Python 3.12 이상을 권장합니다.

```sh
pnpm install --frozen-lockfile
python scripts/collect.py
pnpm dev
```

검증과 빌드:

```sh
python -m unittest discover -s scripts -v
pnpm test
pnpm build
pnpm preview
```

`public/data/events.json`에는 직접 수집·정규화한 실제 일정이 포함되어 있습니다. 앱 실행에 수집기를 먼저 돌릴 필요는 없습니다. 예제 일정은 넣지 않습니다. 아이콘은 빌드 시 Python 표준 라이브러리로 복원합니다. 추가 Python 패키지는 필요하지 않습니다.

## 구조

```text
src/main.tsx                 홈, 캘린더, 레이드, 즐겨찾기, 설정, 상세정보
src/model.ts                KST 변환, 상태·점수 판정, 저장소 검증
src/style.css               모바일 우선 다크 테마
scripts/collect.py          두 소스 정규화, 통합, 검증, 원자적 교체
scripts/test_collect.py     수집기 회귀 테스트
scripts/official-verifications.json  사람에 의해 확인된 공식 근거와 범위
public/data/events.json     마지막 정상 이벤트 스냅샷
public/data/status.json     가장 최근 수집 시도 결과
.github/workflows/          일일 갱신·보완 실행·배포, PR 검증
vite.config.ts             PWA, 경로, 캐시 정책
```

## 수집 정책

- 우선 소스: [Leak Duck](https://raw.githubusercontent.com/zhenga8533/leak-duck/data/events.json). 카테고리별 배열이며 현지 시각은 문자열, 절대 시각은 Unix 초로 제공됩니다. 원래 저장소 URL은 현재 `pokelitee/leak-duck`로 리다이렉트됩니다.
- 보조 소스: [ScrapedDuck](https://raw.githubusercontent.com/bigfoott/ScrapedDuck/data/events.json). 이벤트 배열, 오프셋 없는 현지 시각과 Z로 끝나는 절대 시각, null을 처리합니다.
- 두 소스 모두 Leek Duck을 기반으로 하므로 독립적인 공식 검증으로 간주하지 않습니다.
- 원문 URL을 정규화하여 ID를 만듭니다. 제목·시간이 변경되어도 같은 URL이면 즐겨찾기를 보존합니다. 원문 URL 자체가 변경되는 경우의 의미 기반 통합은 하지 않습니다.
- 주 소스가 우선입니다. 출처별 시각이 다르면 차이를 보존하고 상세정보에 표시합니다. 시작·종료 시각이 없거나 명시적으로 종료 미정인 경우 임의로 만들지 않습니다.
- 현지 시각은 한국 참여용 KST로 변환합니다. 해외 현장 한정 일정은 기본 숨김입니다. 개최 시간대가 없는 해외 현지 시각은 KST로 변환하지 않습니다.
- 소스의 원본 시각, 시간대 종류, 출처, 지역, 보너스, 포켓몬, 이미지, 색이 다른 가능 여부를 보존합니다. 색이 다른 가능 여부의 null은 미확인입니다.
- 수집 목록에서 사라진 미래 일정은 취소로 단정하지 않고 미확인으로 유지합니다. 정상 종료 시각이 지난 일정만 종료로 분류합니다.
- 첫 발견·마지막 내용 변경·마지막 관측을 분리합니다. 첫 발견은 공식 발표일이 아닙니다.
- 소스마다 재시도 3회와 타임아웃을 적용합니다. 소스 하나가 실패하면 정상 소스로 갱신하되 상태는 degraded입니다. 두 소스가 실패하거나 일정이 비정상적으로 급감하면 이전 events.json을 유지하고 status.json에 실패를 기록합니다.
- JSON 구조 검증을 통과한 임시 파일만 교체합니다. 스크립트가 시작조차 못 하는 인프라 장애는 status.json에 기록할 수 없으므로 앱은 36시간 경과 경고도 표시합니다.
- 공식 검증은 명시된 항목만 적용합니다. 현재 확인 기록은 2026-10-24 맥스배틀 데이의 시작·종료·지역·신규 등장입니다. 자동 수집만으로 공식 검증을 부여하지 않습니다. 나머지는 비공식 정보로 표시합니다.
- 공식 기록과 최신 소스 시각이 다르면 경고합니다. 번역 누락은 원문을 보존합니다. 현재 수집된 설명 60개와 고유 보너스 문구 94개는 한국어 번역을 제공합니다. 영문 원문은 상세창에서 별도로 펼쳐 볼 수 있습니다. 원문이 바뀌면 같은 ID라도 이전 번역을 재사용하지 않습니다. 신규·변경 문구는 MyMemory 자동 번역을 시도하며, 한도·연결 오류 시 한국어 준비 안내와 원문 보기 기능을 제공합니다. 자동 번역에는 자동 번역 표시를 붙이며 공식 검증으로 간주하지 않습니다.

## 중요도

개인 추천 점수이며 객관적인 성능·희귀도 수치가 아닙니다. 공식 확인된 신규 등장은 5점, 주요 레이드·커뮤니티 데이는 기본 4점, 일반 일정 3점, 반복 아워·맥스 먼데이는 2점입니다. 그 외 유형별 점수를 1–5로 설정할 수 있습니다. 개별 이벤트의 희귀도나 게임 내 가치를 추측해서 수치화하지 않습니다.

## PWA·캐시

Manifest, 192/512 아이콘, Apple 터치 아이콘, 서비스 워커를 포함합니다. 앱 파일만 precache하고 `data/*.json`은 NetworkOnly와 `cache: no-store`로 다시 요청합니다. 검증에 성공한 데이터만 localStorage에 저장합니다. 연결 실패 시 마지막 정상 데이터를 표시하고 경고합니다. 진입·온라인 복귀·앱 전경 복귀·수동 새로고침 때 최신 배포 데이터를 요청합니다. 수동 새로고침은 GitHub 수집 실행 버튼이 아닙니다.

아이폰은 Safari의 공유 → 홈 화면에 추가로 설치합니다. 갤럭시는 Chrome에서 ⋮ → 설치 및 바로가기 만들기 → 설치를 선택합니다. 버전에 따라 홈 화면에 추가 → 설치로 표시됩니다. 실제 iOS 설치·오프라인 재실행은 HTTPS 배포 후 아이폰에서 확인해야 합니다. 원격 포켓몬 이미지는 오프라인 보장을 하지 않습니다.

## GitHub Pages 배포

공개 저장소: https://github.com/gdaysnap1-dotcom/go-cal · 실제 배포·수집 결과는 저장소의 Actions 탭에서 확인합니다.

1. `gdaysnap1-dotcom/go-cal` 공개 저장소를 생성합니다. 이 폴더가 저장소 루트가 되도록 업로드합니다.
2. Settings → Pages → Build and deployment → Source를 GitHub Actions로 설정합니다.
3. `main` 브랜치에 업로드하면 검증·수집·빌드·Pages 배포가 실행됩니다.
4. Actions → Update events and deploy → Run workflow로 수동 실행할 수 있습니다.
5. 성공한 deploy-pages 출력의 URL과 실제 HTTP 응답을 확인해야 배포 완료입니다. 예상 주소를 실제 배포 주소처럼 보고하지 않습니다.

06:00 KST는 UTC 기준 전날 21:00(`0 21 * * *`)입니다. 09:17 KST(`17 0 * * *`)에 보완 실행합니다. GitHub의 예약 실행은 지연·누락되거나 비활성화될 수 있으므로 정확한 시각 실행을 보장하지 않습니다. 실패 시 이전 정상 데이터와 실패 상태를 배포하고 마지막 단계에서 작업을 실패 처리합니다. GitHub Actions 알림을 활성화하면 실패를 확인할 수 있습니다. 워크플로가 소스를 커밋할 수 있도록 저장소의 Actions 정책이 쓰기를 허용해야 합니다.

프로젝트 경로는 `BASE_PATH=/<repository-name>/`로 빌드합니다. 기본 로컬 빌드는 상대 경로입니다. 루트 사용자 Pages 저장소로 배포한다면 BASE_PATH를 `/`로 바꾸세요.

## 라이선스·권리

[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)를 확인하세요. 이 앱은 Pokémon GO, Niantic, Scopely, Nintendo, Creatures, GAME FREAK, Leek Duck의 공식 앱이 아닙니다. 데이터와 이미지를 소스 코드 라이선스가 허용하는 자산으로 간주하지 않습니다. 광고·유료화 없이 개인용으로 사용합니다.

## 한국어 번역과 모바일 상세창

`scripts/korean.json`은 원문의 SHA-256으로 설명 번역을 연결하고 보너스 원문별 한국어 문구를 저장합니다. `scripts/localize.py`는 새 문구의 자동 번역과 공개 데이터 캐시를 관리합니다. CI의 `GO_CAL_TRANSLATE=1`에서만 외부 번역을 시도합니다. MyMemory의 무료 익명 한도는 일 5,000자이며 앱은 캐시 파일에 일별 사용량을 기록하고 4,500자까지만 요청합니다. 테스트는 네트워크 없이 실행합니다. 번역 오류나 한도 초과는 이벤트 수집 파일을 훼손하지 않습니다.

상세창은 모바일에서 하단 시트로 열립니다. 상단에 안전 여백을 두고 닫기 버튼을 48px 이상으로 유지하며, 본문만 안쪽에서 스크롤됩니다. 하단에도 닫기 버튼을 제공합니다.

안내: [MyMemory 사용 한도](https://mymemory.translated.net/doc/usagelimits.php), [Android Chrome 웹 앱 설치](https://support.google.com/chrome/answer/9658361?hl=ko&co=GENIE.Platform%3DAndroid).
