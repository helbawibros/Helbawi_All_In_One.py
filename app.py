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
    
    .item-label {{ background-color: #1E3A8A; color: white; padding: 10px; border-radius: 5px; font-weight: bold; margin-bottom: 5px; }}
    .wa-button {{ background-color: #25d366; color: white; padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; display: block; text-decoration: none; }}
    
    .stock-card {{ border: 1px solid #ddd; padding: 12px; border-radius: 8px; margin-bottom: 8px; background: #fff; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); border-right: 5px solid #1E3A8A; }}
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

# --- وظيفة حساب الجرد المصححة (تم الاستبدال هنا) ---
def calculate_live_stock(rep_name):
    client = get_gspread_client()
    if not client: return None
    try:
        sheet = client.open_by_key(SHEET_ID)
        rep_sheet = sheet.worksheet(rep_name.strip())
        data_in = rep_sheet.get_all_values()
        if len(data_in) <= 1: return pd.Series()
        
        df_in = pd.DataFrame(data_in[1:], columns=[c.strip() for c in data_in[0]])
        
        # البحث عن عمود الحالة الصحيح (سواء "حالة الطلب" أو "الحالة")
        status_col = 'حالة الطلب' if 'حالة الطلب' in df_in.columns else ('الحالة' if 'الحالة' in df_in.columns else df_in.columns[-1])
        
        # فلترة المصدق فقط
        df_in = df_in[df_in[status_col].astype(str).str.contains('تم التصديق')]
        
        df_in['اسم الصنف'] = df_in['اسم الصنف'].astype(str).str.strip()
        df_in['الكميه المطلوبه'] = pd.to_numeric(df_in['الكميه المطلوبه'], errors='coerce').fillna(0)
        stock_in = df_in.groupby('اسم الصنف')['الكميه المطلوبه'].sum()

        # جلب المبيعات
        url_sales = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={GID_DATA}"
        df_sales = pd.read_csv(url_sales)
        df_sales['المندوب'] = df_sales['المندوب'].astype(str).str.strip()
        df_rep_sales = df_sales[df_sales['المندوب'] == rep_name.strip()].copy()
        df_rep_sales['الصنف'] = df_rep_sales['الصنف'].astype(str).str.strip()
        df_rep_sales['العدد'] = pd.to_numeric(df_rep_sales['العدد'], errors='coerce').fillna(0)
        stock_out = df_rep_sales.groupby('الصنف')['العدد'].sum()

        # طرح المبيعات من الاستلام
        inventory = stock_in.subtract(stock_out, fill_value=0)
        return inventory[inventory > 0]
    except Exception:
        return pd.Series()

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
    st.markdown(f'<div style="text-align:center;"><h3>أهلاً بك سيد {st.session_state.user_name}</h3><p style="color:green; font-weight:bold; font-size:22px;">ببركة الصلاة على محمد وآل محمد</p></div>', unsafe_allow_html=True)
    
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
    st.markdown("### 📋 حمولة السيارة الحالية (الرصيد)")
    with st.spinner("جاري حساب الجرد الفعلي..."):
        inventory = calculate_live_stock(st.session_state.user_name)
        if inventory is not None and not inventory.empty:
            for item, qty in inventory.items():
                if qty > 0:
                    status_color = "#28a745" if qty > 5 else "#dc3545"
                    st.markdown(f"""
                        <div class="stock-card">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="font-size:18px; font-weight:bold;">{item}</span>
                                <span style="font-size:22px; color:{status_color}; font-weight:800;">{qty}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("لا توجد بضاعة مسجلة أو لم يتم التصديق على أي طلبية بعد.")
    
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
                <div class="receipt-comp-name">شركة حلباوي إخوان ش.م.م</div>
                <div class="receipt-comp-addr">بيروت - الرويس</div>
                <div class="receipt-comp-tel">03/220893 - 01/556058</div>
                <div class="dashed-line"></div>
                <div class="receipt-title">{"إشعار مرتجع" if is_ret else "إشعار بالاستلام"}</div>
                <div class="dashed-line"></div>
                <div class="receipt-body">
                    السيد: {c_n}<br>
                    مبلغ وقدره: <span style="font-weight:800;">{net:,.2f}$</span><br>
                    عن فاتورة رقم: #{st.session_state.inv_no}
                </div>
                <div class="receipt-footer">التاريخ: {get_lebanon_time()}<br>المندوب: {st.session_state.user_name}</div>
            </div>
        """, unsafe_allow_html=True)
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
                try:
                    q_val = float(convert_ar_nav(qty))
                    st.session_state.temp_items.append({"الصنف": sel_p, "العدد": q_val, "السعر": PRODUCTS[sel_p]})
                    st.session_state.widget_id += 1; st.rerun()
                except: st.error("خطأ في الرقم")
        if st.button("👁️ معاينة الفاتورة", use_container_width=True, type="primary"): st.session_state.confirmed = True
        if st.session_state.confirmed and st.session_state.temp_items:
            h = float(convert_ar_nav(disc_input))
            raw = sum(i["العدد"] * i["السعر"] for i in st.session_state.temp_items)
            dis_a = raw * (h/100); aft = raw - dis_a
            rows_html, total_vat = "", 0
            for itm in st.session_state.temp_items:
                line_t = itm["العدد"] * itm["السعر"]; line_v = (line_t * (1 - h/100)) * 0.11 if "*" in itm["الصنف"] else 0
                total_vat += line_v; rows_html += f'<tr><td>{itm["الصنف"]}</td><td>{itm["العدد"]}</td><td>{itm["السعر"]:.2f}</td><td>{line_v:.2f}</td><td>{line_t:.2f}</td></tr>'
            net = aft + total_vat
            st.markdown(f"""
                <div class="{"return-preview" if is_ret else "invoice-preview"}">
                    <div class="{"return-header-center" if is_ret else "company-header-center"}">
                        <div class="company-name">شركة حلباوي إخوان ش.م.م</div>
                        <div class="company-details">بيروت - الرويس | 03/220893 - 01/556058</div>
                    </div>
                    <div class="invoice-title-section">
                        <div class="{"return-main-title" if is_ret else "invoice-main-title"}">{title}</div>
                        <div class="invoice-no-small">رقم: #{st.session_state.inv_no}</div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 10px;">
                        <div>الزبون: {cust}</div>
                        <div style="text-align: left;">التاريخ: {get_lebanon_time().split()[0]}<br>المندوب: {st.session_state.user_name}</div>
                    </div>
                    <table class="styled-table">
                        <thead><tr><th>الصنف</th><th>العدد</th><th>السعر</th><th>VAT</th><th>الإجمالي</th></tr></thead>
                        <tbody>{rows_html}</tbody>
                    </table>
                    <div class="summary-section">
                        <div class="summary-row"><span>المجموع:</span><span>${raw:,.2f}</span></div>
                        <div class="summary-row"><span>الحسم ({h}%):</span><span>-${dis_a:,.2f}</span></div>
                        <div class="summary-row" style="font-weight:bold; color:{"#B22222" if is_ret else "#1E3A8A"};"><span>بعد الحسم:</span><span>${aft:,.2f}</span></div>
                        <div class="summary-row"><span>VAT 11%:</span><span>+${total_vat:,.2f}</span></div>
                        <div class="{"return-total-final" if is_ret else "total-final"}">الإجمالي الصافي: ${net:,.2f}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("💾 حفظ وإرسال", use_container_width=True):
                v_vat = f"-{total_vat:.2f}" if is_ret else f"{total_vat:.2f}"
                v_raw = f"-{raw:.2f}" if is_ret else f"{raw:.2f}"
                if send_to_google_sheets(v_vat, v_raw, st.session_state.inv_no, cust, st.session_state.user_name, get_lebanon_time(), is_ret):
                    st.session_state.is_sent = True; st.success("✅ تم الحفظ")
            if st.button("🖨️ طباعة", use_container_width=True, disabled=not st.session_state.is_sent):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        st.divider()
        cb, cr = st.columns(2)
        with cb:
            if st.button("🔙 الرئيسية"): st.session_state.page = 'home'; st.rerun()
        with cr:
            if st.button("🧾 إشعار استلام"): st.session_state.receipt_view = True; st.rerun()

elif st.session_state.page == 'factory_home':
    df_f = load_factory_items()
    st.markdown("## 🏭 طلبية المعمل")
    if df_f is not None:
        for cat in df_f['cat'].unique():
            if st.button(f"📦 قسم {cat}", use_container_width=True):
                st.session_state.factory_cat = cat; st.session_state.page = 'factory_details'; st.rerun()
        
        if st.button("➕ أصناف خاصة (كتابة يدوية)", use_container_width=True):
            st.session_state.factory_cat = "أصناف خاصة"; st.session_state.page = 'factory_special'; st.rerun()
            
        st.divider()
        if st.button("🛒 مراجعة السلة", type="primary", use_container_width=True):
            st.session_state.page = 'factory_review'; st.rerun()
    if st.button("🏠 الرئيسية"): st.session_state.page = 'home'; st.rerun()

elif st.session_state.page == 'factory_special':
    st.markdown("### ➕ إضافة أصناف خاصة")
    with st.form("special_item_form"):
        col_name, col_pack, col_qty = st.columns(3)
        with col_name: s_name = st.text_input("الصنف")
        with col_pack: s_pack = st.text_input("التعبئة")
        with col_qty: s_qty = st.text_input("العدد")
        
        if st.form_submit_button("إضافة إلى السلة"):
            if s_name and s_qty:
                full_name = f"{s_name} ({s_pack})" if s_pack else s_name
                st.session_state.factory_cart[full_name] = {"name": full_name, "qty": s_qty}
                st.success(f"تم إضافة {s_name}")
    if st.button("🔙 العودة لطلبية المعمل"): st.session_state.page = 'factory_home'; st.rerun()

elif st.session_state.page == 'factory_details':
    df_f = load_factory_items(); cat = st.session_state.get('factory_cat', '')
    st.markdown(f"### قسم {cat}")
    cat_df = df_f[df_f['cat'] == cat]
    for pack in cat_df['pack'].unique():
        with st.expander(f"📦 تعبئة: {pack}", expanded=True):
            p_df = cat_df[cat_df['pack'] == pack]
            for _, row in p_df.iterrows():
                st.markdown(f'<div class="item-label">{row["name"]}</div>', unsafe_allow_html=True)
                q = st.text_input("الكمية", key=f"f_{row['name']}_{pack}", label_visibility="collapsed")
                if q: st.session_state.factory_cart[row['name']] = {"name": row['name'], "qty": q}
    if st.button("✅ حفظ والعودة"): st.session_state.page = 'factory_home'; st.rerun()

elif st.session_state.page == 'factory_review':
    st.markdown("### مراجعة سلة المعمل")
    f_list = []
    for k, v in st.session_state.factory_cart.items():
        st.write(f"🔹 {v['name']} -> {v['qty']}"); f_list.append(v)
    if st.button("🚀 إرسال للمعمل والواتساب", use_container_width=True):
        if send_to_factory_sheets(st.session_state.user_name, f_list):
            msg = f"طلبية معمل من: {st.session_state.user_name}\n" + "\n".join([f"- {i['name']}: {i['qty']}" for i in f_list])
            st.markdown(f'<a href="https://wa.me/96103220893?text={urllib.parse.quote(msg)}" class="wa-button">📲 إرسال واتساب</a>', unsafe_allow_html=True)
            st.session_state.factory_cart = {}; st.success("تم التسجيل!")
    if st.button("🔙 عودة"): st.session_state.page = 'factory_home'; st.rerun()

