import streamlit as st
import streamlit.components.v1 as components

# إعدادات الصفحة
st.set_page_config(
    page_title="دفتر ديوني",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تخصيص الألوان والتصميم ليشابه الواجهة الأصلية
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }
    .metric-card {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# تهيئة بيانات الحالة الافتراضية
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'customers' not in st.session_state:
    # هيكل بيانات العملاء والديون
    st.session_state.customers = {
        "أحمد محمد": [
            {"type": "دين", "amount": 500, "date": "2026-06-01", "note": "شراء بضاعة"},
            {"type": "تسديد", "amount": 200, "date": "2026-06-05", "note": "دفعة أولى"}
        ],
        "خالد علي": [
            {"type": "دين", "amount": 1200, "date": "2026-05-20", "note": "قرض شخصي"}
        ]
    }

if 'selected_customer' not in st.session_state:
    st.session_state.selected_customer = None

# شاشة تسجيل الدخول
def login_screen():
    st.markdown("<h1 style='text-align: center;'>تسجيل الدخول - دفتر ديوني</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if username and password:  # يمكنك تخصيص شرط التحقق هنا
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("الرجاء إدخال بيانات الصحيحة")

# الآلة الحاسبة العائمة (تظهر في الواجهة كجزء عائم تفاعلي)
def floating_calculator():
    calc_html = """
    <div id="floating-calc" style="position: fixed; bottom: 20px; left: 20px; background: #1f2937; padding: 15px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); z-index: 9999; width: 220px; direction: ltr;">
        <div style="font-size: 14px; color: #fff; margin-bottom: 5px; text-align: right;">آلة حاسبة</div>
        <input type="text" id="calc-display" style="width: 100%; height: 35px; font-size: 18px; text-align: right; margin-bottom: 10px; background: #111; color: #0ff; border: 1px solid #444; border-radius: 5px;" disabled>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 5px;">
            <button onclick="clearCalc()" style="background: #ef4444; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">C</button>
            <button onclick="appendCalc('/')" style="background: #374151; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">/</button>
            <button onclick="appendCalc('*')" style="background: #374151; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">*</button>
            <button onclick="appendCalc('-')" style="background: #374151; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">-</button>
            <button onclick="appendCalc('7')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">7</button>
            <button onclick="appendCalc('8')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">8</button>
            <button onclick="appendCalc('9')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">9</button>
            <button onclick="appendCalc('+')" style="background: #374151; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">+</button>
            <button onclick="appendCalc('4')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">4</button>
            <button onclick="appendCalc('5')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">5</button>
            <button onclick="appendCalc('6')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">6</button>
            <button onclick="calculateResult()" style="background: #10b981; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer; grid-row: span 2;">=</button>
            <button onclick="appendCalc('1')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">1</button>
            <button onclick="appendCalc('2')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">2</button>
            <button onclick="appendCalc('3')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">3</button>
            <button onclick="appendCalc('0')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer; grid-column: span 2;">0</button>
            <button onclick="appendCalc('.')" style="background: #4b5563; color: #fff; border:none; padding: 8px; border-radius:4px; cursor:pointer;">.</button>
        </div>
    </div>
    <script>
        function appendCalc(val) {
            document.getElementById('calc-display').value += val;
        }
        function clearCalc() {
            document.getElementById('calc-display').value = '';
        }
        function calculateResult() {
            try {
                document.getElementById('calc-display').value = eval(document.getElementById('calc-display').value);
            } catch(e) {
                document.getElementById('calc-display').value = 'خطأ';
            }
        }
    </script>
    """
    components.html(calc_html, height=270)

# تطبيق الرئيسي بعد تسجيل الدخول
def main_app():
    # شريط التنقل الجانبي
    st.sidebar.title("إدارة دفتر ديوني")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.logged_in = False
        st.session_state.selected_customer = None
        st.rerun()

    st.sidebar.markdown("---")
    
    # عرض الآلة الحاسبة العائمة في الجانب أو الشاشة
    floating_calculator()

    # إذا لم يتم اختيار عميل، نعرض قائمة إجمالي العملاء
    if st.session_state.selected_customer is None:
        st.title("📊 لوحة التحكم - إجمالي العملاء")
        
        # إضافة عميل جديد
        with st.expander("➕ إضافة عميل جديد"):
            new_cust_name = st.text_input("اسم العميل الجديد")
            if st.button("حفظ العميل"):
                if new_cust_name and new_cust_name not in st.session_state.customers:
                    st.session_state.customers[new_cust_name] = []
                    st.success(f"تم إضافة العميل {new_cust_name} بنجاح")
                    st.rerun()
                else:
                    st.warning("الاسم موجود مسبقاً أو فارغ")

        st.markdown("### قائمة العملاء")
        
        # بطاقات أو جدول إجمالي العملاء
        if not st.session_state.customers:
            st.info("لا يوجد عملاء مضافين حالياً.")
        else:
            for cust, records in st.session_state.customers.items():
                total_debt = sum(r['amount'] for r in records if r['type'] == 'دين')
                total_paid = sum(r['amount'] for r in records if r['type'] == 'تسديد')
                remaining = total_debt - total_paid

                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                col1.markdown(f"**👤 {cust}**")
                col2.markdown(f"إجمالي الدين: `{total_debt}`")
                col3.markdown(f"المتبقي: **`{remaining}`**")
                
                if col4.button(f"عرض السجل", key=f"btn_{cust}2"):
                    st.session_state.selected_customer = cust
                    st.rerun()
                st.markdown("---")

    else:
        # عرض سجلات الديون الكاملة للعميل المحدد
        cust = st.session_state.selected_customer
        if st.button("⬅️ العودة إلى قائمة العملاء"):
            st.session_state.selected_customer = None
            st.rerun()

        st.title(, فلان: f"📁 سجل ديون العميل: {cust}")

        records = st.session_state.customers[cust]

        # نماذج إضافة دين أو تسديد
        col_add1, col_add2 = st.columns(2)
        with col_add1:
            with st.form(key="add_debt_form"):
                st.subheader("➕ أضف دين جديد")
                d_amount = st.number_input("المبلغ", min_value=0.0, step=10.0, key="d_amt")
                d_date = st.date_input("التاريخ", key="d_date")
                d_note = st.text_input("ملاحظة / البيان", key="d_note")
                submit_debt = st.form_submit_button("حفظ الدين")
                if submit_debt:
                    records.append({"type": "دين", "amount": d_amount, "date": str(d_date), "note": d_note})
                    st.success("تم إضافة الدين بنجاح")
                    st.rerun()

        with col_add2:
            with st.form(key="add_pay_form"):
                st.subheader("💵 تسجيل تسديد")
                p_amount = st.number_input("مبلغ التسديد", min_value=0.0, step=10.0, key="p_amt")
                p_date = st.date_input("تاريخ التسديد", key="p_date")
                p_note = st.text_input("ملاحظة التسديد", key="p_note")
                submit_pay = st.form_submit_button("حفظ التسديد")
                if submit_pay:
                    records.append({"type": "تسديد", "amount": p_amount, "date": str(p_date), "note": p_note})
                    st.success("تم تسجيل التسديد بنجاح")
                    st.rerun()

        st.markdown("---")
        st.subheader("📋 السجلات الكاملة (تعديل وحذف)")

        if not records:
            st.info("لا توجد سجلات مسجلة لهذا العميل بعد.")
        else:
            for idx, rec in enumerate(records):
                col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns([1, 2, 2, 2, 2])
                col_r1.write(f"#{idx+1}")
                col_r2.write(f"**{rec['type']}**")
                col_r3.write(f"المبلغ: {rec['amount']}")
                col_r4.write(f"التاريخ: {rec['date']}")
                
                # زر الحذف والتعديل لكل سطر
                with col_r5:
                    if st.button("🗑️ حذف", key=f"del_{cust}_{idx}"):
                        records.pop(idx)
                        st.success("تم الحذف بنجاح")
                        st.rerun()

        # زر حذف العميل بالكامل
        if st.button("🗑️ حذف العميل وسجلاته بالكامل", type="primary"):
            del st.session_state.customers[cust]
            st.session_state.selected_customer = None
            st.success("تم حذف العميل بنجاح")
            st.rerun()

# التحكم في عرض الشاشة بناءً على حالة تسجيل الدخول
if not st.session_state.logged_in:
    login_screen()
else:
    main_app()
