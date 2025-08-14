import os
import re
from datetime import datetime

try:
    from openpyxl import Workbook
    OPENPYXL_AVAILABLE = True
except Exception:
    OPENPYXL_AVAILABLE = False

from rag import vectorstore, list_all_file_names


QUESTIONS = [
    "계약 해지 조건",
    "Force Majeure 규정",
    "Operator 지정/해임",
    "Participating Interest 산정/변경",
    "Default 및 Remedies",
    "Withdrawal/Surrender",
    "Assignment/양도 승인",
    "분쟁해결(중재)",
    "회계 및 감사(Audit)",
    "Cost Recovery/Profit Oil 배분",
    "Royalty 및 세금",
    "Joint Operating Committee",
    "Carried Interest",
    "정부 참여",
    "Confidentiality",
    "환경/안전(HSE)",
    "Abandonment 비용 분담",
    "Work Program & Budget",
    "Take or Pay/Make Up Gas",
    "Lifting/Nomination",
    "Insurance",
    "회계처리 기준",
    "산출물 가격평가(Valuation)",
    "현지화/로컬콘텐츠",
    "Assignment 시 ROFR",
    "계약 종료 후 잔여의무",
    "중재장소(Venue)",
    "계약변경(Amendment)",
    "Joint Account 관리",
    "현지채용/훈련",
]



def _keywords_for_query(q: str) -> list[str]:
    ql = (q or "").lower()
    if "해지" in ql or "termination" in ql:
        return ["해지", "종료", "termination", "terminate", "suspension", "withdrawal"]
    if "force majeure" in ql or "불가항력" in ql:
        return ["force majeure", "불가항력", "act of god", "beyond reasonable control"]
    if "operator" in ql or "지정" in ql or "해임" in ql:
        return ["operator", "appointment", "removal", "operatorship", "designation"]
    if "participating interest" in ql or "산정" in ql or "변경" in ql or "지분" in ql:
        return ["participating interest", "working interest", "equity interest", "allocation", "re-determination", "지분"]
    if "default" in ql or "remedies" in ql or "remedy" in ql:
        return ["default", "event of default", "breach", "cure period", "remedies", "remedy"]
    if "withdrawal" in ql or "surrender" in ql:
        return ["withdrawal", "surrender", "relinquishment"]
    if "assignment" in ql or "양도" in ql or "승인" in ql:
        return ["assignment", "assign", "transfer", "consent", "approval"]
    if "중재" in ql or "분쟁" in ql or "arbitration" in ql or "dispute" in ql:
        return ["arbitration", "dispute", "dispute resolution", "governing law", "seat of arbitration"]
    if "audit" in ql or "감사" in ql or "회계" in ql:
        return ["audit", "audit rights", "books and records", "inspection", "accounting"]
    if "cost recovery" in ql or "profit oil" in ql or "배분" in ql:
        return ["cost recovery", "profit oil", "cost oil", "recoverable cost", "allocation"]
    if "royalty" in ql or "세금" in ql or "tax" in ql:
        return ["royalty", "royalties", "tax", "withholding tax", "income tax", "petroleum tax", "vat", "royalty rate", "fiscal terms"]
    if "joint operating committee" in ql or "joc" in ql or "operating committee" in ql or "management committee" in ql:
        return ["joint operating committee", "operating committee", "management committee", "committee", "quorum", "voting", "decision"]
    if "carried interest" in ql or "carried" in ql:
        return ["carried interest", "carry", "free carry", "carried costs", "carrying party"]
    if "정부 참여" in ql or "state participation" in ql or "government participation" in ql or "back-in" in ql:
        return ["state participation", "government participation", "noc", "national oil company", "back-in right", "state back-in"]
    if "confidentiality" in ql or "비밀" in ql or "비밀유지" in ql or "nda" in ql:
        return ["confidentiality", "confidential information", "non-disclosure", "nda", "use restriction"]
    if "hse" in ql or "환경" in ql or "안전" in ql or "보건" in ql:
        return ["hse", "health", "safety", "environment", "environmental", "pollution", "spill", "hazard", "환경", "안전"]
    if "abandonment" in ql or "decommission" in ql or "비용 분담" in ql:
        return ["abandonment", "decommissioning", "site restoration", "plug and abandon", "p&a", "abandonment fund", "decommissioning fund", "cost sharing", "apportionment"]
    if "work program" in ql or "budget" in ql or "wp&b" in ql:
        return ["work program", "program and budget", "wp&b", "annual work plan", "budget approval", "afe", "authorization for expenditure"]
    if "take or pay" in ql or "make up gas" in ql or "make-up gas" in ql:
        return ["take or pay", "take-or-pay", "make up gas", "make-up gas", "deficiency", "deliver or pay", "top", "mug"]
    if "lifting" in ql or "nomination" in ql or "오프테이크" in ql:
        return ["lifting", "nomination", "offtake", "lifting program", "lifting schedule", "cargo nomination", "scheduling"]
    if "insurance" in ql or "보험" in ql:
        return ["insurance", "insurer", "coverage", "policy", "liability", "deductible", "additional insured", "waiver of subrogation"]
    if "회계처리 기준" in ql or "accounting standards" in ql or "gaap" in ql or "ifrs" in ql:
        return ["accounting standards", "gaap", "ifrs", "accounting policy", "principles", "methods"]
    if "가격평가" in ql or "valuation" in ql or "가격" in ql:
        return ["valuation", "price", "pricing", "market price", "reference price", "platts", "brent", "henry hub", "index"]
    if "현지화" in ql or "로컬콘텐츠" in ql or "local content" in ql:
        return ["local content", "domestic content", "local employment", "local procurement", "in-country value", "icv"]
    if "rofr" in ql or "우선매수권" in ql or "right of first refusal" in ql or "pre-emption" in ql or "preemption" in ql:
        return ["right of first refusal", "rofr", "preferential right", "pre-emption", "preemptive right"]
    if "잔여의무" in ql or "post-termination" in ql or "survival" in ql:
        return ["post-termination", "survival", "surviving obligations", "continuing obligations"]
    if "venue" in ql or "중재장소" in ql or "place of arbitration" in ql or "seat" in ql:
        return ["venue", "place of arbitration", "seat", "forum"]
    if "amendment" in ql or "변경" in ql or "개정" in ql or "variation" in ql or "modify" in ql:
        return ["amendment", "amend", "variation", "modify", "change", "written amendment", "change order"]
    if "joint account" in ql or "계정" in ql or "jib" in ql or "billing" in ql or "cash call" in ql:
        return ["joint account", "joint interest billing", "jib", "cash call", "statement", "billing", "operator accounting"]
    if "현지채용" in ql or "훈련" in ql or "training" in ql:
        return ["local employment", "training", "training program", "capacity building", "local training", "local hire"]

    # fallback: 간단 토큰 분해
    return [w for w in ql.split() if w]



