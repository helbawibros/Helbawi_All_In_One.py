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
st.set_page_config(page_title="شركة حلباوي إخوان", layout="centered", page_icon=LOGO_FILE)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .header-box { background-color: #1E3A8A; color: white; text-align: center; padding: 10px; border-radius: 10px; margin-bottom: 20px;}
    .item-label { background-color: #1E3A8A; color: white; padding: 12px; border-radius: 8px; font-weight: bold; text-align: right; font-size: 18px; margin-top:5px; }
    .wa-button { background-color: #25d366; color: white; padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 20px; display: block; width: 100%; text-decoration: none; margin-top: 10px; }
    .invoice-preview { background-color: white; padding: 25px; border: 2px solid #1E3A8A; border-radius: 10px; color: black; }
    .styled-table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 15px; text-align: center; color: black; }
    .styled-table th { background-color: #f0f2f6; color: black; padding: 10px; border: 1px solid #000; }
    .styled-table td { padding: 10px; border: 1px solid #000; }
    .total-final { background-color: #d4edda; font-size: 22px; font-weight: 800; color: #155724; border: 2px solid #c3e6cb; margin-top: 10px; padding: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إعدادات الربط مع Google Sheets ---
SHEET_ID = "1-Abj-Kvbe02az8KYZfQL0eal2arKw_wgjVQdJX06IA0"
GID_PRICES = "339292430"
GID_CUSTOMERS = "155973706"

def get_gspread_client():
    try:
        raw_json = st.secrets["gcp_service_account"]["json_data"].strip()
        info = json.loads(raw_json, strict=False)
        creds = Credentials.from_service_account_info(info, scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except: return None

@st.cache_data(ttl=60)
def load_customers(rep_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={GID_CUSTOMERS}"
        df = pd.read_csv(url)
        rep_df = df[df.iloc[:, 0].astype(str).str.strip() == rep_name.strip()]
        return {f"{row.iloc[1]} ({row.iloc[2]})": row.iloc[1] for _, row in rep_df.iterrows()}
    except: return {}

@st.cache_data(ttl=60)
def load_products_pricing():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={GID_PRICES}"
    try:
        df_p = pd.read_csv(url)
        return pd.Series(df_p.iloc[:, 1].values, index=df_p.iloc[:, 0]).to_dict()
    except: return {}

@st.cache_data(ttl=1)
def load_stock_categories():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote('طلبات')}"
    try:
        df = pd.read_csv(url, header=None).dropna(how='all').iloc[:, :5]
        df.columns = ['cat', 'pack', 'sub', 'name', 'sci']
        return df
    except: return None

# --- إدارة الحالة والمستخدمين ---
USERS = {"عبد الكريم حوراني": "9900", "محمد الحسيني": "8822", "علي دوغان": "5500", "عزات حلاوي": "6611", "علي حسين حلباوي": "4455", "محمد حسين حلباوي": "3366", "احمد حسين حلباوي": "7722", "علي محمد حلباوي": "6600"}

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'temp_items' not in st.session_state: st.session_state.temp_items = []
if 'cart_stock' not in st.session_state: st.session_state.cart_stock = {}

if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, use_container_width=True)

# --- الواجهات ---
if not st.session_state.logged_in:
    st.markdown('<div class="header-box"><h1>🔐 دخول المندوبين</h1></div>', unsafe_allow_html=True)
    u = st.selectbox("إختر اسمك", ["-- اختر --"] + list(USERS.keys()))
    p = st.text_input("كلمة السر", type="password")
    if st.button("دخول", use_container_width=True):
        if USERS.get(u) == p:
            st.session_state.logged_in, st.session_state.user_name, st.session_state.page = True, u, 'home'
            st.rerun()

elif st.session_state.page == 'home':
    st.markdown(f'<div class="header-box"><h2>أهلاً سيد {st.session_state.user_name}</h2></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 فاتورة مبيعات", use_container_width=True, type="primary"):
            st.session_state.page, st.session_state.temp_items, st.session_state.is_return = 'billing', [], False
            st.rerun()
    with col2:
        if st.button("🔄 تسجيل مرتجع", use_container_width=True):
            st.session_state.page, st.session_state.temp_items, st.session_state.is_return = 'billing', [], True
            st.rerun()
    st.divider()
    if st.button("📦 طلب بضاعة للمستودع (تحميل)", use_container_width=True):
        st.session_state.page = 'stock_home'
        st.rerun()

# --- قسم الفوترة (القديم المطور) ---
elif st.session_state.page == 'billing':
    st.markdown(f'<div class="header-box"><h3>{"مرتجع" if st.session_state.is_return else "فاتورة"} مبيعات</h3></div>', unsafe_allow_html=True)
    customers = load_customers(st.session_state.user_name)
    prices = load_products_pricing()
    
    sel_c = st.selectbox("اختر الزبون", ["-- اختر --"] + list(customers.keys()))
    disc = st.number_input("الحسم %", 0.0)
    
    st.divider()
    sel_p = st.selectbox("الصنف", ["-- اختر --"] + list(prices.keys()))
    qty = st.number_input("الكمية", 1.0)
    if st.button("➕ إضافة"):
        if sel_p != "-- اختر --":
            st.session_state.temp_items.append({"name": sel_p, "qty": qty, "price": prices[sel_p]})
    
    if st.session_state.temp_items:
        st.markdown('<div class="invoice-preview">', unsafe_allow_html=True)
        rows_html = ""
        raw_total = 0
        for i in st.session_state.temp_items:
            line = i['qty'] * i['price']
            raw_total += line
            rows_html += f"<tr><td>{i['name']}</td><td>{i['qty']}</td><td>{i['price']}$</td><td>{line}$</td></tr>"
        
        final_net = raw_total * (1 - disc/100)
        st.markdown(f'<table class="styled-table"><tr><th>الصنف</th><th>الكمية</th><th>السعر</th><th>الإجمالي</th></tr>{rows_html}</table>', unsafe_allow_html=True)
        st.markdown(f'<div class="total-final">الإجمالي الصافي: {final_net:,.2f}$</div></div>', unsafe_allow_html=True)
    
    if st.button("🔙 عودة"): st.session_state.page = 'home'; st.rerun()

# --- نظام الطلبات الجديد (الأقسام) ---
elif st.session_state.page == 'stock_home':
    st.markdown('<div class="header-box"><h3>📦 طلب بضاعة للمستودع</h3></div>', unsafe_allow_html=True)
    df_s = load_stock_categories()
    if df_s is not None:
        for c in df_s['cat'].unique():
            if st.button(f"📂 قسم {c}", use_container_width=True):
                st.session_state.sel_cat, st.session_state.page = c, 'stock_details'
                st.rerun()
    if st.button("🔙 عودة"): st.session_state.page = 'home'; st.rerun()

elif st.session_state.page == 'stock_details':
    st.subheader(f"قسم {st.session_state.sel_cat}")
    df_s = load_stock_categories()
    cat_df = df_s[df_s['cat'] == st.session_state.sel_cat]
    for _, row in cat_df.iterrows():
        st.markdown(f'<div class="item-label">{row["name"]}</div>', unsafe_allow_html=True)
        q = st.text_input("الكمية", key=f"s_{row['name']}")
        if q: st.session_state.cart_stock[row['name']] = q
    
    if st.button("✅ حفظ والعودة"): st.session_state.page = 'stock_home'; st.rerun()
