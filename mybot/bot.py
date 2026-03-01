"""
Main Discord Bot File
Handles bot initialization and core functionality.
Uses slash commands (app_commands) for easier use.
"""

import discord
from discord import app_commands
from discord.ext import commands
import json
import asyncio
import os
from datetime import datetime, timedelta

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

# Bot setup with intents (required for slash commands and member events)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=config['prefix'], intents=intents, help_command=None)

# Store active tickets and user data
active_tickets = {}
user_ticket_count = {}
join_times = []
spam_tracker = {}


@bot.event
async def on_ready():
    """Called when bot is ready. Syncs slash commands to Discord."""
    print(f'{bot.user} has logged in!')
    print(f'Bot is in {len(bot.guilds)} guild(s)')
    
    # Load cogs
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'Loaded cog: {filename}')
    
    # Sync slash commands (guild-specific for instant update; use None for global)
    guild_id = config.get('guild_id') or None
    if guild_id:
        guild = discord.Object(id=guild_id)
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        print('Slash commands synced to guild.')
    else:
        await bot.tree.sync()
        print('Slash commands synced globally.')
    
    # Set bot status
    await bot.change_presence(activity=discord.Game(name="Managing Server"))


@bot.event
async def on_member_join(member: discord.Member):
    """Handle member joins: welcome message, auto-role, anti-raid detection"""
    current_time = datetime.now()
    join_times.append(current_time)
    
    # Clean old join times (older than timeframe)
    timeframe = config['security_settings']['join_spam_timeframe']
    join_times[:] = [t for t in join_times if (current_time - t).seconds <= timeframe]
    
    # Check for join spam
    threshold = config['security_settings']['join_spam_threshold']
    if len(join_times) >= threshold and config['security_settings']['auto_lock_enabled']:
        guild = member.guild
        await handle_raid_detection(guild)
    
    # Welcome message and auto-role
    welcome_settings = config.get('welcome_settings', {})
    if welcome_settings.get('enabled', True):
        welcome_channel_id = config['channels'].get('welcome', 0)
        if welcome_channel_id:
            welcome_channel = bot.get_channel(welcome_channel_id)
            if welcome_channel:
                welcome_msg = welcome_settings.get(
                    'welcome_message',
                    'Welcome {member} to {server}! We\'re glad to have you here!'
                )
                formatted_msg = welcome_msg.replace('{member}', member.mention).replace('{server}', member.guild.name)
                
                embed = discord.Embed(
                    title="👋 Welcome!",
                    description=formatted_msg,
                    color=discord.Color.green(),
                    timestamp=current_time
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.add_field(name="Member Count", value=member.guild.member_count, inline=True)
                embed.set_footer(text=f"User ID: {member.id}")
                
                await welcome_channel.send(embed=embed)
        
        # Auto-role assignment
        auto_role_id = welcome_settings.get('auto_role', 0)
        if auto_role_id:
            auto_role = member.guild.get_role(auto_role_id)
            if auto_role:
                try:
                    await member.add_roles(auto_role, reason="Auto-role on join")
                except Exception as e:
                    print(f"Error assigning auto-role: {e}")
    
    # Check account age
    min_age = config['security_settings']['min_account_age_days']
    account_age = (current_time - member.created_at).days
    
    if account_age < min_age:
        # Send to verification channel or apply verification role
        verification_channel_id = config['channels']['verification']
        if verification_channel_id:
            channel = bot.get_channel(verification_channel_id)
            if channel:
                await channel.send(
                    f"{member.mention}, your account is too new. "
                    f"Please wait {min_age - account_age} more day(s) or contact staff."
                )


async def handle_raid_detection(guild: discord.Guild):
    """Handle raid detection by locking the server"""
    mod_logs_id = config['channels']['mod_logs']
    if mod_logs_id:
        log_channel = bot.get_channel(mod_logs_id)
        if log_channel:
            await log_channel.send(
                f"⚠️ **RAID DETECTED**\n"
                f"Multiple joins detected in short timeframe. "
                f"Consider enabling verification or locking the server."
            )


@bot.event
async def on_message(message: discord.Message):
    """Handle messages for anti-spam"""
    if message.author.bot:
        return
    
    # Anti-spam check
    user_id = message.author.id
    current_time = datetime.now()
    
    if user_id not in spam_tracker:
        spam_tracker[user_id] = []
    
    spam_tracker[user_id].append(current_time)
    
    # Clean old messages
    timeframe = config['anti_spam_settings']['timeframe_seconds']
    spam_tracker[user_id] = [
        t for t in spam_tracker[user_id] 
        if (current_time - t).seconds <= timeframe
    ]
    
    # Check spam threshold
    max_messages = config['anti_spam_settings']['max_messages']
    if len(spam_tracker[user_id]) > max_messages:
        # Mute user
        mute_role = discord.utils.get(message.guild.roles, name="Muted")
        if not mute_role:
            # Create mute role if it doesn't exist
            mute_role = await message.guild.create_role(
                name="Muted",
                reason="Auto-created for spam protection"
            )
            # Apply to all channels
            for channel in message.guild.channels:
                try:
                    await channel.set_permissions(mute_role, send_messages=False)
                except:
                    pass
        
        duration = config['anti_spam_settings']['mute_duration_minutes']
        await message.author.add_roles(mute_role, reason="Spam detected")
        
        # Log action
        mod_logs_id = config['channels']['mod_logs']
        if mod_logs_id:
            log_channel = bot.get_channel(mod_logs_id)
            if log_channel:
                await log_channel.send(
                    f"🔇 **Auto-Mute**\n"
                    f"User: {message.author.mention} ({message.author.id})\n"
                    f"Reason: Spam detected ({len(spam_tracker[user_id])} messages in {timeframe}s)\n"
                    f"Duration: {duration} minutes"
                )
        
        # Clear spam tracker
        spam_tracker[user_id] = []
        
        await message.channel.send(
            f"{message.author.mention}, you have been muted for {duration} minutes due to spam."
        )
        return
    
    # Process commands
    await bot.process_commands(message)


@bot.command(name='help')
async def help_command(ctx):
    """Display help message (prefix command)."""
    await send_help_embed(ctx.send)

@bot.tree.command(name='help', description='List all bot commands and how to use them')
async def help_slash(interaction: discord.Interaction):
    """Slash command: display help message."""
    await send_help_embed(interaction.response.send_message, ephemeral=True)

async def send_help_embed(send_fn, **kwargs):
    """Shared help embed for prefix and slash help."""
    embed = discord.Embed(
        title="Bot Commands",
        description="Use **slash commands** by typing `/` in the chat. Available commands:",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="Ticket System",
        value="`/ticketpanel` – Create the ticket button panel",
        inline=False
    )
    embed.add_field(
        name="Marketplace (use in #cmds)",
        value="`/hiring` – Post a hiring ad (appears in marketplace)\n"
              "`/hirable` – Post a hirable ad (appears in marketplace)\n"
              "`/marketplaceformat` – Show required post formats",
        inline=False
    )
    embed.add_field(
        name="Moderation",
        value="`/ban` – Ban a user\n`/kick` – Kick a user\n"
              "`/mute` – Mute a user\n`/unmute` – Unmute a user\n"
              "`/warn` – Warn a user\n`/warnings` – View warnings\n"
              "`/clearwarnings` – Clear a user's warnings",
        inline=False
    )
    embed.add_field(
        name="Security",
        value="`/verificationpanel` – Verification button\n"
              "`/lockdown` – Lock server\n`/unlock` – Unlock server\n"
              "`/checkuser` – Check account age",
        inline=False
    )
    embed.add_field(
        name="Staff",
        value="`/approve` – Approve skill role application",
        inline=False
    )
    await send_fn(embed=embed, **kwargs)


# Run the bot
if __name__ == '__main__':
    # Check for environment variable first (for hosting), then config file
    import os
    token = os.getenv('BOT_TOKEN') or config.get('bot_token', '')
    
    if not token or token == "YOUR_BOT_TOKEN_HERE":
        print("ERROR: Please set your bot token in config.json or BOT_TOKEN environment variable")
    else:
        bot.run(token)
