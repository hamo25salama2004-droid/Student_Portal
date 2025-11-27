import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="بوابة الطالب", page_icon="🎓")

# --- الاتصال (نفس الكود) ---
def get_database():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client.open("School_System")

# --- تسجيل الدخول ---
if 'student_logged_in' not in st.session_state:
    st.session_state['student_logged_in'] = False

if not st.session_state['student_logged_in']:
    st.title("🔐 تسجيل دخول الطالب")
    with st.form("st_login"):
        user_code = st.text_input("كود الطالب")
        user_pass = st.text_input("الباسوورد", type="password")
        btn = st.form_submit_button("دخول")
        
        if btn:
            sheet = get_database()
            ws = sheet.worksheet("Students")
            try:
                cell = ws.find(user_code)
                if cell:
                    row_vals = ws.row_values(cell.row)
                    # Password is col 6 (index 5)
                    real_pass = row_vals[5]
                    if str(user_pass).strip() == str(real_pass).strip() and real_pass != "":
                        st.session_state['student_logged_in'] = True
                        st.session_state['student_data'] = row_vals
                        st.rerun()
                    else:
                        st.error("بيانات خاطئة")
                else:
                    st.error("الكود غير موجود")
            except:
                st.error("حدث خطأ في الاتصال")

# --- لوحة التحكم ---
else:
    data = st.session_state['student_data']
    # Data structure: [ID, Name, Phone, Total, Paid, Pass, RegDate]
    
    st.title(f"مرحباً, {data[1]} 👋")
    st.caption(f"تاريخ الدخول: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # 1. بيانات الطالب
    with st.expander("📄 بياناتي المالية", expanded=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("كود الطالب", data[0])
        col2.metric("تاريخ التسجيل", data[6])
        col3.metric("المبلغ المدفوع", f"{data[4]} ج.م")
    
    sheet = get_database()

    # 2. المواد والروابط
    st.subheader("📚 المواد والروابط")
    ws_mat = sheet.worksheet("Materials")
    mat_data = pd.DataFrame(ws_mat.get_all_records())
    
    # عرض المواد العامة
    st.markdown("##### 🌍 روابط عامة")
    global_mats = mat_data[mat_data['Type'] == 'Global']
    for index, row in global_mats.iterrows():
        st.markdown(f"- [{row['Title']}]({row['Link']})")
        
    # عرض مواد المعلمين (يمكنك فلترتها لاحقاً حسب الصف لو أضفت خانة الصف للمواد)
    st.markdown("##### 📖 روابط المواد")
    subject_mats = mat_data[mat_data['Type'] == 'Subject']
    for index, row in subject_mats.iterrows():
         st.markdown(f"- **{row['Title']}**: [اضغط هنا]({row['Link']})")

    # 3. النتائج
    st.subheader("🏆 النتائج والدرجات")
    ws_grades = sheet.worksheet("Grades")
    all_grades = ws_grades.get_all_records()
    df_grades = pd.DataFrame(all_grades)
    
    # تحويل العمود لسترينج للمقارنة
    df_grades['StudentID'] = df_grades['StudentID'].astype(str)
    
    my_grades = df_grades[df_grades['StudentID'] == str(data[0])]
    
    if not my_grades.empty:
        st.table(my_grades[['Subject', 'Score', 'Status', 'Date']])
    else:
        st.info("لم يتم رصد درجات بعد.")
