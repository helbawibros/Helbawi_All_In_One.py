import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
import requests
import urllib.parse
import json
import gspread
from google.oauth2.service_account import Credentials

# --- وظيفة الحصول على توقيت لبنان الحالي ---
def get_lebanon_time():
    return (datetime.utcnow() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")

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
    
    /* تنسيق عام لجعل الخط أسود غامق وواضح */
    html, body, [class*="css"], .stMarkdown, p, span, label {{ 
        font-family: 'Cairo', sans-serif; 
        direction: rtl; 
        text-align: right; 
        color: #000000 !important; /* أسود نقي */
        font-weight: 600;
    }}
    
    /* إخفاء تعليمات الإدخال */
    div[data-testid="InputInstructions"], div[data-baseweb="helper-text"] {{ display: none !important; }}
    
    /* صناديق العناوين */
    .header-box {{ background-color: #1E3A8A; color: white !important; text-align: center; padding: 10px; border-radius: 10px; margin-bottom: 20px;}}
    .header-box h1, .header-box h2 {{ color: white !important; font-weight: 800; }}
    .return-header-box {{ background-color: #B22222; color: white !important; text-align: center; padding: 10px; border-radius: 10px; margin-bottom: 20px;}}
    
    @media print {{
        .no-print {{ display: none !important; }}
        .stButton, .stTextInput, .stSelectbox {{ display: none !important; }}
        body {{ background-color: white !important; }}
    }}

    /* معاينة الفاتورة */
    .invoice-preview {{ background-color: white; padding: 25px; border: 3px solid #1E3A8A; border-radius: 10px; color: black !important; }}
    .return-preview {{ background-color: white; padding: 25px; border: 3px solid #B22222; border-radius: 10px; color: black !important; }}
    .company-name {{ font-size: 28px; font-weight: 800; color: #000 !important; margin-bottom: 5px; }}
    .company-details {{ font-size: 16px; color: #000 !important; font-weight: bold; }}
    .invoice-main-title {{ font-size: 26px; font-weight: 900; color: #1E3A8A !important; text-decoration: underline; }}
    .return-main-title {{ font-size: 26px; font-weight: 900; color: #B22222 !important; text-decoration: underline; }}
    
    /* الجداول */
    .styled-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 16px; color: black !important; font-weight: bold; }}
    .styled-table th {{ background-color: #1E3A8A; color: white !important; padding: 10px; border: 1px solid #000; }}
    .styled-table td {{ padding: 10px; border: 1px solid #000; background-color: #fff; }}
    
    /* الملخص النهائي */
    .summary-row {{ display: flex; justify-content: space-between; padding: 5px 10px; font-size: 18px; border-bottom: 2px solid #eee; color: #000 !important; font-weight: 800; }}
    .total-final {{ background-color: #d4edda; font-size: 24px; font-weight: 900; color: #155724 !important; border: 2px solid #c3e6cb; margin-top: 10px; padding: 10px; text-align: center; }}
    .return-total-final {{ background-color: #f8d7da; font-size: 24px; font-weight: 900; color: #721c24 !important; border: 2px solid #f5c6cb; margin-top: 10px; padding: 10px; text-align: center; }}

    /* كروت الجرد */
    .stock-card {{ 
        border: 2px solid #1E3A8A; 
        padding: 12px; 
        border-radius: 8px; 
        margin-bottom: 8px; 
        background: #ffffff; 
        box-shadow: 3px 3px 6px rgba(0,0,0,0.1); 
        color: #000 !important;
    }}
    .stock-card span {{ color: #000 !important; font-weight: 800 !important; }}

    /* أزرار الواتساب */
    .wa-button {{ background-color: #25d366; color: white !important; padding: 15px; border-radius: 10px; text-align: center; font-weight: 800; display: block; text-decoration: none; font-size: 20px; }}
    
    /* الإيصال الصغير */
    .receipt-container {{ background-color: white; padding: 20px; color: black !important; text-align: center; border: 2px solid #000; }}
    .receipt-body {{ font-size: 24px; font-weight: 800; color: black !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. إعدادات البيانات والربط ---
SHEET_ID = "1-Abj-Kvbe02az8KYZfQL0eal2arKw_wgjVQdJX06IA0"
GID_PRICES = "339292430"
GID_DATA = "0"
GID_CUSTOMERS = "155973706" 

def get_gspread_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        service_account_info = json.loads(st.secrets["gcp_service_account"]["json_data"].strip(), strict=False)
        creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
        return gspread.authorize(creds)
    except: return None

@st.cache_data(ttl=60)
def load_rep_customers(rep_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={GID_CUSTOMERS}"
        df = pd.read_csv(url)
        rep_df = df[df.iloc[:, 0].astype(str).str.strip() == rep_name.strip()]
        return {f"{row.iloc[1]} ({row.iloc[2]})": row.iloc[1] for _, row in rep_df.iterrows()}
    except: return {}

@st.cache_data(ttl=60)
def load_products_from_excel():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={GID_PRICES}"
        df_p = pd.read_csv(url)
        df_p.columns = [c.strip() for c in df_p.columns]
        return pd.Series(df_p.iloc[:, 1].values, index=df_p.iloc[:, 0]).to_dict()
    except: return {"⚠️ خطأ": 0.0}

@st.cache_data(ttl=1)
def load_factory_items():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote('طلبات')}"
    try:
        df = pd.read_csv(url, header=None).dropna(how='all')
        df = df.iloc[:, :5]
        df.columns = ['cat', 'pack', 'sub', 'name', 'sci']
        return df
    except: return None

def get_next_invoice_number():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={GID_DATA}"
        df = pd.read_csv(url)
        if 'رقم الفاتوره' in df.columns:
            valid_nums = pd.to_numeric(df['رقم الفاتوره'], errors='coerce').dropna()
            if not valid_nums.empty: return str(int(valid_nums.max()) + 1)
        return "1001"
    except: return str(random.randint(10000, 99999))

def calculate_live_stock(rep_name):
    client = get_gspread_client()
    if not client: return None
    try:
        sheet = client.open_by_key(SHEET_ID)
        rep_sheet = sheet.worksheet(rep_name.strip())
        data_in = rep_sheet.get_all_values()
        if len(data_in) <= 1: return pd.Series()
        df_in = pd.DataFrame(data_in[1:], columns=data_in[0])
        col_name_idx, col_qty_idx, col_status_idx = 1, 2, 3
        mask = df_in.iloc[:, col_status_idx].astype(str).str.contains('تم', na=False)
        df_confirmed = df_in[mask].copy()
        if df_confirmed.empty: return pd.Series()
        df_confirmed.iloc[:, col_name_idx] = df_confirmed.iloc[:, col_name_idx].astype(str).str.strip()
        df_confirmed.iloc[:, col_qty_idx] = pd.to_numeric(df_confirmed.iloc[:, col_qty_idx], errors='coerce').fillna(0)
        stock_in = df_confirmed.groupby(df_confirmed.columns[col_name_idx])[df_confirmed.columns[col_qty_idx]].sum()
        url_sales = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={GID_DATA}"
        df_sales = pd.read_csv(url_sales)
        if 'المندوب' in df_sales.columns:
            df_sales['المندوب'] = df_sales['المندوب'].astype(str).str.strip()
            df_rep_sales = df_sales[df_sales['المندوب'] == rep_name.strip()].copy()
            df_rep_sales['الصنف'] = df_rep_sales['الصنف'].astype(str).str.strip()
            df_rep_sales['العدد'] = pd.to_numeric(df_rep_sales['العدد'], errors='coerce').fillna(0)
            stock_out = df_rep_sales.groupby('الصنف')['العدد'].sum()
        else: stock_out = pd.Series()
        inventory = stock_in.subtract(stock_out, fill_value=0)
        return inventory[inventory > 0]
    except: return pd.Series()

def send_to_google_sheets(vat, total_pre, inv_no, customer, representative, date_time, is_ret=False):
    url = "https://script.google.com/macros/s/AKfycbzi3kmbVyg_MV1Nyb7FwsQpCeneGVGSJKLMpv2YXBJR05v8Y77-Ub2SpvViZWCCp1nyqA/exec"
    prefix = "(مرتجع) " if is_ret else ""
    l_time = get_lebanon_time()
    data = {"vat_value": vat, "total_before": total_pre, "invoice_no": inv_no, "cust_name": f"{prefix}{customer}", "rep_name": representative, "date_full": l_time}
    try:
        requests.post(url, data=data, timeout=10)
        return True
    except: return False

def send_to_factory_sheets(delegate_name, items_list):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID)
        worksheet = sheet.worksheet(delegate_name.strip())
        l_time = get_lebanon_time()
        rows = [[l_time, i['name'], i['qty'], "بانتظار التصديق"] for i in items_list]
        worksheet.append_rows(rows)
        return True
    except: return False

PRODUCTS = load_products_from_excel()
USERS = {"عبد الكريم حوراني": "9900", "محمد الحسيني": "8822", "علي دوغان": "5500", "عزات حلاوي": "6611", "علي حسين حلباوي": "4455", "محمد حسين حلباوي": "3366", "احمد حسين حلباوي": "7722", "علي محمد حلباوي": "6600"}

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'temp_items' not in st.session_state: st.session_state.temp_items = []
if 'confirmed' not in st.session_state: st.session_state.confirmed = False
if 'receipt_view' not in st.session_state: st.session_state.receipt_view = False
if 'is_sent' not in st.session_state: st.session_state.is_sent = False
if 'is_return' not in st.session_state: st.session_state.is_return = False
if 'widget_id' not in st.session_state: st.session_state.widget_id = 0
if 'factory_cart' not in st.session_state: st.session_state.factory_cart = {}

def convert_ar_nav(text):
    n_map = {'٠':'0','١':'1','٢':'2','٣':'3','٤':'4','٥':'5','٦':'6','٧':'7','٨':'8','٩':'9'}
    return "".join(n_map.get(c, c) for c in text)

st.image(LOGO_FILE, use_container_width=True)

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
    st.markdown(f'<div style="text-align:center;"><h3 style="color:#000;">أهلاً بك سيد {st.session_state.user_name}</h3><p style="color:green; font-weight:900; font-size:24px;">ببركة الصلاة على محمد وآل محمد</p></div>', unsafe_allow_html=True)
    
    col_inv, col_ret = st.columns(2)
    with col_inv:
        if st.button("📝 فاتورة جديدة", use_container_width=True, type="primary"):
            st.session_state.page, st.session_state.temp_items, st.session_state.confirmed, st.session_state.receipt_view, st.session_state.is_sent, st.session_state.is_return = 'order', [], False, False, False, False
            st.session_state.inv_no = get_next_invoice_number(); st.rerun()
    with col_ret:
        if st.button("🔄 تسجيل مرتجع", use_container_width=True):
            st.session_state.page, st.session_state.temp_items, st.session_state.confirmed, st.session_state.receipt_view, st.session_state.is_sent, st.session_state.is_return = 'order', [], False, False, False, True
            st.session_state.inv_no = get_next_invoice_number(); st.rerun()
    
    st.divider()
    col_f, col_s = st.columns(2)
    with col_f:
        if st.button("🏭 طلب بضاعة", use_container_width=True):
            st.session_state.page = 'factory_home'; st.rerun()
    with col_s:
        if st.button("📊 جرد السيارة", use_container_width=True):
            st.session_state.page = 'stock_view'; st.rerun()

elif st.session_state.page == 'stock_view':
    st.markdown('<h3 style="text-align:center; color:#1E3A8A;">📋 جرد رصيد السيارة</h3>', unsafe_allow_html=True)
    inventory = calculate_live_stock(st.session_state.user_name)
    if inventory is not None and not inventory.empty:
        for item, qty in inventory.items():
            if qty > 0:
                sc = "#28a745" if qty > 5 else "#dc3545"
                st.markdown(f"""
                    <div class="stock-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size:20px;">{item}</span>
                            <span style="font-size:24px; color:{sc} !important;">{int(qty)}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("لا توجد بضاعة مسجلة.")
    if st.button("🔙 العودة للرئيسية", use_container_width=True):
        st.session_state.page = 'home'; st.rerun()

elif st.session_state.page == 'order':
    is_ret = st.session_state.is_return
    if st.session_state.receipt_view:
        raw = sum(i["العدد"] * i["السعر"] for i in st.session_state.temp_items)
        h = float(convert_ar_nav(st.session_state.get('last_disc', '0')))
        aft = raw * (1 - h/100)
        vat = sum(((i["العدد"] * i["السعر"]) * (1 - h/100)) * 0.11 for i in st.session_state.temp_items if "*" in i["الصنف"])
        net = aft + vat
        c_n = st.session_state.get('last_cust', '..........')
        st.markdown(f"""
            <div class="receipt-container">
                <div class="company-name">شركة حلباوي إخوان ش.م.م</div>
                <div class="dashed-line" style="border-top: 2px dashed #000; margin: 10px 0;"></div>
                <div class="receipt-body">
                    إلى السيد: {c_n}<br>
                    مبلغ: <span style="font-size:30px;">${net:,.2f}</span><br>
                    رقم الفاتورة: #{st.session_state.inv_no}
                </div>
                <div style="margin-top:20px; font-weight:bold;">التاريخ: {get_lebanon_time()}</div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🖨️ طباعة", use_container_width=True): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        if st.button("🔙 عودة"): st.session_state.receipt_view = False; st.rerun()
    else:
        title = "مرتجع مبيعات" if is_ret else "فاتورة مبيعات"
        st.markdown(f'<h2 style="text-align:center; color:#000;">{title} #{st.session_state.inv_no}</h2>', unsafe_allow_html=True)
        cust_dict = load_rep_customers(st.session_state.user_name)
        col1, col2 = st.columns(2)
        with col1:
            sel_c = st.selectbox("اختر الزبون", ["-- اختر --", "➕ زبون جديد"] + list(cust_dict.keys()))
            cust = st.text_input("اسم الزبون") if sel_c == "➕ زبون جديد" else cust_dict.get(sel_c, "")
        with col2:
            disc_input = st.text_input("الحسم %", value="0")
        
        st.session_state.last_cust, st.session_state.last_disc = cust, disc_input
        st.divider()
        
        wid = st.session_state.widget_id
        sel_p = st.selectbox("الصنف", ["-- اختر --"] + list(PRODUCTS.keys()), key=f"p_{wid}")
        qty = st.text_input("العدد", key=f"q_{wid}")
        if st.button("➕ إضافة", use_container_width=True):
            if sel_p != "-- اختر --" and qty:
                st.session_state.temp_items.append({"الصنف": sel_p, "العدد": float(convert_ar_nav(qty)), "السعر": PRODUCTS[sel_p]})
                st.session_state.widget_id += 1; st.rerun()

        if st.session_state.temp_items:
            h = float(convert_ar_nav(disc_input))
            raw = sum(i["العدد"] * i["السعر"] for i in st.session_state.temp_items)
            dis_a = raw * (h/100); aft = raw - dis_a
            rows_html, total_vat = "", 0
            for itm in st.session_state.temp_items:
                line_t = itm["العدد"] * itm["السعر"]
                line_v = (line_t * (1 - h/100)) * 0.11 if "*" in itm["الصنف"] else 0
                total_vat += line_v
                rows_html += f'<tr><td>{itm["الصنف"]}</td><td>{itm["العدد"]}</td><td>{itm["السعر"]:.2f}</td><td>{line_t:.2f}</td></tr>'
            
            st.markdown(f"""
                <div class="{"return-preview" if is_ret else "invoice-preview"}">
                    <div style="text-align:center;"><div class="company-name">شركة حلباوي إخوان</div></div>
                    <div style="display:flex; justify-content:space-between; margin:10px 0;">
                        <span>الزبون: {cust}</span><span>التاريخ: {get_lebanon_time().split()[0]}</span>
                    </div>
                    <table class="styled-table">
                        <thead><tr><th>الصنف</th><th>العدد</th><th>السعر</th><th>الإجمالي</th></tr></thead>
                        <tbody>{rows_html}</tbody>
                    </table>
                    <div class="summary-row"><span>المجموع:</span><span>${raw:,.2f}</span></div>
                    <div class="summary-row"><span>VAT 11%:</span><span>+${total_vat:,.2f}</span></div>
                    <div class="{"return-total-final" if is_ret else "total-final"}">الصافي: ${aft + total_vat:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("💾 حفظ وإرسال", use_container_width=True, type="primary"):
                if send_to_google_sheets(total_vat, raw, st.session_state.inv_no, cust, st.session_state.user_name, "", is_ret):
                    st.success("✅ تم الحفظ بنجاح")
                    st.session_state.is_sent = True
            
            if st.session_state.is_sent:
                col_p1, col_p2 = st.columns(2)
                with col_p1: st.button("🖨️ طباعة الفاتورة", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
                with col_p2: 
                    if st.button("🧾 إشعار استلام"): st.session_state.receipt_view = True; st.rerun()

    if st.button("🔙 الرئيسية"): st.session_state.page = 'home'; st.rerun()

elif st.session_state.page == 'factory_home':
    st.markdown('<h2 style="text-align:center;">🏭 طلب بضاعة للمعمل</h2>', unsafe_allow_html=True)
    df_f = load_factory_items()
    if df_f is not None:
        for cat in df_f['cat'].unique():
            if st.button(f"📦 قسم {cat}", use_container_width=True):
                st.session_state.factory_cat = cat; st.session_state.page = 'factory_details'; st.rerun()
        if st.button("🛒 مراجعة السلة", type="primary", use_container_width=True):
            st.session_state.page = 'factory_review'; st.rerun()
    if st.button("🏠 الرئيسية"): st.session_state.page = 'home'; st.rerun()

elif st.session_state.page == 'factory_details':
    df_f = load_factory_items(); cat = st.session_state.get('factory_cat', '')
    st.markdown(f"### قسم {cat}")
    cat_df = df_f[df_f['cat'] == cat]
    for _, row in cat_df.iterrows():
        st.markdown(f'<div style="background:#eee; padding:5px; border-radius:5px; margin-top:5px; font-weight:900;">{row["name"]} ({row["pack"]})</div>', unsafe_allow_html=True)
        q = st.text_input("الكمية", key=f"f_{row['name']}")
        if q: st.session_state.factory_cart[row['name']] = {"name": row['name'], "qty": q}
    if st.button("✅ حفظ"): st.session_state.page = 'factory_home'; st.rerun()

elif st.session_state.page == 'factory_review':
    st.markdown("### مراجعة سلة المعمل")
    f_list = [v for k, v in st.session_state.factory_cart.items()]
    for i in f_list: st.write(f"🔹 {i['name']} -> {i['qty']}")
    if st.button("🚀 إرسال"):
        if send_to_factory_sheets(st.session_state.user_name, f_list):
            msg = f"طلبية معمل من: {st.session_state.user_name}\n" + "\n".join([f"- {i['name']}: {i['qty']}" for i in f_list])
            st.markdown(f'<a href="https://wa.me/96103220893?text={urllib.parse.quote(msg)}" class="wa-button">📲 إرسال واتساب</a>', unsafe_allow_html=True)
            st.session_state.factory_cart = {}; st.success("تم التسجيل!")
    if st.button("🔙 عودة"): st.session_state.page = 'factory_home'; st.rerun()
