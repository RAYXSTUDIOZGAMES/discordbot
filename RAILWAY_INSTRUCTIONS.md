# 🚂 How to Deploy on Railway

## 1. Get your code on GitHub
Railway needs your code to be on GitHub.
1. Create a new repository on [GitHub.com](https://github.com/new).
2. Upload all the files in this folder to that repository.
   - You can drag and drop them or use these commands in your terminal:
     ```bash
     git init
     git add .
     git commit -m "Initial commit"
     git branch -M main
     git remote add origin <YOUR_GITHUB_REPO_URL>
     git push -u origin main
     ```

## 2. Create Project on Railway
1. Go to [Railway.app](https://railway.app) and login.
2. Click **+ New Project** (top right).
3. Choose **Deploy from GitHub repo**.
4. Select the repository you just created.
5. Click **Deploy Now**.

## 3. 🔑 IMPORTANT: Add Your Keys (Variables)
Your bot will crash immediately because it doesn't have the keys. You need to add them.

1. Click on your project card in Railway dashboard.
2. Click on the **Variables** tab (it might strictly say "Variables" or have a `{}` icon).
3. Click **+ New Variable**.
4. Add these 3 variables (copy them exactly):

| VARIABLE NAME | VALUE (Paste your key) |
| :--- | :--- |
| `DISCORD_TOKEN` | (Paste your long Discord Bot Token here) |
| `GEMINI_KEY` | (Paste your Google Gemini API Key here) |
| `LOG_CHANNEL_ID` | (Paste your Discord Channel ID here) |

**Example:**
- Variable: `DISCORD_TOKEN`
- Value: `MTEwND...` (your real token)

5. Once added, Railway will automatically restart your bot.

## 4. Check Logs
- Go to the **Logs** tab.
- You should see: `Logged in as YourBotName`.
- If you see errors, check that your keys are correct!
