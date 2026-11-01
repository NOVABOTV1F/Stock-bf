import os
import json
import time
import asyncio
import urllib.request

import discord
from discord import app_commands

TOKEN = os.environ["DISCORD_TOKEN"]
STOCK_URL = os.environ["STOCK_URL"]  # contoh: https://nama-kamu.pages.dev/stock.json
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))  # 0 = tidak posting otomatis
CHECK_EVERY = int(os.environ.get("CHECK_EVERY", "300"))  # detik, default 5 menit

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
last_text = None


def fetch_stock():
    url = f"{STOCK_URL}?t={int(time.time())}"
    req = urllib.request.Request(url, headers={"Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def build_text(data):
    lines = []
    for key, label in (("normal", "Normal Dealer"), ("mirage", "Mirage Dealer")):
        block = data.get(key, {})
        items = block.get("items", [])
        lines.append(f"**{label}**")
        if not items:
            lines.append("Belum ada data.")
        for it in items:
            price = it.get("price")
            if isinstance(price, (int, float)):
                price_txt = f"{int(price):,}".replace(",", ".") + " Beli"
            else:
                price_txt = str(price)
            lines.append(f"{it.get('emoji', '🍇')} **{it.get('name', '?')}** · {price_txt}")
        lines.append("")
    return "\n".join(lines).strip()


@tree.command(name="stock", description="Lihat stock Blox Fruits sekarang")
async def stock_cmd(interaction: discord.Interaction):
    try:
        data = await asyncio.to_thread(fetch_stock)
        await interaction.response.send_message(build_text(data))
    except Exception as e:
        await interaction.response.send_message(f"Gagal ambil stock: {e}", ephemeral=True)


async def watcher():
    global last_text
    await client.wait_until_ready()
    while not client.is_closed():
        try:
            data = await asyncio.to_thread(fetch_stock)
            text = build_text(data)
            if CHANNEL_ID and text != last_text:
                channel = await client.fetch_channel(CHANNEL_ID)
                await channel.send("🔔 Stock diupdate:\n" + text)
            last_text = text
        except Exception as e:
            print("watcher error:", e)
        await asyncio.sleep(CHECK_EVERY)


@client.event
async def on_ready():
    await tree.sync()
    client.loop.create_task(watcher())
    print(f"Login sebagai {client.user}")


client.run(TOKEN)
