import streamlit as st
import pandas as pd
import json
import urllib.parse
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import os

# --- 1. إعدادات الصفحة والهوية ---
LOGO_FILE = "Lgo.png"
st.set_page_config(page_title="نظام حلباوي المتكامل", layout="centered")

# دالة الربط مع جوجل شيت (النسخة الاحترافية)
def get_gsheet_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        raw_json = st.secrets["gcp_service_account"]["json_data"].strip()
        service_account_info = json.loads(raw_json, strict=False)
        creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

# --- 2. جلب البيانات (الأسعار، الزبائن، الأصناف) ---
SHEET_ID = "1-Abj-Kvbe02az8KYZfQL0eal2arKw_wgjVQdJX06IA0"

@st.cache_data(ttl=1)
def load_all_system_data():
    try:
        # رابط الأسعار (Sheet Prices)
        p_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=339292430"
        # رابط الزبائن (Sheet Customers)
        c_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=155973706"
        # رابط طلبات المستودع (Sheet طلبات)
        s_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote('طلبات')}"
        
        return pd.read_csv(p_url), pd.read_csv(c_url), pd.read_csv(s_url, header=None)
    except:
        return None, None, None

df_prices, df_customers, df_stock_items = load_all_system_data()

# --- 3. التنسيق الجمالي (CSS الأصلي) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;800&display=swap');
    html, body, [class*="st-"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .main-header { background-color: #1E3A8A; color: white; text-align: center; padding: 20px; border-radius: 15px; border-bottom: 5px solid #fca311; margin-bottom: 20px; }
    .info-box { background-color: #1c2333; padding: 15px; border-radius: 10px; border: 1px solid #2d3748; color: white; margin-bottom: 20px; }
    .item-label { background-color: #1E3A8A; color: white; padding: 12px; border-radius: 8px; font-weight: bold; font-size: 18px; margin-top: 10px; }
    .total-final { background-color: #ffffcc; color: black; padding: 20px; border-radius: 10px; border: 3px solid #fca311; text-align: center; font-size: 26px; font-weight: bold; }
    input { background-color: #ffffcc !important; color: black !important; font-weight: bold !important; font-size: 20px !important; }
    .wa-button { background-color: #25d366; color: white; padding: 18px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 22px; display: block; text-decoration: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. إدارة الحالة (Session State) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'invoice_items' not in st.session_state: st.session_state.invoice_items = []
if 'stock_cart' not in st.session_state: st.session_state.stock_cart = {}

USERS = {"عبد الكريم حوراني": "9900", "محمد الحسيني": "8822", "علي دوغان": "5500", "عزات حلاوي": "6611", "علي حسين حلباوي": "4455", "محمد حسين حلباوي": "3366", "احمد حسين حلباوي": "7722", "علي محمد حلباوي": "6600"}

# --- 5. منطق الواجهات ---

# شاشة الدخول
if not st.session_state.logged_in:
    st.markdown('<div class="main-header"><h1>🔐 نظام مندوبي حلباوي</h1></div>', unsafe_allow_html=True)
    user_sel = st.selectbox("👤 اختر الاسم", ["-- اختر --"] + list(USERS.keys()))
    pwd = st.text_input("🔑 كلمة السر", type="password")
    if st.button("دخول"):
        if USERS.get(user_sel) == pwd:
            st.session_state.logged_in = True
            st.session_state.user_name = user_sel
            st.session_state.page = 'home'
            st.rerun()
        else:
            st.error("⚠️ كلمة السر غير صحيحة")

# الشاشة الرئيسية
elif st.session_state.page == 'home':
    if os.path.exists(LOGO_FILE): st.image(LOGO_FILE)
    st.markdown(f'<div class="main-header"><h1>أهلاً سيد {st.session_state.user_name}</h1></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 فاتورة مبيعات جديدة", use_container_width=True):
            st.session_state.page = 'billing'
            st.rerun()
    with col2:
        if st.button("📦 طلب تحميل (مستودع)", use_container_width=True):
            st.session_state.page = 'stock_main'
            st.rerun()

# --- واجهة الفوترة (بكامل تفاصيلها الأصلية) ---
elif st.session_state.page == 'billing':
    st.markdown('<div class="main-header"><h1>📄 إنشاء فاتورة</h1></div>', unsafe_allow_html=True)
    
    # اختيار الزبون (مفلتر حسب المندوب)
    rep_custs = df_customers[df_customers.iloc[:, 0].astype(str).str.strip() == st.session_state.user_name.strip()].iloc[:, 1].tolist()
    customer = st.selectbox("🏠 اختر الزبون", rep_custs)
    discount = st.number_input("💰 حسم الفاتورة %", min_value=0.0, step=0.5)
    
    st.divider()
    
    # اختيار الصنف (بالدزينات)
    items_list = df_prices.iloc[:, 0].tolist()
    selected_item = st.selectbox("📦 الصنف", items_list)
    
    c1, c2 = st.columns(2)
    with c1: doz = st.number_input("دزينة", min_value=0, step=1)
    with c2: unit = st.number_input("حبة", min_value=0, step=1)
    
    if st.button("➕ إضافة للصنف"):
        price_per_doz = df_prices[df_prices.iloc[:, 0] == selected_item].iloc[0, 1]
        total_units = (doz * 12) + unit
        if total_units > 0:
            st.session_state.invoice_items.append({
                "name": selected_item,
                "doz": doz,
                "unit": unit,
                "total_units": total_units,
                "price_doz": price_per_doz
            })
            st.success("تمت الإضافة")

    # عرض المعاينة
    if st.session_state.invoice_items:
        st.markdown("### 📋 معاينة الفاتورة")
        grand_total = 0
        for i, entry in enumerate(st.session_state.invoice_items):
            line_price = (entry['total_units'] / 12) * entry['price_doz']
            grand_total += line_price
            st.write(f"🔹 {entry['name']} | {entry['doz']} دزينة و {entry['unit']} حبة | {line_price:,.2f}$")
        
        final_total = grand_total * (1 - discount/100)
        st.markdown(f'<div class="total-final">الإجمالي الصافي: {final_total:,.2f}$</div>', unsafe_allow_html=True)
        
        if st.button("🗑️ تفريغ الفاتورة"):
            st.session_state.invoice_items = []
            st.rerun()

    if st.button("🏠 عودة للرئيسية"):
        st.session_state.page = 'home'
        st.rerun()

# --- واجهة طلبات المستودع (بالأقسام) ---
elif st.session_state.page == 'stock_main':
    st.markdown('<div class="main-header"><h1>📦 طلب تحميل بضاعة</h1></div>', unsafe_allow_html=True)
    
    if df_stock_items is not None:
        df_stock_items.columns = ['cat', 'pack', 'sub', 'name', 'sci']
        for category in df_stock_items['cat'].unique():
            if st.button(f"📂 قسم {category}", use_container_width=True):
                st.session_state.current_cat = category
                st.session_state.page = 'stock_items'
                st.rerun()
    
    if st.button("🛒 مراجعة طلب التحميل"):
        st.session_state.page = 'stock_review'
        st.rerun()
    
    if st.button("🏠 عودة"):
        st.session_state.page = 'home'
        st.rerun()

elif st.session_state.page == 'stock_items':
    st.markdown(f'<div class="main-header"><h1>قسم {st.session_state.current_cat}</h1></div>', unsafe_allow_html=True)
    
    cat_df = df_stock_items[df_stock_items['cat'] == st.session_state.current_cat]
    for _, row in cat_df.iterrows():
        st.markdown(f'<div class="item-label">{row["name"]} ({row["pack"]})</div>', unsafe_allow_html=True)
        q_key = f"q_{row['name']}"
        val = st.text_input("الكمية المطلوب تحميلها", key=q_key)
        if val: st.session_state.stock_cart[row['name']] = val
    
    if st.button("✅ حفظ والعودة للأقسام"):
        st.session_state.page = 'stock_main'
        st.rerun()

elif st.session_state.page == 'stock_review':
    st.markdown('<div class="main-header"><h1>🛒 مراجعة طلب التحميل</h1></div>', unsafe_allow_html=True)
    
    summary = []
    for name, qty in st.session_state.stock_cart.items():
        st.write(f"✅ {name} : {qty}")
        summary.append(f"{name}: {qty}")
    
    if st.button("🚀 إرسال وتحديث الجرد"):
        client = get_gsheet_client()
        if client:
            sheet = client.open_by_key(SHEET_ID).worksheet(st.session_state.user_name)
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            rows = [[now, name, qty, "بانتظار التصديق"] for name, qty in st.session_state.stock_cart.items()]
            sheet.append_rows(rows)
            st.success("✅ تم تحديث الإكسل بنجاح")
            
            # رابط واتساب
            msg = f"طلبية تحميل: {st.session_state.user_name}\n" + "\n".join(summary)
            url = f"https://api.whatsapp.com/send?phone=9613220893&text={urllib.parse.quote(msg)}"
            st.markdown(f'<a href="{url}" target="_blank" class="wa-button">إرسال عبر واتساب الآن ✅</a>', unsafe_allow_html=True)

    if st.button("🔙 عودة"):
        st.session_state.page = 'stock_main'
        st.rerun()
