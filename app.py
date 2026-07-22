import os
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
import json

# --- 0. OTOMATİK TEMA AYARI (Tek Dosya Çözümü) ---
if not os.path.exists('.streamlit'):
    os.makedirs('.streamlit')

config_path = '.streamlit/config.toml'
if not os.path.exists(config_path):
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write("""[theme]
primaryColor = "#0ea5e9"
backgroundColor = "#0f172a"
secondaryBackgroundColor = "#1e293b"
textColor = "#f8fafc"
font = "sans serif"
""")

# --- 1. SAYFA AYARLARI VE GLOBAL CSS ---
st.set_page_config(page_title="Test and Verification Team Panel", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 0rem; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. GLOBAL ÜST BİLGİ (HEADER) ---
st.markdown("""
<div style="display: flex; align-items: center; gap: 20px; background-color: #1e293b; padding: 20px 30px; border-radius: 12px; margin-bottom: 25px; border: 1px solid #334155; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">
    <div style="width: 55px; height: 55px;">
        <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <circle cx="50" cy="50" r="48" fill="#0f172a" stroke="#ffffff" stroke-width="2"/>
            <circle cx="33" cy="53" r="16" fill="#ffffff" />
            <circle cx="67" cy="53" r="16" fill="#ffffff" />
            <circle cx="33" cy="53" r="6" fill="#0f172a" />
            <circle cx="67" cy="53" r="6" fill="#0f172a" />
            <circle cx="31" cy="51" r="2" fill="#ffffff" />
            <circle cx="65" cy="51" r="2" fill="#ffffff" />
            <polygon points="50,65 44,53 56,53" fill="#ffffff" />
            <path d="M 12 43 Q 33 20 50 43 Q 67 20 88 43 Q 67 43 50 33 Q 33 43 12 43 Z" fill="#ffffff" />
        </svg>
    </div>
    <h1 style="margin: 0; font-size: 26px; font-weight: 700; color: #f8fafc; letter-spacing: 0.5px;">Test and Verification Team Operation Support Panel</h1>
</div>
""", unsafe_allow_html=True)


# --- 3. SEKMELER (TABS) ---
tab1, tab2 = st.tabs(["🤖 OlizPay Hata & Operasyon Asistanı", "🛡️ Enqura Operasyon Destek Paneli"])

# =====================================================================
# TAB 1: RAG BOT ASİSTANI
# =====================================================================
with tab1:
    URL = "https://ywqruftnkxbnjxrmlblx.supabase.co"
    KEY = "sb_secret_hGYjIBeij3w4nSbjMN2uHg_HohMAzBN"

    @st.cache_resource
    def init_connection():
        return create_client(URL, KEY)
    supabase = init_connection()

    @st.cache_resource
    def load_model():
        return SentenceTransformer('all-MiniLM-L6-v2')
    model = load_model()

    if "arama_sonuclari" not in st.session_state:
        st.session_state.arama_sonuclari = None
    if "secili_case" not in st.session_state:
        st.session_state.secili_case = None
    if "case_durumu" not in st.session_state:
        st.session_state.case_durumu = None

    def case_sec(sonuc):
        st.session_state.secili_case = sonuc
        st.session_state.case_durumu = None

    def durum_guncelle(durum):
        st.session_state.case_durumu = durum

    def ekran_temizle():
        st.session_state.arama_sonuclari = None
        st.session_state.secili_case = None
        st.session_state.case_durumu = None

    with st.container(border=True):
        st.markdown("<h3 style='margin-top:0;'>Jira Akıllı Arama Motoru</h3>", unsafe_allow_html=True)

        if st.session_state.arama_sonuclari is None:
            with st.form("arama_formu"):
                query = st.text_input("Aramak istediğiniz sorunu yazın (Örn: bildirim ekranı hata veriyor)")
                submit_button = st.form_submit_button("🔍 Veritabanında Ara")

            if submit_button and query:
                with st.spinner('Kayıtlar taranıyor...'):
                    query_embedding = model.encode(query).tolist()
                    try:
                        response = supabase.rpc('match_documents', {
                            'query_embedding': query_embedding,
                            'match_threshold': 0.60, 
                            'match_count': 3
                        }).execute()
                        
                        st.session_state.arama_sonuclari = response.data
                        st.session_state.secili_case = None
                        st.session_state.case_durumu = None
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Arama sırasında hata oluştu: {e}")

        else:
            if st.session_state.secili_case is None:
                sonuclar = st.session_state.arama_sonuclari
                
                if len(sonuclar) == 0:
                    st.warning("Bu konuyla ilgili yeterince benzer bir kayıt bulunamadı.")
                    st.button("🔄 Yeni Arama Yap", on_click=ekran_temizle)
                else:
                    st.success("Bulduğum en ilgili kayıtlar. Lütfen detayını görmek istediğiniz konuya tıklayın:")
                    
                    for sonuc in sonuclar:
                        benzerlik = int(sonuc.get('similarity', 0) * 100)
                        baslik = f"📌 {sonuc['title']} (Benzerlik: %{benzerlik})"
                        st.button(baslik, on_click=case_sec, args=(sonuc,), use_container_width=True)
                    
                    st.markdown("---")
                    st.button("🔄 Aramayı İptal Et ve Geri Dön", on_click=ekran_temizle)

            else:
                secilen = st.session_state.secili_case
                
                try:
                    icerik = json.loads(secilen['content'])
                    kontrol_metni = icerik.get("kontrol_edilmesi_gerekenler", "Belirtilmemiş.")
                    yazilim_metni = icerik.get("yazilim_ekibi_durumu", "Belirtilmemiş.")
                except:
                    kontrol_metni = secilen['content']
                    yazilim_metni = "Kayıt formatı hatalı."

                st.subheader(f"📌 {secilen['title']}")
                
                with st.container(border=True):
                    st.markdown("**🔍 Kontrol Edilmesi Gerekenler:**")
                    st.info(kontrol_metni)
                
                mevcut_durum = st.session_state.case_durumu
                
                if mevcut_durum is None:
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.button("✔️ Sorun Devam Etmiyor (Kapat)", on_click=durum_guncelle, args=("kapatildi",), use_container_width=True)
                    with col2:
                        st.button("❌ Sorun Devam Ediyor (Yazılım)", on_click=durum_guncelle, args=("yazilim",), use_container_width=True)
                
                elif mevcut_durum == "kapatildi":
                    st.success("✅ Case kapatıldı. Herhangi bir işlem gerekmiyor.")
                
                elif mevcut_durum == "yazilim":
                    with st.container(border=True):
                        st.markdown("<span style='color:#ef4444; font-weight:bold;'>🚨 Yazılım Ekibi Değerlendirmesi:</span>", unsafe_allow_html=True)
                        st.warning(yazilim_metni)
                
                st.markdown("---")
                st.button("🔄 Paneli Temizle ve Başa Dön", type="primary", on_click=ekran_temizle, use_container_width=True)


# =====================================================================
# TAB 2: ENQURA HTML PANELİ (GELİŞMİŞ KARANLIK MOD DESTEKLİ)
# =====================================================================
with tab2:
    ENQURA_HTML = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Enqura Panel Operasyon Destek Sistemi</title>
        <style>
            :root {
                --bg-color: transparent;
                --card-bg: #ffffff;
                --text-dark: #2d3748;
                --text-light: #718096;
                --border-color: #e2e8f0;
                --blue-line: #0ea5e9;
                --icon-bg-gray: #cbd5e1;
                --icon-bg-green: #22c55e;
                --icon-bg-red: #ef4444;
                --primary: #2b3b4e;
                --focus-bg: #f8fafc;
                
                --card-success-bg: #f0fdf4;
                --card-success-border: #86efac;
                --card-error-bg: #fef2f2;
                --card-error-border: #fca5a5;
                
                --banner-bg: #e0f2fe;
                --banner-border: #bae6fd;
                --banner-text: #0369a1;
            }

            /* Karanlık Mod (Dark Mode) Uyumluluğu - Streamlit temasını otomatik algılar */
            @media (prefers-color-scheme: dark) {
                :root {
                    --bg-color: transparent;
                    --card-bg: #1e293b;
                    --text-dark: #f8fafc;
                    --text-light: #94a3b8;
                    --border-color: #334155;
                    --primary: #e2e8f0;
                    --focus-bg: #0f172a;
                    --icon-bg-gray: #475569;
                    
                    --card-success-bg: rgba(34, 197, 94, 0.1);
                    --card-success-border: #22c55e;
                    --card-error-bg: rgba(239, 68, 68, 0.1);
                    --card-error-border: #ef4444;

                    --banner-bg: rgba(14, 165, 233, 0.15);
                    --banner-border: #0ea5e9;
                    --banner-text: #38bdf8;
                }
                
                header { background-color: transparent !important; border-bottom-color: var(--border-color) !important; }
                header h1 { color: var(--primary) !important; }
                header svg circle[fill="#2d3748"] { fill: #f8fafc; } /* Logoyu aydınlık yapar */
                header svg circle[fill="#ffffff"] { fill: #1e293b; }
                header svg polygon { fill: #1e293b; }
                header svg path[fill="#ffffff"] { fill: #1e293b; }
                
                footer { background: transparent !important; border-top-color: var(--border-color) !important; }
                .box-error { background-color: rgba(239, 68, 68, 0.1) !important; border-color: #ef4444 !important; color: #fca5a5 !important; }
                .box-warning { background-color: rgba(245, 158, 11, 0.1) !important; border-color: #f59e0b !important; color: #fcd34d !important; }
                .box-success { background-color: rgba(34, 197, 94, 0.1) !important; border-color: #22c55e !important; color: #86efac !important; }
                .box-info { background-color: rgba(14, 165, 233, 0.1) !important; border-color: #38bdf8 !important; color: #7dd3fc !important; }
                .bio-box, .bio-circle, .bio-line { background: #334155 !important; }
                .bio-visual { background: #0f172a !important; border-color: #334155 !important; }
                input, select { color: #f8fafc !important; }
                .info-banner { background-color: var(--banner-bg) !important; border-color: var(--banner-border) !important; color: var(--banner-text) !important; }
            }

            body {
                font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
                background-color: var(--bg-color);
                color: var(--text-dark);
                margin: 0;
                padding: 0;
            }

            header {
                background-color: var(--card-bg);
                padding: 15px 40px;
                display: flex;
                align-items: center;
                gap: 15px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
                border-bottom: 1px solid var(--border-color);
            }

            .logo-container svg { width: 45px; height: 45px; }

            header h1 {
                margin: 0;
                font-size: 22px;
                font-weight: 700;
                color: var(--primary);
                letter-spacing: -0.5px;
            }

            .container {
                max-width: 1450px;
                margin: 30px auto;
                padding: 0 20px;
            }

            .info-banner {
                background-color: var(--banner-bg);
                border: 1px solid var(--banner-border);
                color: var(--banner-text);
                padding: 16px 20px;
                border-radius: 8px;
                margin-bottom: 30px;
                font-size: 14px;
                line-height: 1.5;
                display: flex;
                align-items: flex-start;
                gap: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            }

            .info-banner strong { font-weight: 700; }

            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 20px;
            }

            .card {
                background: var(--card-bg);
                padding: 25px 20px;
                border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
                border: 1px solid var(--border-color);
                transition: all 0.3s ease;
            }

            .card-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 25px;
            }

            .card-title-group h2 {
                font-size: 16px;
                color: var(--primary);
                margin: 0;
                font-weight: 700;
            }

            .card-title-group .blue-line {
                display: block;
                width: 35px;
                height: 3px;
                background-color: var(--blue-line);
                margin-top: 8px;
                border-radius: 2px;
            }

            .status-icon {
                width: 28px;
                height: 28px;
                border-radius: 50%;
                background-color: var(--icon-bg-gray);
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background-color 0.3s ease;
            }
            
            .status-icon.success { background-color: var(--icon-bg-green); }
            .status-icon.error { background-color: var(--icon-bg-red); }
            .status-icon svg { width: 14px; height: 14px; fill: white; }

            .form-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 0;
                border-bottom: 1px solid var(--border-color);
            }

            .form-row:last-child { border-bottom: none; }

            .form-row label {
                font-size: 13px;
                font-weight: 700;
                color: var(--text-dark);
                flex: 1;
            }

            .form-row input, .form-row select {
                flex: 1.2;
                text-align: right;
                border: 1px solid transparent;
                background: transparent;
                font-size: 13px;
                color: var(--text-light);
                padding: 6px;
                outline: none;
                border-radius: 4px;
                transition: all 0.2s;
            }

            .form-row input:focus, .form-row select:focus {
                background: var(--focus-bg);
                border-bottom: 1px solid var(--blue-line);
                color: var(--text-dark);
            }

            .bio-visual {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                margin-bottom: 20px;
                padding: 10px;
                background: #f8fafc;
                border-radius: 8px;
                border: 1px dashed var(--border-color);
            }
            .bio-box { width: 45px; height: 45px; background: #e2e8f0; border-radius: 6px; }
            .bio-circle { width: 30px; height: 30px; background: #e2e8f0; border-radius: 50%; }
            .bio-line { height: 2px; width: 30px; background: #e2e8f0; }

            .btn-submit {
                display: block;
                width: 100%;
                max-width: 350px;
                margin: 40px auto;
                padding: 15px;
                background-color: var(--blue-line);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                box-shadow: 0 4px 10px rgba(14, 165, 233, 0.3);
                transition: opacity 0.3s;
            }
            .btn-submit:hover { opacity: 0.9; }

            #sonuc-alani { display: none; margin-bottom: 40px; }
            .result-box { padding: 20px; border-radius: 8px; margin-bottom: 15px; }
            .result-box ul { margin: 10px 0 0 0; padding-left: 20px; }
            .result-box li { margin-bottom: 8px; line-height: 1.5; font-size: 14px; }
            
            .box-error { background-color: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }
            .box-warning { background-color: #fffbeb; color: #92400e; border: 1px solid #fde68a; }
            .box-success { background-color: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; text-align: center; font-size: 16px; font-weight: bold; }
            .box-info { background-color: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }

            footer {
                text-align: center;
                padding: 30px 20px;
                color: var(--text-light);
                font-size: 13px;
                border-top: 1px solid var(--border-color);
                margin-top: 40px;
                background: var(--card-bg);
            }
            footer a { color: var(--blue-line); text-decoration: none; font-weight: 600; }
            footer a:hover { text-decoration: underline; }
            .footer-team { margin-top: 6px; font-size: 11px; font-weight: bold; color: #94a3b8; letter-spacing: 1px; }

        </style>
    </head>
    <body>

    <header>
        <div class="logo-container">
            <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                <circle cx="50" cy="50" r="48" fill="#2d3748" />
                <circle cx="33" cy="53" r="16" fill="#ffffff" />
                <circle cx="67" cy="53" r="16" fill="#ffffff" />
                <circle cx="33" cy="53" r="6" fill="#2d3748" />
                <circle cx="67" cy="53" r="6" fill="#2d3748" />
                <circle cx="31" cy="51" r="2" fill="#ffffff" />
                <circle cx="65" cy="51" r="2" fill="#ffffff" />
                <polygon points="50,65 44,53 56,53" fill="#ffffff" />
                <path d="M 12 43 Q 33 20 50 43 Q 67 20 88 43 Q 67 43 50 33 Q 33 43 12 43 Z" fill="#ffffff" />
            </svg>
        </div>
        <h1>Enqura Panel Operasyon Destek Sistemi</h1>
    </header>

    <div class="container">
        
        <div class="info-banner">
            <div>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
            </div>
            <div>
                <strong>Uyarı Notu:</strong> Enqura panel üzerinde kişiye dair tüm bilgileri doğru bir şekilde var olanları giriniz, olmayanları boş bırakınız. Yapı buna göre hata tahmini yapacaktır.
            </div>
        </div>
        
        <div class="grid">
            <div class="card" id="card-kps">
                <div class="card-header">
                    <div class="card-title-group">
                        <h2>KPS Bilgileri</h2>
                        <span class="blue-line"></span>
                    </div>
                    <div class="status-icon" id="icon-kps">
                        <svg viewBox="0 0 24 24" id="svg-kps"><path d="M19 13H5v-2h14v2z"/></svg>
                    </div>
                </div>
                <div class="form-row">
                    <label>Kimlik Seri No</label>
                    <input type="text" id="kps-seri">
                </div>
                <div class="form-row">
                    <label>Doğum Tarihi</label>
                    <input type="text" id="kps-dogum" class="date-input" placeholder="GG.AA.YYYY">
                </div>
                <div class="form-row">
                    <label>Son Geçerlilik Tarihi</label>
                    <input type="text" id="kps-gecerlilik" class="date-input" placeholder="GG.AA.YYYY">
                </div>
            </div>

            <div class="card" id="card-ocr">
                <div class="card-header">
                    <div class="card-title-group">
                        <h2>Kimlik Bilgileri (OCR)</h2>
                        <span class="blue-line"></span>
                    </div>
                    <div class="status-icon" id="icon-ocr">
                        <svg viewBox="0 0 24 24" id="svg-ocr"><path d="M19 13H5v-2h14v2z"/></svg>
                    </div>
                </div>
                <div class="form-row">
                    <label>Görseller Net mi?</label>
                    <select id="ocr-gorsel">
                        <option value="">Seçiniz</option>
                        <option value="duzgun">Evet, Net</option>
                        <option value="bozuk">Hayır, Net Değil</option>
                    </select>
                </div>
                <div class="form-row">
                    <label>Kimlik Kırık/Hasarlı mı?</label>
                    <select id="ocr-kirik">
                        <option value="">Seçiniz</option>
                        <option value="hayir">Hayır</option>
                        <option value="evet">Evet, Kırık/Sorunlu</option>
                    </select>
                </div>
                <div class="form-row">
                    <label>Kimlik Seri No</label>
                    <input type="text" id="ocr-seri">
                </div>
                <div class="form-row">
                    <label>Doğum Tarihi</label>
                    <input type="text" id="ocr-dogum" class="date-input" placeholder="GG.AA.YYYY">
                </div>
                <div class="form-row">
                    <label>Son Geçerlilik Tarihi</label>
                    <input type="text" id="ocr-gecerlilik" class="date-input" placeholder="GG.AA.YYYY">
                </div>
            </div>

            <div class="card" id="card-nfc">
                <div class="card-header">
                    <div class="card-title-group">
                        <h2>Kimlik Çip Bilgileri (NFC)</h2>
                        <span class="blue-line"></span>
                    </div>
                    <div class="status-icon" id="icon-nfc">
                        <svg viewBox="0 0 24 24" id="svg-nfc"><path d="M19 13H5v-2h14v2z"/></svg>
                    </div>
                </div>
                <div class="form-row">
                    <label>NFC Verisi Okundu mu?</label>
                    <select id="nfc-durum">
                        <option value="">Seçiniz</option>
                        <option value="dolu">Evet, Okundu</option>
                        <option value="bos">Hayır, Boş</option>
                    </select>
                </div>
                <div class="form-row">
                    <label>Kimlik Seri No</label>
                    <input type="text" id="nfc-seri">
                </div>
                <div class="form-row">
                    <label>Doğum Tarihi</label>
                    <input type="text" id="nfc-dogum" class="date-input" placeholder="GG.AA.YYYY">
                </div>
                <div class="form-row">
                    <label>Son Geçerlilik Tarihi</label>
                    <input type="text" id="nfc-gecerlilik" class="date-input" placeholder="GG.AA.YYYY">
                </div>
            </div>

            <div class="card" id="card-bio">
                <div class="card-header">
                    <div class="card-title-group">
                        <h2>Yüz ve Canlılık Bilgileri</h2>
                        <span class="blue-line"></span>
                    </div>
                    <div class="status-icon" id="icon-bio">
                        <svg viewBox="0 0 24 24" id="svg-bio"><path d="M19 13H5v-2h14v2z"/></svg>
                    </div>
                </div>
                <div class="bio-visual">
                    <div class="bio-box"></div>
                    <div class="bio-line"></div>
                    <div class="bio-circle"></div>
                    <div class="bio-line"></div>
                    <div class="bio-box"></div>
                </div>
                <div class="form-row">
                    <label>Canlılık Skoru (%)</label>
                    <input type="number" id="bio-skor" min="0" max="100">
                </div>
            </div>
        </div>

        <button class="btn-submit" onclick="kontrolEt()">Sistemi Kontrol Et</button>

        <div id="sonuc-alani">
            <div id="hata-kutusu" class="result-box box-error" style="display:none;">
                <strong>🚨 Tespit Edilen Hatalar:</strong>
                <ul id="hata-listesi"></ul>
            </div>
            <div id="uyari-kutusu" class="result-box box-warning" style="display:none;">
                <strong>⚠️ Ekstra Uyarılar ve Yönlendirmeler:</strong>
                <ul id="uyari-listesi"></ul>
            </div>
            <div id="info-kutusu" class="result-box box-info" style="display:none;">
                <ul id="info-listesi"></ul>
            </div>
            <div id="basari-kutusu" class="result-box box-success" style="display:none;">
                ✅ Tüm bilgiler birbiriyle eşleşti ve başarılı şekilde onaylandı.
            </div>
        </div>
    </div>

    <footer>
        <div>Bu sayfa Mahmut Burak Ceylan tarafından geliştirilmiştir.</div>
        <div style="margin-top: 5px;">İletişim ve destek için: <a href="mailto:burak.ceylan@tokeninc.com">burak.ceylan@tokeninc.com</a></div>
        <div class="footer-team">TOKEN TEST AND VERIFICATION TEAM</div>
    </footer>

    <script>
        // --- OTOMATİK TARİH FORMATLAMA (GG.AA.YYYY) ---
        document.querySelectorAll('.date-input').forEach(input => {
            input.addEventListener('input', function(e) {
                let v = this.value.replace(/\D/g, '');
                if (v.length > 2) v = v.substring(0, 2) + '.' + v.substring(2);
                if (v.length > 5) v = v.substring(0, 5) + '.' + v.substring(5);
                this.value = v.substring(0, 10);
            });
        });

        const svgCheck = '<path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/>';
        const svgCross = '<path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>';
        const svgDash = '<path d="M19 13H5v-2h14v2z"/>'; // Nötr durum ikonu

        function tarihGecmisMi(tarihStr) {
            if (!tarihStr || tarihStr.length < 10) return false;
            
            // Gelen tarihteki tüm tire ve slash işaretlerini noktaya çevirerek normalize ediyoruz
            let normalizeTarih = tarihStr.replace(/[-/]/g, '.');
            let parcalar = normalizeTarih.split('.');
            
            if (parcalar.length === 3) {
                let gun = parseInt(parcalar[0]);
                let ay = parseInt(parcalar[1]) - 1; 
                let yil = parseInt(parcalar[2]);
                let girilenTarihObj = new Date(yil, ay, gun);
                let bugun = new Date();
                bugun.setHours(0,0,0,0);
                return girilenTarihObj < bugun;
            }
            return false; 
        }

        // Kart Renklerini ve İkonları Güncelleyen Fonksiyon
        function updateCardState(id, hasData, hasError) {
            const cardElem = document.getElementById('card-' + id);
            const iconElem = document.getElementById('icon-' + id);
            const svgElem = document.getElementById('svg-' + id);

            if (hasError) {
                cardElem.style.backgroundColor = 'var(--card-error-bg)';
                cardElem.style.borderColor = 'var(--card-error-border)';
                iconElem.className = 'status-icon error';
                svgElem.innerHTML = svgCross;
            } else if (hasData) {
                cardElem.style.backgroundColor = 'var(--card-success-bg)';
                cardElem.style.borderColor = 'var(--card-success-border)';
                iconElem.className = 'status-icon success';
                svgElem.innerHTML = svgCheck;
            } else {
                // Hiç veri girilmemişse nötr (gri) kalır, kesinlikle yeşil olmaz
                cardElem.style.backgroundColor = 'var(--card-bg)';
                cardElem.style.borderColor = 'var(--border-color)';
                iconElem.className = 'status-icon';
                svgElem.innerHTML = svgDash;
            }
        }

        function kontrolEt() {
            const kpsSeri = document.getElementById('kps-seri').value.trim();
            const kpsDogum = document.getElementById('kps-dogum').value.trim();
            const kpsGecerlilik = document.getElementById('kps-gecerlilik').value.trim();
            
            const ocrGorsel = document.getElementById('ocr-gorsel').value;
            const ocrKirik = document.getElementById('ocr-kirik').value;
            const ocrSeri = document.getElementById('ocr-seri').value.trim();
            const ocrDogum = document.getElementById('ocr-dogum').value.trim();
            const ocrGecerlilik = document.getElementById('ocr-gecerlilik').value.trim();
            
            const nfcDurum = document.getElementById('nfc-durum').value;
            const nfcSeri = document.getElementById('nfc-seri').value.trim();
            const nfcDogum = document.getElementById('nfc-dogum').value.trim();
            const nfcGecerlilik = document.getElementById('nfc-gecerlilik').value.trim();
            
            const bioSkorStr = document.getElementById('bio-skor').value;
            const bioSkor = parseInt(bioSkorStr);

            // Tarih karşılaştırmalarında (nokta, tire vb.) format hatalarından kaçınmak için 
            // verilerdeki rakam harici tüm karakterleri (\D) siliyoruz.
            const kpsDogumSadeceRakam = kpsDogum.replace(/\D/g, '');
            const ocrDogumSadeceRakam = ocrDogum.replace(/\D/g, '');
            const kpsGecerlilikSadeceRakam = kpsGecerlilik.replace(/\D/g, '');
            const ocrGecerlilikSadeceRakam = ocrGecerlilik.replace(/\D/g, '');

            let hatalar = [];
            let uyarilar = [];

            let errKps = false;
            let errOcr = false;
            let errNfc = false;
            let errBio = false;

            // Panellerde herhangi bir veri var mı kontrolü
            const hasKpsData = kpsSeri !== "" || kpsDogum !== "" || kpsGecerlilik !== "";
            const hasOcrData = ocrSeri !== "" || ocrDogum !== "" || ocrGecerlilik !== "" || ocrKirik !== "" || ocrGorsel !== "";
            const hasNfcData = nfcSeri !== "" || nfcDogum !== "" || nfcGecerlilik !== "" || nfcDurum !== "";
            const hasBioData = bioSkorStr !== "";

            let digerPanellerBos = (!hasOcrData && !hasNfcData && !hasBioData);
            let kpsDigerVerilerVar = (kpsSeri !== "" || kpsGecerlilik !== "");

            if (hasKpsData && !kpsDogum && digerPanellerBos) {
                errKps = true;
                hatalar.push("Sadece KPS alanı var ve başka bilgi gelmemiş. Doğum tarihi alınamadı. Bu da kullanıcının doğum tarihini yanlış girdiği anlamına gelmektedir.<br><span style='color:#475569; font-size:13px;'><strong>Yazılım ekibine iletin:</strong> Lütfen Oliz için 'customer_kps' ve 'customer' tablolarından silin. Kurumsal için 'customer_kps', 'customer' ve 'corporate_user' tablosunda silin.</span>");
            } 
            else if (kpsDigerVerilerVar && !kpsDogum) {
                errKps = true;
                hatalar.push("KPS bilgileri tam doldurulmamış (Doğum tarihi eksik). Genellikle doğum tarihi hatalı demektir.<br><span style='color:#475569; font-size:13px;'><strong>Yazılım ekibine iletin:</strong> Lütfen Oliz için 'customer_kps' ve 'customer' tablolarından silin. Kurumsal için 'customer_kps', 'customer' ve 'corporate_user' tablosunda silin.</span>");
            }
            
            if (ocrKirik === 'evet') {
                errOcr = true;
                hatalar.push("Kimlik kırık/sorunlu görünüyor. Kişinin kimliğini yenilemesi gerekiyor.");
            }

            if (ocrGorsel === 'bozuk') {
                errOcr = true;
                hatalar.push("OCR alanındaki kimlik görselinde kimlik fotoğrafı düzgün çıkmamış. Lütfen işlemi tekrar denettirin, başarısız olursa bu sefer başka bir cihazla onboard edin.");
            }

            if ((kpsSeri && ocrSeri && kpsSeri !== ocrSeri) || (nfcDurum === 'dolu' && kpsSeri && nfcSeri && kpsSeri !== nfcSeri)) {
                errKps = true; errOcr = true;
                if (nfcDurum === 'dolu' && nfcSeri) errNfc = true;
                hatalar.push("Kimlik seri no eşleşmiyor. Kişinin kimliğini veya kimlik bilgilerini e-devlette güncellemesi gerekmektedir.");
            }

            // Temizlenmiş (sadece rakam içeren) doğum tarihleri karşılaştırılıyor
            if (kpsDogumSadeceRakam && ocrDogumSadeceRakam && kpsDogumSadeceRakam !== ocrDogumSadeceRakam) {
                errKps = true; errOcr = true;
                hatalar.push("Doğum tarihleri eşleşmiyor. Doğum tarihini kullanıcı yanlış girmiş.<br><span style='color:#475569; font-size:13px;'><strong>Yazılım ekibine iletin:</strong> Lütfen Oliz için 'customer_kps' ve 'customer' tablolarından silin. Kurumsal için 'customer_kps', 'customer' ve 'corporate_user' tablosunda silin.</span>");
            }

            // Temizlenmiş (sadece rakam içeren) geçerlilik tarihleri karşılaştırılıyor
            if (kpsGecerlilikSadeceRakam && ocrGecerlilikSadeceRakam && kpsGecerlilikSadeceRakam !== ocrGecerlilikSadeceRakam) {
                errKps = true; errOcr = true;
                hatalar.push("Son geçerlilik tarihleri eşleşmiyor.");
            }

            if (tarihGecmisMi(kpsGecerlilik) || tarihGecmisMi(ocrGecerlilik) || (nfcDurum === 'dolu' && tarihGecmisMi(nfcGecerlilik))) {
                if(tarihGecmisMi(kpsGecerlilik)) errKps = true;
                if(tarihGecmisMi(ocrGecerlilik)) errOcr = true;
                if(nfcDurum === 'dolu' && tarihGecmisMi(nfcGecerlilik)) errNfc = true;
                hatalar.push("Geçerlilik tarihi geçmişte kalmış. Kimlik geçerliliği geçmiştir, yeni kimlik çıkartılmalı.");
            }

            if (nfcDurum === 'bos') {
                errNfc = true;
                uyarilar.push("NFC alanı boş gelmiş. Lütfen kimliği görsellerden kontrol edin, kimlik bozuk kırık olabilir, nfc özelliği kapalı olabilir, telefon modelini araştırın nfc özelliği olmayabilir.");
            }

            if (hasBioData && !isNaN(bioSkor) && bioSkor < 60) {
                errBio = true;
                hatalar.push("Canlılık skoru düşük. Düşük ışık veya hareketleri düzgün yapamadığı için olmaktadır.");
            }

            updateCardState('kps', hasKpsData, errKps);
            updateCardState('ocr', hasOcrData, errOcr);
            updateCardState('nfc', hasNfcData, errNfc);
            updateCardState('bio', hasBioData, errBio);

            document.getElementById('sonuc-alani').style.display = 'block';
            const hataKutusu = document.getElementById('hata-kutusu');
            const uyariKutusu = document.getElementById('uyari-kutusu');
            const infoKutusu = document.getElementById('info-kutusu');
            const basariKutusu = document.getElementById('basari-kutusu');
            
            const hataListesi = document.getElementById('hata-listesi');
            const uyariListesi = document.getElementById('uyari-listesi');
            const infoListesi = document.getElementById('info-listesi');

            hataKutusu.style.display = 'none';
            uyariKutusu.style.display = 'none';
            infoKutusu.style.display = 'none';
            basariKutusu.style.display = 'none';
            
            hataListesi.innerHTML = '';
            uyariListesi.innerHTML = '';
            infoListesi.innerHTML = '';

            if (hatalar.length > 0) {
                hataKutusu.style.display = 'block';
                hatalar.forEach(hata => {
                    let li = document.createElement('li');
                    li.innerHTML = hata;
                    hataListesi.appendChild(li);
                });
            }

            if (uyarilar.length > 0) {
                uyariKutusu.style.display = 'block';
                uyarilar.forEach(uyari => {
                    let li = document.createElement('li');
                    li.innerHTML = uyari;
                    uyariListesi.appendChild(li);
                });
            }

            if (hatalar.length === 0 && uyarilar.length === 0) {
                if (!hasKpsData && !hasOcrData && !hasNfcData && !hasBioData) {
                    infoKutusu.style.display = 'block';
                    infoListesi.innerHTML = "<li>ℹ️ Lütfen hata tahmini yapabilmek için Enqura panelindeki mevcut verileri giriniz.</li>";
                } else if (hasKpsData && !hasOcrData && !hasNfcData) {
                    infoKutusu.style.display = 'block';
                    infoListesi.innerHTML = "<li>ℹ️ Sadece KPS verisi girdiniz. Hata bulunamadı ancak doğrulama için diğer alanları da doldurmanız gerekmektedir.</li>";
                } else {
                    basariKutusu.style.display = 'block';
                }
            }
        }
    </script>
    </body>
    </html>
    """
    
    # HTML paneli için yüksekliği arttırdık ki layout daha rahat görünsün
    components.html(ENQURA_HTML, height=1400, scrolling=True)
