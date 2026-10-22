from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import sqlite3
import os

app = FastAPI()

def init_db():
    # استخدام قاعدة بيانات في الذاكرة لـ Vercel
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
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (debt_id) REFERENCES debts (id)
        )
    ''')
    conn.commit()
    return conn

# إنشاء اتصال عالمي بقاعدة البيانات
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
        </style>
    </head>
    <body>
        <nav class="navbar navbar-dark bg-primary mb-4">
            <div class="container">
                <span class="navbar-brand mb-0 h1">💰 تطبيق تسجيل الديون</span>
            </div>
        </nav>
        <div class="container">
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
        <script>
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

# Vercel expects the app to be available
# No additional handler needed
