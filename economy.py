import discord
from discord.ext import commands
import sqlite3
import random
import asyncio
from datetime import datetime, timedelta

class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_name = "economy.db"
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 1000,
            bank INTEGER DEFAULT 0,
            last_daily TEXT,
            last_work TEXT,
            last_rob TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS inventory (
            user_id INTEGER,
            item_name TEXT,
            amount INTEGER,
            PRIMARY KEY (user_id, item_name)
        )''')
        conn.commit()
        conn.close()

    def get_user(self, user_id):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        if not user:
            c.execute('INSERT INTO users (user_id, last_daily, last_work, last_rob) VALUES (?, ?, ?, ?)', 
                      (user_id, datetime.min.isoformat(), datetime.min.isoformat(), datetime.min.isoformat()))
            conn.commit()
            user = (user_id, 1000, 0, datetime.min.isoformat(), datetime.min.isoformat(), datetime.min.isoformat())
        conn.close()
        return user

    def update_balance(self, user_id, amount, bank=False):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        self.get_user(user_id) # Ensure exists
        if bank:
            c.execute('UPDATE users SET bank = bank + ? WHERE user_id = ?', (amount, user_id))
        else:
            c.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        conn.commit()
        conn.close()

    @commands.command(name="balance", aliases=["bal", "wallet"])
    async def balance(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user = self.get_user(member.id)
        embed = discord.Embed(title=f"💸 {member.name}'s Finances", color=0x00FF00)
        embed.add_field(name="Wallet", value=f"${user[1]:,}", inline=True)
        embed.add_field(name="Bank", value=f"${user[2]:,}", inline=True)
        embed.add_field(name="Net Worth", value=f"${user[1] + user[2]:,}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="daily")
    async def daily(self, ctx):
        user = self.get_user(ctx.author.id)
        last_daily = datetime.fromisoformat(user[3])
        if datetime.now() - last_daily < timedelta(hours=24):
            remaining = timedelta(hours=24) - (datetime.now() - last_daily)
            hours, remainder = divmod(remaining.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return await ctx.send(f"⏳ You can claim your daily in **{hours}h {minutes}m**.")
        
        amount = random.randint(500, 2000)
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('UPDATE users SET balance = balance + ?, last_daily = ? WHERE user_id = ?', 
                  (amount, datetime.now().isoformat(), ctx.author.id))
        conn.commit()
        conn.close()
        
        await ctx.send(f"💰 **Daily Reward!** You received **${amount:,}**!")

    @commands.command(name="work")
    async def work(self, ctx):
        user = self.get_user(ctx.author.id)
        last_work = datetime.fromisoformat(user[4])
        if datetime.now() - last_work < timedelta(hours=1):
            remaining = timedelta(hours=1) - (datetime.now() - last_work)
            minutes, _ = divmod(remaining.seconds, 60)
            return await ctx.send(f"⏳ You are tired. Rest for **{minutes}m**.")
        
        jobs = [
            ("as a Video Editor", 800), ("fixing bugs", 900), ("streaming on Twitch", 600),
            ("designing websites", 1200), ("trading crypto", 1500), ("flipping burgers", 300)
        ]
        job, salary = random.choice(jobs)
        actual_salary = random.randint(salary-200, salary+200)
        
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('UPDATE users SET balance = balance + ?, last_work = ? WHERE user_id = ?', 
                  (actual_salary, datetime.now().isoformat(), ctx.author.id))
        conn.commit()
        conn.close()
        
        await ctx.send(f"🔨 You worked **{job}** and earned **${actual_salary:,}**!")

    @commands.command(name="rob")
    async def rob(self, ctx, victim: discord.Member):
        if victim == ctx.author: return await ctx.send("You can't rob yourself!")
        
        user = self.get_user(ctx.author.id)
        last_rob = datetime.fromisoformat(user[5])
        if datetime.now() - last_rob < timedelta(hours=2):
            return await ctx.send("⏳ The police are watching you. Wait a bit.")
            
        victim_data = self.get_user(victim.id)
        if victim_data[1] < 500: return await ctx.send(f"{victim.name} is too poor to rob.")
        
        success = random.random() < 0.4 # 40% success chance
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('UPDATE users SET last_rob = ? WHERE user_id = ?', (datetime.now().isoformat(), ctx.author.id))
        
        if success:
            steal_amount = int(victim_data[1] * random.uniform(0.1, 0.4))
            c.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (steal_amount, ctx.author.id))
            c.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (steal_amount, victim.id))
            msg = f"🔫 **HEIST SUCCESSFUL!** You stole **${steal_amount:,}** from {victim.name}!"
        else:
            fine = 1000
            c.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (fine, ctx.author.id))
            msg = f"🚓 **BUSTED!** You got caught attempting to rob {victim.name} and paid a **${fine}** fine."
            
        conn.commit()
        conn.close()
        await ctx.send(msg)

    @commands.command(name="deposit", aliases=["dep"])
    async def deposit(self, ctx, amount: str):
        user = self.get_user(ctx.author.id)
        wallet = user[1]
        
        if amount.lower() == "all": amount = wallet
        else: 
            try: amount = int(amount)
            except: return await ctx.send("Invalid amount.")
            
        if amount > wallet: return await ctx.send("You don't have that much money.")
        if amount <= 0: return await ctx.send("Amount must be positive.")
        
        self.update_balance(ctx.author.id, -amount)
        self.update_balance(ctx.author.id, amount, bank=True)
        await ctx.send(f"🏦 Deposited **${amount:,}** to your bank.")

    @commands.command(name="withdraw", aliases=["with"])
    async def withdraw(self, ctx, amount: str):
        user = self.get_user(ctx.author.id)
        bank = user[2]
        
        if amount.lower() == "all": amount = bank
        else: 
            try: amount = int(amount)
            except: return await ctx.send("Invalid amount.")
            
        if amount > bank: return await ctx.send("You don't have that much in the bank.")
        if amount <= 0: return await ctx.send("Amount must be positive.")
        
        self.update_balance(ctx.author.id, amount)
        self.update_balance(ctx.author.id, -amount, bank=True)
        await ctx.send(f"💸 Withdrew **${amount:,}** from your bank.")

    @commands.command(name="slots")
    async def slots(self, ctx, bet: int):
        user = self.get_user(ctx.author.id)
        if bet > user[1]: return await ctx.send("You don't have enough money.")
        if bet < 100: return await ctx.send("Minimum bet is $100.")
        
        emojis = ["🍒", "🍊", "🍋", "🍇", "💎", "7️⃣"]
        row = [random.choice(emojis) for _ in range(3)]
        
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        outcome = f"🎰 **{row[0]} | {row[1]} | {row[2]}** 🎰\n"
        
        if row[0] == row[1] == row[2]:
            winnings = bet * 10
            c.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (winnings - bet, ctx.author.id))
            outcome += f"**JACKPOT!** You won **${winnings:,}**!"
        elif row[0] == row[1] or row[1] == row[2] or row[0] == row[2]:
            winnings = int(bet * 1.5)
            c.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (winnings - bet, ctx.author.id))
            outcome += f"**Nice!** You won **${winnings:,}**!"
        else:
            c.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (bet, ctx.author.id))
            outcome += f"ou lost **${bet:,}**."
            
        conn.commit()
        conn.close()
        await ctx.send(outcome)

async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
