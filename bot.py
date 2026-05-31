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

# ------------------ LOSS COMMAND ------------------

@tree.command(name="loss", description="Log weight loss in lbs")
async def loss(interaction: discord.Interaction, amount: str):
    data = load_data()
    user_id = str(interaction.user.id)

    try:
        value = parse_amount(amount)
    except:
        await interaction.response.send_message("❌ Enter a valid number (e.g. 2.5)")
        return

    if value <= 0:
        await interaction.response.send_message("❌ Must be a positive number.")
        return

    if user_id not in data["all_time"]:
        data["all_time"][user_id] = {"total_loss": 0}

    if user_id not in data["weekly"]["users"]:
        data["weekly"]["users"][user_id] = {"total_loss": 0}

    if data["weekly"]["start_date"] is None:
        data["weekly"]["start_date"] = datetime.utcnow().strftime("%Y-%m-%d")

    data["all_time"][user_id]["total_loss"] += value
    data["weekly"]["users"][user_id]["total_loss"] += value

    save_data(data)

    await interaction.response.send_message(f"💀 LOSS logged: -{value}lbs")

# ------------------ GAIN COMMAND ------------------

@tree.command(name="gain", description="Log weight gain in lbs")
async def gain(interaction: discord.Interaction, amount: str):
    data = load_data()
    user_id = str(interaction.user.id)

    try:
        value = parse_amount(amount)
    except:
        await interaction.response.send_message("❌ Enter a valid number (e.g. 2.5)")
        return

    if value <= 0:
        await interaction.response.send_message("❌ Must be a positive number.")
        return

    if user_id not in data["all_time"]:
        data["all_time"][user_id] = {"total_loss": 0}

    if user_id not in data["weekly"]["users"]:
        data["weekly"]["users"][user_id] = {"total_loss": 0}

    if data["weekly"]["start_date"] is None:
        data["weekly"]["start_date"] = datetime.utcnow().strftime("%Y-%m-%d")

    # subtract progress
    data["all_time"][user_id]["total_loss"] -= value
    data["weekly"]["users"][user_id]["total_loss"] -= value

    save_data(data)

    await interaction.response.send_message(f"⚠️ GAIN logged: +{value}lbs")

# ------------------ ALL-TIME LEADERBOARD ------------------

@tree.command(name="leaderboard", description="All-time leaderboard")
async def leaderboard(interaction: discord.Interaction):
    data = load_data()

    ranking = sorted(
        data["all_time"].items(),
        key=lambda x: x[1]["total_loss"],
        reverse=True
    )

    embed = discord.Embed(
        title="💀 ALL-TIME MAFIA LEADERBOARD 💀",
        description="Total lbs lost",
        color=0x1a1a1a
    )

    medals = ["🥇 DON", "🥈 CAPO", "🥉 UNDERBOSS"]

    for i, (uid, info) in enumerate(ranking[:10]):
        user = await client.fetch_user(int(uid))

        rank = medals[i] if i < 3 else f"🕶️ SOLDIER #{i+1}"

        embed.add_field(
            name=f"{rank} — {user.name}",
            value=f"🔥 {info['total_loss']:.2f} lbs",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

# ------------------ WEEKLY LEADERBOARD ------------------

@tree.command(name="weekly", description="Weekly leaderboard")
async def weekly(interaction: discord.Interaction):
    data = load_data()

    start_date = data["weekly"]["start_date"] or "Not started yet"

    ranking = sorted(
        data["weekly"]["users"].items(),
        key=lambda x: x[1]["total_loss"],
        reverse=True
    )

    embed = discord.Embed(
        title="📅 WEEKLY MAFIA LEADERBOARD 📅",
        description=f"Week started: **{start_date}**",
        color=0x2b2b2b
    )

    medals = ["🥇 DON", "🥈 CAPO", "🥉 UNDERBOSS"]

    for i, (uid, info) in enumerate(ranking[:10]):
        user = await client.fetch_user(int(uid))

        rank = medals[i] if i < 3 else f"🕶️ SOLDIER #{i+1}"

        embed.add_field(
            name=f"{rank} — {user.name}",
            value=f"🔥 {info['total_loss']:.2f} lbs",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

# ------------------ PROGRESS ------------------

@tree.command(name="progress", description="Check your total loss")
async def progress(interaction: discord.Interaction):
    data = load_data()
    user_id = str(interaction.user.id)

    if user_id not in data["all_time"]:
        await interaction.response.send_message("No records yet.")
        return

    total = data["all_time"][user_id]["total_loss"]

    await interaction.response.send_message(
        f"📊 You’ve lost **{total:.2f} lbs** total (all-time)"
    )

# ------------------ RESET WEEK ------------------

@tree.command(name="resetweek", description="Reset weekly leaderboard (admin only)")
async def resetweek(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Admin only.")
        return

    data = load_data()

    data["weekly"] = {
        "start_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "users": {}
    }

    save_data(data)

    await interaction.response.send_message("📅 Weekly leaderboard reset.")

# ------------------ HELP ------------------

@tree.command(name="help", description="Show commands")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="💀 Mafia Weight Loss Bot",
        color=0x111111
    )

    embed.add_field(name="/loss", value="Log weight loss in lbs", inline=False)
    embed.add_field(name="/gain", value="Log weight gain in lbs", inline=False)
    embed.add_field(name="/leaderboard", value="All-time leaderboard", inline=False)
    embed.add_field(name="/weekly", value="Weekly leaderboard", inline=False)
    embed.add_field(name="/progress", value="Your total loss", inline=False)
    embed.add_field(name="/resetweek", value="Reset weekly board (admin)", inline=False)

    await interaction.response.send_message(embed=embed)

# ------------------ READY ------------------

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")

client.run(TOKEN)
