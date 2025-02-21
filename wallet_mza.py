import streamlit as st
import requests
import json
import os

# Initial page configuration
st.set_page_config(
    page_title="Wallet Mendoza",
    page_icon="📱",
    layout="centered",
    initial_sidebar_state="auto"
)

# JSON file to store data
DATA_FILE = "data.json"

# Function to load data from JSON
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    else:
        # Create an initial JSON file if it doesn't exist
        initial_data = {"coins": [], "objectives": {}, "locked": False}
        with open(DATA_FILE, "w") as file:
            json.dump(initial_data, file, indent=4)
        return initial_data

# Function to save data to JSON
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Load initial data
data = load_data()

# Initialize data in the session state
if "coins" not in st.session_state:
    st.session_state["coins"] = data.get("coins", [])
if "objectives" not in st.session_state:
    st.session_state["objectives"] = data.get("objectives", {})
if "locked" not in st.session_state:
    st.session_state["locked"] = data.get("locked", False)

def wallet_manager():
    """
    Main page of the application:
    Displays and manages crypto coins, objectives, lock settings, 
    and calculates total profit/loss from current prices.
    """

    st.title("Wallet Mendoza 💰")

    # Lock configuration check
    if st.session_state["locked"]:
        st.warning("Configuration locked. You cannot add coins or modify objectives.")
    else:
        st.success("Configuration is open. You can add coins and set objectives.")

    # --- Manage Coins ---
    if not st.session_state["locked"]:
        with st.expander("Add Coins"):
            search_query = st.text_input("Search coin on CoinGecko")
            if search_query:
                results = search_coins(search_query)
                if results:
                    coin_options = {coin["id"]: f"{coin['name']} ({coin['symbol']})" for coin in results}
                    selected_coin_id = st.selectbox(
                        "Search Results",
                        list(coin_options.keys()),
                        format_func=lambda x: coin_options[x]
                    )
                    coin_name = coin_options[selected_coin_id].split(" (")[0]
                    st.session_state["new_coin"] = {"id": selected_coin_id, "name": coin_name}

            if st.session_state.get("new_coin"):
                st.write(f"You selected: {st.session_state['new_coin']['name']}")
                quantity = st.number_input("Quantity", min_value=0.0, step=0.01, key="quantity_input")
                entry_price = st.number_input("Entry Price (USD)", min_value=0.0, step=0.01, key="entry_price_input")
                if st.button("Confirm Coin"):
                    if "quantity_input" in st.session_state and "entry_price_input" in st.session_state:
                        st.session_state["new_coin"]["quantity"] = st.session_state["quantity_input"]
                        st.session_state["new_coin"]["entry_price"] = st.session_state["entry_price_input"]
                        st.session_state["coins"].append(st.session_state["new_coin"])
                        st.session_state["new_coin"] = {}
                        save_data({
                            "coins": st.session_state["coins"],
                            "objectives": st.session_state["objectives"],
                            "locked": st.session_state["locked"]
                        })
                        st.success("Coin added successfully.")
                    else:
                        st.error("Please fill in all fields correctly.")

        # --- Manage Objectives ---
        with st.expander("Set Objectives"):
            st.write("Add or update your trip objectives:")
            for objective in st.session_state["objectives"]:
                new_value = st.number_input(
                    f"{objective}",
                    value=st.session_state["objectives"][objective],
                    min_value=0.0,
                    step=1.0
                )
                st.session_state["objectives"][objective] = new_value
            
            new_objective = st.text_input("New Objective")
            new_amount = st.number_input("Amount (USD)", min_value=0.0, step=1.0)
            if st.button("Add Objective"):
                if new_objective:
                    st.session_state["objectives"][new_objective] = new_amount
                    save_data({
                        "coins": st.session_state["coins"],
                        "objectives": st.session_state["objectives"],
                        "locked": st.session_state["locked"]
                    })
                    st.success(f"Objective '{new_objective}' added.")

    # --- Lock Configuration Button ---
    if not st.session_state["locked"] and st.button("Lock Configuration"):
        st.session_state["locked"] = True
        save_data({
            "coins": st.session_state["coins"],
            "objectives": st.session_state["objectives"],
            "locked": True
        })
        st.warning("Configuration is now locked. You cannot add coins or modify objectives.")

    # --- Calculate Total Profit/Loss ---
    st.header("Total Profit/Loss")
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
        st.write(f"Gain/Loss for {coin_name}: **${gain_loss:.2f}**")

    st.write(f"**Total Gain/Loss: ${total_gain_loss:.2f}**")

    # --- Show progress towards objectives ---
    st.header("Progress towards Objectives")
    for objective, amount in st.session_state["objectives"].items():
        progress = min(total_gain_loss / amount, 1) if amount > 0 else 0
        st.markdown(f"**{objective}**")
        st.progress(progress)
        st.write(f"Progress: {progress * 100:.2f}% of ${amount:.2f}")
        st.markdown("---")

def search_coins(query):
    """Searches for coins on CoinGecko API."""
    url = f"https://api.coingecko.com/api/v3/search?query={query}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()["coins"]
    else:
        st.error("Error searching for coins on CoinGecko. Try again later.")
        return []

def get_current_price(coin_ids):
    """Gets current prices from CoinGecko for a list of coin IDs."""
    if not coin_ids:
        return {}
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(coin_ids)}&vs_currencies=usd"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Error fetching prices from CoinGecko. Try again later.")
        return {}

def landing_page():
    """Landing page of the application."""
    st.markdown(
        """
        <div style="text-align: center; margin-top: 50px;">
            <h1 style="font-size: 60px; color: #ffcc00;">Wallet Mendoza</h1>
            <p style="font-size: 24px; color: #333;">Monitoring the big gamble</p>
            <p style="font-size: 18px; color: #666;">Is there a surplus or not?</p>
            <a href="?page=wallet" style="font-size: 20px; color: #fff; background-color: #ffcc00; padding: 10px 20px; border-radius: 5px; text-decoration: none;">Enter</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Navigation logic
page = st.experimental_get_query_params().get("page", ["landing"])[0]

if page == "landing":
    landing_page()
elif page == "wallet":
    wallet_manager()

