import streamlit as st
import pandas as pd
import random
from datetime import datetime
import requests
import os
import json
import urllib.parse
import gspread
from google.oauth2.service_account import Credentials

# ضبط الوقت
os.environ['TZ'] = 'Asia/Beirut' 

# --- 1. إعدادات الهوية والتنسيق ---
LOGO_FILE = "IMG_6463.png"

st.set_page_config(
    page_title="شركة حلباوي إخوان", 
    layout="centered",
    page_icon=LOGO_FILE
)

# عرض اللوغو بعرض الشاشة
if os.path.exists(LOGO_FILE):
    st.image(LOGO_FILE, use_container_width=True)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    div[data-testid="InputInstructions"], div[data-baseweb="helper-text"] { display: none !important; }
    .header-box { background-color: #1E3A8A; color: white; text-align: center; padding: 10px; border-radius: 10px; margin-bottom: 20px;}
    .invoice-preview { background-color: white; padding: 25px; border: 2px solid #1E3A8A; border-radius: 10px; color: black; }
    .styled-table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 15px; text-align: center; color: black; }
    .styled-table th { background-color: #f0f2f6; color: black; padding: 10px; border: 1px solid #000; }
    .styled-table td { padding: 10px; border: 1px solid #000; }
    .total-final { background-color: #d4edda; font-size: 22px; font-weight: 800; color: #155724; border: 2px solid #c3e6cb; margin-top: 10px; padding: 10px; text-align: center; }
    .item-label { background-color: #1E3A8A; color: white; padding: 12px; border-radius: 8px; font-weight: bold; text-align: right; font-size: 18px; margin-top:5px;}
    .wa-button { background-color: #25d366; color: white; padding: 20px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 24px; display: block; width: 100%; text-decoration: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. دوال البيانات والربط ---
SHEET_ID = "1-Abj-Kvbe02az8KYZfQL0eal2arKw_wgjVQdJX06IA0"

def send_to_factory_sheets(delegate_name, items_list):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        raw_json = st.secrets["gcp_service_account"]["json_data"].strip()
        service_account_info = json.loads(raw_json, strict=False)
        creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID)
        target = delegate_name.strip()
        worksheet = sheet.worksheet(target)
        rows = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        for item in items_list:
            rows.append([now_str, item['name'], item['qty'], "بانتظار التصديق"])
        if rows: worksheet.append_rows(rows); return True
    except: return False

@st.cache_data(ttl=1)
def load_factory_products():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote('طلبات')}"
    try:
        df = pd.read_csv(url, header=None).dropna(how='all').iloc[:, :5]
        df.columns = ['cat', 'pack', 'sub', 'name', 'sci']
        return df
    except: return None

@st.cache_data(ttl=60)
def load_products_from_excel():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=339292430"
        df_p = pd.read_csv(url)
        df_p.columns = [c.strip() for c in df_p.columns]
        return pd.Series(df_p.iloc[:, 1].values, index=df_p.iloc[:, 0]).to_dict()
    except: return {}

@st.cache_data(ttl=60)
def load_rep_customers(rep_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=155973706"
        df = pd.read_csv(url)
        rep_df = df[df.iloc[:, 0].astype(str).str.strip() == rep_name.strip()]
        return {f"{row.iloc[1]} ({row.iloc[2]})": row.iloc[1] for _, row in rep_df.iterrows()}
    except: return {}

def get_next_invoice_number():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=0"
        df = pd.read_csv(url)
        if 'رقم الفاتوره' in df.columns:
            valid_nums = pd.to_numeric(df['رقم الفاتوره'], errors='coerce').dropna()
            if not valid_nums.empty: return str(int(valid_nums.max()) + 1)
        return "1001"
    except: return str(random.randint(10000, 99999))

def send_to_google_sheets(vat, total_pre, inv_no, customer, representative, date_time, is_ret=False):
    url = "https://script.google.com/macros/s/AKfycbzi3kmbVyg_MV1Nyb7FwsQpCeneGVGSJKLMpv2YXBJR05v8Y77-Ub2SpvViZWCCp1nyqA/exec"
    prefix = "(مرتجع) " if is_ret else ""
    data = {"vat_value": vat, "total_before": total_pre, "invoice_no": inv_no, "cust_name": f"{prefix}{customer}", "rep_name": representative, "date_full": date_time}
    try:
        requests.post(url, data=data, timeout=10)
        return True
    except: return False

def convert_ar_nav(text):
    n_map = {'٠':'0','١':'1','٢':'2','٣':'3','٤':'4','٥':'5','٦':'6','٧':'7','٨':'8','٩':'9'}
    return "".join(n_map.get(c, c) for c in text)

PRODUCTS = load_products_from_excel()
USERS = {"عبد الكريم حوراني": "9900", "محمد الحسيني": "8822", "علي دوغان": "5500", "عزات حلاوي": "6611", "علي حسين حلباوي": "4455", "محمد حسين حلباوي": "3366", "احمد حسين حلباوي": "7722", "علي محمد حلباوي": "6600"}

# --- 3. إدارة الحالة ---
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'special_items' not in st.session_state: st.session_state.special_items = []
if 'temp_items' not in st.session_state: st.session_state.temp_items = []
if 'widget_id' not in st.session_state: st.session_state.widget_id = 0
if 'confirmed' not in st.session_state: st.session_state.confirmed = False
if 'receipt_view' not in st.session_state: st.session_state.receipt_view = False
if 'is_sent' not in st.session_state: st.session_state.is_sent = False

# --- 4. الواجهات ---

if not st.session_state.logged_in:
    st.markdown('<div class="header-box"><h1>🔐 دخول المندوبين</h1></div>', unsafe_allow_html=True)
    user_sel = st.selectbox("إختر اسمك", ["-- اختر --"] + list(USERS.keys()))
    pwd = st.text_input("كلمة السر", type="password")
    if st.button("دخول", use_container_width=True):
        if USERS.get(user_sel) == pwd:
            st.session_state.logged_in, st.session_state.user_name, st.session_state.page = True, user_sel, 'home'
            st.rerun()

elif st.session_state.page == 'home':
    st.markdown(f'<div class="header-box"><h3>أهلاً بك سيد {st.session_state.user_name}</h3><p style="color:green; font-weight:bold; font-size:22px;">ببركة الصلاة على محمد وآل محمد</p></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 فاتورة جديدة", use_container_width=True, type="primary"):
            st.session_state.page, st.session_state.temp_items, st.session_state.confirmed, st.session_state.receipt_view, st.session_state.is_sent, st.session_state.is_return = 'order', [], False, False, False, False
            st.session_state.inv_no = get_next_invoice_number(); st.rerun()
    with col2:
        if st.button("🔄 تسجيل مرتجع", use_container_width=True):
            st.session_state.page, st.session_state.temp_items, st.session_state.confirmed, st.session_state.receipt_view, st.session_state.is_sent, st.session_state.is_return = 'order', [], False, False, False, True
            st.session_state.inv_no = get_next_invoice_number(); st.rerun()
    st.divider()
    if st.button("🏭 طلب بضاعة من المعمل", use_container_width=True):
        st.session_state.page = 'factory_home'; st.rerun()

# --- قسم الفاتورة الكامل (اللي طلبت ما غيّر فيه شي) ---
elif st.session_state.page == 'order':
    is_ret = st.session_state.is_return
    if st.session_state.receipt_view:
        raw = sum(i["العدد"] * i["السعر"] for i in st.session_state.temp_items)
        h = float(convert_ar_nav(st.session_state.get('last_disc', '0')))
        aft = raw * (1 - h/100)
        vat = sum(((i["العدد"] * i["السعر"]) * (1 - h/100)) * 0.11 for i in st.session_state.temp_items if "*" in i["الصنف"])
        net = aft + vat
        c_n = st.session_state.get('last_cust', '..........')
        st.markdown(f'<div class="receipt-container"><div class="receipt-comp-name">شركة حلباوي إخوان ش.م.م</div><div class="receipt-body">السيد: {c_n}<br>مبلغ وقدره: <b>{net:,.2f}$</b><br>عن فاتورة رقم: #{st.session_state.inv_no}</div></div>', unsafe_allow_html=True)
        if st.button("🔙 العودة للفاتورة"): st.session_state.receipt_view = False; st.rerun()
    else:
        title = "مرتجع مبيعات" if is_ret else "فاتورة مبيعات"
        st.markdown(f'<h2 style="text-align:center;">{title} رقم #{st.session_state.inv_no}</h2>', unsafe_allow_html=True)
        cust_dict = load_rep_customers(st.session_state.user_name)
        col1, col2 = st.columns(2)
        with col1:
            search_c = st.text_input("🔍 ابحث عن زبون...")
            f_c = [k for k in cust_dict.keys() if search_c in k] if search_c else list(cust_dict.keys())
            sel_c = st.selectbox("اختر الزبون", ["-- اختر --", "➕ زبون جديد"] + f_c)
            cust = st.text_input("الاسم اليدوي") if sel_c == "➕ زبون جديد" else cust_dict.get(sel_c, sel_c)
        with col2:
            disc_input = st.text_input("الحسم %", value="0")
        st.session_state.last_cust, st.session_state.last_disc = cust, disc_input
        st.divider()
        search_p = st.text_input("🔍 ابحث عن صنف...", key=f"s_{st.session_state.widget_id}")
        f_p = [p for p in PRODUCTS.keys() if search_p in p] if search_p else list(PRODUCTS.keys())
        sel_p = st.selectbox("الصنف", ["-- اختر --"] + f_p, key=f"p_{st.session_state.widget_id}")
        qty = st.text_input("العدد", key=f"q_{st.session_state.widget_id}")
        if st.button("➕ إضافة صنف"):
            if sel_p != "-- اختر --" and qty:
                st.session_state.temp_items.append({"الصنف": sel_p, "العدد": float(convert_ar_nav(qty)), "السعر": PRODUCTS[sel_p]})
                st.session_state.widget_id += 1; st.rerun()
        if st.button("👁️ معاينة"): st.session_state.confirmed = True
        if st.session_state.confirmed and st.session_state.temp_items:
            h = float(convert_ar_nav(disc_input))
            raw = sum(i["العدد"] * i["السعر"] for i in st.session_state.temp_items)
            dis_a = raw * (h/100)
            aft = raw - dis_a
            rows_html, total_vat = "", 0
            for itm in st.session_state.temp_items:
                line_total = itm["العدد"] * itm["السعر"]
                line_vat = (line_total * (1 - h/100)) * 0.11 if "*" in itm["الصنف"] else 0
                total_vat += line_vat
                rows_html += f'<tr><td>{itm["الصنف"]}</td><td>{itm["العدد"]}</td><td>{itm["السعر"]:.2f}</td><td>{line_vat:.2f}</td><td>{line_total:.2f}</td></tr>'
            st.markdown(f'<div class="invoice-preview"><table class="styled-table"><thead><tr><th>الصنف</th><th>العدد</th><th>السعر</th><th>VAT</th><th>الإجمالي</th></tr></thead><tbody>{rows_html}</tbody></table><div class="total-final">الإجمالي: ${aft+total_vat:,.2f}</div></div>', unsafe_allow_html=True)
            if st.button("💾 حفظ"):
                if send_to_google_sheets(f"{total_vat:.2f}", f"{raw:.2f}", st.session_state.inv_no, cust, st.session_state.user_name, datetime.now().strftime("%Y-%m-%d %H:%M"), is_ret):
                    st.session_state.is_sent = True; st.success("✅ تم الحفظ")
        if st.button("🔙 الرئيسية"): st.session_state.page = 'home'; st.rerun()

# --- قسم طلبات المعمل (اللي بعتلي ياه هلق) ---
elif st.session_state.page == 'factory_home':
    df_f = load_factory_products()
    st.markdown('<div class="header-box"><h1>📦 طلبيات المعمل</h1></div>', unsafe_allow_html=True)
    if df_f is not None:
        for c in df_f['cat'].unique():
            if st.button(f"📦 قسم {c}", use_container_width=True):
                st.session_state.sel_cat = c; st.session_state.page = 'factory_details'; st.rerun()
        if st.button("🌟 أصناف خاصة", use_container_width=True): st.session_state.page = 'factory_special'; st.rerun()
        if st.session_state.cart or st.session_state.special_items:
            if st.button("🛒 مراجعة الطلبية", type="primary", use_container_width=True): st.session_state.page = 'factory_review'; st.rerun()
    if st.button("🏠 العودة للرئيسية"): st.session_state.page = 'home'; st.rerun()

elif st.session_state.page == 'factory_details':
    df_f = load_factory_products()
    cat = st.session_state.sel_cat
    st.header(f"قسم {cat}")
    cat_df = df_f[df_f['cat'] == cat]
    for weight in cat_df['pack'].unique():
        with st.expander(f"🔽 {weight}", expanded=True):
            w_df = cat_df[cat_df['pack'] == weight]
            for _, row in w_df.iterrows():
                st.markdown(f'<div class="item-label">{row["name"]}</div>', unsafe_allow_html=True)
                key = f"q_{row['name']}_{row['pack']}"
                val = st.text_input("العدد", key=key, label_visibility="collapsed")
                if val: st.session_state.cart[key] = {'name': row['name'], 'qty': val}
    if st.button("✅ مراجعة وتثبيت"): st.session_state.page = 'factory_review'; st.rerun()
    if st.button("🔙 عودة"): st.session_state.page = 'factory_home'; st.rerun()

elif st.session_state.page == 'factory_review':
    st.header("مراجعة طلبية المعمل")
    final_list = []
    for k, v in st.session_state.cart.items():
        st.write(f"✅ {v['name']}: {v['qty']}"); final_list.append(v)
    if st.button("🚀 إرسال للشركة"):
        if send_to_factory_sheets(st.session_state.user_name, final_list):
            st.success("تم الإرسال!")
            order_text = f"طلبية: {st.session_state.user_name}\n" + "\n".join([f"{i['name']}: {i['qty']}" for i in final_list])
            url = f"https://api.whatsapp.com/send?phone=9613220893&text={urllib.parse.quote(order_text)}"
            st.markdown(f'<a href="{url}" target="_blank" class="wa-button">إرسال واتساب ✅</a>', unsafe_allow_html=True)
    if st.button("🔙 عودة"): st.session_state.page = 'factory_home'; st.rerun()
