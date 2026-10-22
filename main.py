from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
from datetime import datetime
import uvicorn

app = FastAPI()

templates = Jinja2Templates(directory="templates")

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

init_db()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    conn = sqlite3.connect('debts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM clients ORDER BY name')
    clients = [{"id": c[0], "name": c[1]} for c in cursor.fetchall()]
    conn.close()
    return templates.TemplateResponse("index.html", {"request": request, "clients": clients})

@app.get("/api/clients")
async def get_clients():
    conn = sqlite3.connect('debts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, phone FROM clients ORDER BY name')
    clients = [{"id": c[0], "name": c[1], "phone": c[2]} for c in cursor.fetchall()]
    conn.close()
    return clients

@app.post("/api/clients")
async def add_client(request: Request):
    data = await request.json()
    conn = sqlite3.connect('debts.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO clients (name, phone) VALUES (?, ?)', (data['name'], data.get('phone', '')))
        conn.commit()
        conn.close()
        return {"success": True}
    except sqlite3.IntegrityError:
        conn.close()
        return {"success": False, "error": "العميل موجود بالفعل"}

@app.get("/api/clients/{client_id}")
async def get_client(client_id: int):
    conn = sqlite3.connect('debts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, phone FROM clients WHERE id = ?', (client_id,))
    client = cursor.fetchone()
    
    cursor.execute('''
        SELECT id, amount, currency, notes, paid, created_at 
        FROM debts 
        WHERE client_id = ? 
        ORDER BY created_at DESC
    ''', (client_id,))
    debts = [{"id": d[0], "amount": d[1], "currency": d[2], "notes": d[3], "paid": d[4], "created_at": d[5]} for d in cursor.fetchall()]
    
    cursor.execute('SELECT COUNT(*), SUM(amount), SUM(paid) FROM debts WHERE client_id = ?', (client_id,))
    summary = cursor.fetchone()
    
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
    
    return {
        "client": {"id": client[0], "name": client[1], "phone": client[2]},
        "debts": debts,
        "summary": {"count": summary[0], "total": summary[1] or 0, "paid": summary[2] or 0},
        "transactions": [{"type": t[0], "id": t[1], "amount": t[2], "currency": t[3], "date": t[4], "notes": t[5]} for t in transactions]
    }

@app.post("/api/debts")
async def add_debt(request: Request):
    data = await request.json()
    conn = sqlite3.connect('debts.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO debts (client_id, amount, currency, notes) VALUES (?, ?, ?, ?)',
                   (data['client_id'], data['amount'], data['currency'], data.get('notes', '')))
    conn.commit()
    conn.close()
    return {"success": True}

@app.post("/api/payments")
async def add_payment(request: Request):
    data = await request.json()
    conn = sqlite3.connect('debts.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO payments (debt_id, amount) VALUES (?, ?)', (data['debt_id'], data['amount']))
    cursor.execute('UPDATE debts SET paid = paid + ? WHERE id = ?', (data['amount'], data['debt_id']))
    conn.commit()
    conn.close()
    return {"success": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
