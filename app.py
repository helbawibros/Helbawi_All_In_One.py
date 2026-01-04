import streamlit as st
import pandas as pd
import random
from datetime import datetime
import requests
import os

# --- 1. إعدادات التنسيق والهوية (حل مشكلة اللوغو) ---
LOGO_FILE = "Lgo.png"

st.set_page_config(
    page_title="شركة حلباوي إخوان", 
    layout="centered",
)

# دالة لعرض اللوغو بأمان (إذا لم يجد الصورة لن يتوقف البرنامج)
def display_logo_safely():
    if os.path.exists(LOGO_FILE):
        try:
            st.image(LOGO_FILE, use_container_width=True)
        except:
            st.markdown("<h2 style='text-align:center;'>شركة حلباوي إخوان</h2>", unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='text-align:center;'>شركة حلباوي إخوان</h2>", unsafe_allow_html=True)

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;800&display=swap');
    html, body, [class*="css"] {{ font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }}
    
    /* تنسيق نظام إدارة الطلبيات (الستايل القديم) */
    .central-header {{ background-color: #000; color: white; text-align: center; padding: 20px; border-radius: 10px; margin-bottom: 10px; }}
    .status-box {{ background-color: #1a2e1a; color: #4ade80; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 15px; border: 1px solid #2d4a2d; }}

    .header-box {{ background-color: #1E3A8A; color: white; text-align: center; padding: 10px; border-radius: 10px; margin-bottom: 20px;}}
    .invoice-preview {{ background-color: white; padding: 25px; border: 2px solid #1E3A8A; border-radius: 10px; color: black; }}
    .styled-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 15px; text-align: center; color: black; }}
    .styled-table th {{ background-color: #f0f2f6; color: black; padding: 10px; border: 1px solid #000; }}
    .styled-table td {{ padding: 10px; border: 1px solid #000; }}
    .total-final {{ background-color: #d4edda; font-size: 22px; font-weight: 800; color: #155724; border: 2px solid #c3e6cb; margin-top: 10px; padding: 10px; text-align: center; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. إعدادات البيانات ---
SHEET_ID = "1-Abj-Kvbe02az8KYZfQL0eal2arKw_wgjVQdJX06IA0"
GID_PRICES = "339292430"
GID_DATA = "0"
GID_CUSTOMERS = "155973706" 

@st.cache_data(ttl=60)
def load_products_from_excel():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={GID_PRICES}"
        df_p = pd.read_csv(url)
        return pd.Series(df_p.iloc[:, 1].values, index=df_p.iloc[:, 0]).to_dict()
    except: return {"⚠️ خطأ": 0.0}

PRODUCTS = load_products_from_excel()

# --- إدارة الحالة ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'page' not in st.session_state: st.session_state.page = 'login'

USERS = {"عبد الكريم حوراني": "9900", "محمد الحسيني": "8822", "علي دوغان": "5500", "عزات حلاوي": "6611", "علي حسين حلباوي": "4455", "محمد حسين حلباوي": "3366", "احمد حسين حلباوي": "7722", "علي محمد حلباوي": "6600"}

# --- الواجهات ---

if not st.session_state.logged_in:
    display_logo_safely()
    st.markdown('<div class="header-box"><h1>🔐 دخول المندوبين</h1></div>', unsafe_allow_html=True)
    user_sel = st.selectbox("إختر اسمك", ["-- اختر --"] + list(USERS.keys()))
    pwd = st.text_input("كلمة السر", type="password")
    if st.button("دخول", use_container_width=True):
        if USERS.get(user_sel) == pwd:
            st.session_state.logged_in, st.session_state.user_name, st.session_state.page = True, user_sel, 'home'
            st.rerun()

elif st.session_state.page == 'home':
    display_logo_safely()
    st.markdown(f'<div class="header-box"><h3>أهلاً بك سيد {st.session_state.user_name}</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 فاتورة جديدة", use_container_width=True, type="primary"):
            st.session_state.page = 'order' # يفتح كود الفاتورة الخاص بك
            st.rerun()
    with col2:
        if st.button("🛠️ طلبية بضاعة (تحميل)", use_container_width=True):
            st.session_state.page = 'stock_manager' # يفتح النظام المركزي (الصور)
            st.rerun()

elif st.session_state.page == 'order':
    st.button("🔙 عودة للرئيسية", on_click=lambda: st.session_state.update({"page": "home"}))
    st.write("### كود الفاتورة الخاص بك يعمل هنا...")
    # هنا يوضع بقية كود الفاتورة الذي أرسلته (من سطر 144 في كودك)

elif st.session_state.page == 'stock_manager':
    st.markdown('<div class="central-header"><h1>🛠️ نظام إدارة الطلبيات المركزي</h1></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="status-box">📦 يوجد طلبات معلقة لـ {st.session_state.user_name}</div>', unsafe_allow_html=True)
    
    # هنا نضع الجدول الأسود كما في صورتك القديمة
    data = {"الحالة": ["بانتظار التصديق"], "الكمية": [10], "الصنف": ["حمص 9"], "الوقت": [datetime.now().strftime("%H:%M")]}
    st.table(pd.DataFrame(data))
    
    if st.button("🔙 عودة", use_container_width=True):
        st.session_state.page = 'home'
        st.rerun()
