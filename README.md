## Kendi Dokümanların ile Sohbet Et (RAG)

Streamlit arayüzü ile PDF/DOC/DOCX/TXT yükleyip, ChromaDB + HuggingFace Embeddings + Groq LLM ile doküman tabanlı sohbet edebileceğiniz uçtan uca bir RAG uygulaması.

### Özellikler

- **Çoklu dosya yükleme**: `pdf`, `doc`, `docx`, `txt`
- **Chunking**: LangChain `RecursiveCharacterTextSplitter`
- **Embedding**: `sentence-transformers/all-MiniLM-L6-v2`
- **Vector DB**: ChromaDB (persist: `./.rag_chroma`)
- **LLM**: Groq (varsayılan model: `llama-3.1-8b-instant`)
- **Kaynak gösterimi**: yanıt altındaki “Kaynaklar” bölümünde
- **Streaming (bonus)**: API açıkken yanıt token token akar

---

## Kurulum

### 1) Ortam değişkenleri

Groq API key’i gereklidir.

PowerShell (geçici):

```powershell
$env:GROQ_API_KEY="BURAYA_GROQ_KEY"
# Opsiyonel:
$env:GROQ_MODEL="llama-3.1-8b-instant"
```

Alternatif: `secrets.toml`

- `./.streamlit/secrets.toml`

```toml
GROQ_API_KEY="BURAYA_GROQ_KEY"
GROQ_MODEL="llama-3.1-8b-instant"
```

### 2) Paketleri kur

```powershell
& "C:\Users\Ece\AppData\Local\Python\bin\python.exe" -m pip install -r requirements.txt
```

> Not: İlk çalıştırmada embedding modeli indirileceği için biraz zaman alabilir.

---

## Çalıştırma

### A) Önerilen (API tabanlı)

1. API’yi başlat:

```powershell
$env:GROQ_API_KEY="BURAYA_GROQ_KEY"
& "C:\Users\Ece\AppData\Local\Python\bin\python.exe" -m uvicorn api:app --host 0.0.0.0 --port 8000
```

1. Streamlit’i API modunda başlat:

```powershell
$env:RAG_API_URL="http://localhost:8000"
& "C:\Users\Ece\AppData\Local\Python\bin\python.exe" -m streamlit run app.py
```

### B) Tek proses (kolay mod)

API kapalıysa `app.py` otomatik olarak `backend.py`’yi doğrudan import ederek çalışır (streaming yok).

```powershell
$env:GROQ_API_KEY="BURAYA_GROQ_KEY"
& "C:\Users\Ece\AppData\Local\Python\bin\python.exe" -m streamlit run app.py
```

---

## DOC desteği notu

`.doc` (legacy) dosyaları için `backend.py` **best-effort** çalışır:

- En stabil yöntem: **LibreOffice (soffice)** ile `.doc` → `.docx` dönüştürme, sonra okuma
- Eğer LibreOffice yoksa backend “DOC_UNSUPPORTED” hatası döndürür

Eğer `.doc` extraction hatası alırsanız en stabil çözüm: dosyaları `.docx` formatına çevirip yüklemek.

---

## Docker (bonus)

`docker-compose.yml` ile API + UI birlikte çalışır.

```bash
docker compose up --build
```

Sonra:

- UI: `http://localhost:8501`
- API: `http://localhost:8000/health`

