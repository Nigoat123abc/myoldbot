# Discord Bot Setup Tutorial

## 📋 Prerequisites

- Python 3.8 or higher installed
- A Discord account
- A Discord server where you have administrator permissions

## 🔧 Step 1: Install Dependencies

### Option A: Using pip (Recommended)

Open your terminal/command prompt and run:

```bash
pip install -r requirements.txt
```

### Option B: Manual Installation

If the above doesn't work, install packages individually:

```bash
pip install discord.py>=2.3.0
pip install python-dotenv>=1.0.0
```

## 🤖 Step 2: Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"** and give it a name
3. Go to the **"Bot"** section in the left sidebar
4. Click **"Add Bot"** and confirm
5. Under **"Token"**, click **"Reset Token"** and copy the token (you'll need this)
6. Scroll down and enable these **Privileged Gateway Intents**:
   - ✅ **MESSAGE CONTENT INTENT** (Required)
   - ✅ **SERVER MEMBERS INTENT** (Required for member tracking)
7. Save changes

## 🔗 Step 3: Invite Bot to Your Server

1. Go to the **"OAuth2"** → **"URL Generator"** section
2. Select these scopes:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Select these bot permissions:
   - ✅ Manage Channels
   - ✅ Manage Roles
   - ✅ Manage Messages
   - ✅ Ban Members
   - ✅ Kick Members
   - ✅ View Channels
   - ✅ Send Messages
   - ✅ Embed Links
   - ✅ Read Message History
   - ✅ Use External Emojis
4. Copy the generated URL and open it in your browser
5. Select your server and authorize

## ⚙️ Step 4: Configure the Bot

1. Open `config.json` in a text editor
2. Replace `YOUR_BOT_TOKEN_HERE` with your bot token from Step 2
3. Set your `guild_id` (Server ID):
   - Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
   - Right-click your server → Copy Server ID
   - Paste it in `config.json`
4. Configure role IDs:
   - Right-click roles → Copy Role ID
   - Set `staff`, `admin`, `moderator` role IDs
5. Configure channel IDs:
   - Right-click channels → Copy Channel ID
   - Set channel IDs for:
     - `ticket_category`: Category where tickets will be created
     - `ticket_logs`: Channel for ticket logs
     - `marketplace`: Channel for marketplace posts
     - `mod_logs`: Channel for moderation logs
     - `verification`: Channel for verification (optional)

## 🚀 Step 5: Run the Bot Locally

Run the bot with:

```bash
python bot.py
```

You should see: `BotName#1234 has logged in!`

## 🌐 Step 6: Hosting the Bot (Keep It Online 24/7)

### Option 1: Free Hosting - Railway (Recommended - Easiest)

Railway is the easiest and most reliable free option for Discord bots.

1. Go to [Railway](https://railway.app) and sign up with GitHub (free)
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Connect your GitHub account and select your repository
4. Railway will auto-detect Python and install dependencies
5. Add environment variable: `BOT_TOKEN` = your bot token
   - In Railway dashboard, go to your project → Variables tab
   - Add new variable: Name = `BOT_TOKEN`, Value = your bot token
6. **Good news**: The bot already supports environment variables! It will use `BOT_TOKEN` if set, otherwise fall back to `config.json`
7. Deploy! Railway gives $5 free credits monthly (usually enough for a Discord bot)
8. Your bot will stay online 24/7 automatically!

**Note**: If you hit the free limit, Railway will pause your bot. You can upgrade to a paid plan or use another option below.

### Option 2: Free Hosting - Render

1. Go to [Render](https://render.com) and sign up
2. Click **"New"** → **"Web Service"**
3. Connect your GitHub repository
4. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Environment**: Python 3
5. Add environment variable: `BOT_TOKEN` = your bot token
   - In Render dashboard, go to your service → Environment tab
   - Add: Key = `BOT_TOKEN`, Value = your bot token
6. **Good news**: The bot already supports environment variables!
7. Deploy! Free tier includes 750 hours/month (may sleep after inactivity)

### Option 3: Free Hosting - Fly.io (Great Alternative)

1. Go to [Fly.io](https://fly.io) and sign up (free tier available)
2. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
3. Create a `fly.toml` file in your project:
   ```toml
   app = "your-bot-name"
   primary_region = "iad"
   
   [build]
   
   [env]
     BOT_TOKEN = "your_token_here"
   
   [[services]]
     internal_port = 8080
     processes = ["app"]
     protocol = "tcp"
   ```
4. Run: `fly launch` and follow prompts
5. Deploy: `fly deploy`
6. Your bot runs 24/7 on Fly.io's free tier!

### Option 4: Free Hosting - Heroku (Limited Free Tier)

1. Install [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Create a `Procfile` in your project:
   ```
   worker: python bot.py
   ```
3. Login: `heroku login`
4. Create app: `heroku create your-bot-name`
5. Set token: `heroku config:set BOT_TOKEN=your_token_here`
6. Deploy: `git push heroku main`
7. Scale: `heroku ps:scale worker=1`

**Note**: Heroku's free tier was discontinued, but you can use alternatives above.

### Option 5: Free Hosting - CodeSandbox (Simple but Limited)

1. Go to [CodeSandbox](https://codesandbox.io) and sign up
2. Create a new Python sandbox
3. Upload your bot files
4. Install dependencies: `pip install -r requirements.txt`
5. Run: `python bot.py`
6. **Note**: CodeSandbox may have limitations for long-running processes. Better for testing than production.

### Option 6: VPS (Virtual Private Server) - Free Trials Available

1. **Oracle Cloud** (Always Free Tier):
   - Sign up at [Oracle Cloud](https://www.oracle.com/cloud/free/)
   - Create a VM instance (always free)
   - SSH into the server
   - Install Python and dependencies
   - Run bot with `nohup python bot.py &` or use `screen`/`tmux`

2. **Google Cloud Platform** (Free Trial):
   - $300 free credits for 90 days
   - Create a Compute Engine VM
   - Similar setup to Oracle Cloud

3. **AWS** (Free Tier):
   - 12 months free EC2 t2.micro instance
   - Similar setup process

### Option 7: Keep Bot Running Locally (Your Computer)

If you want to run it on your own computer 24/7:

**Windows:**
- Use Task Scheduler to run on startup
- Or use `nssm` (Non-Sucking Service Manager) to run as a Windows service

**Linux/Mac:**
- Use `screen` or `tmux`:
  ```bash
  screen -S discordbot
  python bot.py
  # Press Ctrl+A then D to detach
  ```
- Or use `systemd` to create a service (Linux)

## 📝 Additional Configuration

### Creating Required Roles

Make sure these roles exist in your server:
- **Muted** (will be auto-created if missing)
- **Verified** (for verification system - optional)
- Staff/Admin/Moderator roles (as configured in config.json)

### Setting Up Channels

1. Create a category for tickets
2. Create channels for logs (ticket_logs, mod_logs)
3. Create a marketplace channel
4. Copy their IDs to `config.json`

## 🎯 Quick Start Commands

Once the bot is running:

1. **Create Ticket Panel**: `!ticketpanel` (in any channel)
2. **Create Verification Panel**: `!verificationpanel` (in verification channel)
3. **View Help**: `!help`

## 🔒 Security Tips

1. **Never share your bot token** - Keep `config.json` private
2. Add `config.json` to `.gitignore` if using Git (already included!)
3. **Use environment variables for production hosting** - The bot supports this automatically!
   - Set `BOT_TOKEN` environment variable in your hosting platform
   - This is safer than storing the token in files
4. Regularly update dependencies: `pip install --upgrade discord.py`
5. Never commit your bot token to GitHub - use environment variables instead

## 🐛 Troubleshooting

**Bot doesn't respond:**
- Check if bot token is correct
- Verify bot has necessary permissions
- Check if intents are enabled in Developer Portal

**Tickets not creating:**
- Verify category ID is correct
- Check bot has "Manage Channels" permission

**Commands not working:**
- Ensure bot has "Send Messages" permission
- Check command prefix matches config

## 📚 Resources

- [discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord Developer Portal](https://discord.com/developers/docs)
- [Discord.py Support Server](https://discord.gg/dpy)

## 💡 Tips for Free Hosting

1. **Railway** ⭐ **RECOMMENDED**: Most reliable free option, auto-deploys from GitHub, $5 free credits/month
2. **Render**: Good alternative, 750 free hours/month, may sleep after inactivity
3. **Fly.io**: Great for always-on hosting, generous free tier
4. **Oracle Cloud**: Best for always-on free hosting, but requires more technical setup (VPS)
5. **CodeSandbox**: Good for testing, but not ideal for production bots

**Best Choice**: Start with **Railway** - it's the easiest and most reliable free option. If you need more resources, consider upgrading to a paid plan ($5-10/month) or use Oracle Cloud's free VPS.

**Important**: Always use environment variables for your bot token in production (don't commit `config.json` with your token to GitHub)!

---

**Need Help?** Check the bot's `!help` command or review the code comments for more details.
