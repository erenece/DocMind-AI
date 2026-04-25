from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse

import backend


app = FastAPI(title="Akademi AI RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _err(status: int, code: str, message: str, details: Any | None = None) -> JSONResponse:
    payload: Dict[str, Any] = {"ok": False, "error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return JSONResponse(status_code=status, content=payload)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "service": "rag-api"}


@app.post("/documents/process")
async def process_documents(
    files: List[UploadFile] = File(...),
    x_session_id: Optional[str] = Header(default=None),
) -> JSONResponse:
    # NOTE: Minimal API: single global index in backend.py.
    # Session header is accepted for future extension.
    _ = x_session_id
    try:
        # backend expects file-like objects with .read() and .name; UploadFile.file fits.
        # We attach name to keep metadata consistent.
        wrapped = []
        for f in files:
            f.file.name = f.filename  # type: ignore[attr-defined]
            wrapped.append(f.file)
        result = backend.process_documents(wrapped)
        if not isinstance(result, dict) or not result.get("ok"):
            err = (result or {}).get("error") if isinstance(result, dict) else None
            return _err(400, (err or {}).get("code", "PROCESS_FAILED"), (err or {}).get("message", "İşleme hatası"), (err or {}).get("details"))
        return JSONResponse(status_code=200, content=result)
    except backend.BackendError as e:
        return _err(400, e.code, e.message, e.details)
    except Exception as e:
        return _err(500, "INTERNAL_ERROR", "Beklenmeyen hata", str(e))


@app.post("/chat")
async def chat(
    payload: Dict[str, Any],
    x_session_id: Optional[str] = Header(default=None),
) -> JSONResponse:
    _ = x_session_id
    try:
        query = str(payload.get("query") or "")
        index_id = payload.get("index_id")
        chat_history = payload.get("chat_history")
        top_k = int(payload.get("top_k") or 4)
        result = backend.get_ai_response(query, index_id=index_id, chat_history=chat_history, top_k=top_k)
        if not isinstance(result, dict) or not result.get("ok"):
            err = (result or {}).get("error") if isinstance(result, dict) else None
            return _err(400, (err or {}).get("code", "CHAT_FAILED"), (err or {}).get("message", "Sohbet hatası"), (err or {}).get("details"))
        return JSONResponse(status_code=200, content=result)
    except backend.BackendError as e:
        return _err(400, e.code, e.message, e.details)
    except Exception as e:
        return _err(500, "INTERNAL_ERROR", "Beklenmeyen hata", str(e))


@app.post("/chat/stream")
async def chat_stream(
    payload: Dict[str, Any],
    x_session_id: Optional[str] = Header(default=None),
):
    _ = x_session_id
    query = str(payload.get("query") or "")
    index_id = payload.get("index_id")
    chat_history = payload.get("chat_history")
    top_k = int(payload.get("top_k") or 4)

    async def gen():
        # Simple SSE: event: token / sources / error
        try:
            for kind, data in backend.stream_ai_response(query, index_id=index_id, chat_history=chat_history, top_k=top_k):
                if kind == "token":
                    yield f"event: token\ndata: {str(data).replace('\\n','\\\\n')}\n\n"
                elif kind == "sources":
                    import json

                    yield f"event: sources\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        except backend.BackendError as e:
            import json

            yield f"event: error\ndata: {json.dumps({'code': e.code, 'message': e.message, 'details': e.details}, ensure_ascii=False)}\n\n"
        except Exception as e:
            import json

            yield f"event: error\ndata: {json.dumps({'code': 'INTERNAL_ERROR', 'message': 'Beklenmeyen hata', 'details': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


def _print_run_hint() -> None:
    # Only for local dev convenience (no-op in production).
    if os.getenv("RAG_API_HINT", "1") == "1":
        print("Run: uvicorn api:app --host 0.0.0.0 --port 8000")


_print_run_hint()

