from playwright.sync_api import sync_playwright
from flask import Flask, jsonify, redirect, request
import time
import json

app = Flask(__name__)

# 🛡️ ESCUDO ANTI-REBOTE
CANALES_TRABAJANDO = set()

def cazar_link_m3u8(url_pagina):
    link_maestro = None

    def interceptar_red(request):
        nonlocal link_maestro
        url_peticion = request.url
        es_publicidad = "2mdn.net" in url_peticion or "doubleclick" in url_peticion or "googlesyndication" in url_peticion
        
        if not es_publicidad:
            if (".m3u8" in url_peticion and "chunklist" not in url_peticion) or (".mp4" in url_peticion):
                if link_maestro is None:
                    print(f"🔥 Link válido obtenido -> {url_peticion[:80]}...")
                    link_maestro = url_peticion

    with sync_playwright() as p:
        navegador = p.chromium.launch(
            headless=True, 
            channel="chrome",
            args=["--autoplay-policy=no-user-gesture-required", "--mute-audio"]
        )
        contexto = navegador.new_context()
        pagina = contexto.new_page()
        pagina.on("request", interceptar_red)

        print(f"Ingresando al sitio web: {url_pagina}")
        try:
            pagina.goto(url_pagina, timeout=60000)
            time.sleep(5) 
            
            print("Inyectando la función secreta Reproducir()...")
            try:
                pagina.evaluate("try { Reproducir(); } catch(e) { console.log(e); }")
                print("¡Play forzado con éxito!")
            except Exception as e:
                pagina.locator("#btn_play").click(force=True, timeout=5000)
            
            time.sleep(10)
        except Exception as e:
            print(f"Hubo un problema al cargar la página: {e}")
        finally:
            navegador.close()
            
        return link_maestro

# --- 🚀 EL CABALLO DE TROYA: INYECTAR LINKS AL BACKEND ---
def inyectar_en_apex(id_canal, nuevo_link):
    url_api = f"https://oracleapex.com/ords/ft_app/ft_tv/canal/{id_canal}"
    
    print(f"\n🚀 Disparando API (Camuflaje Chromium) a: {url_api}")
    try:
        with sync_playwright() as p:
            navegador = p.chromium.launch(headless=True, channel="chrome")
            contexto = navegador.new_context()
            
            respuesta = contexto.request.put(
                url_api,
                data={"url_stream": nuevo_link}
            )
            
            if respuesta.status == 200:
                print(f"✅ ¡ÉXITO TOTAL! APEX respondió: {respuesta.text()}")
            else:
                print(f"⚠️ APEX respondió con error {respuesta.status}: {respuesta.text()}")
                
            navegador.close()
    except Exception as e:
        print(f"❌ Error al conectar con el túnel de APEX: {e}")

# --- DICCIONARIO DE MAPEO ---
MAPEO_CANALES = {
    1: "https://futbol-libre.su/espn-premium/",
    2: "https://futbol-libre.su/tnt-sports/",
    3: "https://futbol-libre.su/fox-sports/",
    4: "https://futbol-libre.su/directv-sports/",
    5: "https://futbol-libre.su/tyc-sports/",
    81: "https://futbol-libre.su/espn-1/",
    101: "https://futbol-libre.su/win-sports-premium/",
    121: "https://jetix2021.jahh19channel.xyz"
}

# --- 🔄 RUTA PARA ACTUALIZAR CANALES (La usa el navegador/botón) ---
@app.route('/refrescar/<int:id_canal>', methods=['GET'])
def refrescar_canal(id_canal):
    if id_canal in CANALES_TRABAJANDO:
        print(f"⏳ El navegador intentó una doble petición para el canal {id_canal}. Ignorando...")
        return jsonify({"status": "working", "mensaje": "Ya se está procesando"}), 200

    CANALES_TRABAJANDO.add(id_canal)
    
    try:
        print(f"\n🔔 Actualizar canal: {id_canal}")
        
        if id_canal in MAPEO_CANALES:
            url_partido = MAPEO_CANALES[id_canal]
            print(f"📍 URL detectada: {url_partido}")
        else:
            return jsonify({"status": "error", "mensaje": "Canal no configurado"}), 400

        link_final = cazar_link_m3u8(url_partido)
        
        if link_final:
            inyectar_en_apex(id_canal, link_final)
            
            sesion_apex = request.args.get('session', '')
            url_tu_lista_apex = "https://oracleapex.com/ords/r/ft_app/ft-tv/reproduciendo-canal" 
            if sesion_apex:
                url_tu_lista_apex = f"{url_tu_lista_apex}?session={sesion_apex}"
                
            return redirect(url_tu_lista_apex)
        else:
            return jsonify({"status": "error", "mensaje": "No se encontró m3u8 ni mp4"}), 500
            
    finally:
        CANALES_TRABAJANDO.discard(id_canal)

# --- NUEVO: RUTA PROXY PARA EL CELULAR (Burlamos Akamai para leer DB) ---
# --- RUTA PROXY PARA EL CELULAR (Burlamos Akamai leyendo la pantalla) ---
@app.route('/api/canales', methods=['GET'])
def obtener_canales_db():
    # 👇 LA URL VERDADERA QUE SÍ TRAE EL JSON
    url_api = "https://oracleapex.com/ords/ft_app/ft_tv/lista"
    print(f"\n📱 [PROXY] Celular solicitando canales. Abriendo pestaña con Camuflaje...")
    
    try:
        with sync_playwright() as p:
            navegador = p.chromium.launch(headless=True, channel="chrome")
            
            # Mantenemos el camuflaje humano para que Akamai no sospeche
            contexto = navegador.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            pagina = contexto.new_page() 
            
            respuesta = pagina.goto(url_api)
            time.sleep(2) # 2 segundos bastan para capturar el texto
            
            if respuesta.ok:
                texto_crudo = pagina.evaluate("document.body.innerText")
                datos = json.loads(texto_crudo)
                print("✅ ¡Datos enviados al celular!")
                return jsonify(datos)
            else:
                print(f"⚠️ Error de Oracle: {respuesta.status}. Akamai bloqueó el proxy.")
                return jsonify({"status": "error"}), 500
                
    except Exception as e:
        print(f"❌ Error en Proxy: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500
    finally:
        try:
            navegador.close()
        except:
            pass

if __name__ == "__main__":
    print("🚀 Bot iniciado con Escudo Anti-Rebote y Arquitectura Proxy...")
    app.run(host='0.0.0.0', port=5000)