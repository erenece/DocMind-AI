import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import streamlit as st
import os
import uuid
import requests
import json


@dataclass
class UploadedDoc:
    name: str
    size_bytes: int
    ext: str


def _human_size(num_bytes: int) -> str:
    step = 1024.0
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < step or unit == "TB":
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= step
    return f"{num_bytes} B"


def _get_ext(filename: str) -> str:
    parts = filename.rsplit(".", 1)
    return parts[-1].lower() if len(parts) == 2 else ""


def _doc_icon(ext: str) -> str:
    return {"pdf": "📕", "docx": "📘", "txt": "📄"}.get(ext, "📎")


def _inject_styles() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── Reset & Base ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.block-container {
  padding-top: 1.5rem !important;
  padding-bottom: 3rem !important;
  max-width: 900px !important;
}

/* ── Hide Streamlit branding & toolbar icons ── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
.stDeployButton { display: none !important; }
/* Hide accessibility/wheelchair icon in toolbar */
[data-testid="stToolbarActions"] { display: none !important; }
button[title="Running"] { display: none !important; }
div[data-testid="stStatusWidget"] { display: none !important; }

/* ── Hero Section ── */
.aa-hero {
  position: relative;
  padding: 2rem 2rem 1.75rem 2rem;
  border-radius: 20px;
  margin-bottom: 1.5rem;
  background:
    radial-gradient(ellipse 80% 60% at 10% -10%, rgba(99,102,241,0.22) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 90% 110%, rgba(16,185,129,0.18) 0%, transparent 55%),
    linear-gradient(160deg, rgba(15,23,42,0.85) 0%, rgba(15,23,42,0.55) 100%);
  border: 1px solid rgba(148,163,184,0.12);
  box-shadow: 0 4px 32px rgba(0,0,0,0.35), 0 1px 0 rgba(255,255,255,0.04) inset;
  overflow: hidden;
}
.aa-hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(99,102,241,0.06) 0%, transparent 50%, rgba(16,185,129,0.04) 100%);
  pointer-events: none;
}
.aa-hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px 4px 8px;
  border-radius: 999px;
  background: rgba(16,185,129,0.12);
  border: 1px solid rgba(16,185,129,0.22);
  font-size: .75rem;
  font-weight: 600;
  color: rgba(16,185,129,0.95);
  letter-spacing: .03em;
  margin-bottom: .85rem;
  text-transform: uppercase;
}
.aa-glow-dot {
  width: 7px; height: 7px; border-radius: 999px;
  background: #10b981;
  box-shadow: 0 0 0 3px rgba(16,185,129,0.2), 0 0 12px rgba(16,185,129,0.5);
  display: inline-block;
  animation: aaPulse 2s ease-in-out infinite;
}
@keyframes aaPulse {
  0%, 100% { box-shadow: 0 0 0 3px rgba(16,185,129,0.2), 0 0 12px rgba(16,185,129,0.5); }
  50% { box-shadow: 0 0 0 5px rgba(16,185,129,0.1), 0 0 20px rgba(16,185,129,0.7); }
}
.aa-title {
  font-size: 1.65rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin: 0 0 .45rem 0;
  line-height: 1.2;
  background: linear-gradient(135deg, #f8fafc 30%, rgba(148,163,184,0.85) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.aa-subtitle {
  font-size: .92rem;
  color: rgba(148,163,184,0.82);
  margin-bottom: 1.25rem;
  line-height: 1.5;
}
.aa-chips {
  display: flex;
  gap: .5rem;
  flex-wrap: wrap;
}
.aa-chip {
  display: inline-flex;
  align-items: center;
  gap: .3rem;
  padding: .3rem .65rem;
  border-radius: 999px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(148,163,184,0.12);
  font-size: .78rem;
  color: rgba(148,163,184,0.8);
  font-weight: 500;
  transition: all .2s;
}
.aa-chip:hover {
  background: rgba(99,102,241,0.12);
  border-color: rgba(99,102,241,0.25);
  color: rgba(165,168,255,0.9);
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  border-right: 1px solid rgba(148,163,184,0.08) !important;
  background: rgba(8,12,24,0.6) !important;
}
[data-testid="stSidebar"] > div { padding-top: 1.25rem; }
.aa-sidebar-header {
  display: flex;
  align-items: center;
  gap: .5rem;
  font-size: 1rem;
  font-weight: 700;
  color: #f1f5f9;
  margin-bottom: .35rem;
  letter-spacing: -0.01em;
}
.aa-sidebar-sub {
  font-size: .8rem;
  color: rgba(148,163,184,0.65);
  margin-bottom: 1rem;
  line-height: 1.45;
}

/* ── File cards ── */
.aa-file {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: .6rem .7rem;
  border-radius: 12px;
  background: rgba(15,23,42,0.5);
  border: 1px solid rgba(148,163,184,0.1);
  margin: .35rem 0;
  transition: border-color .2s;
}
.aa-file:hover { border-color: rgba(99,102,241,0.25); }
.aa-file-left { display: flex; gap: .5rem; align-items: center; min-width: 0; }
.aa-file-name {
  font-size: .85rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 190px;
  color: #e2e8f0;
}
.aa-file-meta { font-size: .74rem; color: rgba(148,163,184,0.6); margin-top: 1px; }
.aa-badge {
  font-size: .7rem;
  padding: .18rem .4rem;
  border-radius: 6px;
  background: rgba(99,102,241,0.14);
  border: 1px solid rgba(99,102,241,0.2);
  color: rgba(165,168,255,0.85);
  font-weight: 600;
  letter-spacing: .04em;
  flex-shrink: 0;
}

/* ── Status indicator ── */
.aa-status-ready {
  display: flex;
  align-items: center;
  gap: .4rem;
  font-size: .78rem;
  color: rgba(16,185,129,0.85);
  font-weight: 500;
  padding: .4rem .6rem;
  border-radius: 8px;
  background: rgba(16,185,129,0.08);
  border: 1px solid rgba(16,185,129,0.15);
  margin-top: .5rem;
}

/* ── Process button ── */
div.stButton > button {
  border-radius: 10px !important;
  font-weight: 600 !important;
  font-size: .85rem !important;
  transition: all .2s !important;
  border: 1px solid rgba(148,163,184,0.15) !important;
}
div.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #6366f1, #10b981) !important;
  border: none !important;
  box-shadow: 0 2px 12px rgba(99,102,241,0.3) !important;
}
div.stButton > button[kind="primary"]:hover {
  box-shadow: 0 4px 20px rgba(99,102,241,0.45) !important;
  transform: translateY(-1px);
}

