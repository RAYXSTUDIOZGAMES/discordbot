# Editing Helper Bot 🤖

An advanced Discord bot with AI, Economy, Leveling, and Moderation features.

## 🚀 Features
- **AI Integration:** Enhanced by Google Gemini for smart responses and image analysis.
- **Economy System:** Work, rob, gamble, and trade stocks.
- **Leveling:** Earn XP and view visual rank cards.
- **Moderation:** Anti-spam, anti-raid, and auto-mod capabilities.
- **Utilities:** Reminders, polls, weather, and more.

## 🛠️ Setup Guide

### Local Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `.env` file with your keys:
   ```env
   DISCORD_TOKEN=your_token
   GEMINI_KEY=your_gemini_key
   LOG_CHANNEL_ID=your_channel_id
   ```
3. Run the bot:
   ```bash
   python bot.py
   ```

### 🚄 Deployment on Railway.app

1. **Upload to GitHub:**
   - Push this entire project folder to a new GitHub repository.

2. **Create Project on Railway:**
   - Go to [Railway.app](https://railway.app/).
   - Click **"New Project"** -> **"Deploy from GitHub repo"**.
   - Select your bot's repository.

3. **Configure Settings:**
   - Railway will automatically detect the `Procfile` and use it.
   - Go to the **Variables** tab in your Railway project.
   - Add the following variables (copy from your `.env`):
     - `DISCORD_TOKEN`
     - `GEMINI_KEY`
     - `LOG_CHANNEL_ID`

4. **Deploy:**
   - Railway should automatically deploy. If not, click "Deploy".
   - Your bot will be online!

**⚠️ Important Note:**
This bot currently uses local files (`.db`) for Economy and Leveling data. On Railway, these files may reset when the bot redeploys. To prevent this, you would need to use a persistent volume or an external database like PostgreSQL.