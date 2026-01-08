import os
import json
import sys
import smtplib
import pandas as pd
import matplotlib.pyplot as plt

from email.message import EmailMessage
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet


# =========================
# 1. VALIDACIÓN DE SECRETS
# =========================
required_envs = [
    "GSHEET_CREDENTIALS",
    "SPREADSHEET_ID",
    "EMAIL_USER",
    "EMAIL_PASS"
]

for env in required_envs:
    if not os.getenv(env):
        print(f"ERROR: Falta la variable {env}")
        sys.exit(1)


# =========================
# 2. CONEXIÓN GOOGLE SHEETS
# =========================
creds_dict = json.loads(os.getenv("GSHEET_CREDENTIALS"))

scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)

client = gspread.authorize(credentials)

spreadsheet = client.open_by_key(os.getenv("SPREADSHEET_ID"))
worksheet = spreadsheet.sheet1

data = worksheet.get_all_records()
df = pd.DataFrame(data)

df["fecha"] = pd.to_datetime(df["fecha"])
df["monto"] = pd.to_numeric(df["monto"])


# =========================
# 3. FILTRO MES ACTUAL
# =========================
df["mes"] = df["fecha"].dt.to_period("M")
mes_actual = df["mes"].max()
df_mes = df[df["mes"] == mes_actual]


# =========================
# 4. MÉTRICAS PRINCIPALES
# =========================
ventas_totales = df_mes["monto"].sum()
ventas_categoria = df_mes.groupby("categoría")["monto"].sum()
ventas_mes = df.groupby("mes")["monto"].sum()
top_productos = (
    df_mes.groupby("producto")["monto"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)


# =========================
# 5. GRÁFICAS
# =========================
plt.figure()
ventas_mes.plot()
plt.title("Ventas mensuales")
plt.xlabel("Mes")
plt.ylabel("Monto ($)")
plt.tight_layout()
plt.savefig("ventas_mensuales.png")
plt.close()

plt.figure()
ventas_categoria.plot(kind="bar")
plt.title("Ventas por categoría")
plt.ylabel("Monto ($)")
plt.tight_layout()
plt.savefig("ventas_categoria.png")
plt.close()


# =========================
# 6. CREACIÓN PDF
# =========================
pdf_name = f"reporte_ventas_{mes_actual}.pdf"
styles = getSampleStyleSheet()

doc = SimpleDocTemplate(pdf_name)
elements = []

elements.append(Paragraph("Reporte mensual de ventas", styles["Title"]))
elements.append(Spacer(1, 20))

resumen = f"""
<b>Periodo:</b> {mes_actual}<br/>
<b>Ventas totales:</b> ${ventas_totales:,.2f}<br/>
<b>Categoría con mayor ingreso:</b> {ventas_categoria.idxmax()}
"""

elements.append(Paragraph(resumen, styles["Normal"]))
elements.append(Spacer(1, 20))

elements.append(Paragraph("Ventas en el tiempo", styles["Heading2"]))
elements.append(Image("ventas_mensuales.png", width=400, height=250))
elements.append(Spacer(1, 20))

elements.append(Paragraph("Ventas por categoría", styles["Heading2"]))
elements.append(Image("ventas_categoria.png", width=400, height=250))
elements.append(Spacer(1, 20))

elements.append(Paragraph("Top 10 productos", styles["Heading2"]))
for producto, monto in top_productos.items():
    elements.append(
        Paragraph(f"- {producto}: ${monto:,.2f}", styles["Normal"])
    )

doc.build(elements)


# =========================
# 7. ENVÍO DE CORREO
# =========================
msg = EmailMessage()
msg["Subject"] = f"Reporte mensual de ventas – {mes_actual}"
msg["From"] = os.getenv("EMAIL_USER")
msg["To"] = "hsan66694@gmail.com"

msg.set_content(
    f"""
Hola,

Adjuntamos el reporte mensual de ventas correspondiente a {mes_actual}.

Ventas totales: ${ventas_totales:,.2f}

Este reporte se genera automáticamente.

Saludos.
"""
)

with open(pdf_name, "rb") as f:
    msg.add_attachment(
        f.read(),
        maintype="application",
        subtype="pdf",
        filename=pdf_name
    )

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
    smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
    smtp.send_message(msg)

print("Reporte enviado correctamente")
