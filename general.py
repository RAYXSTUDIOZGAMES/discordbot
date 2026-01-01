import discord
from discord.ext import commands
import logging
import asyncio
import random
import requests
import os
from datetime import datetime, timezone
from utils import log_activity

logger = logging.getLogger('discord_bot')

class GeneralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_reminders = {}
        self.user_notes = {}
        # Presence cycle statuses (rotates every 30 seconds)
        self.PRESENCE_STATUSES = [
            (discord.Activity(type=discord.ActivityType.watching, name="🎬 Editing Help | !list"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.listening, name="your editing questions 🎨"), discord.Status.idle),
            (discord.Activity(type=discord.ActivityType.playing, name="with video effects ⚡"), discord.Status.dnd),
            (discord.Activity(type=discord.ActivityType.watching, name="tutorials 📚"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.playing, name="Valorant 🎮"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.listening, name="your music taste 🎵"), discord.Status.idle),
            (discord.Activity(type=discord.ActivityType.watching, name="anime 📺"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.playing, name="with code ⚙️"), discord.Status.dnd),
            (discord.Activity(type=discord.ActivityType.listening, name="your thoughts 💭"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.watching, name="movies 🍿"), discord.Status.idle),
            (discord.Activity(type=discord.ActivityType.playing, name="chess 🎯"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.watching, name="tech tutorials 🔧"), discord.Status.dnd),
            (discord.Activity(type=discord.ActivityType.listening, name="Discord chats 💬"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.playing, name="with AI magic ✨"), discord.Status.idle),
            (discord.Activity(type=discord.ActivityType.watching, name="creators work 👨‍💻"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.playing, name="rendering videos 🎥"), discord.Status.dnd),
            (discord.Activity(type=discord.ActivityType.playing, name="GTA V 🚗"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.watching, name="over the server 👀"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.listening, name="Spotify 🎧"), discord.Status.idle),
            (discord.Activity(type=discord.ActivityType.playing, name="Minecraft ⛏️"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.watching, name="YouTube 📺"), discord.Status.idle),
            (discord.Activity(type=discord.ActivityType.playing, name="Fortnite 🔫"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.listening, name="lo-fi beats 🌙"), discord.Status.idle),
            (discord.Activity(type=discord.ActivityType.playing, name="League of Legends ⚔️"), discord.Status.dnd),
            (discord.Activity(type=discord.ActivityType.watching, name="Netflix 🎬"), discord.Status.idle),
            (discord.Activity(type=discord.ActivityType.playing, name="Apex Legends 🎯"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.listening, name="your problems 💭"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.playing, name="Overwatch 2 🦸"), discord.Status.dnd),
            (discord.Activity(type=discord.ActivityType.watching, name="Twitch streams 📡"), discord.Status.idle),
            (discord.Activity(type=discord.ActivityType.playing, name="Rocket League 🚀"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.listening, name="rap music 🎤"), discord.Status.idle),
            (discord.Activity(type=discord.ActivityType.playing, name="Counter-Strike 2 💣"), discord.Status.dnd),
            (discord.Activity(type=discord.ActivityType.watching, name="server activity 📊"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.playing, name="COD Warzone 🪖"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.listening, name="chill vibes 🌊"), discord.Status.idle),
            (discord.Activity(type=discord.ActivityType.playing, name="Elden Ring ⚔️"), discord.Status.dnd),
            (discord.Activity(type=discord.ActivityType.watching, name="for rule breakers 🔍"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.playing, name="Roblox 🧱"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.listening, name="EDM 🎵"), discord.Status.idle),
            (discord.Activity(type=discord.ActivityType.playing, name="Among Us 🔪"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.watching, name="memes 😂"), discord.Status.idle),
            (discord.Activity(type=discord.ActivityType.playing, name="FIFA 24 ⚽"), discord.Status.online),
            (discord.Activity(type=discord.ActivityType.listening, name="podcasts 🎙️"), discord.Status.idle),
            (discord.Activity(type=discord.ActivityType.playing, name="Cyberpunk 2077 🌃"), discord.Status.dnd),
            (discord.Activity(type=discord.ActivityType.watching, name="chat for spam 🛡️"), discord.Status.online),
        ]

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f'Bot connected as {self.bot.user.name}')
        
        # Log startup
        server_list = "\n".join([f"• {g.name} ({g.member_count} members)" for g in self.bot.guilds])
        await log_activity(
            self.bot,
            "🟢 Bot Started",
            f"**{self.bot.user.name}** is now online!",
            color=0x00FF00,
            fields={
                "Servers": len(self.bot.guilds),
                "Server List": server_list[:1024] if server_list else "None"
            }
        )
        
        # Start presence cycle
        self.bot.loop.create_task(self.cycle_presence())

    async def cycle_presence(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            activity, status = random.choice(self.PRESENCE_STATUSES)
            await self.bot.change_presence(activity=activity, status=status)
            await asyncio.sleep(30)

    @commands.command(name="hi")
    async def hi_command(self, ctx):
        try:
            await ctx.author.send("HI")
            if ctx.guild: await ctx.send(f"{ctx.author.mention}, I've sent you a DM!")
        except:
            await ctx.send(f"{ctx.author.mention}, HI! (Enable DMs for more)")

    @commands.command(name="help")
    async def help_command(self, ctx):
        help_text = """**═══════════════════════════════════════════════════════════**
**🤖 EDITING HELPER BOT - COMPLETE COMMAND LIST**
**═══════════════════════════════════════════════════════════**

**📋 BASIC COMMANDS:**
• !help - Shows this list
• !files - List available files
• !presets - List color correction presets
• !software_list - List software commands

**💻 SOFTWARE COMMANDS:**
• !aecrack, !pscrack, !mecrack, !prcrack, !topazcrack

**📝 AI TOOLS:**
• !ask, !explain, !improve, !rewrite, !summarize, !analyze
• !idea, !define, !fix, !shorten, !expand, !caption, !script
• !format, !title, !translate, !paragraph

**🛠️ UTILITY TOOLS:**
• !remind <time> <text> - Set reminders
• !note <text> - Save notes
• !timer <time> - Start timer
• !convert <mode> <text> - Convert text
• !emoji <text>, !calculate <math>, !weather <city>
• !profile, !serverinfo

**🎨 CREATIVE TOOLS:**
• !creative, !story, !quote, !brainstorm, !design, !name, !aesthetic, !topics, !motivate

**═══════════════════════════════════════════════════════════**"""
        try:
            await ctx.author.send(help_text)
            if ctx.guild: await ctx.send(f"{ctx.author.mention}, sent help to DMs!")
        except:
            await ctx.send(f"{ctx.author.mention}, enable DMs for full help list.")

    @commands.command(name="remind")
    async def remind_command(self, ctx, time_str: str = None, *, reminder_text: str = None):
        if not time_str or not reminder_text: return await ctx.send("Usage: !remind 5m Buy milk")
        
        try:
            amount = int(''.join(filter(str.isdigit, time_str)))
            unit = ''.join(filter(str.isalpha, time_str)).lower()
            if unit == 'm': delay = amount * 60
            elif unit == 'h': delay = amount * 3600
            elif unit == 's': delay = amount
            else: return await ctx.send("Use: 5m, 1h, 30s")
            
            await ctx.send(f"⏰ Reminder set for {time_str}: **{reminder_text}**")
            await asyncio.sleep(delay)
            try: await ctx.author.send(f"⏰ **REMINDER**: {reminder_text}")
            except: pass
        except: await ctx.send("Error setting reminder.")

    @commands.command(name="note")
    async def note_command(self, ctx, *, note_text: str = None):
        user_id = ctx.author.id
        if not note_text:
            if user_id in self.user_notes:
                notes = "\n".join([f"• {n}" for n in self.user_notes[user_id]])
                await ctx.send(f"📝 **Your Notes:**\n{notes}")
            else: await ctx.send("No notes saved.")
            return
        
        if user_id not in self.user_notes: self.user_notes[user_id] = []
        self.user_notes[user_id].append(note_text)
        await ctx.send("✓ Note saved!")

    @commands.command(name="timer")
    async def timer_command(self, ctx, time_str: str = None):
        if not time_str: return await ctx.send("Usage: !timer 5m")
        try:
            amount = int(''.join(filter(str.isdigit, time_str)))
            unit = ''.join(filter(str.isalpha, time_str)).lower()
            if unit == 'm': seconds = amount * 60
            elif unit == 'h': seconds = amount * 3600
            elif unit == 's': seconds = amount
            else: return await ctx.send("Use: 5m, 1h, 30s")
            
            msg = await ctx.send(f"⏱️ **Timer started**: {time_str}")
            await asyncio.sleep(seconds)
            await msg.edit(content=f"✓ **Timer finished!** {time_str} has passed. {ctx.author.mention}")
        except: await ctx.send("Timer error.")

    @commands.command(name="convert")
    async def convert_command(self, ctx, mode: str = None, *, text: str = None):
        if not mode or not text: return await ctx.send("Usage: !convert <upper/lower/title/reverse> <text>")
        mode = mode.lower()
        if mode == "upper": res = text.upper()
        elif mode == "lower": res = text.lower()
        elif mode == "title": res = text.title()
        elif mode == "reverse": res = text[::-1]
        else: return await ctx.send("Unknown mode.")
        await ctx.send(f"✓ {res[:1900]}")

    @commands.command(name="calculate")
    async def calculate_command(self, ctx, *, expression: str = None):
        if not expression: return await ctx.send("Usage: !calculate 50+50")
        try:
            expression = expression.replace('^', '**')
            # Dangerous but strictly limited env
            res = eval(expression, {"__builtins__": {}}, {}) 
            await ctx.send(f"🧮 {res}")
        except: await ctx.send("Invalid expression.")

    @commands.command(name="weather")
    async def weather_command(self, ctx, *, location: str = None):
        if not location: return await ctx.send("Usage: !weather London")
        try:
            url = f"https://wttr.in/{location}?format=3"
            r = requests.get(url, timeout=5)
            await ctx.send(f"🌤️ {r.text}")
        except: await ctx.send("Weather unavailable.")

    @commands.command(name="profile")
    async def profile_command(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"Profile - {member.name}", color=0x5865F2)
        embed.add_field(name="ID", value=member.id)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        await ctx.send(embed=embed)

    @commands.command(name="serverinfo")
    async def serverinfo_command(self, ctx):
        if not ctx.guild: return
        embed = discord.Embed(title=f"Server Info - {ctx.guild.name}", color=0x5865F2)
        embed.add_field(name="Members", value=ctx.guild.member_count)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GeneralCog(bot))
