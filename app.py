import streamlit as st
import pandas as pd
import json
import random
import urllib.parse
from datetime import datetime
import requests
import gspread
from google.oauth2.service_account import Credentials

# --- 1. إعدادات التنسيق والهوية ---
LOGO_FILE = "Lgo.png"
st.set_page_config(page_title="شركة حلباوي إخوان", layout="centered", page_icon=LOGO_FILE)

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;800&display=swap');
    html, body, [class*="css"] {{ font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }}
    .header-box {{ background-color: #1E3A8A; color: white; text-align: center; padding: 10px; border-radius: 10px; margin-bottom: 20px;}}
    .total-final {{ background-color: #d4edda; font-size: 22px; font-weight: 800; color: #155724; border: 2px solid #c3e6cb; margin-top: 10px; padding: 10px; text-align: center; }}
    .item-label {{ background-color: #1E3A8A; color: white; padding: 12px; border-radius: 8px; font-weight: bold; text-align: right; font-size: 18px; margin-top:5px; }}
    .wa-button {{ background-color: #25d366; color: white; padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 20px; display: block; width: 100%; text-decoration: none; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. إعدادات البيانات والاتصال ---
SHEET_ID = "1-Abj-Kvbe02az8KYZfQL0eal2arKw_wgjVQdJX06IA0"
GID_PRICES = "339292430"
GID_CUSTOMERS = "155973706"

def get_gspread_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        raw_json = st.secrets["gcp_service_account"]["json_data"].strip()
        info = json.loads(raw_json, strict=False)
        creds = Credentials.from_service_account_info(info, scopes=scope)
        return gspread.authorize(creds)
    except: return None

@st.cache_data(ttl=60)
def load_products_list():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote('طلبات')}"
    try:
        df = pd.read_csv(url, header=None).dropna(how='all').iloc[:, :5]
        df.columns = ['cat', 'pack', 'sub', 'name', 'sci']
        return df
    except: return None

# --- إدارة الحالة (Session State) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'cart_stock' not in st.session_state: st.session_state.cart_stock = {}
if 'temp_items' not in st.session_state: st.session_state.temp_items = []

USERS = {"عبد الكريم حوراني": "9900", "محمد الحسيني": "8822", "علي دوغان": "5500", "عزات حلاوي": "6611", "علي حسين حلباوي": "4455", "محمد حسين حلباوي": "3366", "احمد حسين حلباوي": "7722", "علي محمد حلباوي": "6600"}

st.image(LOGO_FILE, use_container_width=True)

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
        if st.button("📝 فاتورة جديدة", use_container_width=True, type="primary"):
            st.session_state.page = 'billing'
            st.rerun()
    with col2:
        if st.button("🔄 تسجيل مرتجع", use_container_width=True):
            st.session_state.page = 'billing' # يتم ضبط حالة المرتجع داخل واجهة الفاتورة
            st.rerun()
            
    st.divider()
    if st.button("📦 طلب بضاعة للمستودع (طلب تحميل)", use_container_width=True):
        st.session_state.page = 'stock_order_home'
        st.rerun()

# --- قسم طلب البضاعة (STOCK ORDER) ---
elif st.session_state.page == 'stock_order_home':
    st.markdown('<div class="header-box"><h1>📦 طلب بضاعة للمستودع</h1></div>', unsafe_allow_html=True)
    df_stock = load_products_list()
    
    if df_stock is not None:
        for c in df_stock['cat'].unique():
            if st.button(f"📂 قسم {c}", use_container_width=True):
                st.session_state.sel_cat = c
                st.session_state.page = 'stock_order_details'
                st.rerun()
        
        st.divider()
        if st.session_state.cart_stock:
            if st.button("🛒 مراجعة الطلبية وتثبيتها", use_container_width=True, type="primary"):
                st.session_state.page = 'stock_review'
                st.rerun()
    
    if st.button("🔙 العودة للرئيسية"):
        st.session_state.page = 'home'
        st.rerun()

elif st.session_state.page == 'stock_order_details':
    cat = st.session_state.sel_cat
    st.markdown(f'<div class="header-box"><h1>قسم {cat}</h1></div>', unsafe_allow_html=True)
    
    df_stock = load_products_list()
    cat_df = df_stock[df_stock['cat'] == cat]
    
    for weight in cat_df['pack'].unique():
        with st.expander(f"🔽 {weight}", expanded=True):
            w_df = cat_df[cat_df['pack'] == weight]
            for _, row in w_df.iterrows():
                st.markdown(f'<div class="item-label">{row["name"]}</div>', unsafe_allow_html=True)
                key = f"stk_{row['name']}"
                curr = st.session_state.cart_stock.get(key, {}).get('qty', "")
                val = st.text_input("العدد المطلوب", value=curr, key=key)
                if val: st.session_state.cart_stock[key] = {'name': row['name'], 'qty': val}
    
    if st.button("✅ حفظ والعودة للأقسام"):
        st.session_state.page = 'stock_order_home'
        st.rerun()

elif st.session_state.page == 'stock_review':
    st.markdown('<div class="header-box"><h1>مراجعة طلبية المستودع</h1></div>', unsafe_allow_html=True)
    final_items = []
    for k, v in st.session_state.cart_stock.items():
        st.write(f"✅ {v['name']} : {v['qty']}")
        final_items.append(v)
    
    if st.button("🚀 إرسال الطلب للشركة", use_container_width=True, type="primary"):
        client = get_gspread_client()
        if client:
            sheet = client.open_by_key(SHEET_ID).worksheet(st.session_state.user_name)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            rows = [[now_str, i['name'], i['qty'], "بانتظار التصديق"] for i in final_items]
            sheet.append_rows(rows)
            st.success("✅ تم إرسال الطلب بنجاح!")
            st.session_state.cart_stock = {}
            # رابط واتساب
            order_text = f"طلبية مستودع: {st.session_state.user_name}\n" + "\n".join([f"{i['name']}: {i['qty']}" for i in final_items])
            url_wa = f"https://api.whatsapp.com/send?phone=9613220893&text={urllib.parse.quote(order_text)}"
            st.markdown(f'<a href="{url_wa}" target="_blank" class="wa-button">إرسال عبر واتساب ✅</a>', unsafe_allow_html=True)

    if st.button("🔙 العودة"):
        st.session_state.page = 'stock_order_home'
        st.rerun()

# --- قسم الفاتورة (BILLING) ---
elif st.session_state.page == 'billing':
    st.markdown('<div class="header-box"><h1>📄 نظام الفواتير</h1></div>', unsafe_allow_html=True)
    st.info("هنا واجهة الفواتير كما كانت في كودك الأصلي...")
    if st.button("🔙 العودة للرئيسية"):
        st.session_state.page = 'home'
        st.rerun()
