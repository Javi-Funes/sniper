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
# 🛡️ MÓDULO 1: AUDITORÍA DE SALIDAS (DUAL)
# ==========================================
def gestionar_salidas():
    print("🔎 Auditando posiciones activas en Google Sheets...")
    alertas = 0
    if not URL_CARTERA: return 0

    try:
        # Parche antibasura y lectura inteligente
        cartera = pd.read_csv(URL_CARTERA, sep=None, engine='python', on_bad_lines='skip')
        cartera.columns = cartera.columns.str.strip()
        
        columnas_requeridas = ['Ticker', 'Precio_Compra', 'Stop_Loss', 'Take_Profit']
        if not all(col in cartera.columns for col in columnas_requeridas):
            print(f"Error: Columnas en el archivo no coinciden: {cartera.columns.tolist()}")
            return 0

        tickers = cartera['Ticker'].tolist()
        data = yf.download(tickers, period="2y", interval="1d", group_by="ticker", auto_adjust=True, progress=False, threads=False)

        for _, row in cartera.iterrows():
            t = row['Ticker']
            df = data.dropna() if len(tickers) == 1 else (data[t].dropna() if t in data else pd.DataFrame())
            
            if df.empty or 'Close' not in df.columns: continue

            cierre = float(df['Close'].iloc[-1])
            alto = float(df['High'].iloc[-1])
            bajo = float(df['Low'].iloc[-1])
            
            # Premium Zones
            max_50 = float(df['High'].iloc[-50:].max())
            min_50 = float(df['Low'].iloc[-50:].min())
            pz_micro = max_50 - (max_50 - min_50) * 0.382
            
            max_250 = float(df['High'].iloc[-250:].max()) if len(df) >= 250 else max_50
            min_250 = float(df['Low'].iloc[-250:].min()) if len(df) >= 250 else min_50
            pz_macro = max_250 - (max_250 - min_250) * 0.382
            
            # Fuerza Institucional
            vol_hoy = float(df['Volume'].iloc[-1])
            ma_vol = float(df['Volume'].rolling(20).mean().iloc[-1])
            score_fuerza = (min(vol_hoy / ma_vol, 2) / 2) * 100
            
            motivo = ""
            if bajo <= float(row['Stop_Loss']):
                motivo = f"🩸 *STOP LOSS EJECUTADO*: El precio perforó los ${float(row['Stop_Loss']):.2f}."
            elif alto >= float(row['Take_Profit']):
                motivo = f"🏆 *TAKE PROFIT ALCANZADO*: El precio tocó tu objetivo de ${float(row['Take_Profit']):.2f}."
            elif cierre >= pz_macro and score_fuerza < 45:
                motivo = f"🌋 *DISTRIBUCIÓN MACRO*: Precio en ${cierre:.2f}. El activo llegó a la zona Premium anual y el volumen muere ({score_fuerza:.1f}%). Salida estructural."
            elif cierre >= pz_micro and score_fuerza < 45:
                motivo = f"⚡ *DISTRIBUCIÓN MICRO*: Precio en ${cierre:.2f}. Zona Premium de corto plazo. Volumen débil ({score_fuerza:.1f}%)."

            if motivo:
                msg = f"⚠️ *ORDEN DE EXTRACCIÓN: {t}*\n\n{motivo}\n\n👉 _Acciona en tu broker y borra la fila en Google Sheets._"
                enviar_telegram(msg)
                alertas += 1
    except Exception as e: 
        print(f"Error en auditoría de cartera: {e}")
    return alertas

