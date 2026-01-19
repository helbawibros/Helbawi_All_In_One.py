import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
import requests
import urllib.parse
import json
import gspread
from google.oauth2.service_account import Credentials
import os

# --- وظيفة الحصول على توقيت لبنان الحالي ---
def get_lebanon_time():
    # هنا أضفت 4 فراغات قبل كلمة return لإصلاح الخطأ
    return (datetime.utcnow() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")

# --- 1. إعدادات التنسيق والهوية ---
LOGO_FILE = "IMG_6463.png"

st.set_page_config(
    page_title="شركة حلباوي إخوان",
    layout="centered",
    page_icon=LOGO_FILE if os.path.exists(LOGO_FILE) else None
)
st.markdown("""
 <style>
 #MainMenu {visibility: hidden;}
 footer {visibility: hidden;}
 header {visibility: hidden;}
 </style>
 """, unsafe_allow_html=True)

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;800&display=swap');
html, body, [class*="css"] {{ font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }}
div[data-testid="InputInstructions"], div[data-baseweb="helper-text"] {{ display: none !important; }}
/* تنسيق شريط الأخبار العاجلة */
.news-ticker {{
    background: #B22222;
    color: white;
    padding: 10px;
    font-weight: bold;
    font-size: 18px;
    border-radius: 5px;
    margin: 15px 0;
    overflow: hidden;
    white-space: nowrap;
    border-right: 5px solid #FFD700;
}}
.news-ticker marquee {{
    margin-bottom: -5px;
}}
.header-box {{ background-color: #1E3A8A; color: white; text-align: center; padding: 10px; border-radius: 10px; margin-bottom: 20px;}}
.return-header-box {{ background-color: #B22222; color: white; text-align: center; padding: 10px; border-radius: 10px; margin-bottom: 20px;}}
.sub-category-header {{
    background-color: #B22222;
    color: white;
    padding: 8px 15px;
    border-radius: 5px;
    font-weight: bold;
    margin-top: 25px;
    text-align: right;
    border-right: 10px solid #FFD700;
    font-size: 18px;
}}
.factory-item-header {{
    background-color: #1E3A8A;
    color: white;
    padding: 8px 15px;
    border-radius: 8px;
    font-weight: bold;
    margin-top: 10px;
    margin-bottom: 5px;
    text-align: right;
    font-size: 16px;
    border-right: 5px solid #FFD700;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.stock-tag {{
    background-color: #ffffff;
    color: #1E3A8A;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 13px;
    font-weight: 800;
}}
input {{ text-align: right !important; direction: rtl !important; }}
@media screen, print {{
    .invoice-preview, .return-preview {{
        border: 2px solid #000 !important;
        padding: 15px !important;
        width: 100% !important;
        background-color: white !important;
        color: black !important;
    }}
    .total-final, .return-total-final {{
        font-size: 20px !important;
        background-color: #f9f9f9 !important;
        border: 2px solid black !important;
        color: black !important;
        margin-top: 5px !important;
    }}
}}
.invoice-preview {{ background-color: white; padding: 25px; border: 2px solid #1E3A8A; border-radius: 10px; color: black; }}
.return-preview {{ background-color: white; padding: 25px; border: 2px solid #B22222; border-radius: 10px; color: black; }}
.company-header-center {{ text-align: center; border-bottom: 2px double #1E3A8A; padding-bottom: 10px; margin-bottom: 10px; }}
.return-header-center {{ text-align: center; border-bottom: 2 double #B22222; padding-bottom: 10px; margin-bottom: 10px; }}
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
.stock-card {{
    border: 2px solid #000; padding: 15px; border-radius: 10px; margin-bottom: 10px; background-color: #001f3f; color: #ffffff;
    box-shadow: 2px 2px 8px rgba(0,0,0,0.3); border-right: 8px solid #FFD700;
}}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
""", unsafe_allow_html=True)

# --- 2. إعدادات البيانات والربط ---
SHEET_ID = "1-Abj-Kvbe02az8KYZfQL0eal2arKw_wgjVQdJX06IA0"
GID_PRICES = "339292430"
GID_DATA = "0"
GID_CUSTOMERS = "155973706"

def get_gspread_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            service_account_info = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
            return gspread.authorize(creds)
        else:
            st.error("⚠️ المفاتيح السرية غير مضافة في إعدادات Streamlit Secrets")
            return None
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

@st.cache_data(ttl=30)
def load_urgent_news():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote('عاجل')}"
        df = pd.read_csv(url, header=None)
        if not df.empty:
            return " • ".join(df[0].astype(str).tolist())
        return ""
    except:
        return ""

@st.cache_data(ttl=60)
def load_rep_customers(rep_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={GID_CUSTOMERS}"
        df = pd.read_csv(url)
        rep_df = df[df.iloc[:, 0].astype(str).str.strip() == rep_name.strip()]
        return {f"{row.iloc[1]} ({row.iloc[2]})": row.iloc[1] for _, row in rep_df.iterrows()}
    except:
        return {}

@st.cache_data(ttl=60)
def load_products_from_excel():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={GID_PRICES}"
        df_p = pd.read_csv(url)
        df_p.columns = [c.strip() for c in df_p.columns]
        return pd.Series(df_p.iloc[:, 1].values, index=df_p.iloc[:, 0]).to_dict()
    except:
        return {"⚠️ خطأ": 0.0}

@st.cache_data(ttl=1)
def load_factory_items():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote('طلبات')}"
    try:
        df = pd.read_csv(url, header=None).dropna(how='all')
        df = df.iloc[:, :5]
        df.columns = ['cat', 'pack', 'sub', 'name', 'sci']
        return df
    except:
        return None

def get_next_invoice_number():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={GID_DATA}"
        df = pd.read_csv(url)
        if 'رقم الفاتوره' in df.columns:
            valid_nums = pd.to_numeric(df['رقم الفاتوره'], errors='coerce').dropna()
            if not valid_nums.empty:
                return str(int(valid_nums.max()) + 1)
        return "1001"
    except:
        return str(random.randint(10000, 99999))

def calculate_live_stock(rep_name):
    client = get_gspread_client()
    if not client: 
        return None
    try:
        sheet = client.open_by_key(SHEET_ID)
        rep_sheet = sheet.worksheet(rep_name.strip())
        data_in = rep_sheet.get_all_values()
        if len(data_in) <= 1: 
            return pd.Series()
        df = pd.DataFrame(data_in[1:], columns=data_in[0])
        df.iloc[:, 2] = pd.to_numeric(df.iloc[:, 2], errors='coerce').fillna(0)
        inventory = df.groupby(df.columns[1])[df.columns[2]].sum()
        return inventory
    except: 
        return pd.Series()

def send_to_google_sheets(vat, total_pre, inv_no, customer, representative, items_list, is_ret=False):
    url_script = "https://script.google.com/macros/s/AKfycbzi3kmbVyg_MV1Nyb7FwsQpCeneGVGSJKLMpv2YXBJR05v8Y77-Ub2SpvViZWCCp1nyqA/exec"
    l_time = get_lebanon_time()
    prefix = "(مرتجع) " if is_ret else ""
    data = {
        "vat_value": vat, 
        "total_before": total_pre, 
        "invoice_no": inv_no, 
        "cust_name": f"{prefix}{customer}", 
        "rep_name": representative, 
        "date_full": l_time
    }
    try:
        requests.post(url_script, data=data, timeout=10)
        client = get_gspread_client()
        if client:
            sheet = client.open_by_key(SHEET_ID)
            rep_sheet = sheet.worksheet(representative.strip())
            rows_to_deduct = []
            for itm in items_list:
                qty_val = itm['العدد'] if is_ret else -itm['العدد']
                status_text = "مبيعات" if not is_ret else "مرتجع من زبون"
                rows_to_deduct.append([l_time, itm['الصنف'], qty_val, status_text])
            rep_sheet.append_rows(rows_to_deduct)
        return True
    except: 
        return False


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
USERS = {
 "عبد الكريم حوراني": "9900",
 "محمد الحسيني": "8822",
 "علي دوغان": "5500",
 "عزات حلاوي": "6611",
 "علي حسين حلباوي": "4455",
 "محمد حسين حلباوي": "3366",
 "احمد حسين حلباوي": "7722",
 "علي محمد حلباوي": "6600"
}

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

if os.path.exists(LOGO_FILE):
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

# --- إضافة شريط الأخبار العاجلة المتحرك ---
urgent_text = load_urgent_news()
if urgent_text:
    st.markdown(f"""
    <div class="news-ticker">
        <marquee behavior="scroll" direction="right" scrollamount="6">
            ⚠️ عاجل من الإدارة: {urgent_text}
        </marquee>
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.page == 'stock_view':
  st.markdown("### 📋 حمولة السيارة (الحاليه)")
  client = get_gspread_client()
  if client:
      try:
          sheet = client.open_by_key(SHEET_ID)
          # 1. جلب قائمة الترتيب من صفحة "اسعار"
          price_sheet = sheet.worksheet("اسعار")
          ordered_names = [n.strip() for n in price_sheet.col_values(1)[1:] if n.strip()]

          # 2. جلب سجلات المندوب
          rep_sheet = sheet.worksheet(st.session_state.user_name.strip())
          data_in = rep_sheet.get_all_values()

          if len(data_in) > 1:
              df = pd.DataFrame(data_in[1:], columns=data_in[0])
              df.iloc[:, 2] = pd.to_numeric(df.iloc[:, 2], errors='coerce').fillna(0)

              # حساب المجموع لكل صنف
              inv_dict = df.groupby(df.columns[1], sort=False)[df.columns[2]].sum().to_dict()

              # إنشاء قائمة للعرض مرتبة
              display_items = []

              # أولاً: إضافة الأصناف الموجودة في قائمة الأسعار (بالترتيب)
              for name in ordered_names:
                  if name in inv_dict:
                      qty = inv_dict.pop(name) # نأخذ القيمة ونحذفها من القاموس المؤقت
                      if qty > 0:
                          display_items.append((name, qty))

              # ثانياً: إضافة أي أصناف متبقية في الجرد وليست في قائمة الأسعار (في الأسفل)
              for name, qty in inv_dict.items():
                  if qty > 0:
                      display_items.append((name, qty))

              # 3. العرض الفعلي في التطبيق
              if display_items:
                   for item, qty in display_items:
                      # المنطق الجديد: إذا الصنف دزينة (*12) الأحمر للـ 1 وما دون، وإلا الأحمر للـ 10 وما دون
                      if "*12" in item:
                          qty_color = "#00FF00" if qty > 1 else "#FF4B4B"
                      else:
                          qty_color = "#00FF00" if qty > 10 else "#FF4B4B"
                         
                      st.markdown(f'<div style="display:flex; justify-content:space-between; padding:10px; border-bottom:1px solid #444;"><span>{item}</span><b style="color:{qty_color};">{int(qty)}</b></div>', unsafe_allow_html=True)

              else:
                  st.info("لا توجد كميات متوفرة.")
          else:
              st.info("لا توجد حركات مسجلة لهذا المندوب.")

      except Exception as e:
          # معالجة الخطأ الذي ظهر لك في الصورة
          st.error(f"خطأ في جلب البيانات: تأكد من تطابق أسماء الأصناف.")
          st.info("💡 نصيحة: تأكد أن الأصناف في صفحة المندوب مطابقة تماماً لصفحة الأسعار.")

  if st.button("🔙 العودة للرئيسية", use_container_width=True):
      st.session_state.page = 'home'; st.rerun()

elif st.session_state.page == 'order':
  is_ret = st.session_state.is_return
  if 'live_stock' not in st.session_state:
      def calculate_live_stock(rep_name):
          client = get_gspread_client()
          if not client: return None
          try:
              sheet = client.open_by_key(SHEET_ID)
              # 1. ترتيب الأصناف من صفحة اسعار
              price_sheet = sheet.worksheet("اسعار")
              ordered_names = [name for name in price_sheet.col_values(1)[1:] if name.strip()]
              # 2. حركات المندوب
              rep_sheet = sheet.worksheet(rep_name.strip())
              data_in = rep_sheet.get_all_values()
              if len(data_in) <= 1: return pd.Series()
              df = pd.DataFrame(data_in[1:], columns=data_in[0])
              df.iloc[:, 2] = pd.to_numeric(df.iloc[:, 2], errors='coerce').fillna(0)
              # 3. الحساب والترتيب
              inventory = df.groupby(df.columns[1], sort=False)[df.columns[2]].sum()
              inventory = inventory.reindex(ordered_names).fillna(0)
              return inventory[inventory > 0]
          except:
              return pd.Series()

      st.session_state.live_stock = calculate_live_stock(st.session_state.user_name)

  if st.session_state.receipt_view:
      raw = sum(i["العدد"] * i["السعر"] for i in st.session_state.temp_items)
      h = float(convert_ar_nav(st.session_state.get('last_disc', '0')))
      aft = raw * (1 - h/100)
      vat = sum(((i["العدد"] * i["السعر"]) * (1 - h/100)) * 0.11 for i in st.session_state.temp_items if "*" in i["الصنف"])
      net = aft + vat
      c_n = st.session_state.get('last_cust', '..........')
      st.markdown(f'<div class="receipt-container"><div class="receipt-comp-name">شركة حلباوي إخوان ش.م.م</div><div class="receipt-comp-addr">بيروت - الرويس</div><div class="receipt-comp-tel">03/220893 - 01/556058</div><div class="dashed-line"></div><div class="receipt-title">{"إشعار مرتجع" if is_ret else "إشعار بالاستلام"}</div><div class="dashed-line"></div><div class="receipt-body">السيد: {c_n}<br>مبلغ وقدره: <span style="font-weight:800;">{net:,.2f}$</span><br>عن فاتورة رقم: #{st.session_state.inv_no}</div><div class="receipt-footer">التاريخ: {get_lebanon_time()}<br>المندوب: {st.session_state.user_name}</div></div>', unsafe_allow_html=True)
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

          # --- ضع هذا الكود المطور مكانه ---
      wid = st.session_state.widget_id
      search_p = st.text_input("🔍 ابحث عن صنف...", key=f"s_{wid}")

      p_list = [p for p in PRODUCTS.keys() if search_p in p]
      sel_p = st.selectbox("الصنف", ["-- اختر --", "➕ صنف غير مدرج (يدوي)"] + p_list, key=f"p_{wid}")

      if sel_p == "➕ صنف غير مدرج (يدوي)":
          m_name = st.text_input("اسم الصنف (كما في الجرد)")
          m_price = st.text_input("السعر ($)")
          m_qty = st.text_input("العدد", key=f"q_manual_{wid}")
          if st.button("➕ إضافة الصنف اليدوي", use_container_width=True):
              if m_name and m_price and m_qty:
                  try:
                      p_v = float(convert_ar_nav(m_price))
                      q_v = float(convert_ar_nav(m_qty))
                      st.session_state.temp_items.append({"الصنف": m_name, "العدد": q_v, "السعر": p_v})
                      st.session_state.widget_id += 1; st.rerun()
                  except: st.error("أرقام غير صحيحة")

      elif sel_p != "-- اختر --":
          stock_val = st.session_state.live_stock.get(sel_p, 0)
          st.info(f"💡 المتوفر: {int(stock_val)}")
          qty_str = st.text_input("العدد", key=f"q_{wid}")
          if st.button("➕ إضافة صنف", use_container_width=True):
              if qty_str.strip():
                  try:
                      q_v = float(convert_ar_nav(qty_str))
                      st.session_state.temp_items.append({"الصنف": sel_p, "العدد": q_v, "السعر": PRODUCTS[sel_p]})
                      st.session_state.widget_id += 1; st.rerun()
                  except: pass

      if st.session_state.temp_items:
          st.markdown("### 🛒 مراجعة الأصناف")
          for i, itm in enumerate(st.session_state.temp_items):
              c_itm, c_del = st.columns([4, 1])
              with c_itm:
                  st.info(f"🔹 {itm['الصنف']} | العدد: {itm['العدد']}")
              with c_del:
                  if st.button("🗑️", key=f"del_{i}"):
                      st.session_state.temp_items.pop(i); st.rerun()

      if st.button("👁️ معاينة الفاتورة", use_container_width=True, type="primary"):
          if len(st.session_state.temp_items) > 11:
              st.error("⚠️ الحد الأقصى 11 صنف فقط.")
          else:
              st.session_state.confirmed = True

      if st.session_state.confirmed and st.session_state.temp_items:
          h_val = float(convert_ar_nav(disc_input))
          raw_sum = sum(i["العدد"] * i["السعر"] for i in st.session_state.temp_items)
          dis_amt = raw_sum * (h_val/100)
          aft_dis = raw_sum - dis_amt

          rows_html = ""
          vat_total = 0
          for itm in st.session_state.temp_items:
              l_t = itm["العدد"] * itm["السعر"]
              l_v = (l_t * (1 - h_val/100)) * 0.11 if "*" in itm["الصنف"] else 0
              vat_total += l_v
              rows_html += "<tr><td style='border:1px solid #ddd; padding:5px;'>" + str(itm['الصنف']) + "</td><td style='border:1px solid #ddd;'>" + str(itm['العدد']) + "</td><td style='border:1px solid #ddd;'>" + f"{itm['السعر']:.2f}" + "</td><td style='border:1px solid #ddd;'>" + f"{l_v:.2f}" + "</td><td style='border:1px solid #ddd;'>" + f"{l_t:.2f}" + "</td></tr>"

          for _ in range(11 - len(st.session_state.temp_items)):
              rows_html += "<tr style='height:35px;'><td style='border:1px solid #ddd;'>&nbsp;</td><td style='border:1px solid #ddd;'>&nbsp;</td><td style='border:1px solid #ddd;'>&nbsp;</td><td style='border:1px solid #ddd;'>&nbsp;</td><td style='border:1px solid #ddd;'>&nbsp;</td></tr>"

          net_total = aft_dis + vat_total
          html_template = """
          <div style="background-color: white; color: black; direction: rtl; font-family: sans-serif; padding: 10px; border: 1px solid #ccc; border-radius: 10px;">
              <div style="text-align: center;">
                  <h2 style="margin: 0; white-space: nowrap; font-size: 32px;">
                  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;شركة حلباوي إخوان <span style="font-size: 16px;">ش.م.م</span>
                  </h2>
                  <p style="margin: 2px 0; font-size: 12px;">بيروت - الرويس | 03/220893 - 01/556058</p>
                  <p style="margin: 1px 0; font-size: 11px; text-align: center; font-weight: bold;">رقم التسجيل: 601_596703</p>
                  <hr style="margin: 8px 0;">
                  <h3 style="color: #1E3A8A; margin: 0;">فاتورة مبيعات</h3>
                  <div style="font-weight: bold;">رقم: #INV_NO</div>
              </div>
              <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 14px;">
                  <span><b>الزبون:</b> <span style="font-weight: 900;">CUST_NAME</span></span>
                  <span style="text-align: left;"><b>التاريخ:</b> DATE_STR<br><b>المندوب:</b> USER_NAME</span>
              </div>
              <table style="width: 100%; border-collapse: collapse; text-align: center; margin-top: 10px; font-size: 12px;">
                  <thead style="background-color: #f4f4f4;">
                      <tr>
                          <th style="border: 1px solid #ddd; padding: 8px;">الصنف</th>
                          <th style="border: 1px solid #ddd;">العدد</th>
                          <th style="border: 1px solid #ddd;">السعر</th>
                          <th style="border: 1px solid #ddd;">VAT</th>
                          <th style="border: 1px solid #ddd;">إجمالي</th>
                      </tr>
                  </thead>
                  <tbody>TABLE_ROWS</tbody>
              </table>
              <div style="margin-top: 10px; border-top: 1px solid #eee; padding-top: 10px;">
                  <div style="display: flex; justify-content: space-between;"><span>المجموع:</span><span>$RAW_SUM</span></div>
                  <div style="display: flex; justify-content: space-between; color: red;"><span>الحسم (DISC_PER%):</span><span>-$DIS_AMT</span></div>
                  <div style="display: flex; justify-content: space-between; font-weight: bold; border-top: 1px dashed #ccc; margin-top: 5px;"><span>بعد الحسم:</span><span>$AFT_DIS</span></div>
                  <div style="display: flex; justify-content: space-between;"><span>ضريبة VAT 11%:</span><span>+$VAT_VAL</span></div>
                  <div style="display: flex; justify-content: space-between; font-weight: bold; font-size: 20px; color: white; background-color: #1E3A8A; margin-top: 10px; padding: 12px; border-radius: 8px;">
                      <span>الإجمالي الصافي:</span><span>$NET_TOT</span>
                  </div>
              </div>
          </div>
          """

          final_html = html_template.replace("INV_NO", str(st.session_state.inv_no))\
                                    .replace("CUST_NAME", str(cust))\
                                    .replace("DATE_STR", str(get_lebanon_time().split()[0]))\
                                    .replace("USER_NAME", str(st.session_state.user_name))\
                                    .replace("TABLE_ROWS", rows_html)\
                                    .replace("RAW_SUM", f"{raw_sum:,.2f}")\
                                    .replace("DISC_PER", str(h_val))\
                                    .replace("DIS_AMT", f"{dis_amt:,.2f}")\
                                    .replace("AFT_DIS", f"{aft_dis:,.2f}")\
                                    .replace("VAT_VAL", f"{vat_total:,.2f}")\
                                    .replace("NET_TOT", f"{net_total:,.2f}")

          st.markdown(final_html, unsafe_allow_html=True)
          total_vat_to_send = vat_total
          raw_sum_to_send = raw_sum

                     # 1. نتحقق إذا كان الزر قد ضُغط مسبقاً لمنع التكرار
          if "is_sent" not in st.session_state:
              st.session_state.is_sent = False

          # 2. إضافة خاصية disabled للزر
          if st.button("💾 حفظ وخصم من الجرد", use_container_width=True, disabled=st.session_state.is_sent):
              v_vat = f"-{total_vat_to_send:.2f}" if is_ret else f"{total_vat_to_send:.2f}"
              v_raw = f"-{raw_sum_to_send:.2f}" if is_ret else f"{raw_sum_to_send:.2f}"
             
              if send_to_google_sheets(v_vat, v_raw, st.session_state.inv_no, cust, st.session_state.user_name, st.session_state.temp_items, is_ret):
                  st.session_state.is_sent = True  # تفعيل القفل فوراً بعد النجاح
                  if 'live_stock' in st.session_state: del st.session_state['live_stock']
                  st.success("✅ تم الحفظ وتحديث الجرد!")
                  st.rerun() # إعادة تشغيل الصفحة ليظهر الزر معطلاً فوراً

          # 3. تنبيه المستخدم في حال تم الحفظ
          if st.session_state.is_sent:
              st.warning("⚠️ هذه الفاتورة تم حفظها مسبقاً ولا يمكن تعديل الجرد مرة أخرى.")

          col1, col2 = st.columns(2)
          with col1:
              if st.button("🖨️ طباعة Xprinter"):
                  st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
          with col2:
              if st.button("🖨️ طباعة عادية"):
                  st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

      st.divider()
      cb, cr = st.columns(2)
      with cb:
          if st.button("🏠 الرئيسية"):
              if 'live_stock' in st.session_state: del st.session_state['live_stock']
              st.session_state.page = 'home'; st.rerun()
      with cr:
          if st.button("🧾 إشعار استلام"): st.session_state.receipt_view = True; st.rerun()

elif st.session_state.page == 'factory_home':
  df_f = load_factory_items()
  st.markdown("## 🏭 طلبية المعمل")
  if 'live_stock' not in st.session_state:
      st.session_state.live_stock = calculate_live_stock(st.session_state.user_name)
  if df_f is not None:
      for cat in df_f['cat'].unique():
          if st.button(f"📦 قسم {cat}", use_container_width=True):
              st.session_state.factory_cat = cat; st.session_state.page = 'factory_details'; st.rerun()
      if st.button("➕ أصناف خاصة", use_container_width=True):
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
  stock = st.session_state.get('live_stock', pd.Series())
  for pack in cat_df['pack'].unique():
      with st.expander(f"📦 تعبئة: {pack}", expanded=True):
          p_df = cat_df[cat_df['pack'] == pack]
          last_sub_title = None
          for _, row in p_df.iterrows():
              current_sub = row['sub']
              if current_sub != last_sub_title:
                  st.markdown(f'<div class="sub-category-header">{current_sub}</div>', unsafe_allow_html=True)
                  last_sub_title = current_sub
              item_name = row["name"]
              current_qty = int(stock.get(item_name, 0))
              st.markdown(f'<div class="factory-item-header"><span>{item_name}</span><span class="stock-tag">معي: {current_qty}</span></div>', unsafe_allow_html=True)
              q = st.text_input("الكمية", key=f"f_{row['name']}_{pack}", label_visibility="collapsed")
              if q: st.session_state.factory_cart[row['name']] = {"name": row['name'], "qty": q}
  st.divider()
  if st.button("✅ حفظ والعودة", use_container_width=True, type="primary"):
      st.session_state.page = 'factory_home'; st.rerun()

elif st.session_state.page == 'factory_review':
  st.markdown("### مراجعة سلة المعمل")
  f_list = []
  for k, v in st.session_state.factory_cart.items():
      st.write(f"🔹 {v['name']} -> {v['qty']}"); f_list.append(v)
  if st.button("🚀 إرسال للمعمل والواتساب", use_container_width=True):
      if send_to_factory_sheets(st.session_state.user_name, f_list):
          msg = f"طلبية معمل من: {st.session_state.user_name}\n" + "\n".join([f"- {i['name']}: {i['qty']}" for i in f_list])
          st.markdown(f'<a href="https://wa.me/96103220894?text={urllib.parse.quote(msg)}" class="wa-button">📲 إرسال واتساب</a>', unsafe_allow_html=True)
          st.session_state.factory_cart = {}; st.success("تم التسجيل!")
  if st.button("🔙 عودة"): st.session_state.page = 'factory_home'; st.rerun()

