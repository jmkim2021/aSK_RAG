import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
try:
    from pinecone import Pinecone  # new SDK
except Exception:
    Pinecone = None  # optional, fall back to sampling
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

def load_system_prompt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# 환경변수 불러오기 (프로젝트 루트와 backend 폴더 모두 시도)
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY_KIM")
PINECONE_INDEX = os.getenv("PINECONE_INDEX_KIM")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_NAMESPACE = ""

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["PINECONE_ENVIRONMENT"] = PINECONE_ENV

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    openai_api_key=OPENAI_API_KEY
)
vectorstore = PineconeVectorStore.from_existing_index(
    index_name=PINECONE_INDEX,
    embedding=embeddings,
    namespace=PINECONE_NAMESPACE,
)

# system_prompt.txt 절대경로
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
system_prompt_path = os.path.join(DATA_DIR, "system_prompt.txt")
system_prompt = load_system_prompt(system_prompt_path)
prompt_template = (
    "{system_prompt}\n\n"
    "Question: {question}\n"
    "Context (chunks/clauses):\n{context}\n\n"
    "Output language: {answer_lang}. Write the entire answer in this language only.\n"
    "Important context rule: Items are tagged as [CONTRACT] (selected agreement) and [LAW] (latest legislation).\n"
    "Treat all [LAW] items as up-to-date and authoritative legal references.\n"
    "If the question concerns law or when [LAW] appears in context, explicitly compare the contract clauses against the latest legislation: identify alignment, discrepancies, and whether any contract provision is overridden by mandatory law.\n"
    "Where the contract text cites outdated statutes, treat [LAW] as controlling for the legal requirement; still ground obligations and remedies primarily in [CONTRACT].\n"
    "Summarize the comparison outcome in the first paragraph. In the evidence list, pair citations from both sources where relevant.\n\n"
    "Citation style (STRICT): Use only the file name and pages inside parentheses, no tags.\n"
    "Format exactly as: (DocumentName, p.X[, p.Y ...]) — e.g., (contract3.pdf, p.7), (law1.pdf, p.18, p.28).\n"
    "Use the exact file name as DocumentName. Prefix each page with 'p.'. Place a single space after each comma.\n"
    "Do not include any tags or extra markers in citations (no [CONTRACT], [LAW], brackets, or dashes). Use only (DocumentName, p.…).\n\n"
    "Respond in exactly three distinct paragraphs, in this order:\n"
    "- First, provide a concise summary answer.\n"
    "- Next, present all supporting clause/page/quotation evidence (one per line, as a list, direct from the context).\n"
    "- Finally, offer concrete practical advice or analysis for the user's position, based only on the quoted clauses.\n"
    "If the user's question contains the exact Korean word '도식화', then AFTER the above three paragraphs, append one additional section at the very end with the exact header line below (do NOT translate this header):\n"
    "【도식화 구조 제안】\n"
    "In that section, do NOT draw a full diagram. Instead, provide a detailed plan for how to visualize it: (1) Node list with labels and 1-line descriptions; (2) Edge list describing directions and conditions; (3) Recommended layout (top-down/left-right) and ordering; (4) Grouping/clusters and boundaries; (5) Legend/notations to use; and (6) Optional short ASCII sketch up to 6 lines.\n"
    "For the optional ASCII sketch: use ONLY plain ASCII characters '-', '>', '(', ')', '[', ']', ':' and spaces; format each line as either 'A -> B' or '- Node: short note'; do NOT attempt alignment, boxes, or grids; do NOT use code fences or Markdown; keep labels in {answer_lang}.\n"
    "\nTerminology policy (STRICT): For the following industry terms, do NOT translate the term itself.\n"
    "Always write the original term exactly as in the source (case preserved). On the first occurrence, immediately add a translation or clarifying note in parentheses in the user's requested output language ({answer_lang}); on later occurrences, the parentheses are optional. Never use any other language in parentheses.\n"
    "Terms: Operator; Non-Operator; Participating Interest; Joint Operating Agreement; Production Sharing Agreement; Cost Oil; Cost Gas; Profit Oil; Profit Gas; Exclusive Operation; Work Program and Budget; AFE; Carried Interest; Relinquishment; Surrender; Defaulting Party; Force Majeure; Assignment; Withdrawal; Entitlement; Lifting; Take or Pay; Make Up Gas; Joint Account; Gross Negligence/Willful Misconduct; Abandonment; Development Plan; Appraisal Well; Exploration Well; Royalty; Additional Profits Tax (APT); Joint Operating Committee (JOC).\n"
    "Example format (use these exact visual headers, not Markdown):\n"
    "【답변 요약】\n(Your summary here)\n\n"
    "【근거】\n(Clause numbers/pages/quotes with citations)\n\n"
    "【실무적 조언】\n(Your advice here)\n"
    "Insert one blank line after each header.\n"
    "Do not add section numbers or extra labels ('1.', '2.', etc). Use only the three specified headers and line breaks to separate each part, EXCEPT when the question contains '도식화'—in that case, add the single extra section at the very end for the schematic structure proposal."
)
prompt = PromptTemplate.from_template(prompt_template)
llm = ChatOpenAI(model="gpt-4.1", openai_api_key=OPENAI_API_KEY, temperature=0)

