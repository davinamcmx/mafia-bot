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

    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "all_time": {},
            "weekly": {
                "start_date": None,
                "users": {}
            }
        }

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

@tree.command(name="progress", description="Check your total progress")
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
        f"📊 Total progress: **{net:.2f} lbs**"
    )

# ------------------ ALL-TIME LEADERBOARD ------------------

@tree.command(name="leaderboard", description="All-time leaderboard")
async def leaderboard(interaction: discord.Interaction):
    data = load_data()

    ranking = sorted(
        data["all_time"].items(),
        key=lambda x: (x[1]["loss"] - x[1]["gain"]),
        reverse=True
    )

    embed = discord.Embed(
        title="💀 ALL-TIME MAFIA LEADERBOARD 💀",
        color=0x1a1a1a
    )

    medals = ["🥇 DON", "🥈 CAPO", "🥉 UNDERBOSS"]

    for i, (uid, info) in enumerate(ranking[:10]):
        user = await client.fetch_user(int(uid))
        net = info["loss"] - info["gain"]

        rank = medals[i] if i < 3 else f"🕶️ SOLDIER #{i+1}"

        embed.add_field(
            name=f"{rank} — {user.name}",
            value=f"🔥 {net:.2f} lbs net",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

# ------------------ WEEKLY LEADERBOARD (UPDATED) ------------------

@tree.command(name="weekly", description="Weekly leaderboard")
async def weekly(interaction: discord.Interaction):
    data = load_data()

    start_date = data["weekly"]["start_date"] or "Not started yet"

    ranking = sorted(
        data["weekly"]["users"].items(),
        key=lambda x: (x[1]["loss"] - x[1]["gain"]),
        reverse=True
    )

    # ---------------- GROUP TOTAL ----------------
    total_group = 0

    for user in data["weekly"]["users"].values():
        total_group += (user["loss"] - user["gain"])

    # ---------------- MAFIA STATUS ----------------
    if total_group > 20:
        status = "🔥 The Mafia is on a HEAVY cut — discipline is strong."
    elif total_group > 0:
        status = "💀 The family is moving in silence… progress is being made."
    elif total_group == 0:
        status = "⚖️ The Mafia is balanced… no movement yet."
    else:
        status = "⚠️ The family is slipping… gains are taking over."

    embed = discord.Embed(
        title="📅 WEEKLY MAFIA LEADERBOARD 📅",
        description=f"Week started: **{start_date}**\n\n{status}",
        color=0x2b2b2b
    )

    embed.add_field(
        name="💀 Total Family Progress This Week",
        value=f"🔥 {total_group:.2f} lbs net",
        inline=False
    )

    medals = ["🥇 DON", "🥈 CAPO", "🥉 UNDERBOSS"]

    for i, (uid, info) in enumerate(ranking[:10]):
        user = await client.fetch_user(int(uid))
        net = info["loss"] - info["gain"]

        rank = medals[i] if i < 3 else f"🕶️ SOLDIER #{i+1}"

        embed.add_field(
            name=f"{rank} — {user.name}",
            value=f"🔥 {net:.2f} lbs net",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

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

    embed.add_field(name="/loss", value="Log weight loss", inline=False)
    embed.add_field(name="/gain", value="Log weight gain", inline=False)
    embed.add_field(name="/progress", value="Show total progress (net)", inline=False)
    embed.add_field(name="/leaderboard", value="All-time leaderboard", inline=False)
    embed.add_field(name="/weekly", value="Weekly leaderboard + group stats", inline=False)
    embed.add_field(name="/resetweek", value="Reset weekly board", inline=False)

    await interaction.response.send_message(embed=embed)

# ------------------ READY ------------------

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")

client.run(TOKEN)