# 엄격 판정을 위한 보조 함수들
HEADER_PATTERNS = [
    r"\b(Article|Art\.?|Clause|Section)\b",
    r"제\s*\d+\s*조",
    r"^\d+(?:\.\d+){0,3}\b",
]


def _has_header_marker(text: str) -> bool:
    if not text:
        return False
    for pat in HEADER_PATTERNS:
        if re.search(pat, text, flags=re.IGNORECASE):
            return True
    return False


def _keyword_hits(text: str, keywords: list[str]) -> tuple[int, int]:
    """(총 매칭 횟수, 고유 키워드 매칭 수) 반환"""
    if not text:
        return 0, 0
    low = text.lower()
    total = sum(low.count(kw.lower()) for kw in keywords)
    unique = sum(1 for kw in set(k.lower() for k in keywords) if kw in low)
    return total, unique


def ensure_output_dir(path: str) -> None:
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def collect_contract_files() -> list[str]:
    names = list_all_file_names(category="contract")
    if names:
        return names
    backend_dir = os.path.dirname(__file__)
    data_dir = os.path.join(backend_dir, "data")
    try:
        files = [f for f in os.listdir(data_dir) if f.lower().endswith(".pdf")]
        files.sort(key=lambda x: x.lower())
        return files
    except Exception:
        return []


def _core_keywords_for_query(q: str) -> list[str]:
    ql = (q or "").lower()
    if "rofr" in ql or "right of first refusal" in ql or "우선매수권" in ql or "pre-emption" in ql or "preemption" in ql:
        return ["right of first refusal", "rofr"]
    if "venue" in ql or "seat" in ql or "place of arbitration" in ql or "중재장소" in ql:
        return ["venue", "seat"]
    if "회계처리 기준" in ql or "accounting standards" in ql or "gaap" in ql or "ifrs" in ql:
        return ["accounting standards", "gaap", "ifrs"]
    if "royalty" in ql or "세금" in ql or "tax" in ql:
        return ["royalty", "tax"]
    if "joint operating committee" in ql or "operating committee" in ql or "management committee" in ql or "joc" in ql:
        return ["operating committee", "committee"]
    if "carried interest" in ql or "carried" in ql:
        return ["carried interest"]
    if "정부 참여" in ql or "state participation" in ql or "government participation" in ql or "back-in" in ql:
        return ["state participation"]
    if "confidentiality" in ql or "비밀" in ql or "비밀유지" in ql or "nda" in ql:
        return ["confidentiality"]
    if "hse" in ql or "환경" in ql or "안전" in ql or "보건" in ql:
        return ["hse"]
    if "abandonment" in ql or "decommission" in ql or "비용 분담" in ql:
        return ["abandonment", "decommissioning"]
    if "work program" in ql or "wp&b" in ql or "budget" in ql:
        return ["work program", "budget"]
    if "take or pay" in ql or "take-or-pay" in ql or "make up gas" in ql or "make-up gas" in ql:
        return ["take or pay", "make up gas"]
    if "lifting" in ql or "nomination" in ql or "offtake" in ql or "오프테이크" in ql:
        return ["lifting", "nomination"]
    if "insurance" in ql or "보험" in ql:
        return ["insurance"]
    if "valuation" in ql or "가격평가" in ql or "가격" in ql:
        return ["valuation", "price"]
    if "현지화" in ql or "로컬콘텐츠" in ql or "local content" in ql:
        return ["local content"]
    if "잔여의무" in ql or "post-termination" in ql or "survival" in ql:
        return ["survival"]
    if "amendment" in ql or "변경" in ql or "개정" in ql or "variation" in ql:
        return ["amendment"]
    if "joint account" in ql or "jib" in ql or "billing" in ql or "cash call" in ql or "계정" in ql:
        return ["joint account"]
    if "현지채용" in ql or "훈련" in ql or "training" in ql:
        return ["training"]
    if "해지" in ql or "termination" in ql:
        return ["termination", "해지"]
    if "force majeure" in ql or "불가항력" in ql:
        return ["force majeure", "불가항력"]
    if "operator" in ql or "지정" in ql or "해임" in ql:
        return ["operator"]
    if "participating interest" in ql or "지분" in ql:
        return ["participating interest", "working interest"]
    if "default" in ql or "remedies" in ql or "위반" in ql:
        return ["default", "breach", "remedies"]
    if "withdrawal" in ql or "surrender" in ql:
        return ["withdrawal", "surrender"]
    if "assignment" in ql or "양도" in ql or "승인" in ql:
        return ["assignment", "consent", "approval"]
    if "중재" in ql or "분쟁" in ql or "arbitration" in ql:
        return ["arbitration", "dispute"]
    if "audit" in ql or "감사" in ql or "회계" in ql:
        return ["audit"]
    if "cost recovery" in ql or "profit oil" in ql or "배분" in ql:
        return ["cost recovery", "profit oil"]

    return []

