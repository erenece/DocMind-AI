```markdown
# 🧠 DocMind-AI: Akıllı Doküman Analiz Asistanı

DocMind-AI, dokümanlarınızı yükleyip içerikleri hakkında soru sorabileceğiniz, yapay zeka destekli (Groq API & Streamlit) bir analiz aracıdır. RAG (Retrieval-Augmented Generation) yapısını kullanarak dokümanlarınızdan anlamlı bilgiler çıkarır.

## 🚀 Özellikler
- **Hızlı Analiz:** Groq LPU altyapısı sayesinde saniyeler içinde cevap üretir.
- **RAG Entegrasyonu:** Doküman içeriğini ChromaDB (veya kullandığın vektör veri tabanı) ile indeksler.
- **Kullanıcı Dostu Arayüz:** Streamlit ile modern ve sade bir web arayüzü.
- **Gizlilik Odaklı:** API anahtarları yerel ortamda güvenle saklanır.

## 🛠️ Kurulum

Projenizi yerel bilgisayarınızda çalıştırmak için şu adımları izleyin:

1. **Depoyu klonlayın:**
   ```bash
   git clone [https://github.com/erenece/DocMind-AI.git](https://github.com/erenece/DocMind-AI.git)
   cd DocMind-AI
   ```

2. **Gerekli kütüphaneleri yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

3. **API Anahtarını ayarlayın:**
   `.streamlit/secrets.toml` dosyasını oluşturun ve içine Groq API anahtarınızı ekleyin:
   ```toml
   GROQ_API_KEY = "gsk_..."
   ```

4. **Uygulamayı çalıştırın:**
   ```bash
   streamlit run app.py
   ```

## 📂 Proje Yapısı
- `app.py`: Ana Streamlit arayüzü.
- `backend.py`: Doküman işleme ve AI mantığı.
- `.streamlit/`: Uygulama yapılandırması ve yerel şifreler.
- `requirements.txt`: Gerekli Python kütüphaneleri.

## 👩‍💻 Geliştirici
- **Ece** - (https://github.com/erenece)
<img width="2158" height="1310" alt="resim" src="https://github.com/user-attachments/assets/dac2df3d-981e-4013-bab6-a8c46e68f202" />

---
*Bu proje, full-stack geliştirme yolculuğumda AI entegrasyonu üzerine yaptığım bir çalışmadır.*
```
