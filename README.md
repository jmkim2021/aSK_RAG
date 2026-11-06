# 글로벌 계약 정보 검색 시스템

**영문 계약서에서 질문과 관련된 조항을 찾아 근거와 함께 답변하는 RAG 웹 서비스입니다.** SK 써니C ‘AI로 일하는 방식 혁신’ 프로젝트에서 백엔드 검색·답변 흐름을 담당했고, 팀 프로젝트는 우수상을 받았습니다.

## 왜 만들었나

해외 지사와 고객사가 사용하는 계약서는 분량이 길고 영문 조항을 직접 찾아 비교하는 데 시간이 많이 들었습니다. 기존 사내 검색과 일반 챗봇만으로는 어느 문서의 몇 쪽을 근거로 답했는지 확인하기 어려웠습니다. 계약서 검색 결과를 답변의 문맥으로 전달하고, 파일명과 페이지를 함께 보여주는 방식으로 이 문제를 다뤘습니다.

## 담당한 작업

- 영문 계약서를 청크로 나누고 `text-embedding-3-large`로 임베딩해 Pinecone에 적재하는 전처리 과정을 구성했습니다.
- 질문을 임베딩해 유사도가 높은 청크를 검색하고, 선택한 계약서와 관련 법령 문맥을 구분해 GPT-4.1에 전달하는 백엔드를 구현했습니다.
- 법률 담당자가 근거를 검토하기 쉽도록 답변 형식과 파일명·페이지 인용 규칙을 프롬프트에 반영했습니다.
- 프론트엔드 팀원과 검색 화면의 요청·응답 형식을 맞추고, 백엔드는 Render, 화면은 GitHub Pages로 배포했습니다.
- 별도로 Ground Truth와 검색 결과의 순서를 비교하는 NDCG@k 평가 코드를 작성해 검색 품질을 점검했습니다.

프로젝트에서 측정한 업무 시간은 기존 방식 대비 **95.2% 단축**됐습니다. 측정 데이터와 평가 스크립트는 현재 공개 저장소에 포함되어 있지 않습니다.

## 이 저장소에서 볼 수 있는 코드

```text
backend/main.py                 FastAPI 검색·계약서 목록 API
backend/rag.py                  Pinecone 검색, 문맥 구성, 답변 생성
backend/data/system_prompt.txt  답변 역할·형식 지침
frontend/src/                  검색 화면
```

공개 코드는 이미 구축된 Pinecone 인덱스를 조회하는 서비스 부분입니다. 계약서 전처리와 NDCG@k 평가 과정은 위의 프로젝트 기여 내용에 해당하지만, 실행 스크립트는 이 저장소에 없습니다. 계약서 원문이나 법령의 최신성을 이 코드만으로 보장하지 않으므로 답변은 원문과 함께 확인해야 합니다.

## 실행 조건과 설치

Python과 Node.js가 필요합니다. 이미 계약서가 적재된 Pinecone 인덱스와 OpenAI·Pinecone 자격증명도 필요합니다. 프로젝트 루트에 `.env`를 만들고 아래 변수에 본인의 값을 넣습니다. 실제 키는 저장소에 올리지 않습니다.

```dotenv
OPENAI_API_KEY=<본인 키>
PINECONE_API_KEY_KIM=<본인 키>
PINECONE_INDEX_KIM=<기존 인덱스 이름>
PINECONE_ENVIRONMENT=<인덱스 환경>
```

첫 번째 터미널에서 백엔드를 실행합니다.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

두 번째 터미널에서 화면을 실행합니다.

```bash
cd frontend
npm ci
npm start
```

## 사용 예시

화면에서 계약서를 선택해 질문하거나, API에 직접 질문을 보낼 수 있습니다.

```bash
curl -X POST http://localhost:8000/api/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"계약의 해지 조건은 무엇인가요?","answer_lang":"ko"}'
```

응답에는 답변과 검색된 청크의 미리보기가 들어 있습니다. [배포된 화면](https://jmkim2021.github.io/aSK_RAG/)에서도 검색 흐름을 볼 수 있습니다.

## 실행 중 문제가 생기면

- 검색 API에서 키나 인덱스 오류가 반환되면 `.env`의 네 변수와 Pinecone에 적재된 인덱스 이름을 확인합니다. 이 저장소에는 인덱스를 새로 만드는 스크립트가 없습니다.
- 검색 결과가 없거나 인용 페이지가 예상과 다르면 원문 PDF와 인덱스 메타데이터를 함께 확인합니다.

문의: jmkim020315@gmail.com
