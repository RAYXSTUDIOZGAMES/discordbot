import discord
from discord.ext import commands
import sqlite3
import random
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import math
import os

class LevelingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_name = "leveling.db"
        self.xp_cooldowns = {}
        self.init_db()
        self.ensure_font()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            last_message_time TEXT
        )''')
        conn.commit()
        conn.close()

    def ensure_font(self):
        # We need a font for the rank card. We'll try to use a system font or default.
        self.font_path = "arial.ttf" # Most windows systems have this.

    def get_user_data(self, user_id):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        if not user:
            c.execute('INSERT INTO users (user_id, xp, level, last_message_time) VALUES (?, 0, 1, ?)', 
                      (user_id, datetime.min.isoformat()))
            conn.commit()
            user = (user_id, 0, 1, datetime.min.isoformat())
        conn.close()
        return user

    def calculate_xp_for_next_level(self, level):
        return 5 * (level ** 2) + 50 * level + 100

    async def draw_rank_card(self, user, member):
        width = 900
        height = 250
        xp, level = user[1], user[2]
        next_level_xp = self.calculate_xp_for_next_level(level)
        prev_level_xp = self.calculate_xp_for_next_level(level - 1) if level > 1 else 0
        
        # Calculate progress
        current_xp_in_level = xp - prev_level_xp
        required_xp_in_level = next_level_xp - prev_level_xp
        progress = min(1.0, max(0.0, current_xp_in_level / required_xp_in_level))

        # Background
        img = Image.new('RGB', (width, height), color=(20, 20, 30))
        draw = ImageDraw.Draw(img)

        # Draw nice gradient or pattern (simple stripes)
        for i in range(0, width, 20):
            draw.line([(i, 0), (i+100, height)], fill=(30, 30, 45), width=2)

        # Avatar
        try:
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            # Download avatar
            from aiohttp import ClientSession
            async with ClientSession() as session:
                async with session.get(str(avatar_url)) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        avatar = Image.open(io.BytesIO(data)).convert("RGBA")
                        avatar = avatar.resize((180, 180))
                        
                        # Make circular mask
                        mask = Image.new('L', (180, 180), 0)
                        mask_draw = ImageDraw.Draw(mask)
                        mask_draw.ellipse((0, 0, 180, 180), fill=255)
                        
                        img.paste(avatar, (35, 35), mask)
        except Exception:
            pass # Failed to load avatar, just skip

        # Text Setup
        try:
            big_font = ImageFont.truetype(self.font_path, 60)
            med_font = ImageFont.truetype(self.font_path, 40)
            small_font = ImageFont.truetype(self.font_path, 30)
        except:
            big_font = ImageFont.load_default()
            med_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Username
        draw.text((240, 50), str(member.name), font=big_font, fill=(255, 255, 255))
        
        # Level and Rank Stats
        draw.text((240, 120), f"LEVEL {level}", font=med_font, fill=(0, 255, 255))
        draw.text((width - 300, 120), f"{current_xp_in_level} / {required_xp_in_level} XP", font=small_font, fill=(200, 200, 200))

        # Progress Bar Background
        bar_x, bar_y = 240, 180
        bar_w, bar_h = 600, 30
        draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], fill=(40, 40, 40))

        # Progress Bar Fill
        fill_w = int(bar_w * progress)
        if fill_w > 0:
            draw.rectangle([bar_x, bar_y, bar_x + fill_w, bar_y + bar_h], fill=(0, 255, 0))

        # Save to buffer
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return

        user_id = message.author.id
        now = datetime.now()
        
        # Cooldown check
        if user_id in self.xp_cooldowns:
            if now - self.xp_cooldowns[user_id] < timedelta(seconds=60):
                return
        
        self.xp_cooldowns[user_id] = now
        
        # Give XP
        xp_gain = random.randint(15, 25)
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        user = self.get_user_data(user_id) # Ensures existence
        new_xp = user[1] + xp_gain
        current_level = user[2]
        
        # Level up check
        needed_xp = self.calculate_xp_for_next_level(current_level)
        level_up = False
        
        if new_xp >= needed_xp:
            current_level += 1
            new_xp = new_xp # We accumulate XP, not reset
            level_up = True
            
        c.execute('UPDATE users SET xp = ?, level = ?, last_message_time = ? WHERE user_id = ?',
                  (new_xp, current_level, now.isoformat(), user_id))
        conn.commit()
        conn.close()
        
        if level_up:
            await message.channel.send(f"🎉 {message.author.mention} leveled up to **Level {current_level}**! 🆙")

    @commands.command(name="rank", aliases=["level"])
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user = self.get_user_data(member.id)
        
        async with ctx.typing():
            buffer = await self.draw_rank_card(user, member)
            await ctx.send(file=discord.File(buffer, filename="rank.png"))

    @commands.command(name="leaderboard", aliases=["lb", "top"])
    async def leaderboard(self, ctx):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('SELECT user_id, level, xp FROM users ORDER BY xp DESC LIMIT 10')
        top_users = c.fetchall()
        conn.close()
        
        embed = discord.Embed(title="🏆 Server Leaderboard", color=0xD4AF37)
        desc = ""
        for i, user in enumerate(top_users, 1):
            member = ctx.guild.get_member(user[0])
            name = member.name if member else f"User {user[0]}"
            desc += f"**#{i}** {name} - Lvl {user[1]} ({user[2]} XP)\n"
        
        embed.description = desc
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LevelingCog(bot))