def best_chunk_preview(query: str, file_name: str, k: int = 16) -> str:
    """해당 계약서에서 질의와 가장 유사한 청크 1개를 골라 1줄 미리보기로 반환.
    - 정확도 향상: 상위 k 내에서 질의 키워드 매칭 수가 가장 많은 청크를 선택
    - 임곗값: 키워드 매칭이 0이면 0 반환
    """
    keywords = _keywords_for_query(query)
    core_keywords = _core_keywords_for_query(query)
    expanded = f"{query} {' '.join(keywords)} Clause Article Section"
    docs_scores = vectorstore.similarity_search_with_score(expanded, k=k, filter={"file_name": file_name})
    if not docs_scores:
        return "0"

    best_text = ""
    best_score = -1.0
    best_hits = 0
    best_unique = 0
    best_has_header = False
    best_rank = 9999
    best_core = False
    for rank, (doc, _score) in enumerate(docs_scores, start=1):
        text = (doc.page_content or "").replace("\n", " ").strip()
        if not text:
            continue
        hits, unique = _keyword_hits(text, keywords)
        has_header = _has_header_marker(text)
        text_low = text.lower()
        core_present = any(core in text_low for core in core_keywords) if core_keywords else False
        # 스코어: 헤더(강) + 코어키워드(강) + 고유키워드(중) + 총 히트(약) + 랭크 보정(약)
        score = (3 if has_header else 0) + (2 if core_present else 0) + (1.5 * unique) + (0.5 * hits) + (0.5 / (rank))
        if score > best_score:
            best_score = score
            best_text = text
            best_hits = hits
            best_unique = unique
            best_has_header = has_header
            best_rank = rank
            best_core = core_present

    # 엄격 임곗값: 최소 2회 이상 키워드 매칭 또는 (1회 매칭이지만 헤더 동반)
    MIN_HITS = 2
    MIN_UNIQUE = 2
    MIN_SCORE = 4.2
    if not best_text:
        return "0"
    if best_hits < MIN_HITS:
        return "0"
    if best_unique < MIN_UNIQUE:
        return "0"
    # 헤더 OR 코어 키워드 중 하나라도 있으면 통과
    if not (best_has_header or best_core):
        return "0"
    if best_rank > 8:
        return "0"
    if best_score < MIN_SCORE:
        return "0"

    # 미리보기 길이 확대
    preview_len = 180
    return f"({best_text[:preview_len]}{'...' if len(best_text) > preview_len else ''})"


def write_matrix(contracts: list[str], out_path: str) -> None:
    if not OPENPYXL_AVAILABLE:
        raise RuntimeError("openpyxl이 설치되어 있지 않습니다. `pip install openpyxl` 후 다시 실행하세요.")

    wb = Workbook()
    ws = wb.active
    ws.title = "results"

    # 헤더
    header = ["No", "Question(질의)"] + contracts
    ws.append(header)

    # 각 질문 행 생성
    for i, q in enumerate(QUESTIONS, start=1):
        row = [i, q]
        for fn in contracts:
            row.append(best_chunk_preview(q, fn))
        ws.append(row)

    ensure_output_dir(out_path)
    wb.save(out_path)


def main():
    contracts = collect_contract_files()
    if not contracts:
        print("계약서 목록을 찾지 못했습니다.")
        return
    out_name = f"multi_question_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    out_path = os.path.join(os.path.dirname(__file__), "output", out_name)
    write_matrix(contracts, out_path)
    print(f"엑셀 저장 완료: {out_path}")


if __name__ == "__main__":
    main()
