import pymupdf as fitz
import os
import re
from typing import Dict, List, Any

class PDFExtractor:
    """
    Extracts, cleans, analyzes, and chunks textual content from subject PDFs.
    Ensures that questions can be mapped directly to source pages and topics.
    """

    MAX_FILE_SIZE_MB = 20
    MIN_TOTAL_WORDS = 20

    @classmethod
    def extract_from_file(cls, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at: {file_path}")

        file_size_bytes = os.path.getsize(file_path)
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
        if file_size_mb > cls.MAX_FILE_SIZE_MB:
            raise ValueError(f"PDF size ({file_size_mb} MB) exceeds maximum allowed limit of {cls.MAX_FILE_SIZE_MB} MB.")

        try:
            doc = fitz.open(file_path)
        except Exception as e:
            raise ValueError(f"Failed to read PDF. The file may be corrupted or password-protected: {str(e)}")

        total_pages = len(doc)
        if total_pages == 0:
            doc.close()
            raise ValueError("The uploaded PDF contains 0 pages.")

        pages_data: List[Dict[str, Any]] = []
        raw_full_text = []
        detected_topics: List[str] = []

        for page_num in range(total_pages):
            page = doc[page_num]
            text = page.get_text("text") or ""
            cleaned_page_text = cls._clean_page_text(text)
            
            page_topics = cls._detect_page_headings(page, text)
            for t in page_topics:
                if t not in detected_topics:
                    detected_topics.append(t)

            pages_data.append({
                "page_number": page_num + 1,
                "text": cleaned_page_text,
                "word_count": len(cleaned_page_text.split()),
                "topics": page_topics
            })
            if cleaned_page_text:
                raw_full_text.append(cleaned_page_text)

        doc.close()

        full_text = "\n\n".join(raw_full_text)
        total_words = len(full_text.split())

        if total_words < cls.MIN_TOTAL_WORDS:
            raise ValueError(
                "We couldn't extract readable text from this PDF. Please ensure you upload a text-based PDF rather than a scanned or image-only document."
            )

        chunks = cls._create_chunks(pages_data)

        if not detected_topics:
            detected_topics = ["Core Principles", "Fundamental Concepts", "Applied Methods"]

        return {
            "filename": os.path.basename(file_path),
            "file_size_mb": file_size_mb,
            "total_pages": total_pages,
            "total_words": total_words,
            "estimated_reading_minutes": max(1, round(total_words / 200)),
            "topics": detected_topics[:15],
            "chunks": chunks,
            "full_text_preview": full_text[:400] + ("..." if len(full_text) > 400 else "")
        }

    @staticmethod
    def _clean_page_text(text: str) -> str:
        if not text:
            return ""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
        text = re.sub(r"^\s*\d+\s*$\n", "", text, flags=re.MULTILINE)
        return text.strip()

    @staticmethod
    def _detect_page_headings(page, text: str) -> List[str]:
        headings = []
        try:
            blocks = page.get_text("dict").get("blocks", [])
            for b in blocks:
                if "lines" in b:
                    for line in b["lines"]:
                        for span in line.get("spans", []):
                            span_text = span.get("text", "").strip()
                            span_size = span.get("size", 0)
                            if span_size >= 12 and len(span_text) >= 3 and len(span_text) <= 65:
                                if span_text not in headings and not span_text.isdigit():
                                    headings.append(span_text)
        except Exception:
            pass

        if not headings and text:
            matches = re.findall(r"^(?:Chapter\s+\d+|[0-9]+(?:\.[0-9]+)*\s+[A-Z][A-Za-z0-9\s]{3,40})", text, flags=re.MULTILINE)
            for m in matches:
                clean_m = m.strip()
                if clean_m not in headings:
                    headings.append(clean_m)

        return headings[:5]

    @classmethod
    def _create_chunks(cls, pages_data: List[Dict[str, Any]], target_chunk_words: int = 600) -> List[Dict[str, Any]]:
        chunks = []
        current_chunk_pages = []
        current_chunk_text = []
        current_chunk_words = 0
        current_chunk_topics = []

        for p in pages_data:
            p_text = p["text"]
            if not p_text:
                continue

            p_words = p["word_count"]
            p_num = p["page_number"]
            p_topics = p["topics"]

            current_chunk_pages.append(p_num)
            current_chunk_text.append(f"--- Page {p_num} ---\n{p_text}")
            current_chunk_words += p_words
            for t in p_topics:
                if t not in current_chunk_topics:
                    current_chunk_topics.append(t)

            if current_chunk_words >= target_chunk_words:
                page_ref = f"Page {current_chunk_pages[0]}" if len(current_chunk_pages) == 1 else f"Pages {current_chunk_pages[0]}-{current_chunk_pages[-1]}"
                primary_topic = current_chunk_topics[0] if current_chunk_topics else f"Section ({page_ref})"
                
                chunks.append({
                    "chunk_id": len(chunks) + 1,
                    "page_range": current_chunk_pages.copy(),
                    "source_reference": f"{page_ref} — {primary_topic}",
                    "primary_topic": primary_topic,
                    "text": "\n\n".join(current_chunk_text),
                    "word_count": current_chunk_words
                })
                current_chunk_pages = []
                current_chunk_text = []
                current_chunk_words = 0
                current_chunk_topics = []

        if current_chunk_text:
            page_ref = f"Page {current_chunk_pages[0]}" if len(current_chunk_pages) == 1 else f"Pages {current_chunk_pages[0]}-{current_chunk_pages[-1]}"
            primary_topic = current_chunk_topics[0] if current_chunk_topics else f"Section ({page_ref})"
            chunks.append({
                "chunk_id": len(chunks) + 1,
                "page_range": current_chunk_pages,
                "source_reference": f"{page_ref} — {primary_topic}",
                "primary_topic": primary_topic,
                "text": "\n\n".join(current_chunk_text),
                "word_count": current_chunk_words
            })

        return chunks
