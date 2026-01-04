import streamlit as st
import pandas as pd
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Helbawi Sales Pro", layout="centered")

# --- دالة الاتصال بجوجل ---
def get_gspread_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        raw_json = st.secrets["gcp_service_account"]["json_data"].strip()
        info = json.loads(raw_json, strict=False)
        creds = Credentials.from_service_account_info(info, scopes=scope)
        return gspread.authorize(creds)
    except: return None

# بيانات الملف الأساسية
SHEET_ID = "1-Abj-Kvbe02az8KYZfQL0eal2arKw_wgjVQdJX06IA0"

# --- الحالة الداخلية للبرنامج ---
if 'page' not in st.session_state: st.session_state.page = 'main'
if 'cart' not in st.session_state: st.session_state.cart = {}

st.title("🚀 تطبيق حلباوي الشامل")

# --- الصفحة الرئيسية ---
if st.session_state.page == 'main':
    st.subheader("اختر العملية المطلوبة:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 فاتورة مبيعات", use_container_width=True):
            st.session_state.page = 'billing'
            st.rerun()
    with col2:
        if st.button("📦 طلب بضاعة للمندوب", use_container_width=True):
            st.session_state.page = 'stock_order'
            st.rerun()

# --- قسم طلب البضاعة ---
elif st.session_state.page == 'stock_order':
    st.header("📦 طلب بضاعة للمستودع")
    # تحميل الأصناف من صفحة اسعار
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=339292430"
        df_prices = pd.read_csv(url)
        products = df_prices.iloc[:, 1].tolist()
        
        selected_prod = st.selectbox("اختر الصنف", ["-- اختر --"] + products)
        qty = st.number_input("الكمية", min_value=1, step=1)
        
        if st.button("➕ إضافة للطلبية"):
            if selected_prod != "-- اختر --":
                st.session_state.cart[selected_prod] = qty
                st.toast(f"تم إضافة {selected_prod}")
        
        if st.session_state.cart:
            st.write("---")
            for p, q in st.session_state.cart.items():
                st.write(f"🔹 {p}: {q}")
            
            if st.button("🚀 إرسال الطلب النهائي"):
                client = get_gspread_client()
                if client:
                    # نرسل الطلب لصفحة المندوب (مثلاً عبد الكريم حوراني)
                    # يمكنك تغيير الاسم هنا ليكون ديناميكياً لاحقاً
                    sheet = client.open_by_key(SHEET_ID).worksheet("عبد الكريم حوراني")
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    rows = [[now, p, q, "بانتظار التصديق"] for p, q in st.session_state.cart.items()]
                    sheet.append_rows(rows)
                    st.success("✅ تم إرسال الطلب بنجاح!")
                    st.session_state.cart = {}
    except:
        st.error("خطأ في تحميل البيانات")

    if st.button("🔙 العودة"):
        st.session_state.page = 'main'
        st.rerun()

# --- قسم الفاتورة ---
elif st.session_state.page == 'billing':
    st.header("📄 نظام الفواتير")
    st.info("قسم الفواتير قيد العمل (سيتم ربطه بصفحة المبيعات)")
    if st.button("🔙 العودة"):
        st.session_state.page = 'main'
        st.rerun()