/* ── Chat messages ── */
section[data-testid="stChatMessage"] {
  padding: .25rem 0;
  background: transparent !important;
}
section[data-testid="stChatMessage"] [data-testid="stChatMessageAvatar"] {
  border-radius: 10px !important;
  overflow: hidden !important;
}

/* ── Chat input ── */
[data-testid="stChatInput"] {
  border-radius: 14px !important;
  border: 1px solid rgba(148,163,184,0.12) !important;
  background: rgba(15,23,42,0.6) !important;
}
[data-testid="stChatInput"]:focus-within {
  border-color: rgba(99,102,241,0.35) !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.08) !important;
}

/* ── Divider ── */
hr { border-color: rgba(148,163,184,0.08) !important; margin: .75rem 0 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.15); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: rgba(148,163,184,0.3); }
</style>
        """,
        unsafe_allow_html=True,
    )


def _resolve_backend() -> tuple[Callable[..., Dict[str, Any]], Callable[..., Dict[str, Any]], Callable[..., Dict[str, Any]]]:
    """
    Backend 'backend.py' içinden get_ai_response / process_documents fonksiyonlarını yükler.
    Import hatası varsa kullanıcıya anlaşılır bir hata döndüren mock fonksiyonlara düşer.
    """
    api_base = os.getenv("RAG_API_URL", "").strip()
    if api_base:
        def _api_process_documents(uploaded_files: List, *_args: Any, **_kwargs: Any) -> Dict[str, Any]:
            files = []
            for f in uploaded_files or []:
                files.append(("files", (f.name, f.getvalue(), "application/octet-stream")))
            headers = {"X-Session-Id": st.session_state.session_id}
            r = requests.post(f"{api_base}/documents/process", files=files, headers=headers, timeout=600)
            return r.json()

        def _api_get_ai_response(user_query: str, *_args: Any, **kwargs: Any) -> Dict[str, Any]:
            payload = {
                "query": user_query,
                "index_id": kwargs.get("index_id"),
                "chat_history": kwargs.get("chat_history"),
                "top_k": 4,
            }
            headers = {"X-Session-Id": st.session_state.session_id}
            r = requests.post(f"{api_base}/chat", json=payload, headers=headers, timeout=600)
            return r.json()

        def _api_summarize_documents(*_args: Any, **kwargs: Any) -> Dict[str, Any]:
            payload = {
                "index_id": kwargs.get("index_id"),
                "max_chars": kwargs.get("max_chars", 12000),
            }
            headers = {"X-Session-Id": st.session_state.session_id}
            r = requests.post(f"{api_base}/documents/summary", json=payload, headers=headers, timeout=600)
            return r.json()

        return _api_get_ai_response, _api_process_documents, _api_summarize_documents

    try:
        import backend  # type: ignore

        get_ai_response = getattr(backend, "get_ai_response", None)
        process_documents = getattr(backend, "process_documents", None)
        summarize_documents = getattr(backend, "summarize_documents", None)
        if callable(get_ai_response) and callable(process_documents) and callable(summarize_documents):
            return get_ai_response, process_documents, summarize_documents
    except Exception:
        pass

    def _mock_get_ai_response(user_query: str, *_args: Any, **_kwargs: Any) -> Dict[str, Any]:
        _ = user_query
        return {
            "ok": True,
            "answer": "⚠️ Backend bağlantısı kurulamadı (mock mod). `backend.py` dosyanızın aynı dizinde olduğundan ve bağımlılıkların yüklü olduğundan emin olun.",
            "sources": [],
        }

    def _mock_process_documents(uploaded_files: List, *_args: Any, **_kwargs: Any) -> Dict[str, Any]:
        _ = uploaded_files
        return {"ok": True, "index_id": "mock", "processed_count": len(uploaded_files or []), "stats": {}, "errors": []}

    def _mock_summarize_documents(*_args: Any, **_kwargs: Any) -> Dict[str, Any]:
        return {
            "ok": True,
            "summary": "⚠️ Özetleme backend bağlantısı olmadığı için mock modda çalışıyor.",
            "sources": [],
        }

    return _mock_get_ai_response, _mock_process_documents, _mock_summarize_documents


def _ensure_state() -> None:
    defaults = {
        "messages": [],
        "uploaded_docs": [],
        "uploaded_files_raw": [],
        "docs_ready": False,
        "index_id": None,
        "upload_fingerprint": None,
        "session_id": str(uuid.uuid4()),
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _fingerprint_uploads(uploaded_files: Optional[List]) -> Optional[tuple]:
    if not uploaded_files:
        return None
    return tuple((getattr(f, "name", ""), int(getattr(f, "size", 0) or 0)) for f in uploaded_files)


def _sync_uploaded_docs(uploaded_files: Optional[List]) -> None:
    new_fp = _fingerprint_uploads(uploaded_files)
    if not uploaded_files:
        if st.session_state.upload_fingerprint is not None:
            st.session_state.uploaded_docs = []
            st.session_state.uploaded_files_raw = []
            st.session_state.docs_ready = False
            st.session_state.index_id = None
            st.session_state.upload_fingerprint = None
        return

    docs: List[UploadedDoc] = [
        UploadedDoc(
            name=getattr(f, "name", "dosya"),
            size_bytes=int(getattr(f, "size", 0) or 0),
            ext=_get_ext(getattr(f, "name", "")),
        )
        for f in uploaded_files
    ]

    st.session_state.uploaded_docs = docs
    st.session_state.uploaded_files_raw = uploaded_files
    if new_fp != st.session_state.upload_fingerprint:
        st.session_state.docs_ready = False
        st.session_state.index_id = None
        st.session_state.upload_fingerprint = new_fp


def _render_sidebar(
    process_documents: Callable[..., Dict[str, Any]],
    summarize_documents: Callable[..., Dict[str, Any]],
) -> None:
    with st.sidebar:
        st.markdown(
            """
