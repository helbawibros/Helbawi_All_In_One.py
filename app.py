import streamlit as st
import pandas as pd
import json
import urllib.parse
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import os

# --- 1. إعدادات الهوية والتنسيق (النسخة الأصلية) ---
LOGO_FILE = "Lgo.png"
st.set_page_config(page_title="شركة حلباوي إخوان", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .header-box { background-color: #1E3A8A; color: white; text-align: center; padding: 15px; border-radius: 10px; border-bottom: 5px solid #fca311; }
    .item-label { background-color: #1E3A8A; color: white; padding: 10px; border-radius: 8px; font-weight: bold; margin-top: 5px; }
    .total-final { background-color: #ffffcc; color: #000; font-size: 24px; font-weight: bold; padding: 15px; border: 2px solid #fca311; text-align: center; border-radius: 10px; }
    .wa-button { background-color: #25d366; color: white; padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; display: block; text-decoration: none; font-size: 22px; }
    input { background-color: #ffffcc !important; font-weight: bold !important; font-size: 20px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. جلب البيانات ---
SHEET_ID = "1-Abj-Kvbe02az8KYZfQL0eal2arKw_wgjVQdJX06IA0"

@st.cache_data(ttl=60)
def load_all_data():
    # جلب الأسعار والزبائن والطلبات
    p_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=339292430"
    c_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=155973706"
    s_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=طلبات"
    return pd.read_csv(p_url), pd.read_csv(c_url), pd.read_csv(s_url, header=None)

df_p, df_c, df_s = load_all_data()

# --- إدارة الحالة ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'cart_invoice' not in st.session_state: st.session_state.cart_invoice = []
if 'cart_stock' not in st.session_state: st.session_state.cart_stock = {}

USERS = {"عبد الكريم حوراني": "9900", "محمد الحسيني": "8822", "علي دوغان": "5500", "عزات حلاوي": "6611", "علي حسين حلباوي": "4455", "محمد حسين حلباوي": "3366", "احمد حسين حلباوي": "7722", "علي محمد حلباوي": "6600"}

# --- الواجهات ---
if st.session_state.page == 'login':
    st.markdown('<div class="header-box"><h1>🔐 دخول المندوبين</h1></div>', unsafe_allow_html=True)
    user = st.selectbox("إختر اسمك", ["-- اختر --"] + list(USERS.keys()))
    pwd = st.text_input("كلمة السر", type="password")
    if st.button("دخول", use_container_width=True):
        if USERS.get(user) == pwd:
            st.session_state.user_name = user
            st.session_state.page = 'home'
            st.rerun()

elif st.session_state.page == 'home':
    if os.path.exists(LOGO_FILE): st.image(LOGO_FILE)
    st.markdown(f'<div class="header-box"><h3>أهلاً {st.session_state.user_name}</h3></div>', unsafe_allow_html=True)
    
    if st.button("📝 فاتورة جديدة (دزينات وأسعار)", use_container_width=True):
        st.session_state.page = 'billing'
        st.rerun()
    
    st.divider()
    
    if st.button("📦 طلب بضاعة للمستودع (بالأقسام)", use_container_width=True):
        st.session_state.page = 'stock_home'
        st.rerun()

# --- قسم الفوترة (بشكلها الأصلي الذي تحبه) ---
elif st.session_state.page == 'billing':
    st.markdown('<div class="header-box"><h1>📝 فاتورة مبيعات</h1></div>', unsafe_allow_html=True)
    
    # فلترة الزبائن حسب المندوب
    rep_customers = df_c[df_c.iloc[:, 0] == st.session_state.user_name].iloc[:, 1].tolist()
    cust = st.selectbox("الزبون", rep_customers)
    
    # اختيار الصنف والكمية بالدزينة
    prod_list = df_p.iloc[:, 0].tolist()
    item = st.selectbox("الصنف", prod_list)
    col_q1, col_q2 = st.columns(2)
    with col_q1: doz = st.number_input("دزينة", step=1, value=0)
    with col_q2: unit = st.number_input("حبة", step=1, value=0)
    
    if st.button("➕ إضافة للفاتورة"):
        price = df_p[df_p.iloc[:, 0] == item].iloc[0, 1]
        total_units = (doz * 12) + unit
        st.session_state.cart_invoice.append({"item": item, "qty": total_units, "price": price, "display": f"{doz} دزينة و {unit} حبة"})

    # عرض الفاتورة والطباعة
    if st.session_state.cart_invoice:
        st.markdown("### 📋 المعاينة")
        total_invoice = 0
        for i in st.session_state.cart_invoice:
            line_total = i['qty'] * (i['price']/12)
            total_invoice += line_total
            st.write(f"✅ {i['item']} | {i['display']} | الإجمالي: {line_total:,.2f}$")
        
        st.markdown(f'<div class="total-final">صافي الفاتورة: {total_invoice:,.2f}$</div>', unsafe_allow_html=True)
        
        if st.button("🔙 العودة للرئيسية"):
            st.session_state.page = 'home'
            st.rerun()

# --- قسم طلب البضاعة (الذي أرسلته أنت بالأقسام) ---
elif st.session_state.page == 'stock_home':
    st.markdown('<div class="header-box"><h1>📦 طلب بضاعة للمستودع</h1></div>', unsafe_allow_html=True)
    cats = df_s.iloc[:, 0].unique()
    for c in cats:
        if st.button(f"📂 قسم {c}", use_container_width=True):
            st.session_state.sel_cat = c
            st.session_state.page = 'stock_details'
            st.rerun()
    if st.button("🏠 عودة"): st.session_state.page = 'home'; st.rerun()

elif st.session_state.page == 'stock_details':
    st.subheader(f"قسم {st.session_state.sel_cat}")
    items_in_cat = df_s[df_s[0] == st.session_state.sel_cat]
    for _, row in items_in_cat.iterrows():
        st.markdown(f'<div class="item-label">{row[3]}</div>', unsafe_allow_html=True)
        q = st.text_input("العدد", key=f"stock_{row[3]}")
        if q: st.session_state.cart_stock[row[3]] = q
    
    if st.button("✅ حفظ"): st.session_state.page = 'stock_home'; st.rerun()

