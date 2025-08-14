import React, { useState, useEffect } from "react";
import * as XLSX from "xlsx";
import { Document, Packer, Paragraph, TextRun } from 'docx';
import { saveAs } from 'file-saver';
import "./SearchPage.css"; // App.css에서 SearchPage.css로 변경되었을 수 있습니다.
import logo from './assets/logo.png'; 

interface ChunkPreview {
  file: string;
  page: number;
  preview: string;
}
interface HistoryItem {
  question: string;
  answer: string;
  file: string;
  bookmark: boolean;
  previewChunks: ChunkPreview[];
}

function getSortedHistory(history: HistoryItem[]) {
  const bookmarks = history.filter((h) => h.bookmark);
  const others = history.filter((h) => !h.bookmark);
  return [...bookmarks, ...others];
}

const SearchPage: React.FC = () => {
  const [question, setQuestion] = useState("");
  const [language, setLanguage] = useState<"ko" | "en">("ko");
  const [contracts, setContracts] = useState<string[]>([]);
  const [file, setFile] = useState<string>("전체 계약서");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);

  // --- 기능 추가를 위한 상태들 ---
  const [selectedIndices, setSelectedIndices] = useState<number[]>([]);
  const [currentView, setCurrentView] = useState<'history' | 'bookmarks'>('history');
  const [isDownloadMenuOpen, setIsDownloadMenuOpen] = useState(false);

  // --- 기능 추가를 위한 핸들러 함수들 ---
  const handleViewChange = (view: 'history' | 'bookmarks') => {
    setCurrentView(view);
    setSelectedIdx(null);
    setSelectedIndices([]);
  };

  const handleSelectionChange = (indexToToggle: number) => {
    setSelectedIndices(prev =>
      prev.includes(indexToToggle)
        ? prev.filter(index => index !== indexToToggle)
        : [...prev, indexToToggle]
    );
  };

  const handleDownload = (format: 'xlsx' | 'docx') => {
    if (selectedIndices.length === 0) {
      alert("다운로드할 항목을 하나 이상 선택해주세요.");
      return;
    }
    const selectedData = selectedIndices.map(index => sortedHistory[index]);
    const today = new Date().toISOString().slice(0, 10);

    if (format === 'xlsx') {
      const excelData = selectedData.map(item => ({
        '질문': item.question, 'AI 답변': item.answer, '선택한 계약서': item.file, '북마크 여부': item.bookmark ? 'Y' : 'N'
      }));
      const worksheet = XLSX.utils.json_to_sheet(excelData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, "검색기록");
      XLSX.writeFile(workbook, `aSK_selected_history_${today}.xlsx`);
    }

    if (format === 'docx') {
      const docChildren: Paragraph[] = selectedData.flatMap(item => [
        new Paragraph({ children: [new TextRun({ text: "[질문]", bold: true, size: 28 })], spacing: { before: 200, after: 100 } }),
        new Paragraph({ text: item.question, spacing: { after: 300 } }),
        new Paragraph({ children: [new TextRun({ text: "[AI 답변]", bold: true, size: 28 })], spacing: { after: 100 } }),
        new Paragraph({ text: item.answer, spacing: { after: 300 } }),
        new Paragraph({ children: [new TextRun({ text: `(파일: ${item.file})`, color: "888888", size: 20 })], spacing: { after: 200 } }),
        new Paragraph({ text: "---", alignment: 'center', spacing: { after: 400, before: 400 } })
      ]);
      const doc = new Document({ sections: [{ children: docChildren }] });
      Packer.toBlob(doc).then(blob => saveAs(blob, `aSK_selected_history_${today}.docx`));
    }
    setIsDownloadMenuOpen(false);
  };

  // 계약서 목록
  useEffect(() => {
    fetch("http://localhost:8000/api/contracts")
      .then((res) => res.json())
      .then((data) => setContracts(["전체 계약서", ...(data.contracts || [])]))
      .catch(() => setContracts(["전체 계약서"]));
  }, []);

  // 검색 실행
  const handleSearch = async () => {
    if (!question.trim()) {
      alert("질문을 입력하세요.");
      return;
    }
    setLoading(true);
    setSelectedIndices([]);
    try {
      const res = await fetch("http://localhost:8000/api/search", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: question, file_name: file === "전체 계약서" ? null : file, answer_lang: language }),
      });
      const data = await res.json();
      const item: HistoryItem = {
        question, answer: data.answer, file: data.file, bookmark: false,
        previewChunks: (data.preview_chunks || []).map((p: string) => ({ file: data.file, page: 0, preview: p })),
      };
      setHistory((h) => getSortedHistory([item, ...h]).slice(0, 30));
      setSelectedIdx(0);
      setQuestion("");
      setCurrentView('history');
    } catch (e) {
      alert("검색 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const toggleBookmark = (idx: number) => {
    setHistory((h) => getSortedHistory(h.map((it, i) => i === idx ? { ...it, bookmark: !it.bookmark } : it)));
    setSelectedIdx(0);
  };

  const deleteHistory = (idx: number) => {
    setHistory((h) => getSortedHistory(h.filter((_, i) => i !== idx)));
    setSelectedIndices(prev => prev.filter(i => i !== idx));
    setSelectedIdx(null);
  };

  const handleSelectHistory = (idx: number) => setSelectedIdx(idx);

  const sortedHistory = getSortedHistory(history);

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-view-selector">
            <button className={`view-tab-button ${currentView === 'history' ? 'active' : ''}`} onClick={() => handleViewChange('history')}>
              검색 기록
            </button>
            <button className={`view-tab-button ${currentView === 'bookmarks' ? 'active' : ''}`} onClick={() => handleViewChange('bookmarks')}>
              북마크
            </button>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="h1" style={{ fontSize: 18, margin: 0 }}>목록</div>
            <div className="download-container">
              <button onClick={() => setIsDownloadMenuOpen(prev => !prev)} className="download-button">
                다운로드
              </button>
              {isDownloadMenuOpen && (
                <div className="download-dropdown">
                  <button className="download-option-button" onClick={() => handleDownload('docx')}>Word (.docx)로 저장</button>
                  <button className="download-option-button" onClick={() => handleDownload('xlsx')}>Excel (.xlsx)로 저장</button>
                </div>
              )}
            </div>
          </div>
        </div>

        {sortedHistory.filter(item => currentView === 'history' || (currentView === 'bookmarks' && item.bookmark)).length === 0 ? (
          <div className="sub" style={{ textAlign: 'center', marginTop: 20 }}>
            {currentView === 'history' ? '아직 기록 없음' : '북마크 없음'}
          </div>
        ) : (
          sortedHistory.map((item, idx) => {
            if (currentView === 'bookmarks' && !item.bookmark) return null;
            return (
              <div key={idx} className={`history-item ${selectedIdx === idx ? "active" : ""}`}>
                <input
                  type="checkbox"
                  className="history-item-checkbox"
                  checked={selectedIndices.includes(idx)}
                  onChange={() => handleSelectionChange(idx)}
                />
                <button className="history-title" onClick={() => handleSelectHistory(idx)} title={item.question}>
                  {item.question.length > 18 ? item.question.slice(0, 18) + "..." : item.question}
                </button>
                <button className={`star ${item.bookmark ? "on" : ""}`} onClick={() => toggleBookmark(idx)} title="북마크">★</button>
                <button className="del" onClick={() => deleteHistory(idx)} title="삭제">🗑️</button>
              </div>
            );
          })
        )}
      </aside>

      {/* Main */}
      <main className="main">
        <div className="container">
          <div className="header">
            <img src={logo} alt="aSK logo" className="brand-logo" />
            <div>
              <h1 className="brand-title">글로벌 계약 정보 검색 시스템</h1>
              <div className="brand-sub">계약 관련 질문을 입력하면, 계약서 근거와 답변을 AI가 제공합니다.</div>
            </div>
          </div>

          <form className="search-surface" onSubmit={(e) => { e.preventDefault(); handleSearch(); }}>
            <div className="toolbar">
              <label><span className="label">언어</span><select className="select" value={language} onChange={(e) => setLanguage(e.target.value as "ko" | "en")}><option value="ko">한국어</option><option value="en">English</option></select></label>
              <label><span className="label">계약서</span><select className="select" value={file} onChange={(e) => setFile(e.target.value)}>{contracts.map((opt) => (<option key={opt} value={opt}>{opt}</option>))}</select></label>
              <input className="input" type="text" placeholder={language === "ko" ? "예: 계약 해지 조건은 무엇인가요?" : "e.g., What are the termination conditions?"} value={question} onChange={(e) => setQuestion(e.target.value)} disabled={loading} />
              <button type="submit" className="btn-primary" disabled={loading}>{loading ? "검색 중..." : "검색 실행"}</button>
            </div>
          </form>

          {selectedIdx !== null && sortedHistory[selectedIdx] ? (
            <section style={{ marginTop: 10 }}>
              <div className="section-title"><span className="chip chip-lg">선택한 계약서</span>{sortedHistory[selectedIdx].file}</div>
              <div className="section-title"><span className="chip chip-lg">질문</span></div>
              <div className="card">{sortedHistory[selectedIdx].question}</div>
              <div className="section-title"><span className="chip chip-lg">AI 답변</span></div>
              <div className="card">
                <div className="card-head"><div className="sub">요약 · 근거 · 조언 형식</div>
                  <button className="icon-btn" onClick={() => navigator.clipboard.writeText(sortedHistory[selectedIdx].answer)}>📋 복사</button>
                </div>
                <div className="answer">{sortedHistory[selectedIdx].answer}</div>
              </div>
              <div className="section-title"><span className="chip chip-lg">검색된 청크 미리보기</span></div>
              <div className="card">
                {sortedHistory[selectedIdx].previewChunks.length === 0 ? (<div className="empty">검색된 청크가 없습니다.</div>) : (<ul className="list">{sortedHistory[selectedIdx].previewChunks.map((c, i) => (<li key={i}>{c.preview}</li>))}</ul>)}
              </div>
            </section>
          ) : (
            <div className="empty" style={{ marginTop: 12 }}>상단에서 언어/계약서를 선택하고 질문을 입력한 뒤 <b className="accent">검색 실행</b>을 눌러주세요.</div>
          )}
        </div>
      </main>
    </div>
  );
};

// 컴포넌트 이름을 SearchPage로 변경
const SearchPageWrapper: React.FC = () => <SearchPage />;

export default SearchPageWrapper;