<div class="aa-sidebar-header">
  <span>📂</span> Döküman Yönetimi
</div>
<div class="aa-sidebar-sub">PDF, DOCX veya TXT yükleyin, ardından işleyin.</div>
            """,
            unsafe_allow_html=True,
        )

        uploaded_files = st.file_uploader(
            "Dosya Yükle",
            type=["pdf", "doc", "docx", "txt"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )

        _sync_uploaded_docs(uploaded_files)

        if st.session_state.uploaded_docs:
            for d in st.session_state.uploaded_docs:
                st.markdown(
                    f"""
<div class="aa-file">
  <div class="aa-file-left">
    <div style="font-size:1.1rem;flex-shrink:0">{_doc_icon(d.ext)}</div>
    <div style="min-width:0">
      <div class="aa-file-name" title="{d.name}">{d.name}</div>
      <div class="aa-file-meta">{_human_size(d.size_bytes)}</div>
    </div>
  </div>
  <div class="aa-badge">{d.ext.upper() if d.ext else "FILE"}</div>
</div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                """<div style="font-size:.82rem;color:rgba(148,163,184,0.5);text-align:center;padding:1.2rem 0;">
                Henüz dosya yüklenmedi
                </div>""",
                unsafe_allow_html=True,
            )

        if st.session_state.docs_ready:
            st.markdown(
                '<div class="aa-status-ready"><span>✓</span> Dökümanlar hazır</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<div style='margin-top:.75rem'></div>", unsafe_allow_html=True)

        can_process = bool(st.session_state.uploaded_files_raw)
        process_clicked = st.button(
            "⚙️  Dökümanları İşle",
            type="primary",
            disabled=not can_process,
            use_container_width=True,
        )

        if process_clicked and can_process:
            with st.status("Dökümanlar işleniyor…", expanded=True) as status:
                st.write("📄 Dosyalar okunuyor")
                time.sleep(0.3)
                st.write("✂️ Parçalama (chunking)")
                time.sleep(0.4)
                st.write("🧠 Vektörleştirme (embedding)")
                time.sleep(0.5)
                st.write("🗄️ İndeksleme (vector store)")
                time.sleep(0.4)

                try:
                    result = process_documents(st.session_state.uploaded_files_raw)
                except Exception as e:
                    import traceback as _tb
                    status.update(label="İşlem başarısız", state="error", expanded=True)
                    st.error(f"{type(e).__name__}: {e}", icon="❌")
                    st.code(_tb.format_exc(), language="text")
                    st.session_state.docs_ready = False
                    st.session_state.index_id = None
                    return

                if not isinstance(result, dict) or not result.get("ok"):
                    err = (result or {}).get("error") if isinstance(result, dict) else None
                    msg = (err or {}).get("message") if isinstance(err, dict) else "Döküman işleme başarısız."
                    details = (err or {}).get("details") if isinstance(err, dict) else None
                    status.update(label="İşlem başarısız", state="error", expanded=True)
                    st.error(msg, icon="❌")
                    if details:
                        with st.expander("Hata detayı"):
                            st.code(str(details), language="text")
                    st.session_state.docs_ready = False
                    st.session_state.index_id = None
                    return

                status.update(label="Tamamlandı ✓", state="complete", expanded=False)

            st.session_state.docs_ready = True
            st.session_state.index_id = result.get("index_id")
            st.success("Dökümanlar hazır, soru sorabilirsiniz.", icon="✅")

            if result.get("errors"):
                with st.expander("⚠️ Uyarılar"):
                    st.json(result["errors"])

        if st.session_state.docs_ready:
            summarize_clicked = st.button(
                "📝 Dökümanları Özetle",
                use_container_width=True,
            )
            if summarize_clicked:
                with st.status("Özet hazırlanıyor…", expanded=False):
                    try:
                        summary_result = summarize_documents(
                            index_id=st.session_state.index_id,
                            max_chars=12000,
                        )
                    except Exception as e:
                        summary_result = {"ok": False, "error": {"code": "SUMMARY_EXCEPTION", "message": str(e)}}

                if not isinstance(summary_result, dict) or not summary_result.get("ok"):
                    err = (summary_result or {}).get("error") if isinstance(summary_result, dict) else None
                    msg = (err or {}).get("message") if isinstance(err, dict) else "Özet üretilemedi."
                    st.error(msg, icon="❌")
                else:
                    summary_text = summary_result.get("summary") or "Özet üretilemedi (boş cevap)."
                    st.session_state.messages.append({"role": "assistant", "content": f"## Doküman Özeti\n\n{summary_text}"})
                    st.success("Özet hazır. Sohbette görüntüleyebilirsiniz.", icon="✅")
                    st.rerun()

        # Sidebar footer
        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:.72rem;color:rgba(148,163,184,0.3);text-align:center'>DocMind AI • RAG Engine</div>",
            unsafe_allow_html=True,
        )


