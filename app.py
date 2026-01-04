import streamlit as st
import pandas as pd
import json
import random
import urllib.parse
from datetime import datetime
import requests
import gspread
from google.oauth2.service_account import Credentials
import os

# --- 1. إعدادات التنسيق والهوية ---
LOGO_FILE = "Lgo.png"

st.set_page_config(page_title="شركة حلباوي إخوان", layout="centered")

# التأكد من وجود اللوغو لتجنب الخطأ الذي ظهر في الصورة
if os.path.exists(LOGO_FILE):
    st.image(LOGO_FILE, use_container_width=True)
else:
    st.title("شركة حلباوي إخوان")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .header-box { background-color: #1E3A8A; color: white; text-align: center; padding: 10px; border-radius: 10px; margin-bottom: 20px;}
    .item-label { background-color: #1E3A8A; color: white; padding: 12px; border-radius: 8px; font-weight: bold; text-align: right; font-size: 18px; margin-top:5px; }
    .wa-button { background-color: #25d366; color: white; padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 20px; display: block; width: 100%; text-decoration: none; }
    .total-final { background-color: #d4edda; font-size: 22px; font-weight: 800; color: #155724; border: 2px solid #c3e6cb; margin-top: 10px; padding: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. البيانات والاتصال ---
SHEET_ID = "1-Abj-Kvbe02az8KYZfQL0eal2arKw_wgjVQdJX06IA0"

def get_gspread_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        raw_json = st.secrets["gcp_service_account"]["json_data"].strip()
        info = json.loads(raw_json, strict=False)
        creds = Credentials.from_service_account_info(info, scopes=scope)
        return gspread.authorize(creds)
    except: return None

@st.cache_data(ttl=60)
def load_stock_products():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote('طلبات')}"
    try:
        df = pd.read_csv(url, header=None).dropna(how='all').iloc[:, :5]
        df.columns = ['cat', 'pack', 'sub', 'name', 'sci']
        return df
    except: return None

# --- إدارة الحالة ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'cart_stock' not in st.session_state: st.session_state.cart_stock = {}

USERS = {"عبد الكريم حوراني": "9900", "محمد الحسيني": "8822", "علي دوغان": "5500", "عزات حلاوي": "6611", "علي حسين حلباوي": "4455", "محمد حسين حلباوي": "3366", "احمد حسين حلباوي": "7722", "علي محمد حلباوي": "6600"}

# --- الواجهات ---
if not st.session_state.logged_in:
    st.markdown('<div class="header-box"><h1>🔐 دخول المندوبين</h1></div>', unsafe_allow_html=True)
    user_sel = st.selectbox("إختر اسمك", ["-- اختر --"] + list(USERS.keys()))
    pwd = st.text_input("كلمة السر", type="password")
    if st.button("دخول", use_container_width=True):
        if USERS.get(user_sel) == pwd:
            st.session_state.logged_in, st.session_state.user_name, st.session_state.page = True, user_sel, 'home'
            st.rerun()

elif st.session_state.page == 'home':
    st.markdown(f'<div class="header-box"><h2>أهلاً بك سيد {st.session_state.user_name}</h2></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 فاتورة مبيعات / مرتجع", use_container_width=True):
            st.info("سيتم تحويلك لنظام الفواتير القديم...")
    with col2:
        if st.button("📦 طلب بضاعة (المستودع)", use_container_width=True, type="primary"):
            st.session_state.page = 'stock_order_home'
            st.rerun()

# --- نظام الطلبات (الأقسام) ---
elif st.session_state.page == 'stock_order_home':
    st.header("📦 اختيار القسم")
    df_s = load_stock_products()
    if df_s is not None:
        for c in df_s['cat'].unique():
            if st.button(f"📦 قسم {c}", use_container_width=True):
                st.session_state.sel_cat = c
                st.session_state.page = 'stock_details'
                st.rerun()
        if st.session_state.cart_stock:
            st.divider()
            if st.button("🛒 مراجعة وتثبيت الطلب", use_container_width=True, type="primary"):
                st.session_state.page = 'stock_review'
                st.rerun()
    if st.button("🔙 عودة"): st.session_state.page = 'home'; st.rerun()

elif st.session_state.page == 'stock_details':
    cat = st.session_state.sel_cat
    st.subheader(f"قسم {cat}")
    df_s = load_stock_products()
    cat_df = df_s[df_s['cat'] == cat]
    for weight in cat_df['pack'].unique():
        with st.expander(f"🔽 {weight}", expanded=True):
            for _, row in cat_df[cat_df['pack'] == weight].iterrows():
                st.markdown(f'<div class="item-label">{row["name"]}</div>', unsafe_allow_html=True)
                key = f"q_{row['name']}"
                qty = st.text_input("الكمية", key=key)
                if qty: st.session_state.cart_stock[key] = {'name': row['name'], 'qty': qty}
    if st.button("✅ حفظ والعودة"): st.session_state.page = 'stock_order_home'; st.rerun()

elif st.session_state.page == 'stock_review':
    st.header("🛒 مراجعة الطلب النهائي")
    items = []
    for k, v in st.session_state.cart_stock.items():
        st.write(f"🔹 {v['name']} : {v['qty']}")
        items.append(v)
    
    if st.button("🚀 إرسال للشركة", use_container_width=True):
        client = get_gspread_client()
        if client:
            sheet = client.open_by_key(SHEET_ID).worksheet(st.session_state.user_name)
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            rows = [[now, i['name'], i['qty'], "بانتظار التصديق"] for i in items]
            sheet.append_rows(rows)
            st.success("✅ تم الإرسال!")
            st.session_state.cart_stock = {}
            # رابط واتساب
            txt = f"طلبية: {st.session_state.user_name}\n" + "\n".join([f"{i['name']}: {i['qty']}" for i in items])
            url = f"https://api.whatsapp.com/send?phone=9613220893&text={urllib.parse.quote(txt)}"
            st.markdown(f'<a href="{url}" target="_blank" class="wa-button">إرسال واتساب</a>', unsafe_allow_html=True)
    if st.button("🔙 عودة"): st.session_state.page = 'stock_order_home'; st.rerun()
