import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

def get_bcv_rate():
    """Obtiene la tasa oficial del BCV haciendo web scraping (Comprobado que funciona)."""
    url = "https://www.bcv.org.ve/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        usd_container = soup.find("div", {"id": "dolar"})
        if usd_container:
            rate_element = usd_container.find("strong")
            if rate_element:
                return float(rate_element.text.strip().replace(",", "."))
    except Exception as e:
        print(f"Error detectado en BCV: {e}")
    return None

def get_usdt_buy_rate():
    """
    PLAN A: Simula entrar a usdt.com.ve para hacer scraping de la tasa de compra.
    Busca la clase específica <span class="rate-display rate-buy">
    """
    url = "https://www.usdt.com.ve/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Buscar el span con las clases exactas que indicaste
        rate_element = soup.select_one("span.rate-display.rate-buy")
        
        if rate_element:
            # Extraer el texto, limpiar posibles puntos de miles y cambiar la coma por punto decimal
            rate_text = rate_element.text.strip()
            # Ejemplo: "860,00" -> 860.00
            clean_rate = rate_text.replace(".", "").replace(",", ".")
            return float(clean_rate)
            
    except Exception as e:
        print(f"Error detectado al hacer scraping en usdt.com.ve: {e}")
        
    return None

def get_paralelo_rate():
    """
    PLAN B: Obtiene la tasa del dólar paralelo usando DolarApi.
    Solo se ejecuta si el scraping a usdt.com.ve falla.
    """
    url = "https://ve.dolarapi.com/v1/dolares/paralelo"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if "promedio" in data and data["promedio"] is not None:
            return float(data["promedio"])
            
    except Exception as e:
        print(f"Error en DolarApi (Paralelo de respaldo): {e}")
        
    return None

def main():
    # 1. Obtener tasa oficial
    bcv = get_bcv_rate()
    
    # 2. Obtener tasa paralela (Con lógica de Plan A y Plan B)
    paralelo = get_usdt_buy_rate() # Intenta scraping primero
    
    if paralelo is None:
        print("Fallo el Plan A (Scraping usdt.com.ve). Consultando Plan B (DolarApi)...")
        paralelo = get_paralelo_rate() # Si falla, usa la API como respaldo
    else:
        print("Plan A exitoso: Dato extraido de usdt.com.ve")
    
    # 3. Resguardo de valores (Si todo falla guarda 0.0)
    bcv_val = bcv if bcv is not None else 0.0
    binance_val = paralelo if paralelo is not None else 0.0

    # Fecha y hora actual
    now = datetime.now().isoformat()
    
    # 4. Preparar la estructura de carpetas
    os.makedirs("v1/dolares", exist_ok=True)
    
    oficial = {
        "moneda": "USD",
        "nombre": "Oficial",
        "promedio": bcv_val,
        "fechaActualizacion": now
    }
    with open("v1/dolares/oficial", "w") as f:
        json.dump(oficial, f, indent=4)
        
    paralelo_data = {
        "moneda": "USD",
        "nombre": "Paralelo",
        "promedio": binance_val,
        "fechaActualizacion": now
    }
    with open("v1/dolares/paralelo", "w") as f:
        json.dump(paralelo_data, f, indent=4)

    index_data = [oficial, paralelo_data]
    with open("index.json", "w") as f:
        json.dump(index_data, f, indent=4)

    print(f"Proceso finalizado. BCV: {bcv_val} | Paralelo (Compra): {binance_val}")

if __name__ == "__main__":
    main()
