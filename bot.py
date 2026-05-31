import discord
from discord import app_commands
import json
import os

TOKEN = os.getenv("TOKEN")

DATA_FILE = "data.json"

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ------------------ DATA ------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def parse_loss(loss):
    return float(loss.replace("lbs", "").replace("lb", "").strip())

# ------------------ WEIGH IN ------------------

@tree.command(name="weighin", description="Log weight lost in lbs")
async def weighin(interaction: discord.Interaction, loss: str):
    data = load_data()
    user_id = str(interaction.user.id)

    try:
        loss_value = parse_loss(loss)
    except:
        await interaction.response.send_message("❌ Enter a valid number (e.g. 2.5)")
        return

    if loss_value <= 0:
        await interaction.response.send_message("❌ Must be a positive number.")
        return

    if user_id not in data:
        data[user_id] = {
            "total_loss": 0,
            "entries": []
        }

    data[user_id]["total_loss"] += loss_value
    data[user_id]["entries"].append(loss_value)

    save_data(data)

    await interaction.response.send_message(
        f"💀 Logged: -{loss_value}lbs lost"
    )

# ------------------ LEADERBOARD ------------------

@tree.command(name="leaderboard", description="Show Mafia leaderboard")
async def leaderboard(interaction: discord.Interaction):
    data = load_data()

    if not data:
        await interaction.response.send_message("No data yet.")
        return

    ranking = sorted(
        data.items(),
        key=lambda x: x[1]["total_loss"],
        reverse=True
    )

    embed = discord.Embed(
        title="💀 MAFIA WEIGHT LOSS LEADERBOARD 💀",
        description="Ranked by total lbs lost",
        color=0x1a1a1a
    )

    medals = ["🥇 DON", "🥈 CAPO", "🥉 UNDERBOSS"]

    for i, (uid, info) in enumerate(ranking[:10]):
        user = await client.fetch_user(int(uid))
        loss = info["total_loss"]

        if i < 3:
            rank = medals[i]
        else:
            rank = f"🕶️ SOLDIER #{i+1}"

        embed.add_field(
            name=f"{rank} — {user.name}",
            value=f"🔥 {loss:.2f} lbs lost",
            inline=False
        )

    embed.set_footer(text="Mafia Weight Loss League 💀")

    await interaction.response.send_message(embed=embed)

# ------------------ PROGRESS ------------------

@tree.command(name="progress", description="Check your total loss")
async def progress(interaction: discord.Interaction):
    data = load_data()
    user_id = str(interaction.user.id)

    if user_id not in data:
        await interaction.response.send_message("No records yet.")
        return

    user = data[user_id]

    await interaction.response.send_message(
        f"📊 You’ve lost **{user['total_loss']:.2f} lbs** total"
    )

# ------------------ RESET ------------------

@tree.command(name="resetcompetition", description="Reset leaderboard (admin only)")
async def resetcompetition(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Admin only.")
        return

    save_data({})
    await interaction.response.send_message("💣 Competition reset.")

# ------------------ HELP ------------------

@tree.command(name="help", description="Show Mafia bot commands")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="💀 Mafia Weight Loss Bot Help",
        description="Available commands:",
        color=0x111111
    )

    embed.add_field(
        name="/weighin loss: X",
        value="Log weight lost in lbs (example: 2.5)",
        inline=False
    )

    embed.add_field(
        name="/leaderboard",
        value="Shows mafia rankings",
        inline=False
    )

    embed.add_field(
        name="/progress",
        value="Shows your total weight loss",
        inline=False
    )

    embed.add_field(
        name="/resetcompetition",
        value="(Admin only) resets leaderboard",
        inline=False
    )

    embed.set_footer(text="Mafia Weight Loss League 💀")

    await interaction.response.send_message(embed=embed)

# ------------------ READY ------------------

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")

client.run(TOKEN)