# ==========================================
# 🎯 MÓDULO 2: ESCÁNER DE NUEVAS OPORTUNIDADES (DUAL)
# ==========================================
def buscar_entradas():
    activos = [
        "GGAL", "YPF", "BMA", "CEPU", "PAMP.BA", "EDN", "LOMA", "CRESY", "TGS", "VIST",
        "MELI", "NU", "AGRO", "GLOB", "TX", "ALUA.BA", "TXAR.BA", "STNE", "PAGS",
        "EWZ", "VALE", "PBR", "ITUB", "BBD", 
        "BABA", "AMZN", "AAPL", "MSFT", "NVDA", "TSLA", "META", "GOOGL", "AMD", 
        "KO", "PEP", "MCD", "WMT", "JPM", "V", "MA", "DIS", "NFLX", "INTC", "CSCO", 
        "XOM", "CVX", "SPY", "QQQ", "DIA", "IWM", "EEM", "XLF", "XLE", "ARKK"
    ]
    print(f"📡 Escaneando motor fractal (Micro/Macro) en {len(activos)} activos...")
    data = yf.download(activos, period="2y", interval="1d", group_by="ticker", auto_adjust=True, progress=False, threads=False)
    
    entradas = 0
    for t in activos:
        try:
            df = data.dropna() if len(activos) == 1 else (data[t].dropna() if t in data else pd.DataFrame())
            if df.empty or 'Volume' not in df.columns or len(df) < 250:
                continue

            df['MA20_Vol'] = df['Volume'].rolling(window=20).mean()
            cierre = float(df['Close'].iloc[-1])
            apertura = float(df['Open'].iloc[-1])
            alto = float(df['High'].iloc[-1])
            bajo = float(df['Low'].iloc[-1])
            vol = float(df['Volume'].iloc[-1])
            ma_vol = float(df['MA20_Vol'].iloc[-1])
            ayer = float(df['Close'].iloc[-2])
            
            # --- CÁLCULOS MACRO ---
            r_high_macro = float(df['High'].iloc[-250:].max())
            r_low_macro = float(df['Low'].iloc[-250:].min())
            ote_macro = r_high_macro - (r_high_macro - r_low_macro) * 0.786
            tp_macro = r_low_macro + (r_high_macro - r_low_macro) * 1.618
            sl_macro = r_low_macro * 0.90
            pz_macro = r_high_macro - (r_high_macro - r_low_macro) * 0.382

            # --- CÁLCULOS MICRO ---
            r_high_micro = float(df['High'].iloc[-50:].max())
            r_low_micro = float(df['Low'].iloc[-50:].min())
            ote_micro = r_high_micro - (r_high_micro - r_low_micro) * 0.786
            tp_micro = r_low_micro + (r_high_micro - r_low_micro) * 1.618
            sl_micro = r_low_micro * 0.98
            pz_micro = r_high_micro - (r_high_micro - r_low_micro) * 0.382
            
            # --- FUERZA ---
            rango = alto - bajo if (alto - bajo) > 0 else 0.0001
            desp = abs(cierre - apertura) / rango
            vol_rel = vol / ma_vol if ma_vol > 0 else 1
            fuerza = (desp * 0.6 + (min(vol_rel, 2) / 2) * 0.4) * 100
            
            # --- GATILLOS ---
            es_macro = bajo <= ote_macro and fuerza > 70 and cierre > ayer
            es_micro = bajo <= ote_micro and fuerza > 70 and cierre > ayer

            if es_macro:
                msg = (
                    f"🌋 *ALERTA MACRO (LARGO PLAZO)* 🌋\n\n"
                    f"🎯 *Activo:* {t} | 💰 *Entrada:* ${cierre:.2f}\n"
                    f"🔥 *Fuerza:* {fuerza:.1f}% | ✅ *Suelo Anual Detectado*\n\n"
                    f"📋 *DATOS PARA GOOGLE SHEET:*\n"
                    f"🛑 *Stop Loss:* ${sl_macro:.2f}\n"
                    f"🎯 *Take Profit:* ${tp_macro:.2f}\n"
                    f"⚠️ *Premium Zone:* ${pz_macro:.2f}\n"
                )
                enviar_telegram(msg)
                entradas += 1
            elif es_micro:
                msg = (
                    f"⚡ *ALERTA MICRO (SWING TRADING)* ⚡\n\n"
                    f"🎯 *Activo:* {t} | 💰 *Entrada:* ${cierre:.2f}\n"
                    f"🔥 *Fuerza:* {fuerza:.1f}% | ✅ *Rebote de Corto Plazo*\n\n"
                    f"📋 *DATOS PARA GOOGLE SHEET:*\n"
                    f"🛑 *Stop Loss:* ${sl_micro:.2f}\n"
                    f"🎯 *Take Profit:* ${tp_micro:.2f}\n"
                    f"⚠️ *Premium Zone:* ${pz_micro:.2f}\n"
                )
                enviar_telegram(msg)
                entradas += 1
                
        except Exception as e:
            # Aquí es donde fallaba la sangría. ¡Ahora está blindado!
            print(f"Error procesando el activo {t}: {e}")
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
        f"🟢 *BÚNKER SMC: REPORTE DUAL (Micro/Macro)*\n"
        f"📅 Fecha: {fecha_hoy}\n"
        f"🛡️ Salidas detectadas: {salidas}\n"
        f"🎯 Nuevas Entradas: {entradas}\n\n"
        f"_Sistemas blindados y en suspensión._"
    )
    enviar_telegram(mensaje_final)
    print("Operación finalizada. Transmisión cerrada.")