def _render_header() -> None:
    st.markdown(
        """
<div class="aa-hero">
  <div class="aa-hero-badge">
    <span class="aa-glow-dot"></span>
    RAG · Canlı
  </div>
  <p class="aa-title">DocMind AI — Akıllı Döküman Asistanı</p>
  <div class="aa-subtitle">
    Yüklediğiniz dökümanları analiz eder, kaynak göstererek yanıt üretir.
  </div>
  <div class="aa-chips">
    <span class="aa-chip">✦ Özet çıkar</span>
    <span class="aa-chip">⌕ Kaynaklı yanıt</span>
    <span class="aa-chip">◈ Bilgi çıkarımı</span>
    <span class="aa-chip">⚡ Hızlı</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _maybe_seed_welcome() -> None:
    if st.session_state.messages:
        return
    welcome = (
        "Merhaba! **DocMind AI Döküman Asistanı**'na hoş geldiniz.\n\n"
        "Başlamak için:\n"
        "1. Sol panelden **PDF, DOCX veya TXT** yükleyin\n"
        "2. **Dökümanları İşle** butonuna tıklayın\n"
        "3. Dökümanlarınız hakkında istediğiniz soruyu sorun\n\n"
        "_Hazır olduğunuzda yazmaya başlayabilirsiniz._"
    )
    st.session_state.messages.append({"role": "assistant", "content": welcome})


def _render_chat(get_ai_response: Callable[..., Dict[str, Any]]) -> None:
    for msg in st.session_state.messages:
        role = msg["role"]
        avatar = role  # "user" or "assistant" — always safe
        with st.chat_message(role):
            st.markdown(msg["content"])

    user_text = st.chat_input("Dökümanlarınız hakkında bir soru sorun…")
    if not user_text:
        return

    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        sources: List[Dict[str, Any]] = []
        reply = ""

        if st.session_state.docs_ready:
            with st.status("Yanıt üretiliyor…", expanded=False):
                time.sleep(0.25)
                api_base = os.getenv("RAG_API_URL", "").strip()
                if api_base:
                    sources = []
                    answer_parts: List[str] = []

                    def _sse_stream():
                        payload = {
                            "query": user_text,
                            "index_id": st.session_state.index_id,
                            "chat_history": st.session_state.messages[-12:],
                            "top_k": 4,
                        }
                        headers = {"X-Session-Id": st.session_state.session_id}
                        with requests.post(
                            f"{api_base}/chat/stream",
                            json=payload,
                            headers=headers,
                            stream=True,
                            timeout=600,
                        ) as resp:
                            resp.raise_for_status()
                            event = None
                            data_buf = []
                            for raw in resp.iter_lines(decode_unicode=True):
                                if raw is None:
                                    continue
                                line = raw.strip()
                                if not line:
                                    if event and data_buf:
                                        yield event, "\n".join(data_buf)
                                    event = None
                                    data_buf = []
                                    continue
                                if line.startswith("event:"):
                                    event = line.split(":", 1)[1].strip()
                                elif line.startswith("data:"):
                                    data_buf.append(line.split(":", 1)[1].lstrip())

                    ph = st.empty()
                    try:
                        for ev, data in _sse_stream():
                            if ev == "token":
                                token = data.replace("\\n", "\n")
                                answer_parts.append(token)
                                ph.markdown("".join(answer_parts))
                            elif ev == "sources":
                                sources = json.loads(data)
                            elif ev == "error":
                                err = json.loads(data)
                                raise RuntimeError(err.get("message", "Streaming error"))
                        reply = "".join(answer_parts).strip() or "Yanıt üretilemedi (boş cevap)."
                        result = {
                            "ok": True,
                            "answer": reply,
                            "sources": sources,
                            "index_id": st.session_state.index_id,
                        }
                    except Exception as e:
                        result = {"ok": False, "error": {"code": "STREAM_FAILED", "message": str(e)}}
                else:
                    try:
                        result = get_ai_response(
                            user_text,
                            index_id=st.session_state.index_id,
                            chat_history=st.session_state.messages[-12:],
                        )
                    except Exception as e:
                        result = {"ok": False, "error": {"code": "BACKEND_EXCEPTION", "message": str(e)}}

                if not isinstance(result, dict) or not result.get("ok"):
                    err_obj = (result or {}).get("error") if isinstance(result, dict) else None
                    err_msg = (err_obj or {}).get("message") if isinstance(err_obj, dict) else "Yanıt üretilemedi."
                    reply = f"❌ Hata: {err_msg}"
                else:
                    reply = result.get("answer") or "Yanıt üretilemedi (boş cevap)."
                    st.session_state.index_id = result.get("index_id") or st.session_state.index_id
                    sources = result.get("sources") or []
        else:
            reply = (
                "⚠️ Henüz döküman yüklenmedi veya işlenmedi.\n\n"
                "_Sol panelden dosya yükleyip **Dökümanları İşle**'ye basın._"
            )

        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

        if sources:
            with st.expander(f"📎 {len(sources)} kaynak"):
                for i, s in enumerate(sources, start=1):
                    filename = s.get("filename", "doküman")
                    snippet = s.get("snippet", "")
                    score = s.get("score", None)
                    score_str = f"  —  `{score:.3f}`" if isinstance(score, (int, float)) else ""
                    st.markdown(f"**{i}. {filename}**{score_str}")
                    if snippet:
                        st.caption(snippet)
                    if i < len(sources):
                        st.divider()


def main() -> None:
    st.set_page_config(
        page_title="DocMind AI · Akıllı Döküman Asistanı",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _inject_styles()
    _ensure_state()

    # Streamlit secrets → env
    try:
        if "GROQ_API_KEY" in st.secrets and not os.getenv("GROQ_API_KEY"):
            os.environ["GROQ_API_KEY"] = str(st.secrets["GROQ_API_KEY"])
    except Exception:
        pass

    get_ai_response, process_documents, summarize_documents = _resolve_backend()

    _render_sidebar(process_documents, summarize_documents)
    _render_header()
    _maybe_seed_welcome()
    _render_chat(get_ai_response)


if __name__ == "__main__":
    main()