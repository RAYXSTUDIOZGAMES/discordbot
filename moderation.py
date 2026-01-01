import discord
from discord.ext import commands
import logging
from datetime import datetime, timedelta, timezone
import re
import os
from google import genai
from google.genai import types
import aiohttp
import io
from PIL import Image
from utils import log_activity, is_server_admin, get_server_admin_name

logger = logging.getLogger('discord_bot')

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_warnings = {} # user_id: {"warnings": count, "last_spam_time": timestamp}
        self.guild_join_history = {} # guild_id: [{"user_id": id, "timestamp": time}, ...]
        self.gemini_client = genai.Client(api_key=os.getenv("GEMINI_KEY"))
        
        self.PROFANITY_WORDS = {
            'fuck', 'fucker', 'fucking', 'fucked', 'fucks', 'fuckoff', 'fuckface', 'fuckhead',
            'shit', 'shitty', 'shithead', 'shitface', 'bullshit', 'horseshit', 'chickenshit', 'batshit', 'apeshit', 'dipshit',
            'ass', 'asshole', 'dumbass', 'jackass', 'asshat', 'asswipe', 'fatass', 'badass',
            'bitch', 'bitchy', 'bitches', 'sonofabitch',
            'bastard', 'bastards',
            'damn', 'dammit', 'goddamn', 'goddammit',
            'hell', 'hellhole',
            'crap', 'crappy',
            'piss', 'pissed', 'pissoff',
            'dick', 'dickhead', 'dickface', 'dickwad',
            'cock', 'cocksucker', 'cockhead',
            'cunt', 'cunts',
            'twat', 'twats',
            'pussy', 'pussies',
            'douchebag', 'douche', 'douchenozzle',
            'motherfucker', 'motherfucking', 'mofo',
            'nigga', 'nigger', 'niggas', 'niggers', 'negro', 'nig',
            'faggot', 'fag', 'fags', 'faggots', 'faggy',
            'dyke', 'dykes',
            'tranny', 'trannie',
            'whore', 'whores', 'whorish',
            'slut', 'sluts', 'slutty',
            'skank', 'skanky',
            'hoe', 'hoes', 'hoebag',
            'retard', 'retarded', 'retards', 'tard',
            'spic', 'spics', 'spick',
            'chink', 'chinks',
            'gook', 'gooks',
            'wetback', 'wetbacks',
            'kike', 'kikes',
            'beaner', 'beaners',
            'cracker', 'crackers',
            'honky', 'honkey',
            'pedo', 'pedophile', 'pedophiles', 'paedo',
            'rapist', 'rape', 'raping',
            'molester', 'molest',
            'incest',
            'gay sex', 'gaysex',
            'porn', 'porno', 'pornography',
            'nude', 'nudes', 'nudity',
            'naked',
            'sex', 'sexy', 'sexting',
            'masturbate', 'masturbation', 'jerkoff', 'wank', 'wanker', 'wanking',
            'blowjob', 'handjob', 'rimjob',
            'dildo', 'vibrator',
            'cum', 'cumshot', 'cumming',
            'orgasm', 'orgasms',
            'horny', 'horney',
            'boobs', 'boobies', 'tits', 'titties', 'titty',
            'penis', 'vagina', 'genitals',
            'anal', 'anus',
            'erection', 'boner',
            'kys', 'killurself', 'killyourself',
            'suicide', 'suicidal',
            'nazi', 'nazis', 'hitler',
            'terrorist', 'terrorism',
            'jihad', 'jihadist'
        }
        
        self.SLUR_PATTERNS = [
            r'n+[i1!]+[g9]+[a@4]+[s$]*',
            r'n+[i1!]+[g9]+[e3]+[r]+[s$]*',
            r'f+[a@4]+[g9]+[s$]*',
            r'f+[a@4]+[g9]+[o0]+[t]+[s$]*',
            r'r+[e3]+[t]+[a@4]+[r]+[d]+[s$]*',
            r'c+[u]+[n]+[t]+[s$]*',
            r'b+[i1!]+[t]+[c]+[h]+[e3]*[s$]*',
            r'w+[h]+[o0]+[r]+[e3]+[s$]*',
            r's+[l1]+[u]+[t]+[s$]*',
            r'p+[e3]+[d]+[o0]+[s$]*',
            r'd+[i1!]+[c]+[k]+[s$]*',
            r'c+[o0]+[c]+[k]+[s$]*',
            r'p+[u]+[s$]+[y]+',
            r'a+[s$]+[s$]+[h]+[o0]+[l1]+[e3]+[s$]*',
        ]

    def detect_spam(self, message_content):
        msg_lower = message_content.lower().strip()
        if len(msg_lower) < 3: return False, None
        
        if len(msg_lower) > 5 and len(set(msg_lower.replace(' ', ''))) == 1:
            return True, "Repeated characters spam"
        
        char_freq = {}
        for char in msg_lower:
            if char != ' ': char_freq[char] = char_freq.get(char, 0) + 1
        if char_freq and max(char_freq.values()) / sum(char_freq.values()) > 0.5:
            return True, "Excessive repeated character spam"
        
        if len(msg_lower) > 5:
            for pattern_len in [2, 3]:
                if len(msg_lower) >= pattern_len * 3:
                    pattern = msg_lower[:pattern_len]
                    repeats = 0
                    for i in range(0, len(msg_lower) - pattern_len + 1, pattern_len):
                        if msg_lower[i:i+pattern_len] == pattern or all(c in pattern for c in msg_lower[i:i+pattern_len]):
                            repeats += 1
                    if repeats >= len(msg_lower) // pattern_len * 0.6:
                        return True, "Gibberish spam"
        
        if len(msg_lower) > 10 and message_content.count(message_content.upper()) / len(message_content) > 0.7:
            return True, "Excessive caps spam"
        
        if message_content.count('@') > 3:
            return True, "Excessive mentions spam"
        
        emoji_count = len([c for c in message_content if ord(c) > 0x1F300])
        if emoji_count > 5 and len(msg_lower) < 20:
            return True, "Excessive emojis spam"
        
        return False, None

    async def timeout_user(self, user, guild, hours=24):
        try:
            timeout_duration = timedelta(hours=hours)
            await user.timeout(timeout_duration, reason=f"Auto-muted after 3 spam warnings")
            logger.info(f"Timed out {user.name} for {hours} hours")
            return True
        except Exception as e:
            logger.error(f"Error timing out user: {str(e)}")
            return False

    def detect_invite_links(self, content):
        invite_patterns = [
            r'discord\.gg/[a-zA-Z0-9]+',
            r'discord\.com/invite/[a-zA-Z0-9]+',
            r'discordapp\.com/invite/[a-zA-Z0-9]+',
        ]
        for pattern in invite_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False

    def detect_profanity(self, content):
        content_lower = content.lower()
        content_normalized = re.sub(r'[^a-z0-9\s]', '', content_lower)
        content_no_spaces = content_normalized.replace(' ', '')
        
        words = re.findall(r'\b\w+\b', content_lower)
        for word in words:
            if word in self.PROFANITY_WORDS:
                return True, word
        
        for phrase in self.PROFANITY_WORDS:
            if ' ' in phrase and phrase in content_lower:
                return True, phrase
        
        for pattern in self.SLUR_PATTERNS:
            match = re.search(pattern, content_no_spaces, re.IGNORECASE)
            if match:
                return True, match.group()
        
        return False, None

    async def download_image(self, url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        img = Image.open(io.BytesIO(image_data))
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        buffer = io.BytesIO()
                        img.save(buffer, format='JPEG', quality=85)
                        return buffer.getvalue()
        except:
            pass
        return None

    async def analyze_image_content(self, image_url):
        try:
            image_data = await self.download_image(image_url)
            if not image_data: return False, None
            
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_bytes(data=image_data, mime_type="image/jpeg"),
                            types.Part.from_text("Analyze this image. Is it inappropriate, NSFW, contains nudity, violence, gore, hate symbols, or explicit content? Reply with ONLY 'YES' or 'NO' followed by a brief reason.")
                        ]
                    )
                ]
            )
            result = response.text.strip().upper()
            is_bad = result.startswith('YES')
            reason = response.text.strip() if is_bad else None
            return is_bad, reason
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return False, None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or message.author.bot:
            return
        
        if 'bmr' in message.author.name.lower():
            return
        
        if isinstance(message.channel, discord.DMChannel):
            return

        # 1. Profanity Check
        if not (hasattr(message.author, 'guild_permissions') and message.author.guild_permissions.administrator):
            has_profanity, bad_word = self.detect_profanity(message.content)
            if has_profanity:
                try:
                    await message.delete()
                    logger.info(f"Deleted profanity from {message.author.name}: {bad_word}")
                    await message.channel.send(f"⚠️ {message.author.mention} - Your message was removed for containing inappropriate language. You have been muted for 24 hours.", delete_after=10)
                    await message.author.timeout(timedelta(hours=24), reason=f"Profanity: {bad_word}")
                except Exception as e:
                    logger.error(f"Profanity handling error: {e}")
                return # Stop processing this message

        # 2. Image Moderation
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                is_bad, reason = await self.analyze_image_content(attachment.url)
                if is_bad:
                    try:
                        await message.delete()
                        await message.channel.send(f"🚫 {message.author.mention} - Your image was removed for containing inappropriate content. You have been muted for 24 hours.", delete_after=10)
                        await message.author.timeout(timedelta(hours=24), reason="Inappropriate image")
                    except: pass
                    return

        # 3. Spam Check
        is_spam, spam_reason = self.detect_spam(message.content)
        if is_spam:
            user_id = message.author.id
            current_time = datetime.now(timezone.utc)
            if user_id not in self.user_warnings:
                self.user_warnings[user_id] = {"warnings": 0, "last_spam_time": current_time}
            
            time_diff = (current_time - self.user_warnings[user_id]["last_spam_time"]).total_seconds()
            if time_diff < 300:
                self.user_warnings[user_id]["warnings"] += 1
            else:
                self.user_warnings[user_id]["warnings"] = 1
            self.user_warnings[user_id]["last_spam_time"] = current_time
            
            try: await message.delete()
            except: pass
            
            warnings = self.user_warnings[user_id]["warnings"]
            if warnings == 1:
                await message.channel.send(f"⚠️ {message.author.mention} - Stop spamming! ({spam_reason})")
            elif warnings == 2:
                await message.channel.send(f"⚠️⚠️ {message.author.mention} - One more and you'll be muted!")
            elif warnings >= 3:
                await self.timeout_user(message.author, message.guild, hours=24)
                await message.channel.send(f"🔇 {message.author.mention} has been **muted for 24 hours**.")
                self.user_warnings[user_id]["warnings"] = 0
            return

        # 4. Security Check (Invites)
        if self.detect_invite_links(message.content):
            try:
                await message.delete()
                await message.channel.send(f"🔒 {message.author.mention} - Invite links are forbidden.")
            except: pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        guild_id = guild.id
        current_time = datetime.now(timezone.utc)
        
        if guild_id not in self.guild_join_history:
            self.guild_join_history[guild_id] = []
        
        self.guild_join_history[guild_id].append({"user_id": member.id, "timestamp": current_time})
        two_min_ago = current_time - timedelta(minutes=2)
        self.guild_join_history[guild_id] = [j for j in self.guild_join_history[guild_id] if j["timestamp"] > two_min_ago]
        
        # Anti-Raid
        one_min_ago = current_time - timedelta(minutes=1)
        simultaneous_joins = [j for j in self.guild_join_history[guild_id] if j["timestamp"] > one_min_ago]
        
        if len(simultaneous_joins) >= 5:
            embed = discord.Embed(title="🚨 POTENTIAL RAID DETECTED", description=f"**{len(simultaneous_joins)} users joined simultaneously.**", color=discord.Color.red())
            for channel in guild.text_channels:
                if 'mod' in channel.name or 'log' in channel.name:
                    try: await channel.send(embed=embed)
                    except: pass
        
        # Account Age
        if (current_time - member.created_at).days < 7:
            embed = discord.Embed(title="⚠️ New Account Join", description=f"{member.mention} joined with a **{(current_time - member.created_at).days}-day-old** account", color=discord.Color.yellow())
            for channel in guild.text_channels:
                if 'welcome' in channel.name or 'mod' in channel.name:
                    try: await channel.send(embed=embed)
                    except: pass

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        from utils import guild_inviters, save_guild_inviters
        logger.info(f'Bot joined new server: {guild.name} (ID: {guild.id})')
        
        inviter_name = "Unknown"
        try:
            async for entry in guild.audit_logs(limit=10, action=discord.AuditLogAction.bot_add):
                if entry.target.id == self.bot.user.id:
                    inviter = entry.user
                    inviter_name = inviter.name
                    guild_inviters[str(guild.id)] = inviter.id
                    save_guild_inviters(guild_inviters)
                    break
        except:
            if guild.owner:
                guild_inviters[str(guild.id)] = guild.owner.id
                save_guild_inviters(guild_inviters)
                inviter_name = guild.owner.name
        
        await log_activity(self.bot, "📥 Joined New Server", f"Bot added to **{guild.name}** by {inviter_name}", color=0x00FF00)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        from utils import guild_inviters, save_guild_inviters
        logger.info(f'Bot removed from server: {guild.name} (ID: {guild.id})')
        if str(guild.id) in guild_inviters:
            del guild_inviters[str(guild.id)]
            save_guild_inviters(guild_inviters)
        await log_activity(self.bot, "📤 Left Server", f"Bot removed from **{guild.name}**", color=0xFF0000)

    @commands.command(name="ban")
    async def ban_command(self, ctx, member: discord.Member = None):
        if not is_server_admin(ctx.author, ctx.guild):
            return await ctx.send("❌ You don't have permission.")
        if not member: return await ctx.send("Usage: !ban @user")
        
        if 'bmr' in member.name.lower() or is_server_admin(member, ctx.guild):
            return await ctx.send("❌ Cannot ban this user.")
            
        try:
            await ctx.guild.ban(member, reason=f"Banned by {ctx.author.name}")
            await ctx.send(f"🔨 {member.name} has been **BANNED**.")
            await log_activity(self.bot, "🔨 User Banned", f"**{member.name}** was banned by {ctx.author.name}", color=0xFF0000)
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @commands.command(name="timeout")
    async def timeout_command(self, ctx, member: discord.Member = None, duration: str = None):
        if not is_server_admin(ctx.author, ctx.guild):
            return await ctx.send("❌ You don't have permission.")
        if not member or not duration: return await ctx.send("Usage: !timeout @user 1h")
        
        try:
            seconds = 0
            if 'h' in duration: seconds = int(duration.replace('h','')) * 3600
            elif 'm' in duration: seconds = int(duration.replace('m','')) * 60
            elif 'd' in duration: seconds = int(duration.replace('d','')) * 86400
            elif 's' in duration: seconds = int(duration.replace('s',''))
            
            await member.timeout(timedelta(seconds=seconds), reason=f"Timeout by {ctx.author.name}")
            await ctx.send(f"🔇 {member.name} timed out for {duration}.")
            await log_activity(self.bot, "🔇 User Timed Out", f"**{member.name}** timed out by {ctx.author.name}", color=0xFFA500)
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @commands.command(name="mute")
    async def mute_command(self, ctx, member: discord.Member = None, duration: str = None):
        await ctx.invoke(self.timeout_command, member=member, duration=duration)

    @commands.command(name="unmute")
    async def unmute_command(self, ctx, member: discord.Member = None):
        if not is_server_admin(ctx.author, ctx.guild):
            return await ctx.send("❌ Permission denied.")
        try:
            await member.timeout(None, reason="Unmuted")
            await ctx.send(f"🔊 {member.name} unmuted.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
