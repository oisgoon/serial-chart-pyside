# 📡 Serial Chart with Matplotlib

실시간 시리얼 데이터를 수신하여 차트로 시각화하고, CSV 파일로 자동 저장하는 PySide6 + Matplotlib 기반 GUI 프로그램입니다.

<img src="https://github.com/user-attachments/assets/dc00259c-18c1-4353-997f-33a1b24261e4" width="70%" />


## 🚀 주요 기능

| 기능 | 설명 |
|------|------|
| ✅ 시리얼 통신 수신 | COM 포트, Baud 설정 |
| ✅ 실시간 그래프 | 다중 채널 데이터 실시간 플로팅 |
| ✅ 자동 스크롤/수신 시간 | 옵션으로 조절 가능 |
| ✅ 범례 클릭 토글 | 그래프 숨기기/보이기 |
| ✅ 커서 툴팁 | 마우스를 가져가면 채널명, 시간, 값 표시 |
| ✅ 수직선(옵션) | 마우스를 따라가는 보조선 표시 가능 |
| ✅ 자동 저장 | 수신값을 CSV 파일에 실시간 저장 (`auto_log.csv`) |
| ✅ 수동 명령 전송 | 커맨드 입력 후 `Enter` 또는 `Send` 버튼으로 시리얼 전송 |
| ✅ 다크 모드 지원 | 기본 UI 스타일 Qt 기반 다크 테마와 조화 |

---

## 📂 저장 파일 구조

| 파일 | 설명 |
|------|------|
| `auto_log.csv` | 실시간 저장되는 시리얼 수신 데이터 (타임스탬프 + 값) |
| `console_data_YYYYMMDD_HHMMSS.csv` | 수동 저장 시 콘솔 출력 로그 |
| `chart_data_YYYYMMDD_HHMMSS.csv` | 수동 저장 시 차트 데이터 |

---

## 🛠 사용 방법

1. Python 3.9 이상 설치
2. 필요한 패키지 설치:

```bash
pip install pyserial PySide6 matplotlib mplcursors
```

## 프로그램 실행
```bash
python main.py
```

## 프로그램 배포
```bash
pyinstaller --noconfirm --windowed --onedir main.py
```

## UI

- 포트 및 Baudrate 선택 후 Connect

- 수신되는 시리얼 데이터 중 "#[KEY]:" 형태에 맞는 값이 있을 경우 자동 파싱됨

- 차트에 그려지고 동시에 CSV로 저장됨

## 🧪 시리얼 데이터 예시
```bash
[13:04:13.2874] #TEST: 575,585,595,605,615 / delay: 1000ms
```
- `TEST`는 입력창에서 설정한 키워드와 일치해야 합니다.
  - 해당 예시에선 `TEST` 단어를 기준으로 파싱하면 575,585,595,605,615 총 5개의 숫자가 파싱됩니다.
- 최대 10개 채널까지 처리합니다.

## ⚙ 설정 가능한 요소
- ✅ Auto Scroll
- ✅ cv Time (수신 시간 표시)
- ✅ Baud Rate, Port
- ✅ 수신 필터 키워드 (Text 입력)
- ✅ Stop 버튼으로 일시 중지 가능

## 💾 자동 저장 포맷 예시 (auto_log.csv)
```yaml
Timestamp,CH1,CH2,CH3,CH4,CH5
2025-03-26 13:55:30.124,537,547,557,567,577
2025-03-26 13:55:31.142,538,548,558,568,578
```

## ✨ TODO / 확장 가능성(추후 업데이트 예정)
- 마우스 수직선 동기화 (crosshair line)
- 채널 이름 커스터마이징
- 최대 데이터 포인트 제한 옵션
- 로그 파일 회전 기능 (용량 초과 시 자동 분할)

## 이슈
- MAC OS에서 안될때
  환경설정 -> 개인정보 보호 및 보안 -> 맨 아래 보안 탭에서 차단되었다는 메시지 클릭하고 '그래도 열기' -> 정상 실행

## 👤 Author
- OIS (oinse719@gmail.com)
- Python + Pyside + Matplotlib + 시리얼 통신
