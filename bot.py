import discord
from discord import app_commands
import json
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")
DATA_FILE = "data.json"

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ------------------ DATA ------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "all_time": {},
            "weekly": {
                "start_date": None,
                "users": {}
            }
        }

    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def parse_amount(amount):
    return float(amount.replace("lbs", "").replace("lb", "").strip())

# ------------------ LOSS ------------------

@tree.command(name="loss", description="Log weight loss in lbs")
async def loss(interaction: discord.Interaction, amount: str):
    data = load_data()
    user_id = str(interaction.user.id)

    value = parse_amount(amount)

    if value <= 0:
        await interaction.response.send_message("❌ Must be positive.")
        return

    if user_id not in data["all_time"]:
        data["all_time"][user_id] = {"loss": 0, "gain": 0}

    if user_id not in data["weekly"]["users"]:
        data["weekly"]["users"][user_id] = {"loss": 0, "gain": 0}

    if data["weekly"]["start_date"] is None:
        data["weekly"]["start_date"] = datetime.utcnow().strftime("%Y-%m-%d")

    data["all_time"][user_id]["loss"] += value
    data["weekly"]["users"][user_id]["loss"] += value

    save_data(data)

    await interaction.response.send_message(f"💀 LOSS logged: -{value}lbs")

# ------------------ GAIN ------------------

@tree.command(name="gain", description="Log weight gain in lbs")
async def gain(interaction: discord.Interaction, amount: str):
    data = load_data()
    user_id = str(interaction.user.id)

    value = parse_amount(amount)

    if value <= 0:
        await interaction.response.send_message("❌ Must be positive.")
        return

    if user_id not in data["all_time"]:
        data["all_time"][user_id] = {"loss": 0, "gain": 0}

    if user_id not in data["weekly"]["users"]:
        data["weekly"]["users"][user_id] = {"loss": 0, "gain": 0}

    if data["weekly"]["start_date"] is None:
        data["weekly"]["start_date"] = datetime.utcnow().strftime("%Y-%m-%d")

    data["all_time"][user_id]["gain"] += value
    data["weekly"]["users"][user_id]["gain"] += value

    save_data(data)

    await interaction.response.send_message(f"⚠️ GAIN logged: +{value}lbs")

# ------------------ PROGRESS ------------------

@tree.command(name="progress", description="Check your progress")
async def progress(interaction: discord.Interaction):
    data = load_data()
    user_id = str(interaction.user.id)

    if user_id not in data["all_time"]:
        await interaction.response.send_message("No records yet.")
        return

    loss = data["all_time"][user_id]["loss"]
    gain = data["all_time"][user_id]["gain"]
    net = loss - gain

    await interaction.response.send_message(
        f"📊 Loss: {loss:.2f} lbs\n⚠️ Gain: {gain:.2f} lbs\n🔥 Net: {net:.2f} lbs"
    )
