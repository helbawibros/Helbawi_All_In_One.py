import streamlit as st
import pandas as pd
import json
from datetime import datetime
import requests
import gspread
from google.oauth2.service_account import Credentials

# --- الإعدادات الأساسية ---
st.set_page_config(page_title="Helbawi Sales Pro", layout="centered")

def get_gspread_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        raw_json = st.secrets["gcp_service_account"]["json_data"].strip()
        service_account_info = json.loads(raw_json, strict=False)
        creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
        return gspread.authorize(creds)
    except: return None

SHEET_ID = "1-Abj-Kvbe02az8KYZfQL0eal2arKw_wgjVQdJX06IA0"
GID_PRICES = "339292430"

# --- واجهة المستخدم ---
if 'page' not in st.session_state: st.session_state.page = 'main'
if 'cart_order' not in st.session_state: st.session_state.cart_order = {}

st.title("🚀 تطبيق حلباوي المتكامل")
st.write(f"المندوب: {st.session_state.get('user_name', 'عام')}")

# --- القائمة الرئيسية ---
if st.session_state.page == 'main':
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 فاتورة مبيعات", use_container_width=True):
            st.session_state.page = 'billing'
            st.rerun()
            
    with col2:
        if st.button("📦 طلب بضاعة (المستودع)", use_container_width=True):
            st.session_state.page = 'stock_order'
            st.rerun()
    
    st.markdown("---")
    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# --- قسم طلب البضاعة (الذي نجحنا فيه اليوم) ---
elif st.session_state.page == 'stock_order':
    st.header("📦 طلب بضاعة جديد")
    
    # تحميل الأصناف من صفحة "اسعار"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={GID_PRICES}"
    df_prices = pd.read_csv(url)
    products = df_prices.iloc[:, 1].tolist()
    
    selected_prod = st.selectbox("اختر الصنف", ["-- اختر --"] + products)
    quantity = st.number_input("الكمية المطلوبة", min_value=1, step=1)
    
    if st.button("➕ إضافة للطلبية"):
        if selected_prod != "-- اختر --":
            st.session_state.cart_order[selected_prod] = quantity
            st.toast(f"تم إضافة {selected_prod}")

    if st.session_state.cart_order:
        st.write("### مراجعة الطلب:")
        for p, q in st.session_state.cart_order.items():
            st.write(f"🔹 {p} : {q}")
        
        if st.button("🚀 إرسال الطلبية الآن"):
            client = get_gspread_client()
            if client:
                try:
                    # نستخدم اسم المندوب المسجل للدخول كاسم للصفحة
                    rep_name = st.session_state.get('user_name', 'عبد الكريم حوراني') 
                    sheet = client.open_by_key(SHEET_ID).worksheet(rep_name)
                    
                    rows = [[datetime.now().strftime("%Y-%m-%d %H:%M"), p, q, "بانتظار التصديق"] 
                            for p, q in st.session_state.cart_order.items()]
                    
                    sheet.append_rows(rows)
                    st.success("✅ تم إرسال الطلب لبرنامج الإدارة بنجاح!")
                    st.session_state.cart_order = {}
                except Exception as e:
                    st.error(f"فشل الإرسال: تأكد من وجود صفحة باسمك")
    
    if st.button("🔙 العودة للقائمة"):
        st.session_state.page = 'main'
        st.rerun()

# --- قسم الفوترة (billing) يتم دمجه هنا بنفس الطريقة ---
elif st.session_state.page == 'billing':
    st.header("📄 نظام الفواتير")
    st.info("هنا نضع كود الفوترة الذي عملنا عليه سابقاً...")
    if st.button("🔙 العودة"):
        st.session_state.page = 'main'
        st.rerun()
