# Discord Bot 

A comprehensive Discord bot built with discord.py featuring ticket system, marketplace, moderation, and anti-raid security.

## Features

### 🎫 Ticket System
- Button-based ticket creation
- Two ticket types:
  - **Bug Report**: For reporting bugs and issues
  - **Skill Role Application**: For applying to skill roles (with interactive form!)
- Private ticket channels
- **Skill Role Application Flow**: User clicks button → fills modal form → staff reviews → `/approve` assigns role
- Close ticket button
- Comprehensive logging

### 👋 Welcome System
- Customizable welcome message in designated channel
- Auto-role assignment on join
- Welcome embed with member info

### 💼 Marketplace System
- Post hiring advertisements
- Post hirable advertisements
- Format enforcement
- Auto-delete incorrect posts
- Configurable cooldown system

### 🛡️ Moderation
- Ban, kick, mute, unmute commands
- Warning system with tracking
- Message logging
- Anti-spam protection

### 🔒 Anti-Raid Security
- Join spam detection
- Auto-lock server capability
- Account age verification
- Verification system with buttons

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure the bot:**
   - Edit `config.json` with your bot token and server IDs
   - Set **`channels.cmds`** to your **#cmds** channel ID (where users run `/hiring` and `/hirable`)
   - Set **`channels.hiring_posts`** to your **#hiring-posts** channel ID (where hiring posts appear)
   - Set **`channels.hirable_posts`** to your **#hirable-posts** channel ID (where hirable posts appear)
   - See `tuto.md` for detailed setup instructions

3. **Run the bot:**
   ```bash
   python bot.py
   ```

## Slash commands (recommended)

Type **`/`** in any channel to use slash commands. They are synced when the bot starts (guild-specific if `guild_id` is set in config).

- **Marketplace:** 
  - Use **`/hiring`** in **#cmds** → opens an easy form → bot posts in **#hiring-posts**
  - Use **`/hirable`** in **#cmds** → opens an easy form → bot posts in **#hirable-posts**
  - Forms have separate fields - no manual formatting needed!
  - You can also use these commands directly in their respective channels
- **Tickets:** `/ticketpanel`, `/approve`
- **Moderation:** `/ban`, `/kick`, `/mute`, `/unmute`, `/warn`, `/warnings`, `/clearwarnings`
- **Security:** `/verificationpanel`, `/lockdown`, `/unlock`, `/checkuser`
- **Help:** `/help`

## Configuration

All settings are in `config.json`:
- Bot token
- Role IDs (staff, admin, moderator)
- Channel IDs: **ticket_category**, **ticket_logs**, **hiring_posts**, **hirable_posts**, **cmds**, **mod_logs**, **verification**, **welcome**
- **Welcome settings**: Enable/disable welcome messages, custom message, auto-role ID
- Security settings
- Anti-spam settings

## Commands (slash and prefix)

Prefix commands still work (e.g. `!help`). Slash commands are recommended.

### Ticket
- `/ticketpanel` or `!ticketpanel` – Create ticket panel
- **Skill Role Application**: When a skill ticket is created, user clicks "Start Application" button → fills out form → staff reviews → `/approve` assigns role

### Moderation
- `/ban`, `/kick`, `/mute`, `/unmute`, `/warn`, `/warnings`, `/clearwarnings` (or `!ban`, etc.)

### Marketplace
- **Use in #cmds:** `/hiring` → opens form → posts in **#hiring-posts**, `/hirable` → opens form → posts in **#hirable-posts**
- Forms make it easy - just fill in the fields (Title, Description, Budget, etc.)
- You can also use `/hiring` directly in **#hiring-posts** or `/hirable` in **#hirable-posts**
- `/marketplaceformat` or `!marketplaceformat` – Show post formats

### Security (Staff/Admin/Moderator only)
- `/verificationpanel`, `/lockdown`, `/unlock`, `/checkuser` (or `!...`)
- **Role-restricted:** Only users with staff, admin, or moderator roles (configured in config.json) can use these commands

### Utility
- `/help` or `!help` – Show help
- `/approve` or `!approve` – Approve skill role application

## Project Structure

```
hiddentalentsbot/
├── bot.py                 # Main bot file
├── config.json            # Configuration file
├── requirements.txt       # Python dependencies
├── tuto.md               # Detailed setup tutorial
├── README.md             # This file
├── .gitignore            # Git ignore file
└── cogs/                 # Bot cogs/modules
    ├── tickets.py        # Ticket system
    ├── marketplace.py    # Marketplace system
    ├── moderation.py     # Moderation commands
    └── security.py       # Security features
```

## Hosting

See `tuto.md` for detailed hosting instructions including:
- Free hosting options (Replit, Railway, Render)
- VPS setup (Oracle Cloud, AWS, GCP)
- Local hosting setup

## Requirements

- Python 3.8+
- discord.py 2.3.0+
- A Discord bot token

## License

This project is open source and available for modification.

## Support

For issues or questions, check the code comments or refer to:
- [discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord Developer Portal](https://discord.com/developers/docs)

