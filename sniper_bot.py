import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime

# ==========================================
# ⚙️ CONFIGURACIÓN DE CONEXIONES (SEGURIDAD MÁXIMA)
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
URL_CARTERA = os.environ.get("URL_CARTERA")

def enviar_telegram(mensaje):
    """Transmisor seguro hacia el búnker."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: 
        print("Error OpSec: Faltan credenciales de Telegram.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"})

# ==========================================
# 🛡️ MÓDULO 1: AUDITORÍA DE SALIDAS
# ==========================================
def gestionar_salidas():
    print("🔎 Auditando posiciones activas en Google Sheets...")
    alertas = 0
    if not URL_CARTERA:
        print("Aviso: No se detectó URL_CARTERA en los secretos. Omitiendo auditoría de salidas.")
        return 0

    try:
        cartera = pd.read_csv(URL_CARTERA)
        if cartera.empty: return 0

        tickers = cartera['Ticker'].tolist()
        data = yf.download(tickers, period="1y", interval="1d", group_by="ticker", auto_adjust=True, progress=False)

        for _, row in cartera.iterrows():
            t = row['Ticker']
            
            # Extracción robusta anti-errores de yfinance
            if len(tickers) == 1:
                df = data.dropna()
            else:
                df = data[t].dropna() if t in data else pd.DataFrame()
            
            if df.empty or 'Close' not in df.columns: 
                continue

            cierre = float(df['Close'].iloc[-1])
            alto = float(df['High'].iloc[-1])
            bajo = float(df['Low'].iloc[-1])
            
            max_50 = float(df['High'].iloc[-50:].max())
            min_50 = float(df['Low'].iloc[-50:].min())
            premium_zone = max_50 - (max_50 - min_50) * 0.382
            
            vol_hoy = float(df['Volume'].iloc[-1])
            ma_vol = float(df['Volume'].rolling(20).mean().iloc[-1])
            score_fuerza = (min(vol_hoy / ma_vol, 2) / 2) * 100
            
            motivo = ""
            if bajo <= float(row['Stop_Loss']):
                motivo = f"🩸 *STOP LOSS EJECUTADO*: El precio perforó los ${float(row['Stop_Loss']):.2f}."
            elif alto >= float(row['Take_Profit']):
                motivo = f"🏆 *TAKE PROFIT ALCANZADO*: El precio tocó tu objetivo de ${float(row['Take_Profit']):.2f}."
            elif cierre >= premium_zone and score_fuerza < 45:
                motivo = f"📉 *ALERTA DE DISTRIBUCIÓN (Premium Zone)*: Precio en ${cierre:.2f}. Volumen institucional en {score_fuerza:.1f}%."

            if motivo:
                msg = f"⚠️ *ORDEN DE EXTRACCIÓN: {t}*\n\n{motivo}\n\n👉 _Acciona en tu broker y borra la fila en Google Sheets._"
                enviar_telegram(msg)
                alertas += 1
    except Exception as e: 
        print(f"Error en auditoría de cartera: {e}")
    return alertas

# ==========================================
# 🎯 MÓDULO 2: ESCÁNER DE NUEVAS OPORTUNIDADES
# ==========================================
def buscar_entradas():
    activos = [
        # 🇦🇷 ADRs y Acciones Locales (Fuerte Beta)
        "GGAL", "YPF", "BMA", "CEPU", "PAMP.BA", "EDN", "LOMA", "CRESY", "TGS", "VIST",
        "MELI", "NU", "AGRO", "GLOB", "DESP.BA", "TX", "ALUA.BA", "TXAR.BA", "STNE", "PAGS",
        
        # 🇧🇷 Brasil (Commodities y Bancos)
        "EWZ", "VALE", "PBR", "ITUB", "BBD", 
        
        # 🇺🇸 CEDEARs (Tech, Value & Mega Caps)
        "BABA", "AMZN", "AAPL", "MSFT", "NVDA", "TSLA", "META", "GOOGL", "AMD", 
        "KO", "PEP", "MCD", "WMT", "JPM", "V", "MA", "DIS", "NFLX", "INTC", "CSCO", 
        "XOM", "CVX", 
        
        # 🌐 ETFs (Índices y Sectores Globales)
        "SPY", "QQQ", "DIA", "IWM", "EEM", "XLF", "XLE", "ARKK"
    ]
    print(f"📡 Escaneando microestructura de {len(activos)} activos...")
    data = yf.download(activos, period="1y", interval="1d", group_by="ticker", auto_adjust=True, progress=False)
    
    entradas = 0
    for t in activos:
        try:
            # Extracción robusta anti-errores
            if len(activos) == 1:
                df = data.dropna()
            else:
                df = data[t].dropna() if t in data else pd.DataFrame()
                
            if df.empty or 'Volume' not in df.columns:
                continue

            df['MA20_Vol'] = df['Volume'].rolling(window=20).mean()
            cierre = float(df['Close'].iloc[-1])
            apertura = float(df['Open'].iloc[-1])
            alto = float(df['High'].iloc[-1])
            bajo = float(df['Low'].iloc[-1])
            vol = float(df['Volume'].iloc[-1])
            ma_vol = float(df['MA20_Vol'].iloc[-1])
            ayer = float(df['Close'].iloc[-2])
            
            r_high = float(df['High'].iloc[-50:].max())
            r_low = float(df['Low'].iloc[-50:].min())
            
            ote = r_high - (r_high - r_low) * 0.786
            tp_1618 = r_low + (r_high - r_low) * 1.618
            sl_estructural = r_low * 0.98  
            pz_intermedia = r_high - (r_high - r_low) * 0.382
            
            rango = alto - bajo if (alto - bajo) > 0 else 0.0001
            desp = abs(cierre - apertura) / rango
            vol_rel = vol / ma_vol if ma_vol > 0 else 1
            fuerza = (desp * 0.6 + (min(vol_rel, 2) / 2) * 0.4) * 100
            
            if bajo <= ote and fuerza > 70 and cierre > ayer:
                msg = (
                    f"🚨 *NUEVA ALERTA DE FRANCOTIRADOR* 🚨\n\n"
                    f"🎯 *Activo:* {t}\n"
                    f"💰 *Precio Entrada:* ${cierre:.2f}\n"
                    f"🔥 *Fuerza Institucional:* {fuerza:.1f}%\n"
                    f"✅ *Estructura:* MSS Confirmado en Zona OTE\n\n"
                    f"📋 *DATOS PARA TU GOOGLE SHEET:*\n"
                    f"🛑 *Stop Loss:* ${sl_estructural:.2f}\n"
                    f"🎯 *Take Profit:* ${tp_1618:.2f}\n"
                    f"⚠️ *Premium Zone:* ${pz_intermedia:.2f}\n"
                )
                enviar_telegram(msg)
                entradas += 1
        except Exception as e:
            print(f"Error procesando {t}: {e}")
            continue
    return entradas

# ==========================================
# 🚀 EJECUCIÓN DEL FLUJO PRINCIPAL
# ==========================================
if __name__ == "__main__":
    print("Iniciando operaciones del Búnker SMC...")
    salidas = gestionar_salidas()
    entradas = buscar_entradas()
    
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    mensaje_final = (
        f"🟢 *REPORTE DE BÚNKER SMC*\n"
        f"📅 Fecha: {fecha_hoy}\n"
        f"🛡️ Alertas de Salida emitidas: {salidas}\n"
        f"🎯 Nuevas Entradas detectadas: {entradas}\n\n"
        f"_Sistemas en modo suspensión hasta el próximo ciclo._"
    )
    enviar_telegram(mensaje_final)
    print("Operación finalizada. Transmisión cerrada.")
