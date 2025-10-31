import time
from humanfriendly import format_timespan
import re
import pandas as pd
import keyboard
import mouse
from win32gui import GetWindowText, GetForegroundWindow
import discord
from discord.ext import tasks
import asyncio
import os
from dotenv import load_dotenv

# Activity tracker
class ActivityTracker:
    def __init__(self):
        self.df = pd.read_csv("values.csv")
        self.last_active = time.time()
        self.df.loc[self.df["activity"] == "work", "time"] = 0
        self.df.loc[self.df["activity"] == "brainrot", "time"] = 0
        
        keyboard.on_press(lambda e: self.update_activity())
        mouse.on_click(lambda: self.update_activity())
        
    def update_activity(self):
        self.last_active = time.time()
        
    def add_csv_time(self, activity):
        updated_time_amount = int(self.df.loc[self.df["activity"] == activity, "time"].item()) + 10
        self.df.loc[self.df["activity"] == activity, "time"] = updated_time_amount
        self.df.to_csv("values.csv", index=False)
    
    def check_activity(self):
        idle_time = time.time() - self.last_active
        current_activity = GetWindowText(GetForegroundWindow())
        
        if re.search(r"^.+(Studio Code|Google Chrome|Github|Gitlab)$", current_activity) and idle_time < 60:
            print("You're working right now, hurray!")
            self.add_csv_time("work")
        else:
            print("Stop watching AI slop, please")
            self.add_csv_time("brainrot")

# Discord bot
class DiscordBot(discord.Client):
    def __init__(self, activity_tracker):
        load_dotenv()
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.activity_tracker = activity_tracker
    
    async def on_ready(self):
        print(f'Logged in as {self.user}')
        self.check_activity.start()
    
    async def on_message(self, message):
        if message.author == self.user:
            return
            
        if message.content.startswith('!stats'):
            df = pd.read_csv("values.csv")
            work_time = df.loc[df["activity"] == "work", "time"].item()
            brainrot_time = df.loc[df["activity"] == "brainrot", "time"].item()
            
            await message.channel.send(
                f"**Productivity Stats for <@483536140805341205>:**\n"
                f"Was coding for {format_timespan(work_time)}\n"
                f"Was doomscrolling(or, well, definitely not coding) for {format_timespan(brainrot_time)}\n"
                f"Total: {format_timespan(work_time + brainrot_time)} spent"
            )
    
    @tasks.loop(seconds=10)
    async def check_activity(self):
        self.activity_tracker.check_activity()

async def main():
    tracker = ActivityTracker()
    bot = DiscordBot(tracker)
    
    await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    asyncio.run(main())