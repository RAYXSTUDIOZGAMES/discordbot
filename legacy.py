import discord
from discord.ext import commands
import os
import glob
import logging

logger = logging.getLogger('discord_bot')

class LegacyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ignore_commands = [
            "help", "hi", "files", "software_list", "presets", 
            "aecrack", "pscrack", "mecrack", "prcrack", "topazcrack", 
            "ban", "mute", "timeout", "unmute",
            "ask", "explain", "improve", "rewrite", "summarize", "analyze", "idea", "define", "helper",
            "fix", "shorten", "expand", "caption", "script", "format", "title", "translate", "paragraph",
            "remind", "note", "timer", "convert", "emoji", "calculate", "weather", "profile", "serverinfo",
            "creative", "story", "quote", "brainstorm", "design", "name", "aesthetic", "topics", "motivate",
            # New Economy & Leveling commands to ignore
            "work", "rob", "daily", "shop", "buy", "balance", "bal", "inventory", "inv", "slots", "gamble",
            "rank", "level", "leaderboard", "xp"
        ]

    @commands.command(name="files")
    async def list_files_command(self, ctx):
        files_dir = "files"
        if not os.path.exists(files_dir):
            return await ctx.send("No files available currently.")
        
        all_files = []
        for file in glob.glob(f"{files_dir}/*"):
            if os.path.isfile(file):
                filename = os.path.basename(file)
                command_name = os.path.splitext(filename)[0]
                all_files.append(f"!{command_name} - {filename}")

        if not all_files: return await ctx.send("No files available.")
        
        all_files.sort()
        response = f"**Available Files:**\n```\n" + "\n".join(all_files) + "\n```\nType the command (e.g., !foggy_cc) to receive the file."
        try:
            await ctx.author.send(response)
            if ctx.guild: await ctx.send(f"{ctx.author.mention}, check your DMs!")
        except:
            await ctx.send("Couldn't DM you. Here's the list:\n" + response)

    @commands.command(name="software_list")
    async def software_list_command(self, ctx):
        software_list = [
            "**Software Commands:**",
            "!aecrack - Adobe After Effects crack information",
            "!pscrack - Adobe Photoshop crack information",
            "!mecrack - Media Encoder crack information",
            "!prcrack - Adobe Premiere Pro crack information",
            "!topazcrack - Topaz Suite crack information"
        ]
        response = "\n".join(software_list)
        try:
            await ctx.author.send(response)
            if ctx.guild: await ctx.send(f"{ctx.author.mention}, check your DMs!")
        except:
            await ctx.send(response)

    @commands.command(name="presets")
    async def presets_command(self, ctx):
        files_dir = "files"
        if not os.path.exists(files_dir): return await ctx.send("No presets available.")
        
        ffx_files = []
        for file in glob.glob(f"{files_dir}/*.ffx"):
            if os.path.isfile(file):
                filename = os.path.basename(file)
                command_name = os.path.splitext(filename)[0]
                ffx_files.append(f"!{command_name} - {filename}")
        
        if not ffx_files: return await ctx.send("No presets available.")
        
        ffx_files.sort()
        response = f"**Available Presets:**\n```\n" + "\n".join(ffx_files) + "\n```"
        try:
            await ctx.author.send(response)
            if ctx.guild: await ctx.send(f"{ctx.author.mention}, check your DMs!")
        except:
            await ctx.send(response)

    @commands.command(name="aecrack")
    async def aecrack_command(self, ctx):
        response = "**Adobe After Effects Crack Links**\n\n# [2025 (v25.1)](<https://notabin.com/?fb7cab495eecf221#FiT2GfKpydCLgzWGKUv8jHVdMB8dn2YqDoi6E17qEa7F>)\n# [2024 (v24.6.2)](<https://paste.to/?d06e0c5b7a227356#DoWsXVNiFCvYpxZdvE793tu8jnxmq66bxw3k4WpuLA63>)\n# [2022 (v22.6)](<https://paste.to/?2de1e37edd288c59#HKgmUNUEfKG4z3ZrQ6pGxcqiroeHcZqS7AxuEqScHv2t>)\n# [2020 (v17.7)](<https://paste.to/?4c06b2d0730e4b4e#BwAWrNgK633RtYnzGB25us53Z6pMN4QzocRY9MNoFCeU>)\n\n**Installation:**\n_1) Mount the ISO._\n_2) Run autoplay.exe._\n\n**Note:**\n_Cloud-based functionality will not work for this crack. You must ensure to block internet connections to the app in case of unlicensed errors._"
        try: await ctx.author.send(response); await ctx.send(f"{ctx.author.mention}, Check DMs!") if ctx.guild else None
        except: await ctx.send(f"{ctx.author.mention}, enable DMs!\n{response}")

    @commands.command(name="pscrack")
    async def pscrack_command(self, ctx):
        response = "**Adobe Photoshop Crack Information**\n\n# [PHOTOSHOP 2025](<https://hidan.sh/tfbctrj9jn54i>)\n\n# INSTALLATION\n1) Mount the ISO.\n2) Run autoplay.exe.\n\n**Note:**\nCloud-based functionality will not work. Block internet connections.\nEnsure to use uBlock Origin."
        try: await ctx.author.send(response); await ctx.send(f"{ctx.author.mention}, Check DMs!") if ctx.guild else None
        except: await ctx.send(f"{ctx.author.mention}, enable DMs!\n{response}")

    @commands.command(name="mecrack")
    async def mecrack_command(self, ctx):
        response = "**Media Encoder Crack Information**\n\n# [MEDIA ENCODER 2025](<https://hidan.sh/s6ljnz5eizd2>)\n\n# Installation:\n1) Mount the ISO.\n2) Run autoplay.exe.\n\n# Note:\nDo not utilise H.264 or H.265 through ME.\nCloud-based functionality will not work."
        try: await ctx.author.send(response); await ctx.send(f"{ctx.author.mention}, Check DMs!") if ctx.guild else None
        except: await ctx.send(f"{ctx.author.mention}, enable DMs!\n{response}")

    @commands.command(name="prcrack")
    async def prcrack_command(self, ctx):
        response = "**Adobe Premiere Pro Crack Information**\n\n# [PREMIERE PRO 2025](<https://hidan.sh/rlr5vmxc2kbm>)\n\n# Installation:\n1) Mount the ISO.\n2) Run autoplay.exe.\n\n# Note:\nCloud-based functionality will not work. Block internet connections."
        try: await ctx.author.send(response); await ctx.send(f"{ctx.author.mention}, Check DMs!") if ctx.guild else None
        except: await ctx.send(f"{ctx.author.mention}, enable DMs!\n{response}")

    @commands.command(name="topazcrack")
    async def topazcrack_command(self, ctx):
        response = "**Topaz Video AI Crack Information**\n\n# [TOPAZ 6.0.3 PRO](<https://tinyurl.com/Topaz-video-ai-6)\n\n# INSTALLATION\n1) Replace rlm1611.dll in C:\\Program Files\\Topaz Labs LLC\\Topaz Video AI\\.\n2) Copy license.lic to C:\\ProgramData\\Topaz Labs LLC\\Topaz Video AI\\models.\n\n**Note:**\nArchive says 6.0.3, but it works."
        try: await ctx.author.send(response); await ctx.send(f"{ctx.author.mention}, Check DMs!") if ctx.guild else None
        except: await ctx.send(f"{ctx.author.mention}, enable DMs!\n{response}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user: return
        if not message.content.startswith('!') or len(message.content) <= 1: return

        requested_file = message.content[1:]
        requested_file_lower = requested_file.lower()
        first_word = requested_file_lower.split()[0] if requested_file_lower else ""

        if first_word in self.ignore_commands:
            return

        file_paths = [
            f"files/{requested_file}",
            f"files/{requested_file.replace('_', ' ')}",
            f"files/{requested_file.replace(' ', '_')}"
        ]
        file_paths.extend([p.lower() for p in file_paths])
        
        file_extensions = ["", ".txt", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".mp3", ".mp4", ".zip", ".ffx"]
        found_file = None
        
        for base_path in file_paths:
            for ext in file_extensions:
                potential_path = f"{base_path}{ext}"
                if os.path.exists(potential_path) and os.path.isfile(potential_path):
                    found_file = potential_path
                    break
            if found_file: break

        if found_file:
            try:
                await message.author.send(f"Here's your requested file: `{requested_file}`", file=discord.File(found_file))
                if message.guild: await message.channel.send(f"{message.author.mention}, I've sent the file to your DMs!")
            except:
                await message.channel.send(f"{message.author.mention}, I couldn't DM you (privacy settings).")
        else:
            # Simple checking for existence to keep "fuzzy matching" logic simple or just return
            # For now, just logging failure or ignoring to prevent spamming "File not found" on unknown commands
            pass

async def setup(bot):
    await bot.add_cog(LegacyCog(bot))
