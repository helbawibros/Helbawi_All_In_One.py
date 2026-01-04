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

# --- 1. إعدادات التنسيق والهوية ---
LOGO_FILE = "IMG_6463.png"

st.set_page_config(
    page_title="شركة حلباوي إخوان", 
    layout="centered", 
    page_icon=LOGO_FILE
)

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;800&display=swap');
    html, body, [class*="css"] {{ font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }}
    div[data-testid="InputInstructions"], div[data-baseweb="helper-text"] {{ display: none !important; }}
    
    .header-box {{ background-color: #1E3A8A; color: white; text-align: center; padding: 10px; border-radius: 10px; margin-bottom: 20px;}}
    .return-header-box {{ background-color: #B22222; color: white; text-align: center; padding: 10px; border-radius: 10px; margin-bottom: 20px;}}
    
    @media print {{
        .no-print {{ display: none !important; }}
        .stButton, .stTextInput, .stSelectbox {{ display: none !important; }}
        body {{ background-color: white !important; }}
    }}

    .invoice-preview {{ background-color: white; padding: 25px; border: 2px solid #1E3A8A; border-radius: 10px; color: black; }}
    .return-preview {{ background-color: white; padding: 25px; border: 2px solid #B22222; border-radius: 10px; color: black; }}
    .company-header-center {{ text-align: center; border-bottom: 2px double #1E3A8A; padding-bottom: 10px; margin-bottom: 10px; }}
    .return-header-center {{ text-align: center; border-bottom: 2px double #B22222; padding-bottom: 10px; margin-bottom: 10px; }}
    .company-name {{ font-size: 28px; font-weight: 800; color: black; margin-bottom: 5px; }}
    .company-details {{ font-size: 16px; color: black; line-height: 1.4; }}
    .invoice-title-section {{ text-align: center; margin: 15px 0; }}
    .invoice-main-title {{ font-size: 24px; font-weight: bold; color: #1E3A8A; text-decoration: underline; }}
    .return-main-title {{ font-size: 24px; font-weight: bold; color: #B22222; text-decoration: underline; }}
    .invoice-no-small {{ font-size: 14px; color: #333; margin-top: 5px; font-weight: bold; }}
    
    .styled-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 15px; text-align: center; color: black; }}
    .styled-table th {{ background-color: #f0f2f6; color: black; padding: 10px; border: 1px solid #000; }}
    .styled-table td {{ padding: 10px; border: 1px solid #000; }}
    
    .summary-section {{ margin-top: 15px; width: 100%; }}
    .summary-row {{ display: flex; justify-content: space-between; padding: 5px 10px; font-size: 16px; border-bottom: 1px solid #ddd; }}
    .total-final {{ background-color: #d4edda; font-size: 22px; font-weight: 800; color: #155724; border: 2px solid #c3e6cb; margin-top: 10px; padding: 10px; text-align: center; }}
    .return-total-final {{ background-color: #f8d7da; font-size: 22px; font-weight: 800; color: #721c24; border: 2px solid #f5c6cb; margin-top: 10px; padding: 10px; text-align: center; }}

    .receipt-container {{ background-color: white; padding: 20px; color: black; text-align: center; border: 1px solid #eee; }}
    .receipt-comp-name {{ font-size: 32px; font-weight: 800; margin-bottom: 5px; }}
    .receipt-comp-addr {{ font-size: 18px; margin-bottom: 2px; }}
    .receipt-comp-tel {{ font-size: 18px; margin-bottom: 10px; }}
    .dashed-line {{ border-top: 2px dashed black; margin: 10px 0; }}
    .receipt-title {{ font-size: 35px; font-weight: 800; margin: 15px 0; }}
    .receipt-body {{ font-size: 22px; text-align: right; line-height: 2; margin: 20px 0; }}
    .receipt-footer {{ font-size: 18px; text-align: left; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px; }}

    /* ستايل نظام الطلبيات */
    .item-label {{ background-color: #1E3A8A; color: white; padding: 12px; border-radius: 8px; font-weight: bold; text-align: right; font-size: 18px; }}
    .wa-button {{ background-color: #25d366; color: white; padding: 20px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 24px; display: block; width: 100%; text-decoration: none; margin-top: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. إعدادات البيانات ---
SHEET_ID = "1-Abj-Kvbe02az8KYZfQL0eal2arKw_wgjVQdJX06IA0"

# دالة إرسال الطلبيات للمعمل (كودك الجديد)
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
        if rows:
            worksheet.append_rows(rows)
            return True
    except: return False

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

@st.cache_data(ttl=60)
def load_products_from_excel():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=339292430"
        df_p = pd.read_csv(url)
        df_p.columns = [c.strip() for c in df_p.columns]
        return pd.Series(df_p.iloc[:, 1].values, index=df_p.iloc[:, 0]).to_dict()
    except: return {"⚠️ خطأ": 0.0}

@st.cache_data(ttl=1)
def load_factory_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote('طلبات')}"
    try:
        df = pd.read_csv(url, header=None).dropna(how='all')
        df = df.iloc[:, :5]
        df.columns = ['cat', 'pack', 'sub', 'name', 'sci']
        return df
    except: return None

PRODUCTS = load_products_from_excel()

def send_to_google_sheets(vat, total_pre, inv_no, customer, representative, date_time, is_ret=False):
    url = "https://script.google.com/macros/s/AKfycbzi3kmbVyg_MV1Nyb7FwsQpCeneGVGSJKLMpv2YXBJR05v8Y77-Ub2SpvViZWCCp1nyqA/exec"
    prefix = "(مرتجع) " if is_ret else ""
    data = {"vat_value": vat, "total_before": total_pre, "invoice_no": inv_no, "cust_name": f"{prefix}{customer}", "rep_name": representative, "date_full": date_time}
    try:
        requests.post(url, data=data, timeout=10)
        return True
    except: return False

USERS = {"عبد الكريم حوراني": "9900", "محمد الحسيني": "8822", "علي دوغان": "5500", "عزات حلاوي": "6611", "علي حسين حلباوي": "4455", "محمد حسين حلباوي": "3366", "احمد حسين حلباوي": "7722", "علي محمد حلباوي": "6600"}

# إدارة الحالة
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'temp_items' not in st.session_state: st.session_state.temp_items = []
if 'confirmed' not in st.session_state: st.session_state.confirmed = False
if 'receipt_view' not in st.session_state: st.session_state.receipt_view = False
if 'is_sent' not in st.session_state: st.session_state.is_sent = False
if 'is_return' not in st.session_state: st.session_state.is_return = False
if 'widget_id' not in st.session_state: st.session_state.widget_id = 0
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'special_items' not in st.session_state: st.session_state.special_items = []

def convert_ar_nav(text):
    n_map = {'٠':'0','١':'1','٢':'2','٣':'3','٤':'4','٥':'5','٦':'6','٧':'7','٨':'8','٩':'9'}
    return "".join(n_map.get(c, c) for c in text)

# --- عرض اللوغو بعرض الشاشة ---
if os.path.exists(LOGO_FILE):
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
    st.markdown('<div class="header-box"><h2>شركة حلباوي إخوان</h2></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;"><h3>أهلاً بك سيد {st.session_state.user_name}</h3><p style="color:green; font-weight:bold; font-size:22px;">ببركة الصلاة على محمد وآل محمد</p></div>', unsafe_allow_html=True)
    
    col_inv, col_ret = st.columns(2)
    with col_inv:
        if st.button("📝 فاتورة جديدة", use_container_width=True, type="primary"):
            st.session_state.page, st.session_state.temp_items, st.session_state.confirmed, st.session_state.receipt_view, st.session_state.is_sent, st.session_state.is_return = 'order', [], False, False, False, False
            st.session_state.inv_no = get_next_invoice_number()
            st.rerun()
    with col_ret:
        if st.button("🔄 تسجيل مرتجع", use_container_width=True):
            st.session_state.page, st.session_state.temp_items, st.session_state.confirmed, st.session_state.receipt_view, st.session_state.is_sent, st.session_state.is_return = 'order', [], False, False, False, True
            st.session_state.inv_no = get_next_invoice_number()
            st.rerun()
    
    st.divider()
    if st.button("🏭 طلب بضاعة من المعمل", use_container_width=True):
        st.session_state.page = 'factory_order'
        st.rerun()

# --- قسم المعمل الجديد ---
elif st.session_state.page == 'factory_order':
    df_f = load_factory_data()
    st.markdown('<div class="header-box"><h1>🏭 طلب بضاعة من المعمل</h1></div>', unsafe_allow_html=True)
    st.write(f"المندوب: {st.session_state.user_name}")
    
    if df_f is not None:
        for c in df_f['cat'].unique():
            if st.button(f"📦 قسم {c}", use_container_width=True):
                st.session_state.sel_cat = c; st.session_state.page = 'f_details'; st.rerun()
        if st.button("🌟 أصناف خاصة", use_container_width=True):
            st.session_state.page = 'f_special'; st.rerun()
        if st.session_state.cart or st.session_state.special_items:
            if st.button("🛒 مراجعة الطلبية", use_container_width=True, type="primary"):
                st.session_state.page = 'f_review'; st.rerun()
    if st.button("🔙 عودة للرئيسية"): st.session_state.page = 'home'; st.rerun()

elif st.session_state.page == 'f_details':
    df_f = load_factory_data()
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
    if st.button("🛒 الذهاب للمراجعة"): st.session_state.page = 'f_review'; st.rerun()
    if st.button("🔙 عودة"): st.session_state.page = 'factory_order'; st.rerun()

elif st.session_state.page == 'f_review':
    st.header("مراجعة الطلبية")
    final_list = []
    for k, v in st.session_state.cart.items():
        st.write(f"✅ {v['name']}: {v['qty']}"); final_list.append(v)
    if st.button("🚀 إرسال الطلب للشركة", use_container_width=True):
        if send_to_factory_sheets(st.session_state.user_name, final_list):
            st.success("تم الإرسال!")
            order_text = f"طلبية: {st.session_state.user_name}\n" + "\n".join([f"{i['name']}: {i['qty']}" for i in final_list])
            url = f"https://api.whatsapp.com/send?phone=9613220893&text={urllib.parse.quote(order_text)}"
            st.markdown(f'<a href="{url}" target="_blank" class="wa-button">إرسال واتساب ✅</a>', unsafe_allow_html=True)
    if st.button("🔙 عودة"): st.session_state.page = 'factory_order'; st.rerun()

# --- واجهة الفاتورة (الأصلية كما هي) ---
elif st.session_state.page == 'order':
    is_ret = st.session_state.is_return
    if st.session_state.receipt_view:
        raw = sum(i["العدد"] * i["السعر"] for i in st.session_state.temp_items)
        h = float(convert_ar_nav(st.session_state.get('last_disc', '0')))
        aft = raw * (1 - h/100)
        vat = sum(((i["العدد"] * i["السعر"]) * (1 - h/100)) * 0.11 for i in st.session_state.temp_items if "*" in i["الصنف"])
        net = aft + vat
        c_n = st.session_state.get('last_cust', '..........')
        st.markdown(f"""<div class="receipt-container"><div class="receipt-comp-name">شركة حلباوي إخوان ش.م.م</div><div class="receipt-body">السيد: {c_n}<br>مبلغ وقدره: <span style="font-weight:800;">{net:,.2f}$</span><br>عن فاتورة رقم: #{st.session_state.inv_no}</div></div>""", unsafe_allow_html=True)
        if st.button("🖨️ طباعة الإيصال", use_container_width=True): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        if st.button("🔙 العودة للفاتورة", use_container_width=True): st.session_state.receipt_view = False; st.rerun()
    else:
        title = "مرتجع مبيعات" if is_ret else "فاتورة مبيعات"
        st.markdown(f'<h2 class="no-print" style="text-align:center; color:{"#B22222" if is_ret else "#1E3A8A"};">{title} رقم #{st.session_state.inv_no}</h2>', unsafe_allow_html=True)
        cust_dict = load_rep_customers(st.session_state.user_name)
        col1, col2 = st.columns(2)
        with col1:
            search_c = st.text_input("🔍 ابحث عن زبون...")
            f_c = [k for k in cust_dict.keys() if search_c in k] if search_c else list(cust_dict.keys())
            sel_c = st.selectbox("اختر الزبون", ["-- اختر --", "➕ زبون جديد (كتابة يدوية)"] + f_c)
            cust = st.text_input("اكتب اسم الزبون الجديد هنا") if sel_c == "➕ زبون جديد (كتابة يدوية)" else cust_dict.get(sel_c, sel_c if sel_c != "-- اختر --" else "")
        with col2:
            disc_input = st.text_input("الحسم %", value="0")
        st.session_state.last_cust, st.session_state.last_disc = cust, disc_input
        st.divider()
        wid = st.session_state.widget_id
        search_p = st.text_input("🔍 ابحث عن صنف...", key=f"s_{wid}")
        f_p = [p for p in PRODUCTS.keys() if search_p in p] if search_p else list(PRODUCTS.keys())
        sel_p = st.selectbox("الصنف", ["-- اختر --"] + f_p, key=f"p_{wid}")
        qty = st.text_input("العدد", key=f"q_{wid}")
        if st.button("➕ إضافة صنف", use_container_width=True):
            if sel_p != "-- اختر --" and qty:
                st.session_state.temp_items.append({"الصنف": sel_p, "العدد": float(convert_ar_nav(qty)), "السعر": PRODUCTS[sel_p]})
                st.session_state.widget_id += 1; st.rerun()
        if st.button("👁️ معاينة الفاتورة", use_container_width=True, type="primary"): st.session_state.confirmed = True
        if st.session_state.confirmed and st.session_state.temp_items:
            h = float(convert_ar_nav(disc_input))
            raw = sum(i["العدد"] * i["السعر"] for i in st.session_state.temp_items)
            dis_a, aft = raw * (h/100), raw - (raw * (h/100))
            rows_html, total_vat = "", 0
            for itm in st.session_state.temp_items:
                line_total = itm["العدد"] * itm["السعر"]
                line_vat = (line_total * (1 - h/100)) * 0.11 if "*" in itm["الصنف"] else 0
                total_vat += line_vat
                rows_html += f'<tr><td>{itm["الصنف"]}</td><td>{itm["العدد"]}</td><td>{itm["السعر"]:.2f}</td><td>{line_vat:.2f}</td><td>{line_total:.2f}</td></tr>'
            st.markdown(f'<div class="{"return-preview" if is_ret else "invoice-preview"}"><table class="styled-table"><thead><tr><th>الصنف</th><th>العدد</th><th>السعر</th><th>VAT</th><th>الإجمالي</th></tr></thead><tbody>{rows_html}</tbody></table><div class="{"return-total-final" if is_ret else "total-final"}">الإجمالي الصافي: ${aft + total_vat:,.2f}</div></div>', unsafe_allow_html=True)
            if st.button("💾 حفظ وإرسال", use_container_width=True):
                if send_to_google_sheets(f"{total_vat:.2f}", f"{raw:.2f}", st.session_state.inv_no, cust, st.session_state.user_name, datetime.now().strftime("%Y-%m-%d %H:%M"), is_ret):
                    st.session_state.is_sent = True; st.success("✅ تم الحفظ")
            if st.button("🖨️ طباعة", use_container_width=True, disabled=not st.session_state.is_sent):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        st.divider()
        col_b, col_r = st.columns(2)
        with col_b:
            if st.button("🔙 الرئيسية"): st.session_state.page = 'home'; st.rerun()
        with col_r:
            if st.button("🧾 إشعار استلام"): st.session_state.receipt_view = True; st.rerun()