# 법령 키워드 감지
LAW_KEYWORDS = [
    "법", "법령", "law", "legislation"
]

def _contains_law_keyword(text: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    if any(k in text for k in ["법", "법령"]):
        return True
    return any(k in lowered for k in ["law", "legislation"]) 

def rag_search(query, file_name=None, category=None, answer_lang="ko", top_k=5):
    # 1) 계약서 검색: 선택한 계약서는 항상 포함
    contract_docs: list = []
    if file_name:
        contract_docs = vectorstore.similarity_search(
            query, k=top_k, filter={"file_name": file_name}
        )
    else:
        # 파일이 지정되지 않으면 우선 필터 없이 전체에서 검색
        all_docs = vectorstore.similarity_search(
            query, k=top_k, filter=None
        )
        # 계약서 추정 규칙: category=='contract' 이거나 파일명이 contract로 시작
        contract_docs = [
            d for d in all_docs
            if (d.metadata.get("category") == "contract")
            or str(d.metadata.get("file_name", "")).lower().startswith("contract")
        ]
        # 계약서로 추정되는 문서가 없으면 전체 결과라도 반환
        if not contract_docs:
            contract_docs = all_docs

    # 2) 법령 키워드가 있고 특정 계약서가 선택된 경우에만 law 카테고리를 비교용으로 추가
    add_law = bool(file_name) and (_contains_law_keyword(query) or (category == "law"))
    law_docs: list = []
    if add_law:
        law_docs = vectorstore.similarity_search(
            query, k=top_k, filter={"category": "law"}
        )

    # 3) 컨텍스트 병합: 계약서 우선, 다음 법령
    docs = contract_docs + law_docs
    def _line_for(doc):
        src_cat = doc.metadata.get("category")
        src_file = doc.metadata.get("file_name")
        raw_page = doc.metadata.get("page_num")
        try:
            page_num = int(raw_page) if raw_page is not None else 0
        except Exception:
            page_num = 0
        src_tag = "CONTRACT" if (src_cat == "contract" or (file_name and src_file == file_name)) else ("LAW" if src_cat == "law" else (src_cat or "SRC"))
        return f"- [{src_tag}] [{src_file or '알수없음'} p.{page_num}] {doc.page_content}"

    context = "\n".join([_line_for(doc) for doc in docs])
    prompt_txt = prompt.format(
        system_prompt=system_prompt,
        question=query,
        context=context,
        answer_lang=answer_lang,
    )

    # 🔥 요청된 언어로 직접 생성 (용어/괄호 언어 일관성 보장)
    answer = llm.invoke(prompt_txt).content.strip()

    # 청크 미리보기 리스트
    chunk_previews = []
    for i, chunk in enumerate(docs, 1):
        file_ = chunk.metadata.get("file_name", "알수없음")
        raw_page = chunk.metadata.get("page_num")
        try:
            page_ = int(raw_page) if raw_page is not None else 0
        except Exception:
            page_ = 0
        cat_ = chunk.metadata.get("category", "미지정")
        text = chunk.page_content.replace("\n", " ")
        preview = text[:180]
        src_tag = "CONTRACT" if (cat_ == "contract" or (file_name and file_ == file_name)) else ("LAW" if cat_ == "law" else (cat_ or "SRC"))
        chunk_previews.append(
            f"{i}. [{src_tag}] [{file_} / p.{page_}] {preview}{'...' if len(text) > 180 else ''}"
        )
    return {
        "question": query,
        "answer": answer,
        "file": file_name or "전체 계약서",
        "category": ("law" if add_law else (category or "전체")),
        "preview_chunks": chunk_previews,
    }


# 신뢰성(Confidence) 관련 로직은 사용되지 않아 제거되었습니다.


def list_index_file_names(category: str | None = None, top_k: int = 1000) -> list[str]:
    """Pinecone 벡터 인덱스에서 메타데이터의 file_name 값을 수집해 정렬된 유니크 리스트로 반환한다.

    전략: 중립 쿼리로 상위 k개를 조회해 file_name을 수집한다. 인덱스 규모가 작을 때 실용적이다.
    필요 시 k를 조정해 커버리지를 늘릴 수 있다.
    """
    filter_dict = {"category": category} if category else None
    try:
        docs = vectorstore.similarity_search(" ", k=top_k, filter=filter_dict)
    except Exception:
        # 임베딩/모델 오류 시 빈 리스트 반환
        return []
    names = []
    seen = set()
    for doc in docs:
        name = (doc.metadata or {}).get("file_name")
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    names.sort(key=lambda x: x.lower())
    return names


def list_all_file_names(category: str | None = None) -> list[str]:
    """Pinecone의 list API를 이용해 모든 벡터를 페이지네이션으로 순회하며 file_name을 수집한다.
    가능한 경우 이 경로를 사용하고, 실패 시 list_index_file_names로 폴백한다.
    """
    if Pinecone is None or not PINECONE_API_KEY or not PINECONE_INDEX:
        return list_index_file_names(category=category, top_k=2000)

    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX)
        file_names: set[str] = set()
        token = None
        while True:
            # 다양한 SDK 버전을 호환하기 위해 kwargs를 유연하게 전달
            kwargs = {"limit": 1000, "include_values": False, "include_metadata": True}
            if PINECONE_NAMESPACE:
                kwargs["namespace"] = PINECONE_NAMESPACE
            if token:
                kwargs["pagination_token"] = token
            resp = index.list(**kwargs)

            # resp가 dict 또는 객체일 수 있음
            vectors = None
            if isinstance(resp, dict):
                vectors = resp.get("vectors") or resp.get("data")
                token = (resp.get("pagination") or {}).get("next") or resp.get("pagination_token")
            else:
                vectors = getattr(resp, "vectors", None) or getattr(resp, "data", None) or resp
                token = getattr(resp, "pagination_token", None) or getattr(resp, "next", None)

            if not vectors:
                break
            for v in vectors:
                md = getattr(v, "metadata", None)
                if md is None and isinstance(v, dict):
                    md = v.get("metadata")
                name = (md or {}).get("file_name")
                if name:
                    file_names.add(name)
            if not token:
                break
        names = sorted(file_names, key=lambda x: x.lower())
        # 필터 요청 시 적용
        if category:
            # list API 호출에서 메타 필터를 못 걸 경우를 대비한 후처리(추정)
            names = [n for n in names if n]
        return names
    except Exception:
        # 어떤 이유로든 실패하면 샘플링 폴백
        return list_index_file_names(category=category, top_k=5000)
