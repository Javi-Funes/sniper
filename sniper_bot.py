import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os

# ==========================================
# ⚙️ CREDENCIALES ENCRIPTADAS (Vía GitHub Secrets)
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def enviar_alerta_francotirador(ticker, precio, ote, fuerza):
    mensaje = (
        f"🚨 *ALERTA DE FRANCOTIRADOR SMC* 🚨\n\n"
        f"🎯 *Activo:* {ticker}\n"
        f"💰 *Precio Actual:* ${precio:.2f}\n"
        f"📉 *Zona OTE:* ${ote:.2f} (En Descuento)\n"
        f"🔥 *Fuerza Institucional:* {fuerza:.1f}%\n"
        f"✅ *MSS:* Confirmado (Rechazo Alcista)\n\n"
        f"🛡️ _Acción: Evaluar entrada con Stop Loss estructural._"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Error enviando alerta para {ticker}: {e}")

# ==========================================
# 1. CONFIGURACIÓN DEL RADAR
# ==========================================
tickers_byma = [
    "GGAL", "YPF", "BMA", "CEPU", "PAMP.BA", "EDN", "LOMA", "CRESY", "TGS", "VIST",
    "MELI", "NU", "AGRO", "GLOB", "ALUA.BA", "TXAR.BA", "STNE", "PAGS",
    "EWZ", "VALE", "PBR", "ITUB", "BBD", 
    "BABA", "AMZN", "AAPL", "MSFT", "NVDA", "TSLA", "META", "GOOGL", "AMD", 
    "KO", "PEP", "MCD", "WMT", "JPM", "V", "MA", "DIS", "NFLX", "INTC", "CSCO", 
    "XOM", "CVX", "SPY", "QQQ", "DIA"
]

print("📡 Iniciando escaneo algorítmico y enlace con Telegram...")
data = yf.download(tickers_byma, period="1y", interval="1d", group_by="ticker", auto_adjust=True, progress=False)

alertas_enviadas = 0

# ==========================================
# 2. MOTOR DE MICROESTRUCTURA
# ==========================================
for ticker in tickers_byma:
    try:
        df = data[ticker].dropna()
        if len(df) < 55: continue
            
        df['MA20_Vol'] = df['Volume'].rolling(window=20).mean()
        
        hoy_close = float(df['Close'].iloc[-1])
        hoy_open = float(df['Open'].iloc[-1])
        hoy_high = float(df['High'].iloc[-1])
        hoy_low = float(df['Low'].iloc[-1])
        hoy_vol = float(df['Volume'].iloc[-1])
        ma20_vol_hoy = float(df['MA20_Vol'].iloc[-1])
        ayer_close = float(df['Close'].iloc[-2])
        
        r_high = float(df['High'].iloc[-50:].max())
        r_low = float(df['Low'].iloc[-50:].min())
        ote_level = r_high - (r_high - r_low) * 0.786
        
        rango_vela = hoy_high - hoy_low if (hoy_high - hoy_low) > 0 else 0.0001
        desplazamiento = abs(hoy_close - hoy_open) / rango_vela
        vol_relativo = hoy_vol / ma20_vol_hoy if ma20_vol_hoy > 0 else 1
        strength_score = (desplazamiento * 0.6 + (min(vol_relativo, 2) / 2) * 0.4) * 100
        
        en_zona_ote = hoy_low <= ote_level
        tiene_fuerza = strength_score > 70
        hay_mss = hoy_close > ayer_close
        
        if en_zona_ote and tiene_fuerza and hay_mss:
            enviar_alerta_francotirador(ticker, hoy_close, ote_level, strength_score)
            alertas_enviadas += 1
            
    except Exception as e:
        pass

print(f"\n🔫 ESCANEO COMPLETADO. Alertas disparadas: {alertas_enviadas}")
