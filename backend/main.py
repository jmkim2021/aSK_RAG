# backend/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# rag 모듈은 Pinecone/OpenAI 초기화를 포함하므로 엔드포인트 내부에서 지연 임포트한다.

app = FastAPI()

# CORS 설정: 모든 도메인 허용 (개발/프론트 연동 편의)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# 환경변수 불러오기 (.env) - 루트 기준
from pathlib import Path
ROOT_DOTENV = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=str(ROOT_DOTENV))

# 검색 API용 요청 데이터 모델
class SearchRequest(BaseModel):
    query: str
    file_name: str | None = None
    category: str | None = None
    answer_lang: str = "ko"


# 검색 API (POST)
@app.post("/api/search")
def search_endpoint(req: SearchRequest):
    try:
        # 지연 임포트
        from rag import rag_search
        result = rag_search(
            query=req.query,
            file_name=req.file_name,
            category=req.category,
            answer_lang=req.answer_lang,
            top_k=5,
        )
        return result
    except Exception as e:
        # 간단한 오류 메시지를 반환해 프론트에서 원인 확인 가능하도록 함
        return {"error": str(e), "query": req.query, "file": req.file_name, "category": req.category}
# main.py

@app.get("/api/contracts")
def list_contracts():
    """계약서 파일명 목록을 반환한다.

    의존성 최소화 및 초보 사용자 환경을 위해 기본적으로 로컬 `backend/data` 디렉터리를 스캔한다.
    (다른 사용자가 .env/Pinecone를 설정하지 않아도 동작)
    """
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    try:
        files = [f for f in os.listdir(data_dir) if f.lower().endswith(".pdf")]
    except Exception:
        files = []
    files.sort(key=lambda x: x.lower())
    return {"contracts": files}
