# backend/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# NOTE: Avoid importing heavy RAG modules at startup. Use lazy, relative imports inside endpoints.

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
        # 지연 임포트 (backend 패키지 기준 상대 임포트)
        from .rag import rag_search
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
    # Pinecone 인덱스에서 file_name 메타데이터를 수집하여 정렬 반환
    # 지연 임포트 (backend 패키지 기준 상대 임포트)
    try:
        from .rag import list_all_file_names
        files = list_all_file_names(category="contract")
    except Exception:
        files = []
    if not files:
        # 폴백: 기존 로컬 data 디렉토리 스캔
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        try:
            files = [f for f in os.listdir(data_dir) if f.endswith(".pdf")]
        except Exception:
            files = []
        files.sort(key=lambda x: x.lower())
    return {"contracts": files}
