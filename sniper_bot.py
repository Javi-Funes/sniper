import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime

# ==========================================
# ⚙️ CREDENCIALES ENCRIPTADAS (Vía GitHub Secrets)
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def enviar_mensaje_telegram(mensaje):
    """Función maestra para transmitir al búnker vía Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Credenciales de Telegram no encontradas en el servidor.")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Fallo en la transmisión de Telegram: {e}")

def enviar_alerta_francotirador(ticker, precio, ote, fuerza):
    """Dispara la alerta táctica cuando el Smart Money confirma entrada."""
    mensaje = (
        f"🚨 *ALERTA DE FRANCOTIRADOR SMC* 🚨\n\n"
        f"🎯 *Activo:* {ticker}\n"
        f"💰 *Precio Cierre:* ${precio:.2f}\n"
        f"📉 *Zona OTE (0.786):* ${ote:.2f}\n"
        f"🔥 *Fuerza Institucional:* {fuerza:.1f}%\n"
        f"✅ *Estructura (MSS):* Confirmado (Rechazo Alcista)\n\n"
        f"🛡️ _Acción: Evaluar entrada mañana. Stop Loss bajo el mínimo de hoy (Riesgo máx 1.5%)._"
    )
    enviar_mensaje_telegram(mensaje)

# ==========================================
# 1. CONFIGURACIÓN DEL RADAR (ACCIONES + ETFs)
# ==========================================
tickers_byma = [
    # ADRs y Acciones Locales (BYMA)
    "GGAL", "YPF", "BMA", "CEPU", "PAMP.BA", "EDN", "LOMA", "CRESY", "TGS", "VIST",
    "MELI", "NU", "AGRO", "GLOB", "DESP.BA", "TX", "ALUA.BA", "TXAR.BA", "STNE", "PAGS",
    "EWZ", "VALE", "PBR", "ITUB", "BBD", 
    
    # CEDEARs (Mega Caps & Value)
    "BABA", "AMZN", "AAPL", "MSFT", "NVDA", "TSLA", "META", "GOOGL", "AMD", 
    "KO", "PEP", "MCD", "WMT", "JPM", "V", "MA", "DIS", "NFLX", "INTC", "CSCO", 
    "XOM", "CVX", 
    
    # ETFs (Los índices y sectores más pesados en BYMA)
    "SPY",   # S&P 500
    "QQQ",   # Nasdaq 100
    "DIA",   # Dow Jones
    "IWM",   # Russell 2000 (Small Caps)
    "EEM",   # Emerging Markets
    "XLF",   # Financial Sector
    "XLE",   # Energy Sector
    "ARKK"   # Ark Innovation ETF
]

print(f"📡 BÚNKER TÁCTICO: Iniciando barrido de {len(tickers_byma)} activos...")
data = yf.download(tickers_byma, period="1y", interval="1d", group_by="ticker", auto_adjust=True, progress=False)

# Aplanar columnas si yfinance devuelve MultiIndex
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

alertas_enviadas = 0
activos_analizados = 0

# ==========================================
# 2. MOTOR DE MICROESTRUCTURA (SMC / WYCKOFF)
# ==========================================
for ticker in tickers_byma:
    try:
        df = data[ticker].dropna()
        if len(df) < 55: 
            continue
            
        activos_analizados += 1
        df['MA20_Vol'] = df['Volume'].rolling(window=20).mean()
        
        # Telemetría de la última sesión
        hoy_close = float(df['Close'].iloc[-1])
        hoy_open = float(df['Open'].iloc[-1])
        hoy_high = float(df['High'].iloc[-1])
        hoy_low = float(df['Low'].iloc[-1])
        hoy_vol = float(df['Volume'].iloc[-1])
        ma20_vol_hoy = float(df['MA20_Vol'].iloc[-1])
        ayer_close = float(df['Close'].iloc[-2])
        
        # Estructura Macro (Últimos 50 días)
        r_high = float(df['High'].iloc[-50:].max())
        r_low = float(df['Low'].iloc[-50:].min())
        ote_level = r_high - (r_high - r_low) * 0.786
        
        # Proxy de Fuerza Institucional (60% Desplazamiento / 40% Volumen)
        rango_vela = hoy_high - hoy_low if (hoy_high - hoy_low) > 0 else 0.0001
        desplazamiento = abs(hoy_close - hoy_open) / rango_vela
        vol_relativo = hoy_vol / ma20_vol_hoy if ma20_vol_hoy > 0 else 1
        strength_score = (desplazamiento * 0.6 + (min(vol_relativo, 2) / 2) * 0.4) * 100
        
        # Reglas de Gatillo SMC
        en_zona_ote = hoy_low <= ote_level
        tiene_fuerza = strength_score > 70
        hay_mss = hoy_close > ayer_close
        
        # Ejecución de Alerta
        if en_zona_ote and tiene_fuerza and hay_mss:
            print(f"🔥 OBJETIVO FIJADO: {ticker} | Fuerza: {strength_score:.1f}%")
            enviar_alerta_francotirador(ticker, hoy_close, ote_level, strength_score)
            alertas_enviadas += 1
            
    except Exception as e:
        print(f"Error procesando {ticker}: {e}")
        pass

# ==========================================
# 3. PING DE SUPERVIVENCIA (REPORTE DE CIERRE)
# ==========================================
fecha_hoy = datetime.now().strftime("%Y-%m-%d")
print("\n" + "="*60)
print(f"🔫 BARRIDO COMPLETADO ({fecha_hoy}). Alertas: {alertas_enviadas}")
print("="*60)

mensaje_final = (
    f"🟢 *BÚNKER SMC - REPORTE DE CIERRE*\n"
    f"📅 Fecha: {fecha_hoy}\n"
    f"📊 Activos escaneados: {activos_analizados}/{len(tickers_byma)}\n"
    f"🎯 Alertas tácticas generadas: {alertas_enviadas}\n\n"
    f"_El radar entra en modo suspensión hasta el próximo ciclo._"
)
enviar_mensaje_telegram(mensaje_final)
