import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="تسجيل الديون", page_icon="💰", layout="wide")

st.markdown("""
    <style>
    div.stButton > button[kind="primary"] {
        background-color: #dc3545 !important;
        color: white !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #c82333 !important;
    }
    .green-btn {
        background-color: #28a745 !important;
        color: white !important;
    }
    .green-btn:hover {
        background-color: #218838 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💰 تطبيق تسجيل الديون")

def init_db():
    conn = sqlite3.connect('debts.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            notes TEXT,
            paid REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            debt_id INTEGER,
            amount REAL NOT NULL,
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (debt_id) REFERENCES debts (id)
        )
    ''')
    conn.commit()
    conn.close()

def get_clients():
    conn = sqlite3.connect('debts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM clients ORDER BY name')
    clients = cursor.fetchall()
    conn.close()
    return clients

def add_client(name, phone=""):
    conn = sqlite3.connect('debts.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO clients (name, phone) VALUES (?, ?)', (name, phone))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def add_debt(client_id, amount, currency, notes=""):
    conn = sqlite3.connect('debts.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO debts (client_id, amount, currency, notes) VALUES (?, ?, ?, ?)',
                   (client_id, amount, currency, notes))
    conn.commit()
    debt_id = cursor.lastrowid
    conn.close()
    return debt_id

def get_client_debts(client_id):
    conn = sqlite3.connect('debts.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, amount, currency, notes, paid, created_at 
        FROM debts 
        WHERE client_id = ? 
        ORDER BY created_at DESC
    ''', (client_id,))
    debts = cursor.fetchall()
    conn.close()
    return debts

def add_payment(debt_id, amount):
    conn = sqlite3.connect('debts.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO payments (debt_id, amount) VALUES (?, ?)', (debt_id, amount))
    cursor.execute('UPDATE debts SET paid = paid + ? WHERE id = ?', (amount, debt_id))
    conn.commit()
    conn.close()

def get_debt_payments(debt_id):
    conn = sqlite3.connect('debts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT amount, payment_date FROM payments WHERE debt_id = ? ORDER BY payment_date DESC', (debt_id,))
    payments = cursor.fetchall()
    conn.close()
    return payments

def get_client_transactions(client_id):
    conn = sqlite3.connect('debts.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 'debt' as type, d.id, d.amount, d.currency, d.created_at, d.notes, NULL as related_debt_id
        FROM debts d
        WHERE d.client_id = ?
        UNION ALL
        SELECT 'payment' as type, p.id, p.amount, d.currency, p.payment_date, NULL as notes, p.debt_id
        FROM payments p
        JOIN debts d ON p.debt_id = d.id
        WHERE d.client_id = ?
        ORDER BY created_at DESC
    ''', (client_id, client_id))
    transactions = cursor.fetchall()
    conn.close()
    return transactions

init_db()

if "selected_client_id" not in st.session_state:
    st.session_state.selected_client_id = None

if "selected_client_name" not in st.session_state:
    st.session_state.selected_client_name = None

clients = get_clients()
client_options = {"-- عميل جديد --": 0}
for client_id, client_name in clients:
    client_options[client_name] = client_id

if st.session_state.selected_client_id is not None:
    if st.button("← العودة إلى قائمة العملاء"):
        st.session_state.selected_client_id = None
        st.session_state.selected_client_name = None
        st.rerun()
    
    client_id = st.session_state.selected_client_id
    client_name = st.session_state.selected_client_name
    
    st.title(f"👤 سجل العميل: {client_name}")
    
    st.subheader("📊 ملخص الحساب")
    
    conn = sqlite3.connect('debts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*), SUM(amount), SUM(paid) FROM debts WHERE client_id = ?', (client_id,))
    result = cursor.fetchone()
    total_debts_count = result[0] or 0
    total_amount = result[1] or 0.0
    total_paid = result[2] or 0.0
    remaining_balance = total_amount - total_paid
    conn.close()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("إجمالي الديون", total_debts_count)
    with col2:
        st.metric("إجمالي المدفوعات", f"{total_paid:,.2f}")
    with col3:
        st.metric("الرصيد المتبقي", f"{remaining_balance:,.2f}")
    
    st.divider()
    
    st.subheader("📋 سجل العمليات")
    transactions = get_client_transactions(client_id)
    
    if not transactions:
        st.info("لا توجد عمليات لهذا العميل")
    else:
        import pandas as pd
        transaction_data = []
        for trans in transactions:
            trans_type, trans_id, amount, currency, date, notes, related_debt_id = trans
            if trans_type == 'debt':
                type_label = "دين"
                type_color = "🔴"
            else:
                type_label = "تسديد"
                type_color = "🟢"
            
            transaction_data.append({
                "": type_color,
                "النوع": type_label,
                "المبلغ": f"{amount:,.2f} {currency}",
                "التاريخ": date
            })
        
        df = pd.DataFrame(transaction_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    st.subheader("⚡ عمليات سريعة")
    col_left, col_right = st.columns(2)
    
    with col_left:
        with st.container():
            if st.button("💵 تسجيل تسديد", use_container_width=True, key="green_payment_btn"):
                st.session_state.show_payment = True
                st.rerun()
            
            if st.session_state.get("show_payment", False):
                debts = get_client_debts(client_id)
                if debts:
                    debt_options = {f"دين {d[1]:,.2f} {d[2]} - {d[5]}": d[0] for d in debts}
                    selected_debt_display = st.selectbox("اختر الدين للتسديد", list(debt_options.keys()), key="pay_debt_select")
                    pay_amount_str = st.text_input("مبلغ التسديد", key="pay_amount_input")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("تأكيد التسديد", key="confirm_payment"):
                            selected_debt_id = debt_options[selected_debt_display]
                            try:
                                pay_amount = float(pay_amount_str) if pay_amount_str else 0.0
                            except ValueError:
                                pay_amount = 0.0
                            
                            if pay_amount > 0:
                                debt_amount = next(d[1] - d[4] for d in debts if d[0] == selected_debt_id)
                                if pay_amount <= debt_amount:
                                    add_payment(selected_debt_id, pay_amount)
                                    st.success(f"تم تسديد {pay_amount:,.2f} بنجاح!")
                                    st.session_state.show_payment = False
                                    st.rerun()
                                else:
                                    st.error(f"المبلغ المُدخل يتجاوز المتبقي ({debt_amount:,.2f})")
                            else:
                                st.error("الرجاء إدخال المبلغ")
                    
                    with col_b:
                        if st.button("إلغاء", key="cancel_payment"):
                            st.session_state.show_payment = False
                            st.rerun()
                else:
                    st.info("لا توجد ديون للتسديد")
    
    with col_right:
        with st.container():
            if st.button("➕ إضافة دين جديد", use_container_width=True, type="primary"):
                st.session_state.show_add_debt = True
                st.rerun()
            
            if st.session_state.get("show_add_debt", False):
                new_amount_str = st.text_input("المبلغ", key="add_debt_amount")
                new_currency = st.selectbox("العملة", ["ريال يمني", "ريال سعودي", "دولار أمريكي"], key="add_debt_currency")
                new_notes = st.text_area("ملاحظات (اختياري)", key="add_debt_notes")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("تأكيد الإضافة", key="confirm_add_debt"):
                        try:
                            new_amount = float(new_amount_str) if new_amount_str else 0.0
                        except ValueError:
                            new_amount = 0.0
                        
                        if new_amount > 0:
                            add_debt(client_id, new_amount, new_currency, new_notes)
                            st.success("تم إضافة الدين بنجاح!")
                            st.session_state.show_add_debt = False
                            st.rerun()
                        else:
                            st.error("الرجاء إدخال المبلغ")
                
                with col_b:
                    if st.button("إلغاء", key="cancel_add_debt"):
                        st.session_state.show_add_debt = False
                        st.rerun()

else:
    tab1, tab2 = st.tabs(["➕ إضافة دين", "📋 سجلات العملاء"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header("إضافة دين جديد")
            
            selected_client = st.selectbox("اختر العميل", list(client_options.keys()))
            
            if selected_client == "-- عميل جديد --":
                with st.form("new_client_form"):
                    new_client_name = st.text_input("اسم العميل الجديد")
                    new_client_phone = st.text_input("رقم الهاتف (اختياري)")
                    new_client_submit = st.form_submit_button("إضافة العميل")
                    
                    if new_client_submit and new_client_name:
                        if add_client(new_client_name, new_client_phone):
                            st.success("تم إضافة العميل بنجاح!")
                            st.rerun()
                        else:
                            st.error("العميل موجود بالفعل!")
            else:
                client_id = client_options[selected_client]
                
                with st.form("debt_form"):
                    amount_str = st.text_input("المبلغ")
                    currency = st.selectbox("العملة", ["ريال يمني", "ريال سعودي", "دولار أمريكي"])
                    notes = st.text_area("ملاحظات (اختياري)")
                    
                    submitted = st.form_submit_button("حفظ الدين")
                    
                    if submitted:
                        try:
                            amount = float(amount_str) if amount_str else 0.0
                        except ValueError:
                            amount = 0.0
                        
                        if amount > 0:
                            add_debt(client_id, amount, currency, notes)
                            st.success("تم حفظ الدين بنجاح!")
                            st.rerun()
                        else:
                            st.error("الرجاء إدخال المبلغ")
        
        with col2:
            st.header("ملخص عام")
            
            conn = sqlite3.connect('debts.db')
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM debts')
            total_debts = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(amount - paid) FROM debts')
            total_amount = cursor.fetchone()[0] or 0.0
            conn.close()
            
            st.metric("إجمالي الديون", total_debts)
            st.metric("إجمالي المبالغ المتبقية", f"{total_amount:,.2f}")
    
    with tab2:
        st.header("سجلات العملاء")
        
        search_query = st.text_input("🔍 بحث عن عميل", key="search_client_input")
    filtered_clients = [c for c in clients if search_query.lower() in c[1].lower()]

    for client_id, client_name in filtered_clients:
     if st.button(f"👤 {client_name}", key=f"client_{client_id}"):
        st.session_state.selected_client_id = client_id
        st.session_state.selected_client_name = client_name
        st.rerun()