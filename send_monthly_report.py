import pandas as pd
import smtplib
import os
import json
import gspread
from email.message import EmailMessage
from datetime import datetime
from io import StringIO
from google.oauth2.service_account import Credentials

# =============================
# CREDENCIALES GOOGLE SHEETS
# =============================

creds_dict = json.loads(os.getenv("GSHEET_CREDENTIALS"))
scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
client = gspread.authorize(creds)

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# =============================
# CARGAR DATOS
# =============================

data = sheet.get_all_records()
df = pd.DataFrame(data)
df["fecha"] = pd.to_datetime(df["fecha"])

# =============================
# MES ANTERIOR
# =============================

hoy = datetime.today()
year = hoy.year
month = hoy.month - 1

if month == 0:
    month = 12
    year -= 1

df_mes = df[
    (df["fecha"].dt.year == year) &
    (df["fecha"].dt.month == month)
]

if df_mes.empty:
    raise ValueError("No hay ventas para el mes anterior")

# =============================
# KPIs
# =============================

ventas_totales = df_mes["monto"].sum()
ticket_promedio = df_mes["monto"].mean()
num_ventas = len(df_mes)

# =============================
# CSV
# =============================

buffer = StringIO()
df_mes.to_csv(buffer, index=False)

# =============================
# EMAIL
# =============================

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = "cliente@correo.com"

msg = EmailMessage()
msg["Subject"] = f"Reporte de ventas – {month}/{year}"
msg["From"] = EMAIL_USER
msg["To"] = EMAIL_TO

msg.set_content(
    f"""
Reporte automático de ventas

Periodo: {month}/{year}

Ventas totales: ${ventas_totales:,.2f} MXN
Ticket promedio: ${ticket_promedio:,.2f} MXN
Número de ventas: {num_ventas}

Este reporte fue generado automáticamente.
"""
)

msg.add_attachment(
    buffer.getvalue(),
    subtype="csv",
    filename=f"reporte_ventas_{month}_{year}.csv"
)

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(EMAIL_USER, EMAIL_PASS)
    server.send_message(msg)

print("Reporte enviado correctamente")
