from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import sqlite3

app = FastAPI()

def init_db():
    conn = sqlite3.connect(':memory:')
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
            currency TEXT,
            notes TEXT,
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (debt_id) REFERENCES debts (id)
        )
    ''')
    conn.commit()
    return conn

db_connection = init_db()

@app.get("/", response_class=HTMLResponse)
async def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>تطبيق تسجيل الديون</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Cairo', sans-serif; background-color: #f8f9fa; }
            .client-card { cursor: pointer; transition: transform 0.2s; }
            .client-card:hover { transform: translateY(-5px); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            .green-btn { background-color: #28a745; color: white; }
            .green-btn:hover { background-color: #218838; color: white; }
            .red-btn { background-color: #dc3545; color: white; }
            .red-btn:hover { background-color: #c82333; color: white; }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-dark bg-primary mb-4">
            <div class="container">
                <span class="navbar-brand mb-0 h1">💰 تطبيق تسجيل الديون</span>
            </div>
        </nav>

        <div class="container" id="home-view">
            <div class="row mb-4">
                <div class="col-md-6">
                    <h2>إضافة عميل جديد</h2>
                    <div class="card">
                        <div class="card-body">
                            <form id="add-client-form">
                                <div class="mb-3">
                                    <label class="form-label">اسم العميل</label>
                                    <input type="text" class="form-control" id="client-name" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">رقم الهاتف (اختياري)</label>
                                    <input type="text" class="form-control" id="client-phone">
                                </div>
                                <button type="submit" class="btn btn-primary">إضافة العميل</button>
                            </form>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <h2>سجلات العملاء</h2>
                    <div id="clients-list" class="row"></div>
                </div>
            </div>
        </div>

        <div class="container" id="client-view" style="display: none;">
            <button class="btn btn-secondary mb-3" onclick="goHome()">← العودة</button>
            <h2 id="client-name-display"></h2>
            
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title">إجمالي الديون</h5>
                            <h3 class="card-text" id="total-debts">0</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title">إجمالي المدفوعات</h5>
                            <h3 class="card-text" id="total-paid">0</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title">الرصيد المتبقي</h5>
                            <h3 class="card-text" id="remaining">0</h3>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card mb-4">
                <div class="card-header">
                    <h5>سجل العمليات</h5>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>النوع</th>
                                    <th>المبلغ</th>
                                    <th>التاريخ</th>
                                </tr>
                            </thead>
                            <tbody id="transactions-table"></tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-success text-white">
                            <h5>💵 تسجيل تسديد</h5>
                        </div>
                        <div class="card-body">
                            <form id="payment-form">
                                <div class="mb-3">
                                    <label class="form-label">اختر الدين</label>
                                    <select class="form-select" id="debt-select" required></select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">مبلغ التسديد</label>
                                    <input type="number" class="form-control" id="payment-amount" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">العملة</label>
                                    <select class="form-select" id="payment-currency" required>
                                        <option value="ريال يمني" selected>ريال يمني</option>
                                        <option value="ريال سعودي">ريال سعودي</option>
                                        <option value="دولار أمريكي">دولار أمريكي</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">ملاحظات (اختياري)</label>
                                    <textarea class="form-control" id="payment-notes"></textarea>
                                </div>
                                <button type="submit" class="btn green-btn">تسديد</button>
                            </form>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-danger text-white">
                            <h5>➕ إضافة دين جديد</h5>
                        </div>
                        <div class="card-body">
                            <form id="debt-form">
                                <div class="mb-3">
                                    <label class="form-label">المبلغ</label>
                                    <input type="number" class="form-control" id="debt-amount" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">العملة</label>
                                    <select class="form-select" id="debt-currency" required>
                                        <option value="ريال يمني">ريال يمني</option>
                                        <option value="ريال سعودي">ريال سعودي</option>
                                        <option value="دولار أمريكي">دولار أمريكي</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">ملاحظات (اختياري)</label>
                                    <textarea class="form-control" id="debt-notes"></textarea>
                                </div>
                                <button type="submit" class="btn red-btn">إضافة الدين</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            let currentClientId = null;

            async function loadClients() {
                const response = await fetch('/api/clients');
                const clients = await response.json();
                const list = document.getElementById('clients-list');
                list.innerHTML = '';
                clients.forEach(client => {
                    list.innerHTML += `
                        <div class="col-md-6 mb-3">
                            <div class="card client-card" onclick="viewClient(${client.id}, '${client.name}')">
                                <div class="card-body">
                                    <h5 class="card-title">👤 ${client.name}</h5>
                                    <p class="card-text text-muted">اضغط لعرض السجل</p>
                                </div>
                            </div>
                        </div>
                    `;
                });
            }

            document.getElementById('add-client-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const name = document.getElementById('client-name').value;
                const phone = document.getElementById('client-phone').value;
                const response = await fetch('/api/clients', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, phone })
                });
                if (response.ok) {
                    alert('تم إضافة العميل بنجاح!');
                    document.getElementById('client-name').value = '';
                    document.getElementById('client-phone').value = '';
                    loadClients();
                } else {
                    alert('حدث خطأ');
                }
            });

            async function viewClient(clientId, clientName) {
                currentClientId = clientId;
                document.getElementById('home-view').style.display = 'none';
                document.getElementById('client-view').style.display = 'block';
                document.getElementById('client-name-display').textContent = `👤 ${clientName}`;
                
                const response = await fetch(`/api/clients/${clientId}`);
                const data = await response.json();
                
                document.getElementById('total-debts').textContent = data.summary.count;
                document.getElementById('total-paid').textContent = data.summary.paid.toLocaleString();
                document.getElementById('remaining').textContent = (data.summary.total - data.summary.paid).toLocaleString();
                
                const tbody = document.getElementById('transactions-table');
                tbody.innerHTML = '';
                
                data.transactions.forEach(t => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${t.type === 'debt' ? '🔴 دين' : '🟢 تسديد'}</td>
                        <td>${t.amount.toLocaleString()} ${t.currency}</td>
                        <td>${new Date(t.date).toLocaleString('ar-SA')}</td>
                    `;
                    tbody.appendChild(row);
                });
                
                const debtSelect = document.getElementById('debt-select');
                debtSelect.innerHTML = '';
                data.debts.forEach(d => {
                    const option = document.createElement('option');
                    option.value = d.id;
                    option.textContent = `دين ${d.amount.toLocaleString()} ${d.currency} - ${new Date(d.created_at).toLocaleDateString('ar-SA')}`;
                    debtSelect.appendChild(option);
                });
            }

            function goHome() {
                document.getElementById('home-view').style.display = 'block';
                document.getElementById('client-view').style.display = 'none';
                currentClientId = null;
            }

            document.getElementById('payment-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const debtId = document.getElementById('debt-select').value;
                const amount = parseFloat(document.getElementById('payment-amount').value);
                const currency = document.getElementById('payment-currency').value;
                const notes = document.getElementById('payment-notes').value;
                
                const response = await fetch('/api/payments', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ debt_id: debtId, amount, currency, notes })
                });
                
                if (response.ok) {
                    alert('تم التسديد بنجاح!');
                    document.getElementById('payment-amount').value = '';
                    document.getElementById('payment-notes').value = '';
                    viewClient(currentClientId, document.getElementById('client-name-display').textContent.replace('👤 ', ''));
                }
            });

            document.getElementById('debt-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const amount = parseFloat(document.getElementById('debt-amount').value);
                const currency = document.getElementById('debt-currency').value;
                const notes = document.getElementById('debt-notes').value;
                
                const response = await fetch('/api/debts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ client_id: currentClientId, amount, currency, notes })
                });
                
                if (response.ok) {
                    alert('تم إضافة الدين بنجاح!');
                    viewClient(currentClientId, document.getElementById('client-name-display').textContent.replace('👤 ', ''));
                }
            });

            loadClients();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/clients")
async def get_clients():
    cursor = db_connection.cursor()
    cursor.execute('SELECT id, name, phone FROM clients ORDER BY name')
    clients = [{"id": c[0], "name": c[1], "phone": c[2]} for c in cursor.fetchall()]
    return JSONResponse(content=clients)

@app.post("/api/clients")
async def add_client(request: Request):
    data = await request.json()
    cursor = db_connection.cursor()
    try:
        cursor.execute('INSERT INTO clients (name, phone) VALUES (?, ?)', (data['name'], data.get('phone', '')))
        db_connection.commit()
        return JSONResponse(content={"success": True})
    except sqlite3.IntegrityError:
        return JSONResponse(content={"success": False, "error": "العميل موجود بالفعل"})

@app.get("/api/clients/{client_id}")
async def get_client(client_id: int):
    cursor = db_connection.cursor()
    cursor.execute('SELECT id, name, phone FROM clients WHERE id = ?', (client_id,))
    client = cursor.fetchone()
    
    cursor.execute('SELECT id, amount, currency, notes, paid, created_at FROM debts WHERE client_id = ? ORDER BY created_at DESC', (client_id,))
    debts = [{"id": d[0], "amount": d[1], "currency": d[2], "notes": d[3], "paid": d[4], "created_at": d[5]} for d in cursor.fetchall()]
    
    cursor.execute('SELECT COUNT(*), SUM(amount), SUM(paid) FROM debts WHERE client_id = ?', (client_id,))
    summary = cursor.fetchone()
    
    cursor.execute('''
        SELECT 'debt' as type, d.id, d.amount, d.currency, d.created_at, d.notes
        FROM debts d
        WHERE d.client_id = ?
        UNION ALL
        SELECT 'payment' as type, p.id, p.amount, p.currency, p.payment_date, p.notes
        FROM payments p
        JOIN debts d ON p.debt_id = d.id
        WHERE d.client_id = ?
        ORDER BY created_at DESC
    ''', (client_id, client_id))
    transactions = cursor.fetchall()
    
    return JSONResponse(content={
        "client": {"id": client[0], "name": client[1], "phone": client[2]},
        "debts": debts,
        "summary": {"count": summary[0], "total": summary[1] or 0, "paid": summary[2] or 0},
        "transactions": [{"type": t[0], "id": t[1], "amount": t[2], "currency": t[3], "date": t[4], "notes": t[5]} for t in transactions]
    })

@app.post("/api/debts")
async def add_debt(request: Request):
    data = await request.json()
    cursor = db_connection.cursor()
    cursor.execute('INSERT INTO debts (client_id, amount, currency, notes) VALUES (?, ?, ?, ?)',
                   (data['client_id'], data['amount'], data['currency'], data.get('notes', '')))
    db_connection.commit()
    return JSONResponse(content={"success": True})

@app.post("/api/payments")
async def add_payment(request: Request):
    data = await request.json()
    cursor = db_connection.cursor()
    cursor.execute('INSERT INTO payments (debt_id, amount, currency, notes) VALUES (?, ?, ?, ?)', 
                   (data['debt_id'], data['amount'], data.get('currency', 'ريال يمني'), data.get('notes', '')))
    cursor.execute('UPDATE debts SET paid = paid + ? WHERE id = ?', (data['amount'], data['debt_id']))
    db_connection.commit()
    return JSONResponse(content={"success": True})
