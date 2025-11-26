import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="Teacher Portal", layout="centered", page_icon="👨‍🏫")
st.markdown("""<style>body { direction: rtl; } .stButton>button { width: 100%; }</style>""", unsafe_allow_html=True)

SHEET_NAME = "users_database"

@st.cache_resource
def get_client():
    if "gcp_service_account" not in st.secrets:
        st.error("⚠️ يرجى إضافة المفاتيح في Secrets لهذا التطبيق.")
        st.stop()
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except: return None

def main():
    if 'teacher_user' not in st.session_state:
        st.markdown("<h1 style='text-align: center; color: #2e86c1;'>👨‍🏫 بوابة المعلم</h1>", unsafe_allow_html=True)
        with st.form("login"):
            c = st.text_input("كود المعلم")
            p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول"):
                client = get_client()
                try:
                    ws = client.open(SHEET_NAME).worksheet("Teachers_Main")
                    df = pd.DataFrame(ws.get_all_records())
                    df['Code'] = df['Code'].astype(str).str.strip()
                    df['Password'] = df['Password'].astype(str).str.strip()
                    u = df[(df['Code']==str(c).strip()) & (df['Password']==str(p).strip())]
                    if not u.empty:
                        st.session_state['teacher_user'] = u.iloc[0].to_dict()
                        st.rerun()
                    else: st.error("خطأ في البيانات")
                except: st.error("خطأ اتصال")
    else:
        u = st.session_state['teacher_user']
        st.markdown(f"### أهلاً بك د/ {u['Name']}")
        if st.button("خروج", type="primary"):
            del st.session_state['teacher_user']
            st.rerun()
        st.divider()
        st.info("المواد الدراسية المسندة إليك")
        
        client = get_client()
        sheet = client.open(SHEET_NAME)
        try:
            sub_ws = sheet.worksheet("Subjects_Data")
            df_sub = pd.DataFrame(sub_ws.get_all_records())
            df_sub['Teacher_Code'] = df_sub['Teacher_Code'].astype(str)
            my_subs = df_sub[df_sub['Teacher_Code'] == str(u['Code'])]
            
            if not my_subs.empty:
                for i, r in my_subs.iterrows():
                    with st.expander(f"📘 مادة: {r['Subject_Name']} (الفرقة {r['Year_Level']})"):
                        st_code = st.text_input("كود الطالب", key=f"s{i}")
                        grade = st.selectbox("التقدير", ["-", "ناجح", "راسب", "امتياز"], key=f"g{i}")
                        if st.button("رصد الدرجة", key=f"b{i}"):
                            if st_code and grade != "-":
                                try:
                                    ws_st = sheet.worksheet(st_code)
                                    ws_st.append_row([f"نتيجة {r['Subject_Name']}", grade, str(datetime.now()), ""])
                                    st.success(f"تم رصد {grade} للطالب")
                                except: st.error("كود الطالب غير صحيح")
            else: st.warning("لا توجد مواد مسندة إليك.")
        except: st.error("جدول المواد غير موجود")

if __name__ == '__main__':
    main()
