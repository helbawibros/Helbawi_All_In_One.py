import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام طلبيات حلباوي", layout="centered")

# --- دالة الربط مع جوجل شيت (النظام الجديد) ---
def send_to_google_sheets(delegate_name, items_list):
    try:
        # إعداد التصاريح
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file('creds.json', scopes=scope)
        client = gspread.authorize(creds)
        
        # فتح ملف الإكسل (استخدمت الـ ID الخاص بك)
        sheet = client.open_by_key("1-Abj-Kvbe02az8KYZfQL0eal2arKw_wgjVQdJX06IA0")
        
        # الدخول للصفحة التي تحمل اسم المندوب
        try:
            worksheet = sheet.worksheet(delegate_name)
        except:
            st.error(f"⚠️ لم يتم العثور على صفحة باسم '{delegate_name}' في ملف الإكسل")
            return False

        # تحضير الأسطر للإرسال
        rows_to_append = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        for item in items_list:
            # ترتيب الأعمدة: التاريخ | اسم الصنف | الكمية | الحالة
            rows_to_append.append([now_str, item['name'], item['qty'], "بانتظار التصديق"])
        
        if rows_to_append:
            worksheet.append_rows(rows_to_append)
            return True
    except Exception as e:
        st.error(f"❌ فشل الاتصال بالإكسل: {e}")
        return False

# 2. جلب البيانات (للأصناف)
SHEET_ID = "1-Abj-Kvbe02az8KYZfQL0eal2arKw_wgjVQdJX06IA0"
SHEET_NAME = "طلبات"
DIRECT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(SHEET_NAME)}"

@st.cache_data(ttl=1)
def load_data():
    try:
        df = pd.read_csv(DIRECT_URL, header=None).dropna(how='all')
        df = df.iloc[:, :5]
        df.columns = ['cat', 'pack', 'sub', 'name', 'sci']
        return df
    except:
        return None

df = load_data()

