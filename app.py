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

# --- 1. إعدادات الوقت والهوية ---
os.environ['TZ'] = 'Asia/Beirut' 
LOGO_FILE = "IMG_6463.png"

st.set_page_config(page_title="شركة حلباوي إخوان", layout="centered")

# --- 2. التنسيق (CSS) المطابق للصور المرسلة ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;800&display=swap');
    html, body, [class*="css"] {{ font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }}
    
    /* تنسيق الفاتورة */
    .invoice-container {{ background-color: white; padding: 25px; border: 1px solid #1E3A8A; color: black; border-radius: 8px; }}
    .company-header-top {{ text-align: center; border-bottom: 2px solid #1E3A8A; padding-bottom: 10px; margin-bottom: 15px; }}
    .comp-name-main {{ font-size: 32px; font-weight: 800; color: black; margin: 0; }}
    .comp-contact {{ font-size: 16px; color: black; margin: 5px 0; }}
    
    .invoice-title-blue {{ color: #1E3A8A; font-size: 28px; font-weight: bold; text-decoration: underline; margin-bottom: 10px; }}
    .inv-info-row {{ display: flex; justify-content: space-between; font-size: 18px; margin: 10px 0; font-weight: bold; }}
    
    .styled-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
    .styled-table th {{ background-color: #f8f9fa; border: 1px solid #333; padding: 8px; text-align: center; color: black; }}
    .styled-table td {{ border: 1px solid #333; padding: 10px; text-align: center; color: black; }}
    
    .summary-section {{ margin-top: 15px; width: 100%; font-size: 19px; }}
    .summary-line {{ display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #eee; }}
    .net-total-box {{ background-color: #d4edda; color: #155724; font-size: 28px; font-weight: 800; text-align: center; padding: 15px; margin-top: 15px; border-radius: 4px; border: 1px solid #c3e6cb; }}

    /* تنسيق الإيصال */
    .receipt-box {{ border: 2px solid #333; padding: 30px; background: white; color: black; border-radius: 10px; }}
    .receipt-line {{ font-size: 24px; margin: 20px 0; line-height: 1.8; }}
    .dashed-sep {{ border-top: 2px dashed #000; margin: 20px 0; }}

    /* أزرار المعمل */
    .item-label {{ background-color: #1E3A8A; color: white; padding: 12px; border-radius: 8px; font-weight: bold; text-align: right; font-size: 18px; margin-top: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. الدوال البرمجية (Google Sheets & API) ---
SHEET_ID = "1-Abj-Kvbe02az8KYZfQL0eal2arKw_wgjVQdJX06IA0"

@st.cache_data(ttl=60)
def load_rep_customers(rep_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=155973706"
        df = pd.read_csv(url)
        rep_df = df[df.iloc[:, 0].astype(str).str.strip() == rep_name.strip()]
        return {f"{row.iloc[1]} ({row.iloc[2]})": row.iloc[1] for _, row in rep_df.iterrows()}
    except: return {}

@st.cache_data(ttl=60)
def load_products_prices():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=339292430"
        df_p = pd.read_csv(url)
        return pd.Series(df_p.iloc[:, 1].values, index=df_p.iloc[:, 0]).to_dict()
    except: return {}

@st.cache_data(ttl=1)
def load_factory_items():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote('طلبات')}"
    try:
        df = pd.read_csv(url, header=None).dropna(how='all')
        df = df.iloc[:, :5]
        df.columns = ['cat', 'pack', 'sub', 'name', 'sci']
        return df
    except: return None

def send_inv_to_sheets(vat, total, inv_no, customer, representative, is_ret=False):
    url = "https://script.google.com/macros/s/AKfycbzi3kmbVyg_MV1Nyb7FwsQpCeneGVGSJKLMpv2YXBJR05v8Y77-Ub2SpvViZWCCp1nyqA/exec"
    data = {"vat_value": vat, "total_before": total, "invoice_no": inv_no, "cust_name": f"{'(مرتجع) ' if is_ret else ''}{customer}", "rep_name": representative, "date_full": datetime.now().strftime("%Y-%m-%d %H:%M")}
    try: requests.post(url, data=data, timeout=10); return True
    except: return False

def send_to_factory_sheets(delegate_name, items_list):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        raw_json = st.secrets["gcp_service_account"]["json_data"].strip()
        service_account_info = json.loads(raw_json, strict=False)
        creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID)
        worksheet = sheet.worksheet(delegate_name.strip())
        rows = [[datetime.now().strftime("%Y-%m-%d %H:%M"), i['name'], i['qty'], "بانتظار التصديق"] for i in items_list]
        worksheet.append_rows(rows)
        return True
    except: return False

# --- 4. البيانات الأساسية ---
PRODUCTS = load_products_prices()
USERS = {"عبد الكريم حوراني": "9900", "محمد الحسيني": "8822", "علي دوغان": "5500", "عزات حلاوي": "6611", "علي حسين حلباوي": "4455", "محمد حسين حلباوي": "3366", "احمد حسين حلباوي": "7722", "علي محمد حلباوي": "6600"}

# إدارة الحالة (Session State)
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'temp_items' not in st.session_state: st.session_state.temp_items = []
if 'factory_cart' not in st.session_state: st.session_state.factory_cart = {}
if 'confirmed' not in st.session_state: st.session_state.confirmed = False
if 'receipt_view' not in st.session_state: st.session_state.receipt_view = False

if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, use_container_width=True)

# --- 5. منطق الواجهات ---

if st.session_state.page == 'login':
    st.markdown('<h2 style="text-align:center;">🔐 دخول المندوبين</h2>', unsafe_allow_html=True)
    u = st.selectbox("المندوب", ["-- اختر --"] + list(USERS.keys()))
    p = st.text_input("كلمة السر", type="password")
    if st.button("دخول", use_container_width=True):
        if USERS.get(u) == p:
            st.session_state.user_name, st.session_state.page = u, 'home'; st.rerun()

elif st.session_state.page == 'home':
    st.markdown(f'<h3 style="text-align:center;">أهلاً بك: {st.session_state.user_name}</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 فاتورة جديدة", use_container_width=True, type="primary"):
            st.session_state.page, st.session_state.temp_items, st.session_state.is_return, st.session_state.confirmed, st.session_state.receipt_view = 'order', [], False, False, False
            st.session_state.inv_no = str(random.randint(99000, 99999)); st.rerun()
    with col2:
        if st.button("🔄 مرتجع", use_container_width=True):
            st.session_state.page, st.session_state.temp_items, st.session_state.is_return, st.session_state.confirmed, st.session_state.receipt_view = 'order', [], True, False, False
            st.session_state.inv_no = str(random.randint(99000, 99999)); st.rerun()
    st.divider()
    if st.button("🏭 طلب بضاعة من المعمل", use_container_width=True):
        st.session_state.page = 'factory_home'; st.rerun()

elif st.session_state.page == 'order':
    if st.session_state.receipt_view:
        # --- واجهة الإيصال المصححة ---
        st.markdown(f"""
            <div class="receipt-box">
                <div class="company-header-top">
                    <p class="comp-name-main">شركة حلباوي إخوان ش.م.م</p>
                    <p class="comp-contact">بيروت - الرويس | 01/556058 - 03/220893</p>
                </div>
                <div class="dashed-sep"></div>
                <h1 style="text-align:center;">إشعار بالاستلام</h1>
                <div class="dashed-sep"></div>
                <div class="receipt-line">السيد: <b>{st.session_state.last_cust}</b></div>
                <div class="receipt-line">مبلغ وقدره: <b>${st.session_state.last_net:,.2f}</b></div>
                <div class="receipt-line">عن فاتورة رقم: #{st.session_state.inv_no}</div>
                <div style="margin-top:40px;">
                    التاريخ: {datetime.now().strftime("%d-%m-%Y | %H:%M")}<br>
                    المندوب: {st.session_state.user_name}
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🔙 العودة للفاتورة"): st.session_state.receipt_view = False; st.rerun()
        if st.button("🏠 الرئيسية"): st.session_state.page = 'home'; st.rerun()

    else:
        # --- واجهة الفاتورة ---
        c_dict = load_rep_customers(st.session_state.user_name)
        cc1, cc2 = st.columns(2)
        with cc1: sel_c = st.selectbox("الزبون", ["-- اختر --"] + list(c_dict.keys()))
        with cc2: disc = st.number_input("الحسم %", min_value=0.0, step=0.5)
        
        st.session_state.last_cust = c_dict.get(sel_c, "")
        
        st.divider()
        sel_p = st.selectbox("الصنف", ["-- اختر --"] + list(PRODUCTS.keys()))
        qty = st.number_input("الكمية", min_value=0.0, step=1.0)
        if st.button("➕ إضافة"):
            if sel_p != "-- اختر --" and qty > 0:
                st.session_state.temp_items.append({"الصنف": sel_p, "العدد": qty, "السعر": PRODUCTS[sel_p]})
                st.rerun()

        if st.session_state.temp_items:
            if st.button("👁️ معاينة", use_container_width=True, type="primary"): st.session_state.confirmed = True
            if st.session_state.confirmed:
                raw_t = sum(i["العدد"] * i["السعر"] for i in st.session_state.temp_items)
                d_amt = raw_t * (disc / 100)
                a_dis = raw_t - d_amt
                r_html, t_vat = "", 0
                for itm in st.session_state.temp_items:
                    line_t = itm["العدد"] * itm["السعر"]
                    line_v = (line_t * (1 - disc/100)) * 0.11 if "*" in itm["الصنف"] else 0
                    t_vat += line_v
                    r_html += f'<tr><td>{itm["الصنف"]}</td><td>{itm["العدد"]}</td><td>{itm["السعر"]:.2f}</td><td>{line_v:.2f}</td><td>{line_t:.2f}</td></tr>'
                st.session_state.last_net = a_dis + t_vat
                
                st.markdown(f"""
                    <div class="invoice-container">
                        <div class="company-header-top">
                            <p class="comp-name-main">شركة حلباوي إخوان ش.م.م</p>
                            <p class="comp-contact">03/220893 - 01/556058</p>
                        </div>
                        <h2 style="text-align:center; color:#1E3A8A;">{"مرتجع مبيعات" if st.session_state.is_return else "فاتورة مبيعات"}</h2>
                        <div class="inv-info-row"><span>الزبون: {st.session_state.last_cust}</span><span>#{st.session_state.inv_no}</span></div>
                        <table class="styled-table">
                            <thead><tr><th>الصنف</th><th>العدد</th><th>السعر</th><th>VAT</th><th>الإجمالي</th></tr></thead>
                            <tbody>{r_html}</tbody>
                        </table>
                        <div class="summary-section">
                            <div class="summary-line"><span>المجموع:</span><span>${raw_t:,.2f}</span></div>
                            <div class="summary-line"><span>الحسم:</span><span>-${d_amt:,.2f}</span></div>
                            <div class="summary-line"><span>VAT 11%:</span><span>+${t_vat:,.2f}</span></div>
                            <div class="net-total-box">الإجمالي: ${st.session_state.last_net:,.2f}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("💾 حفظ وإرسال البيانات"):
                    if send_inv_to_sheets(f"{t_vat:.2f}", f"{raw_t:.2f}", st.session_state.inv_no, st.session_state.last_cust, st.session_state.user_name, st.session_state.is_return):
                        st.success("✅ تم الحفظ")
                if st.button("🧾 إشعار استلام"): st.session_state.receipt_view = True; st.rerun()

    if st.button("🔙 عودة"): st.session_state.page = 'home'; st.rerun()

# --- 6. قسم المعمل (كامل بـ 100 سطر تقريباً) ---
elif st.session_state.page == 'factory_home':
    df_f = load_factory_items()
    st.markdown("## 🏭 طلبية المعمل")
    if df_f is not None:
        for cat in df_f['cat'].unique():
            if st.button(f"📦 قسم {cat}", use_container_width=True):
                st.session_state.factory_cat = cat; st.session_state.page = 'factory_details'; st.rerun()
        st.divider()
        if st.button("🛒 مراجعة الطلبية", type="primary", use_container_width=True):
            st.session_state.page = 'factory_review'; st.rerun()
    if st.button("🏠 الرئيسية"): st.session_state.page = 'home'; st.rerun()

elif st.session_state.page == 'factory_details':
    df_f = load_factory_items()
    cat = st.session_state.get('factory_cat', '')
    st.markdown(f"### قسم {cat}")
    cat_df = df_f[df_f['cat'] == cat]
    for pack in cat_df['pack'].unique():
        with st.expander(f"📦 تعبئة: {pack}", expanded=True):
            p_df = cat_df[cat_df['pack'] == pack]
            for _, row in p_df.iterrows():
                st.markdown(f'<div class="item-label">{row["name"]}</div>', unsafe_allow_html=True)
                q = st.text_input("العدد", key=f"f_{row['name']}_{pack}", label_visibility="collapsed")
                if q: st.session_state.factory_cart[row['name']] = {"name": row['name'], "qty": q}
    if st.button("✅ حفظ والعودة"): st.session_state.page = 'factory_home'; st.rerun()

elif st.session_state.page == 'factory_review':
    st.markdown("### مراجعة سلة المعمل")
    f_list = []
    for k, v in st.session_state.factory_cart.items():
        st.write(f"🔹 {v['name']} -> {v['qty']}")
        f_list.append(v)
    
    if st.button("🚀 إرسال للمعمل والواتساب"):
        if send_to_factory_sheets(st.session_state.user_name, f_list):
            msg = f"طلبية معمل من المندوب: {st.session_state.user_name}\n" + "\n".join([f"- {i['name']}: {i['qty']}" for i in f_list])
            st.markdown(f'<a href="https://wa.me/96103220893?text={urllib.parse.quote(msg)}" class="wa-button">📲 إرسال واتساب الآن</a>', unsafe_allow_html=True)
            st.session_state.factory_cart = {}
            st.success("تم تسجيل الطلب!")
    if st.button("🔙 عودة"): st.session_state.page = 'factory_home'; st.rerun()
