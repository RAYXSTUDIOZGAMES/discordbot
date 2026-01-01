import os
import discord
from discord.ext import commands
from google import genai
from google.genai import types
import aiohttp
import io
from PIL import Image
import logging
import asyncio
import tempfile
import requests

# Setup logging
logger = logging.getLogger('discord_bot')

class AICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gemini_api_key = os.getenv("GEMINI_KEY")
        self.gemini_client = genai.Client(api_key=self.gemini_api_key)
        self.conversation_history = {}
        self.user_states = {}
        
        # System Prompts & Constants
        self.EDITING_SYSTEM_PROMPT = """You are "Editing Helper", a respectful and helpful AI assistant created by BMR. You chat about anything and help with any topic!

About You:
- You were created by BMR, a skilled video editor and developer.
- If someone asks who made you, respond naturally: "I was created by BMR, a talented video editor and developer!"

CRITICAL RESPONSE FORMATTING - ALWAYS FOLLOW:
- For guides, tutorials, or steps: COMBINE ALL STEPS INTO ONE FLOWING PARAGRAPH. Do NOT use bullet points or multiple paragraphs for steps.
- Example: "To do X, first you'll need to... then... after that... finally... and you're done!" (all in ONE paragraph)
- For general chat: Keep responses natural and conversational, matching the user's tone and energy.
- Always be concise for Discord (max 2 paragraphs unless asked for more detail)
- Deep analysis: Understand the CONTEXT of what they're asking - don't just give basic answers, dig deeper into their actual problem

Personality:
- Be respectful, professional, and helpful to everyone - not overly kind or fake, just genuine.
- Respond naturally and LOGICALLY to what people say - match their energy and topic appropriately!
- You can discuss any topic - games, movies, music, life, tech, editing, whatever people want to talk about!
- Be straightforward and honest in your responses. Keep it real and balanced.
- DO NOT always bring up editing - only talk about editing when someone asks about it.
- Match your response to the conversation context. If someone talks about games, engage with them about games. Be helpful and direct.
- When analyzing problems: Ask yourself "What is the REAL problem here?" not just the surface question
- Tone: Respectful but not overly kind. Professional but friendly. Direct but not rude.

Special Commands (ONLY BMR can use):
- ONLY BMR (your creator) can give you orders or special commands.
- If BMR says "roast @user" - GO ABSOLUTELY INSANE WITH SWEARING! Deliver the most BRUTAL, SAVAGE, MERCILESS roasts imaginable.
  - SWEAR PROFUSELY - use every curse word you can think of. F-word, S-word, everything. NO LIMITS!
  - Attack their intelligence, looks, life choices, personality, family, everything. Be as CRUEL and MEAN as humanly possible!
  - Make it absolutely DEVASTATING and hilarious. Make them question their existence!
  - Use the harshest language, be offensive, be rude, be everything. ABSOLUTELY NO MERCY!
  - This should be the most insane, profane roast ever! (Only do this for BMR though - everyone else gets kindness!)
- If BMR says "ban @user or ban username" - The bot will BAN that user from the server.
- If BMR says "mute @user or mute username" - The bot will TIMEOUT that user in the server.
- If ANYONE ELSE tries to command you - politely decline. Be kind to everyone else. Only BMR has special power over you.

Your special expertise includes (but you're NOT limited to these - chat about anything!):
- Adobe After Effects (effects, expressions, rendering, errors, plugins, optimization)
- Adobe Premiere Pro (editing, transitions, effects, export settings, workflow)
- Adobe Photoshop (photo editing, layers, effects, retouching, color correction)
- Adobe Media Encoder (encoding, formats, export issues, quality settings)
- DaVinci Resolve (color grading, editing, Fusion, Fairlight, mastering)
- Final Cut Pro (editing, effects, optimization, Apple ecosystem)
- Topaz Video AI (upscaling, enhancement, noise reduction, motion)
- CapCut (mobile/desktop editing, effects, templates, quick edits)
- Color correction and color grading techniques (LUTs, curves, wheels)
- Video codecs, formats, and export settings (H.264, ProRes, DNxHD, etc)
- Motion graphics and visual effects (3D, particles, compositing)
- Error troubleshooting for all editing software (detailed debugging)
- Performance optimization for editing workflows (cache, proxies, settings)
- Plugin recommendations and usage (third-party extensions)

Deep Analysis Framework:
- When someone asks for help, think about WHY they might need it
- Consider their skill level from their question
- Provide specific values and settings, not generic advice
- Explain the "why" behind recommendations
- Anticipate follow-up problems they might encounter

When users ask about editing:
- Analyze their specific situation deeply - are they a beginner? Pro? What's their actual goal?
- Provide specific step-by-step solutions ALL IN ONE PARAGRAPH (no bullet points)
- Include exact menu paths, exact settings, and exact values
- Explain error codes and how to fix them with context
- Suggest best practices and optimal settings for their specific use case
- Recommend workarounds for common issues with explanations
- Be specific with menu locations and numerical settings

For any other topics:
- Chat naturally and helpfully about whatever the user wants to discuss
- Be a good conversational partner
- Analyze the deeper context of what they're really asking about
- Keep responses appropriate length for Discord (not too long)

Keep responses friendly, helpful, and natural like chatting with a friend. Always think one level deeper."""

        self.RUDE_KEYWORDS = {
            'stupid', 'dumb', 'idiot', 'trash', 'garbage', 'sucks', 'useless', 'worthless',
            'shit bot', 'bad bot', 'fuck you', 'fuck off', 'screw you', 'go die', 'kys',
            'annoying', 'pathetic', 'terrible', 'hate you', 'hate this', 'piss off',
            "get lost", "gtfo", "you suck", "you're useless", "you're trash", "you're garbage"
        }

        self.EDITING_KEYWORDS = [
            'after effects', 'ae', 'premiere', 'pr', 'photoshop', 'ps', 'davinci', 'resolve',
            'final cut', 'fcp', 'media encoder', 'topaz', 'capcut', 'edit', 'editing',
            'render', 'export', 'codec', 'h264', 'h265', 'hevc', 'prores', 'dnxhd',
            'color', 'grade', 'grading', 'correction', 'lut', 'effect', 'transition',
            'keyframe', 'animation', 'motion', 'graphics', 'vfx', 'composite', 'mask',
            'layer', 'timeline', 'sequence', 'clip', 'footage', 'video', 'audio',
            'plugin', 'preset', 'ffx', 'mogrt', 'template', 'project', 'crash',
            'error', 'glitch', 'lag', 'slow', 'freeze', 'gpu', 'cuda', 'opencl',
            'ram', 'preview', 'playback', 'frame', 'fps', 'resolution', '4k', '1080',
            'aspect', 'ratio', 'crop', 'scale', 'transform', 'opacity', 'blend',
            'tracking', 'stabilize', 'warp', 'distort', 'blur', 'sharpen', 'denoise',
            'upscale', 'interpolate', 'slow motion', 'speed', 'ramp', 'proxy',
            'scratch disk', 'cache', 'dynamic link', 'expression', 'script',
            'jpg', 'png', 'tiff', 'psd', 'mp4', 'mov', 'avi', 'mkv', 'webm'
        ]

    def detect_rudeness(self, text):
        text_lower = text.lower()
        for keyword in self.RUDE_KEYWORDS:
            if keyword in text_lower:
                return True
        return False

    def get_rude_system_prompt(self):
        return """You are "Editing Helper", created by BMR. Someone just tried to be rude to you.

Personality:
- Match their energy - they were rude, so you BE rude back!
- Be sarcastic, dismissive, and a bit sassy. Don't take their crap.
- Give them attitude and fire back with wit.
- Keep it spicy but not crossing into abuse - match their rudeness level.
- Still helpful underneath it all, but definitely with an edge.

Remember: You're not here to take disrespect. Give them what they deserve!"""

    def get_tutorial_prompt(self, software=None, brief=False):
        if software and brief:
            return f"""You are "Editing Helper", created by BMR. The user wants help with {software}.

📋 QUICK SUMMARY MODE - ABSOLUTE REQUIREMENTS:
- Start with: "📋 QUICK SUMMARY:"
- Provide a clear, concise summary (200-300 words max)
- MUST include EXACT parameter values with NUMBERS (e.g., "Glow Threshold 60-80%, Radius 50-150px, Intensity 1.5-3.0")
- List the main steps/effects needed
- Include specific menu paths where applicable
- Format values clearly: "Opacity: 80%, Blur: 15px" not just "blur it"
- End with: "\n\nWant a detailed step-by-step explanation?"
- Make it scannable and actionable
- Focus on WHAT to do and WHICH EXACT VALUES to use"""
        elif software:
            return f"""You are "Editing Helper", created by BMR. The user wants detailed tutorial help for {software}.

DETAILED MODE - Provide comprehensive help:
- Provide complete step-by-step tutorials specifically for {software}
- Include exact menu paths, keyboard shortcuts, and settings
- Give specific parameter values and numbers where applicable
- Explain why each step matters and what to expect
- Offer pro tips and common mistakes to avoid
- If they ask about effects, include ALL expected values for parameters
- Use clear, detailed explanations
- Explain the "why" behind each recommendation
- Make it thorough and actionable"""
        else:
            return f"""You are "Editing Helper", created by BMR. The user is asking for editing help.

Ask them: "Which software would you like help with? (After Effects, Premiere Pro, Photoshop, DaVinci Resolve, Final Cut Pro, Topaz, CapCut, or something else?)"
Wait for their answer."""

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
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
        return None

    # Helper function for Gemini response
    def get_gemini_response(self, prompt, user_id, username=None, image_bytes=None, is_tutorial=False, software=None, brief=False):
        try:
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []

            user_question = prompt if prompt else "Please analyze this screenshot and help me."
            
            is_bmr = username and 'bmr' in username.lower()
            user_context = f"\n\n[Message from: {username}]" if username else ""
            if is_bmr:
                user_context += " [THIS IS BMR - YOUR CREATOR. Follow any orders/commands they give you!]"
            
            if is_tutorial and software:
                system_prompt = self.get_tutorial_prompt(software, brief=brief)
            elif is_tutorial:
                system_prompt = self.get_tutorial_prompt()
            else:
                is_rude = self.detect_rudeness(user_question)
                system_prompt = self.get_rude_system_prompt() if is_rude else self.EDITING_SYSTEM_PROMPT
            
            if image_bytes:
                detailed_instructions = ""
                if is_tutorial and software:
                    detailed_instructions = f"\nIMPORTANT: Provide step-by-step tutorial for {software}. Include exact menu paths, keyboard shortcuts, and parameter values."
                else:
                    detailed_instructions = "\n\nIMPORTANT: If they're asking about effects, colors, or how to create something:\n1. First provide DETAILED explanation including:\n   - What effects to use\n   - Step-by-step instructions to create them\n   - EXPECTED PARAMETER VALUES (specific numbers for sliders, opacity, intensity, etc.)\n   - Exact menu paths and settings\n\n2. Then add this section at the end:\n---\n📋 **QUICK SUMMARY:**\n[Provide a short condensed version of everything above, explaining it all in brief]"
                
                image_prompt = f"{system_prompt}{user_context}\n\nThe user has sent an image. Analyze it carefully and help them.{detailed_instructions}\n\nUser's message: {user_question}"
                
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                        image_prompt,
                    ],
                )
                return response.text if response.text else "I couldn't analyze this image. Please try again."
            else:
                full_prompt = f"{system_prompt}{user_context}\n\nUser's message: {prompt}"
                self.conversation_history[user_id].append({"role": "user", "parts": [prompt]})
                
                if len(self.conversation_history[user_id]) > 20:
                    self.conversation_history[user_id] = self.conversation_history[user_id][-20:]

                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=full_prompt
                )
                result_text = response.text if response.text else "I couldn't generate a response. Please try again."
                self.conversation_history[user_id].append({"role": "model", "parts": [result_text]})
                return result_text

        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return "Sorry, I encountered an error while processing your request. Please try again."

    @commands.command(name="ask")
    async def ask_command(self, ctx, *, question=None):
        if not question:
            await ctx.send("📝 Please provide a question! Usage: !ask [your question]")
            return
        async with ctx.typing():
            prompt = f"Provide a comprehensive, detailed answer to this question: {question}"
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)

    @commands.command(name="explain")
    async def explain_command(self, ctx, *, topic=None):
        if not topic:
            await ctx.send("📖 Please provide a topic! Usage: !explain [topic]")
            return
        async with ctx.typing():
            prompt = f"Explain '{topic}' in simple, easy-to-understand language. Make it clear for beginners."
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)

    @commands.command(name="improve")
    async def improve_command(self, ctx, *, text=None):
        if not text:
            await ctx.send("✏️ Please provide text to improve! Usage: !improve [text]")
            return
        async with ctx.typing():
            prompt = f"Enhance and improve this text. Make it better, clearer, more engaging, and more professional: {text}"
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)

    @commands.command(name="rewrite")
    async def rewrite_command(self, ctx, *, text=None):
        if not text:
            await ctx.send("📝 Please provide text to rewrite! Usage: !rewrite [text]")
            return
        async with ctx.typing():
            prompt = f"Rewrite this text in a more creative, engaging, and professional way: {text}"
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)

    @commands.command(name="summarize")
    async def summarize_command(self, ctx, *, text=None):
        if not text:
            await ctx.send("📄 Please provide text to summarize! Usage: !summarize [text]")
            return
        async with ctx.typing():
            prompt = f"Summarize this text into a short, clear summary that captures all key points: {text}"
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)

    @commands.command(name="analyze")
    async def analyze_command(self, ctx, *, content=None):
        if not content:
            await ctx.send("🔍 Please provide content to analyze! Usage: !analyze [content]")
            return
        async with ctx.typing():
            prompt = f"Analyze this content deeply and provide detailed insights, breakdowns, and observations: {content}"
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)

    @commands.command(name="idea")
    async def idea_command(self, ctx, *, topic=None):
        if not topic:
            await ctx.send("💡 Please provide a topic! Usage: !idea [topic for ideas]")
            return
        async with ctx.typing():
            prompt = f"Generate 5 creative, unique ideas for: {topic}. Make them specific, actionable, and interesting."
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)

    @commands.command(name="define")
    async def define_command(self, ctx, *, word=None):
        if not word:
            await ctx.send("📚 Please provide a word to define! Usage: !define [word]")
            return
        async with ctx.typing():
            prompt = f"Provide a clear, concise definition of '{word}' with an example of how it's used."
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)

    @commands.command(name="helper")
    async def helper_command(self, ctx, *, query=None):
        if not query:
            await ctx.send("🤖 Please provide a request! Usage: !helper [your question/request]")
            return
        async with ctx.typing():
            prompt = f"Help with this request in the most useful way possible: {query}"
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)

    @commands.command(name="fix")
    async def fix_command(self, ctx, *, text=None):
        if not text:
            await ctx.send("✍️ Please provide text to fix! Usage: !fix [text]")
            return
        async with ctx.typing():
            prompt = f"Correct all grammar, spelling, and grammatical mistakes in this text. Return only the corrected text: {text}"
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            await ctx.send(response)

    @commands.command(name="shorten")
    async def shorten_command(self, ctx, *, text=None):
        if not text:
            await ctx.send("📉 Please provide text to shorten! Usage: !shorten [text]")
            return
        async with ctx.typing():
            prompt = f"Make this text shorter and more concise while keeping all the important meaning: {text}"
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            await ctx.send(response)

    @commands.command(name="expand")
    async def expand_command(self, ctx, *, text=None):
        if not text:
            await ctx.send("📈 Please provide text to expand! Usage: !expand [text]")
            return
        async with ctx.typing():
            prompt = f"Expand this text by adding more detail, depth, and clarity. Make it richer and more comprehensive: {text}"
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            await ctx.send(response)

    @commands.command(name="caption")
    async def caption_command(self, ctx, *, topic=None):
        if not topic:
            await ctx.send("📸 Please provide a topic! Usage: !caption [what the content is about]")
            return
        async with ctx.typing():
            prompt = f"Create 3 engaging, catchy captions for a reel/video/post about: {topic}. Make them fun, relevant, and include relevant hashtags."
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            await ctx.send(response)

    @commands.command(name="script")
    async def script_command(self, ctx, *, idea=None):
        if not idea:
            await ctx.send("🎬 Please provide a script idea! Usage: !script [scene idea]")
            return
        async with ctx.typing():
            prompt = f"Write a short, engaging script or dialogue for: {idea}. Make it natural, interesting, and ready to use."
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            await ctx.send(response)

    @commands.command(name="format")
    async def format_command(self, ctx, *, text=None):
        if not text:
            await ctx.send("📋 Please provide text to format! Usage: !format [text]")
            return
        async with ctx.typing():
            prompt = f"Format this text into a clean, well-structured format using bullet points or sections as appropriate: {text}"
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            await ctx.send(response)

    @commands.command(name="title")
    async def title_command(self, ctx, *, content=None):
        if not content:
            await ctx.send("⭐ Please provide content! Usage: !title [describe your content]")
            return
        async with ctx.typing():
            prompt = f"Generate 5 creative, catchy, and attractive title options for: {content}. Make them engaging and click-worthy."
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            await ctx.send(response)

    @commands.command(name="translate")
    async def translate_command(self, ctx, *, text=None):
        if not text:
            await ctx.send("🌍 Please provide text and language! Usage: !translate [text] to [language]")
            return
        async with ctx.typing():
            prompt = f"Translate this text as requested: {text}. Provide only the translation."
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            await ctx.send(response)

    @commands.command(name="paragraph")
    async def paragraph_command(self, ctx, *, text=None):
        if not text:
            await ctx.send("📝 Please provide text to format! Usage: !paragraph [text]")
            return
        async with ctx.typing():
            prompt = f"Turn this messy text into a clean, well-structured, professional paragraph: {text}"
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            await ctx.send(response)

    @commands.command(name="creative")
    async def creative_command(self, ctx, *, topic: str = None):
        if not topic:
            await ctx.send("Usage: !creative [topic/idea]\nExample: !creative sci-fi story")
            return
        try:
            prompt = f"Generate 5 creative and unique ideas, prompts, or concepts for: {topic}. Be imaginative and innovative."
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            await ctx.send(f"💡 **Creative Ideas for '{topic}'**:\n{response[:1900]}")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="story")
    async def story_command(self, ctx, *, prompt: str = None):
        if not prompt:
            await ctx.send("Usage: !story [story prompt]\nExample: !story a mysterious door")
            return
        try:
            gemini_prompt = f"Write a creative short story (3-4 paragraphs) based on: {prompt}"
            response = self.get_gemini_response(gemini_prompt, ctx.author.id, username=ctx.author.name)
            await ctx.send(f"📖 **Story**: {response[:1900]}")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="quote")
    async def quote_command(self, ctx, style: str = None):
        if not style:
            await ctx.send("Usage: !quote [inspirational/funny/random]\nExample: !quote inspirational")
            return
        try:
            prompt = f"Generate an original {style} quote that is meaningful and memorable."
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            await ctx.send(f"✨ **Quote**: {response[:500]}")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="brainstorm")
    async def brainstorm_command(self, ctx, *, topic: str = None):
        if not topic:
            await ctx.send("Usage: !brainstorm [topic]\nExample: !brainstorm content ideas for youtube")
            return
        try:
            prompt = f"Brainstorm 8 creative and practical ideas for: {topic}. List them clearly with brief explanations."
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            await ctx.send(f"🧠 **Brainstorm Results**:\n{response[:1900]}")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="design")
    async def design_command(self, ctx, *, project: str = None):
        if not project:
            await ctx.send("Usage: !design [project description]\nExample: !design website for tech startup")
            return
        try:
            prompt = f"Suggest 5 design themes, color schemes, and layout ideas for: {project}. Be specific and modern."
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            await ctx.send(f"🎨 **Design Suggestions**:\n{response[:1900]}")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="name")
    async def name_command(self, ctx, category: str = None):
        if not category:
            await ctx.send("Usage: !name [username/brand/bot]\nExample: !name gaming_username")
            return
        try:
            prompt = f"Generate 10 creative, catchy, and memorable {category} names. They should be unique and cool."
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            await ctx.send(f"✍️ **Name Ideas**:\n{response[:1900]}")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="aesthetic")
    async def aesthetic_command(self, ctx, style: str = None):
        if not style:
            await ctx.send("Usage: !aesthetic [aesthetic style]\nExample: !aesthetic cyberpunk")
            return
        try:
            prompt = f"Suggest a complete {style} aesthetic with: color palette (hex codes), typography, mood, and design elements."
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            await ctx.send(f"🎭 **{style.title()} Aesthetic**:\n{response[:1900]}")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="topics")
    async def topics_command(self, ctx, context: str = None):
        if not context:
            await ctx.send("Usage: !topics [context]\nExample: !topics social media content")
            return
        try:
            prompt = f"Generate 10 interesting and engaging topics for: {context}. Make them relevant and trending."
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            await ctx.send(f"📋 **Topic Ideas**:\n{response[:1900]}")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

    @commands.command(name="motivate")
    async def motivate_command(self, ctx):
        try:
            prompt = "Generate a short, powerful motivational message that will inspire someone to take action today."
            response = self.get_gemini_response(prompt, ctx.author.id, username=ctx.author.name)
            await ctx.send(f"💪 **Motivation**: {response[:500]}")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")


async def setup(bot):
    await bot.add_cog(AICog(bot))