# 3. التنسيق (نفس الستايل الخاص بك)
st.markdown("""
    <style>
    html, body, [class*="st-"], div, p, h1, h2, h3, button, input {
        font-family: 'Tahoma', 'Arial', sans-serif !important;
    }
    .stApp { background-color: #0E1117; color: white; direction: rtl; }
    .main-header { 
        background-color: #1E3A8A; text-align: center; padding: 25px 10px; 
        border-radius: 15px; border-bottom: 5px solid #fca311; margin-bottom: 20px; 
    }
    .main-header h1 { margin: 0; font-size: 28px !important; color: white; font-weight: bold; }
    .main-header p { margin: 5px 0 0 0; font-size: 18px; color: #fca311; }
    .info-box {
        background-color: #1c2333; padding: 12px; border-radius: 10px;
        border: 1px solid #2d3748; margin-bottom: 20px; text-align: right;
    }
    div.stButton > button {
        width: 100% !important; background-color: #fca311 !important;
        color: #1E3A8A !important; font-weight: bold !important;
        height: 65px !important; font-size: 22px !important;
        border-radius: 10px !important; border: none !important;
    }
    input { 
        background-color: #ffffcc !important; color: #000000 !important; 
        font-weight: bold !important; text-align: right !important;
        height: 55px !important; font-size: 20px !important;
    }
    .item-label { 
        background-color: #1E3A8A; color: white; padding: 12px; 
        border-radius: 8px; font-weight: bold; text-align: right; font-size: 18px;
    }
    .wa-button {
        background-color: #25d366; color: white; padding: 20px; 
        border-radius: 12px; text-align: center; font-weight: bold; 
        font-size: 24px; display: block; width: 100%; text-decoration: none; margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# إدارة الحالة
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'special_items' not in st.session_state: st.session_state.special_items = []
if 'page' not in st.session_state: st.session_state.page = 'home'
if 'cust_name' not in st.session_state: st.session_state.cust_name = ""

now = datetime.now().strftime("%Y-%m-%d | %H:%M")

if df is not None:
    if st.session_state.page == 'home':
        st.markdown('<div class="main-header"><h1>طلبيات المندوبين</h1><p>شركة حلباوي إخوان</p></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-box">🗓️ {now} <br> 👤 المندوب الحالي: {st.session_state.cust_name if st.session_state.cust_name else "---"}</div>', unsafe_allow_html=True)

        st.markdown("<p style='text-align:right; font-weight:bold;'>👤 اختر أو اكتب اسم المندوب (مطابق لاسم الصفحة):</p>", unsafe_allow_html=True)
        st.session_state.cust_name = st.text_input("n_in", value=st.session_state.cust_name, label_visibility="collapsed")
        
        st.markdown("<p style='text-align:right; font-weight:bold;'>📂 الأقسام:</p>", unsafe_allow_html=True)
        for c in df['cat'].unique():
            if st.button(f"📦 قسم {c}"):
                st.session_state.sel_cat = c
                st.session_state.page = 'details'
                st.rerun()
        
        if st.button("🌟 أصناف خاصة"):
            st.session_state.page = 'special'
            st.rerun()
        
        if st.session_state.cart or st.session_state.special_items:
            st.divider()
            if st.button("🛒 مراجعة الطلبية"):
                st.session_state.page = 'review'
                st.rerun()

    elif st.session_state.page == 'special':
        st.markdown('<div class="main-header"><h1>أصناف خاصة</h1></div>', unsafe_allow_html=True)
        if st.button("🏠 العودة للرئيسية"):
            st.session_state.page = 'home'
            st.rerun()
            
        st.markdown("<p style='text-align:right;'>اسم الصنف:</p>", unsafe_allow_html=True)
        sp_name = st.text_input("sp1", label_visibility="collapsed")
        st.markdown("<p style='text-align:right;'>التعبئة:</p>", unsafe_allow_html=True)
        sp_pack = st.text_input("sp2", label_visibility="collapsed")
        st.markdown("<p style='text-align:right;'>العدد:</p>", unsafe_allow_html=True)
        sp_qty = st.text_input("sp3", label_visibility="collapsed")
        
        if st.button("➕ إضافة للطلبية"):
            if sp_name and sp_qty:
                st.session_state.special_items.append({'name': sp_name, 'pack': sp_pack, 'qty': sp_qty})
                st.success("تمت الإضافة")
            else: st.error("أدخل الاسم والعدد")
        
        if st.button("🛒 مراجعة وتثبيت"):
            st.session_state.page = 'review'
            st.rerun()

    elif st.session_state.page == 'details':
        cat = st.session_state.sel_cat
        st.markdown(f'<div class="main-header"><h1>{cat}</h1></div>', unsafe_allow_html=True)
        if st.button("🏠 العودة للرئيسية"):
            st.session_state.page = 'home'
            st.rerun()

        cat_df = df[df['cat'] == cat]
        for weight in cat_df['pack'].unique():
            with st.expander(f"🔽 {weight}", expanded=True):
                w_df = cat_df[cat_df['pack'] == weight]
                for sub in w_df['sub'].unique():
                    st.markdown(f'<div style="color:#fca311; font-weight:bold; text-align:right; margin:10px 0;">{sub}</div>', unsafe_allow_html=True)
                    for _, row in w_df[w_df['sub'] == sub].iterrows():
                        st.markdown(f'<div class="item-label">{row["name"]}</div>', unsafe_allow_html=True)
                        key = f"q_{row['name']}_{row['pack']}"
                        curr = st.session_state.cart.get(key, {}).get('qty', "")
                        val = st.text_input("العدد", value=curr, key=key+"_v", label_visibility="collapsed")
                        if val: st.session_state.cart[key] = {'name': row['name'], 'qty': val}
                        elif val == "" and key in st.session_state.cart: del st.session_state.cart[key]
        
        if st.button("🛒 مراجعة وتثبيت"):
            st.session_state.page = 'review'
            st.rerun()

    elif st.session_state.page == 'review':
        st.markdown('<div class="main-header"><h1>مراجعة الطلبية</h1></div>', unsafe_allow_html=True)
        st.markdown(f"<div class='info-box'>👤 المندوب: {st.session_state.cust_name}</div>", unsafe_allow_html=True)
        
        final_list = []
        for k, v in st.session_state.cart.items():
            st.markdown(f"<p style='text-align:right; font-size:18px;'>✅ {v['name']} : <b>{v['qty']}</b></p>", unsafe_allow_html=True)
            final_list.append({'name': v['name'], 'qty': v['qty']})
            
        for item in st.session_state.special_items:
            disp = f"{item['name']} ({item['pack']})" if item['pack'] else item['name']
            st.markdown(f"<p style='text-align:right; font-size:18px;'>✅ {disp} : <b>{item['qty']}</b></p>", unsafe_allow_html=True)
            final_list.append({'name': disp, 'qty': item['qty']})
        
        st.divider()
        if st.button("🚀 إرسال الطلب للشركة وتحديث الجرد"):
            if st.session_state.cust_name:
                # 1. محاولة الإرسال لجوجل شيت
                with st.spinner('جاري تحديث الجرد في الإكسل...'):
                    success = send_to_google_sheets(st.session_state.cust_name, final_list)
                
                if success:
                    st.success("✅ تم تحديث جرد الفان بنجاح!")
                    # 2. تجهيز واتساب
                    order_text = f"طلبية: {st.session_state.cust_name}\nالتوقيت: {now}\n" + "\n".join([f"{i['name']}: {i['qty']}" for i in final_list])
                    url = f"https://api.whatsapp.com/send?phone=9613220893&text={urllib.parse.quote(order_text)}"
                    st.markdown(f'<a href="{url}" target="_blank" class="wa-button">إرسال عبر واتساب الآن ✅</a>', unsafe_allow_html=True)
            else: 
                st.error("⚠️ يرجى كتابة اسم المندوب أولاً في الصفحة الرئيسية")
