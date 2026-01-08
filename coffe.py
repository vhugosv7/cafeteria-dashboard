import streamlit as st
import pandas as pd
import smtplib
from email.message import EmailMessage
from io import StringIO
import plotly.express as px

# -----------------------------
# Configuración de la app
# -----------------------------
st.set_page_config(page_title="Demo Ventas 2026", layout="wide")
st.title("Demo de Ventas 2026")
st.markdown("Carga tus ventas en CSV, analiza y envía un reporte automático por correo.")

# -----------------------------
# Carga de CSV
# -----------------------------
st.subheader("Carga tu archivo CSV")
uploaded_file = st.file_uploader("Sube un CSV con columnas: fecha, categoria, producto, monto", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["mes"] = df["fecha"].dt.month
    
    # -----------------------------
    # Filtros
    # -----------------------------
    st.sidebar.header("Filtros")

    categorias = st.sidebar.multiselect(
        "Categoría",
        options=df["categoria"].unique(),
        default=df["categoria"].unique()
    )

    meses = st.sidebar.multiselect(
        "Mes",
        options=sorted(df["mes"].unique()),
        default=sorted(df["mes"].unique())
    )

    filtered_df = df[(df["categoria"].isin(categorias)) & (df["mes"].isin(meses))]

    # -----------------------------
    # KPIs
    # -----------------------------
    st.subheader("Indicadores clave")
    #   col1 = st.columns(1)
    #   col1.metric("Ventas totales", f"${filtered_df['monto'].sum():,.0f} MXN")
    st.markdown("""
    <style>
    .kpi-card {
        padding: 20px;
        border-radius: 14px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.10);
    }

    .kpi-green {
        background-color: #DCFCE7;
       
        box-shadow: 0 6px 18px rgba(0,0,0,0.15);
    }
                
    .kpi-green:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.20);
        border-left: 6px solid #16A34A;
        cursor: pointer;
    }

    .kpi-blue {
        background-color: #DBEAFE;
        border-left: 6px solid #2563EB;
        box-shadow: 0 6px 18px rgba(0,0,0,0.15);
    }

    .kpi-orange {
        background-color: #FEF3C7;
        border-left: 6px solid #D97706;
        box-shadow: 0 6px 18px rgba(0,0,0,0.15);
    }

    .kpi-title {
        margin: 0;
        font-size: 16px;
    }

    .kpi-value {
        margin: 6px 0;
        font-size: 30px;
        font-weight: bold;
    }

    .kpi-delta {
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="kpi-card kpi-green"><p class="kpi-title">Ventas totales</p><p class="kpi-value">${:,.0f} MXN</p></div>'.format(filtered_df['monto'].sum()), unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="kpi-card kpi-blue"><p class="kpi-title">Ticket promedio</p><p class="kpi-value">${:,.0f} MXN</p></div>'.format(filtered_df['monto'].mean()), unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="kpi-card kpi-orange"><p class="kpi-title">Número de ventas</p><p class="kpi-value">{:,}</p></div>'.format(len(filtered_df)), unsafe_allow_html=True)



    # -----------------------------
    # Tabla
    # -----------------------------
    st.subheader("Tabla con detalle de ventas")
    st.dataframe(filtered_df, use_container_width=True)
    
    # -----------------------------
    # Gráficas
    # -----------------------------
    st.subheader("Ventas por categoría")
    
    sales = filtered_df.groupby("categoria")["monto"].sum().reset_index()
    fig2 = px.bar(
    sales,
    x='categoria',
    y='monto',
    text='monto',
    title='Ventas por categoría', 
    labels={'monto':'Monto MXN', 'categoria':'Categoría'},
    color='monto',
    color_continuous_scale='Viridis')

    st.plotly_chart(fig2, use_container_width=True)
    
    st.subheader(" Ventas por mes")
    monthly_sales = filtered_df.groupby("mes")["monto"].sum().reset_index()
    fig3 = px.line(
        monthly_sales,
        x="mes",
        y="monto",
        text="monto",
        title="Ventas por mes",
        labels={"mes": "Mes", "monto": "Monto MXN"},
        markers=True
    )
    fig3.update_traces(textposition="top center")
    st.plotly_chart(fig3, use_container_width=True)



    # -----------------------------
    # Envío de reporte por correo
    # -----------------------------
    st.subheader("Enviar reporte por correo")
    email_to = st.text_input("Correo destino")

    if st.button("Enviar reporte"):
        csv_buffer = StringIO()
        filtered_df.to_csv(csv_buffer, index=False)

        msg = EmailMessage()
        msg["Subject"] = "Reporte de ventas - Cafetería"
        msg["From"] = st.secrets["EMAIL_USER"]
        msg["To"] = email_to
        msg.set_content("Adjuntamos el reporte de ventas generado desde el dashboard.")

        msg.add_attachment(
            csv_buffer.getvalue(),
            subtype="csv",
            filename="reporte_ventas.csv"
        )

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(st.secrets["EMAIL_USER"], st.secrets["EMAIL_PASS"])
                
                server.send_message(msg)
            st.success("Reporte enviado correctamente")
        except Exception as e:
            st.error(f"Error al enviar correo: {e}")
#alja fqjb qteu lckv
else:
    st.warning("Sube un archivo CSV para comenzar")

st.markdown("---")

st.caption("Demo avanzada: carga de datos + envío automático de reportes.")
