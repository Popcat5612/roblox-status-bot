from dotenv import load_dotenv
import os
import discord
from discord.ext import commands, tasks
import aiohttp
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread

# 👉 Flask 웹 서버 구성
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Roblox Discord Bot 작동 중!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# 👉 디스코드 봇 로직
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

last_status = None

# 채널 ID 처리
try:
    channel_id = int(DISCORD_CHANNEL_ID) if DISCORD_CHANNEL_ID else 1429833042096164884
except ValueError:
    print("❗ DISCORD_CHANNEL_ID 환경변수가 올바른 숫자가 아닙니다. 기본값 사용.")
    channel_id = 1429833042096164884

async def get_status_from_html():
    url = "https://status.roblox.com/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                print(f"🔍 응답 코드: {resp.status}")  # ✅ 로그: 응답 상태
                if resp.status != 200:
                    print("❗ 응답이 200이 아님")
                    return None
                text = await resp.text()

        print("🔍 HTML 일부 출력:")
        print(text[:500])  # ✅ 로그: HTML 앞부분 일부 출력

        soup = BeautifulSoup(text, "html.parser")
        status_element = soup.select_one(".page-status__title")

        if status_element:
            print(f"✅ 상태 텍스트 추출됨: {status_element.text.strip()}")  # ✅ 로그: 추출된 상태
            return status_element.text.strip()
        else:
            print("❗ '.page-status__title' 요소를 찾을 수 없음")  # ✅ 로그: 선택자 실패
            return None

    except Exception as e:
        print(f"❗ 상태 크롤링 중 오류 발생: {e}")
        return None

async def get_roblox_status():
    status = await get_status_from_html()
    if status:
        return f"(크롤링) {status}"
    return "상태 정보를 가져올 수 없습니다."

@bot.event
async def on_ready():
    print(f"✅ 봇 로그인됨: {bot.user}")
    check_status.start()

@tasks.loop(minutes=5)
async def check_status():
    global last_status
    channel = bot.get_channel(channel_id)
    if channel is None:
        print(f"❗ 채널을 찾을 수 없음 (ID: {channel_id})")
        return

    try:
        current_status = await get_roblox_status()
        if last_status is None:
            last_status = current_status
            await channel.send(f"📡 Roblox 상태 모니터링 시작됨: **{current_status}**")
        elif current_status != last_status:
            await channel.send(f"⚠️ Roblox 상태 변경됨!\n이전: **{last_status}**\n현재: **{current_status}**")
            last_status = current_status
    except Exception as e:
        print(f"❗ 상태 체크 중 오류 발생: {e}")

@bot.command()
async def robloxstatus(ctx):
    status = await get_roblox_status()
    await ctx.send(f"📡 현재 Roblox 상태: **{status}**")

# 👉 HTTP 서버 먼저 켜고, 봇 실행
if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("❗ DISCORD_BOT_TOKEN 환경변수가 설정되지 않았습니다.")
    else:
        keep_alive()  # 🟢 Flask 서버 켜기
        bot.run(DISCORD_BOT_TOKEN)
