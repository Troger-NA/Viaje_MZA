import streamlit as st
import requests
import json
import os

# Configuración inicial de la página
# Configuración inicial de la página
st.set_page_config(
    page_title="Wallet Mendoza",
    page_icon="📱",
    layout="centered",
    initial_sidebar_state="auto",  # Opcional: controla el estado inicial de la barra lateral
)
# Archivo JSON para almacenar datos
DATA_FILE = "data.json"

# Función para cargar datos desde JSON
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    else:
        # Crear archivo JSON inicial si no existe
        initial_data = {"coins": [], "objectives": {}, "locked": False}
        with open(DATA_FILE, "w") as file:
            json.dump(initial_data, file, indent=4)
        return initial_data

# Función para guardar datos en JSON
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Cargar datos iniciales
data = load_data()

# Inicializar datos en la sesión
if "coins" not in st.session_state:
    st.session_state["coins"] = data.get("coins", [])
if "objectives" not in st.session_state:
    st.session_state["objectives"] = data.get("objectives", {})
if "locked" not in st.session_state:
    st.session_state["locked"] = data.get("locked", False)

# Función para la página principal de la app
def wallet_manager():
    st.title("Wallet Mendoza 💰")

    # Bloquear configuración
    if st.session_state["locked"]:
        st.warning("Configuración bloqueada. No puedes agregar más monedas ni modificar objetivos.")
    else:
        st.success("Configuración abierta. Puedes agregar monedas y configurar objetivos.")

    # Gestión de monedas
    if not st.session_state["locked"]:
        with st.expander("Añadir Monedas"):
            search_query = st.text_input("Buscar moneda en CoinGecko")
            if search_query:
                results = search_coins(search_query)
                if results:
                    coin_options = {coin["id"]: f"{coin['name']} ({coin['symbol']})" for coin in results}
                    selected_coin_id = st.selectbox("Resultados de búsqueda", list(coin_options.keys()), format_func=lambda x: coin_options[x])
                    coin_name = coin_options[selected_coin_id].split(" (")[0]
                    st.session_state["new_coin"] = {"id": selected_coin_id, "name": coin_name}

            if st.session_state.get("new_coin"):
                st.write(f"Seleccionaste: {st.session_state['new_coin']['name']}")
                quantity = st.number_input("Cantidad", min_value=0.0, step=0.01, key="quantity_input")
                entry_price = st.number_input("Precio de entrada (USD)", min_value=0.0, step=0.01, key="entry_price_input")
                if st.button("Confirmar Moneda"):
                    if "quantity_input" in st.session_state and "entry_price_input" in st.session_state:
                        st.session_state["new_coin"]["quantity"] = st.session_state["quantity_input"]
                        st.session_state["new_coin"]["entry_price"] = st.session_state["entry_price_input"]
                        st.session_state["coins"].append(st.session_state["new_coin"])
                        st.session_state["new_coin"] = {}
                        save_data({"coins": st.session_state["coins"], "objectives": st.session_state["objectives"], "locked": st.session_state["locked"]})
                        st.success("Moneda agregada correctamente.")
                    else:
                        st.error("Por favor, completa todos los campos correctamente.")

        # Gestión de objetivos
        with st.expander("Configurar Objetivos"):
            st.write("Añade o actualiza los objetivos de tu viaje:")
            for objective in st.session_state["objectives"]:
                new_value = st.number_input(f"{objective}", value=st.session_state["objectives"][objective], min_value=0.0, step=1.0)
                st.session_state["objectives"][objective] = new_value
            
            new_objective = st.text_input("Nuevo objetivo")
            new_amount = st.number_input("Monto (USD)", min_value=0.0, step=1.0)
            if st.button("Añadir Objetivo"):
                if new_objective:
                    st.session_state["objectives"][new_objective] = new_amount
                    save_data({"coins": st.session_state["coins"], "objectives": st.session_state["objectives"], "locked": st.session_state["locked"]})
                    st.success(f"Objetivo '{new_objective}' añadido.")

    # Botón para bloquear configuración
    if not st.session_state["locked"] and st.button("Bloquear Configuración"):
        st.session_state["locked"] = True
        save_data({"coins": st.session_state["coins"], "objectives": st.session_state["objectives"], "locked": True})
        st.warning("La configuración ha sido bloqueada. No se pueden agregar más monedas ni modificar objetivos.")

    # Calcular ganancia/pérdida total
    st.header("Ganancia/Pérdida Total")
    coin_ids = [coin["id"] for coin in st.session_state["coins"]]
    current_prices = get_current_price(coin_ids)
    total_gain_loss = 0.0
    for coin in st.session_state["coins"]:
        coin_name = coin["name"]
        entry_price = coin["entry_price"]
        quantity = coin["quantity"]
        current_price = current_prices.get(coin["id"], {}).get("usd", 0)
        gain_loss = quantity * (current_price - entry_price)
        total_gain_loss += gain_loss
        st.write(f"Ganancia/Pérdida para {coin_name}: **${gain_loss:.2f}**")
    st.write(f"**Ganancia/Pérdida Total: ${total_gain_loss:.2f}**")

    # Mostrar progreso hacia objetivos
    st.header("Progreso hacia Objetivos")
    for objective, amount in st.session_state["objectives"].items():
        progress = min(total_gain_loss / amount, 1) if amount > 0 else 0
        st.markdown(f"**{objective}**")
        st.progress(progress)
        st.write(f"Progreso: {progress * 100:.2f}% hacia ${amount:.2f}")
        st.markdown("---")

# Función para buscar monedas en CoinGecko
def search_coins(query):
    url = f"https://api.coingecko.com/api/v3/search?query={query}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()["coins"]
    else:
        st.error("Error al buscar monedas en CoinGecko. Intenta nuevamente más tarde.")
        return []

# Función para obtener precios actuales desde CoinGecko
def get_current_price(coin_ids):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(coin_ids)}&vs_currencies=usd"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Error al consultar los precios en CoinGecko. Intenta nuevamente más tarde.")
        return {}

# Función para la landing page
def landing_page():
    st.markdown(
        """
        <div style="text-align: center; margin-top: 50px;">
            <h1 style="font-size: 60px; color: #ffcc00;">Wallet Mendoza</h1>
            <p style="font-size: 24px; color: #333;">Monitoreo de la timba</p>
            <p style="font-size: 18px; color: #666;">¿Hay sobre o no hay sobre?</p>
            <a href="?page=wallet" style="font-size: 20px; color: #fff; background-color: #ffcc00; padding: 10px 20px; border-radius: 5px; text-decoration: none;">Entrar</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Lógica de navegación
page = st.experimental_get_query_params().get("page", ["landing"])[0]

if page == "landing":
    landing_page()
elif page == "wallet":
    wallet_manager()

