// frontend/src/types.ts

export interface ChunkPreview {
  file: string;
  page: number;
  preview: string;
}

export interface HistoryItem {
  question: string;
  answer: string;
  file: string;
  bookmark: boolean;
  previewChunks: ChunkPreview[];
}

export type Language = "ko" | "en";
