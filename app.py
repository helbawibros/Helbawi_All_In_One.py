import streamlit as st
import pandas as pd
import random
from datetime import datetime
import requests
import json
import urllib.parse
import os

# --- 1. إعدادات الهوية والشعار الجديد ---
LOGO_FILE = "IMG_6463.png"  # تم التحديث لاسم الملف الجديد

st.set_page_config(
    page_title="شركة حلباوي إخوان", 
    layout="centered"
)

# عرض الشعار الجديد بأمان
if os.path.exists(LOGO_FILE):
    try:
        st.image(LOGO_FILE, use_container_width=True)
    except:
        st.markdown("<h1 style='text-align:center;'>شركة حلباوي إخوان</h1>", unsafe_allow_html=True)
else:
    # محاولة أخيرة في حال كان هناك اختلاف في حالة الأحرف
    st.markdown("<h1 style='text-align:center;'>شركة حلباوي إخوان</h1>", unsafe_allow_html=True)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .header-box { background-color: #1E3A8A; color: white; text-align: center; padding: 10px; border-radius: 10px; margin-bottom: 20px;}
    .central-header { background-color: #000; color: white; text-align: center; padding: 20px; border-radius: 10px; margin-bottom: 10px; }
    .status-box { background-color: #1a2e1a; color: #4ade80; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 15px; border: 1px solid #2d4a2d; }
    .invoice-preview { background-color: white; padding: 25px; border: 2px solid #1E3A8A; border-radius: 10px; color: black; }
    .styled-table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 15px; text-align: center; color: black; }
    .styled-table th { background-color: #f0f2f6; color: black; padding: 10px; border: 1px solid #000; }
    .styled-table td { padding: 10px; border: 1px solid #000; }
    .total-final { background-color: #d4edda; font-size: 22px; font-weight: 800; color: #155724; border: 2px solid #c3e6cb; margin-top: 10px; padding: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إعدادات البيانات والروابط ---
SHEET_ID = "1-Abj-Kvbe02az8KYZfQL0eal2arKw_wgjVQdJX06IA0"
GID_PRICES = "339292430"
GID_DATA = "0"
GID_CUSTOMERS = "155973706" 

@st.cache_data(ttl=60)
def load_rep_customers(rep_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={GID_CUSTOMERS}"
        df = pd.read_csv(url)
        rep_df = df[df.iloc[:, 0].astype(str).str.strip() == rep_name.strip()]
        return {f"{row.iloc[1]} ({row.iloc[2]})": row.iloc[1] for _, row in rep_df.iterrows()}
    except: return {}

@st.cache_data(ttl=60)
def load_products_from_excel():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={GID_PRICES}"
        df_p = pd.read_csv(url)
        df_p.columns = [c.strip() for c in df_p.columns]
        return pd.Series(df_p.iloc[:, 1].values, index=df_p.iloc[:, 0]).to_dict()
    except: return {"⚠️ خطأ في التحميل": 0.0}

def get_next_invoice_number():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={GID_DATA}"
        df = pd.read_csv(url)
        valid_nums = pd.to_numeric(df['رقم الفاتوره'], errors='coerce').dropna()
        return str(int(valid_nums.max()) + 1) if not valid_nums.empty else "1001"
    except: return str(random.randint(1000, 9999))

PRODUCTS = load_products_from_excel()

# --- إدارة الحالة (Session State) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'temp_items' not in st.session_state: st.session_state.temp_items = []
if 'widget_id' not in st.session_state: st.session_state.widget_id = 0

USERS = {"عبد الكريم حوراني": "9900", "محمد الحسيني": "8822", "علي دوغان": "5500", "عزات حلاوي": "6611", "علي حسين حلباوي": "4455", "محمد حسين حلباوي": "3366", "احمد حسين حلباوي": "7722", "علي محمد حلباوي": "6600"}

# --- التنقل بين الصفحات ---

if not st.session_state.logged_in:
    st.markdown('<div class="header-box"><h1>🔐 دخول المندوبين</h1></div>', unsafe_allow_html=True)
    user_sel = st.selectbox("إختر اسمك", ["-- اختر --"] + list(USERS.keys()))
    pwd = st.text_input("كلمة السر", type="password")
    if st.button("دخول", use_container_width=True):
        if USERS.get(user_sel) == pwd:
            st.session_state.logged_in, st.session_state.user_name, st.session_state.page = True, user_sel, 'home'
            st.rerun()

elif st.session_state.page == 'home':
    st.markdown(f'<div class="header-box"><h3>أهلاً بك سيد {st.session_state.user_name}</h3></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 فاتورة جديدة", use_container_width=True, type="primary"):
            st.session_state.page, st.session_state.temp_items = 'order', []
            st.session_state.inv_no = get_next_invoice_number()
            st.rerun()
    with col2:
        if st.button("🛠️ إدارة الطلبيات", use_container_width=True):
            st.session_state.page = 'stock_manager'
            st.rerun()

elif st.session_state.page == 'order':
    st.markdown(f'<div class="header-box"><h3>فاتورة مبيعات #{st.session_state.inv_no}</h3></div>', unsafe_allow_html=True)
    
    cust_dict = load_rep_customers(st.session_state.user_name)
    sel_c = st.selectbox("اختر الزبون", ["-- اختر --"] + list(cust_dict.keys()))
    
    st.divider()
    search_p = st.text_input("🔍 ابحث عن صنف...")
    f_p = [p for p in PRODUCTS.keys() if search_p.lower() in p.lower()] if search_p else list(PRODUCTS.keys())
    sel_p = st.selectbox("الصنف", ["-- اختر --"] + f_p, key=f"p_{st.session_state.widget_id}")
    qty = st.number_input("الكمية", min_value=1, step=1)
    
    if st.button("➕ إضافة للفاتورة", use_container_width=True):
        if sel_p != "-- اختر --":
            st.session_state.temp_items.append({"الصنف": sel_p, "العدد": qty, "السعر": PRODUCTS[sel_p]})
            st.session_state.widget_id += 1
            st.rerun()
            
    if st.session_state.temp_items:
        st.write("---")
        for i, item in enumerate(st.session_state.temp_items):
            st.write(f"✅ {item['الصنف']} - العدد: {item['العدد']}")

    if st.button("🔙 عودة للرئيسية", use_container_width=True):
        st.session_state.page = 'home'
        st.rerun()

elif st.session_state.page == 'stock_manager':
    st.markdown('<div class="central-header"><h1>🛠️ نظام إدارة الطلبيات المركزي</h1></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="status-box">📦 طلبات معلقة لـ {st.session_state.user_name}</div>', unsafe_allow_html=True)
    
    # محاكاة الجدول كما في الصورة المطلوبة
    data = {
        "الحالة": ["بانتظار التصديق"] * 2,
        "الكمية": [10, 15],
        "اسم الصنف": ["حمص 9", "بهار حلو"],
        "التاريخ": [datetime.now().strftime("%Y-%m-%d")] * 2
    }
    st.table(pd.DataFrame(data))
    
    if st.button("🔙 عودة للرئيسية", use_container_width=True):
        st.session_state.page = 'home'
        st.rerun()
