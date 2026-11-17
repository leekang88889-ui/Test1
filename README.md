# 🛒 쇼핑 리스트

장 볼 물건을 추가·수정·삭제하고 체크할 수 있는 간단한 웹 앱입니다. Python과 Streamlit으로 만들었습니다.
요구사항은 [PRD.md](PRD.md)를 참고하세요.

## 기능
- 아이템 추가 (입력 후 Enter 또는 "추가" 버튼)
- 구매 완료 체크 (취소선 표시, `N / M 완료` 진행 현황)
- 이름 수정 (✏️ → 저장 ✔ / 취소 ✖)
- 삭제 (🗑️), 체크된 항목 모두 삭제
- 새로고침해도 목록 유지 (`items.json`에 저장)
- 모바일 화면 지원, 라이트/다크 테마 대응

## 실행 방법
Python 3.10 이상이 필요합니다.

```bash
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 http://localhost:8501 로 접속합니다.
같은 네트워크의 다른 기기에서 접속되지 않게 하려면 `streamlit run app.py --server.address localhost`로 실행하세요.

## 파일 구성
| 파일 | 설명 |
|---|---|
| `app.py` | 앱 전체 (저장소, 로직, 화면) |
| `requirements.txt` | 의존성 (`streamlit>=1.50,<2`) |
| `items.json` | 데이터 파일. 첫 저장 때 자동 생성되며 git에는 올라가지 않음 |
| `PRD.md` | 제품 요구사항 문서 |
| `PROMPTS.md` | 단계별 개발 프롬프트 |

## 데이터 저장 방식과 한계
- 목록은 서버의 `items.json` 한 파일에 저장되고, **접속한 모든 사람이 같은 목록을 공유**합니다.
- 변경할 때마다 파일의 최신 내용을 읽어서 반영하므로, 여러 탭·여러 사람이 동시에 써도 서로의 변경이 덮어써지지 않습니다. 다른 사람이 바꾼 내용은 내 화면에서 다음 동작(또는 새로고침) 때 보입니다.
- Streamlit Community Cloud는 앱이 재시작되거나 다시 배포되면 서버 파일이 초기화될 수 있습니다. 즉 **배포 환경에서는 데이터가 사라질 수 있습니다.** 개인용·데모용으로 쓰거나, 오래 보관해야 한다면 Google Sheets, Supabase 같은 외부 저장소로 바꾸세요.
- 저장소 접근은 `app.py`의 `load_items()` / `save_items()` 두 함수에 모여 있어 교체하기 쉽게 되어 있습니다.

## 배포 (Streamlit Community Cloud)
1. 이 폴더를 GitHub 저장소로 올립니다. (`items.json`은 `.gitignore`에 포함되어 있어 올라가지 않습니다.)
2. [share.streamlit.io](https://share.streamlit.io)에 GitHub 계정으로 로그인합니다.
3. **New app**에서 저장소, 브랜치, 메인 파일(`app.py`)을 선택하고 Deploy를 누릅니다.
4. 발급된 `https://<앱이름>.streamlit.app` 주소로 접속해 확인합니다.
