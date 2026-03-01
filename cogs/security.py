"""
Security Cog
Additional security features and anti-raid protection
"""

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import json
from datetime import datetime, timedelta

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)


class VerificationView(View):
    """Verification button view"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Verify", style=discord.ButtonStyle.success, emoji="✅")
    async def verify_button(self, interaction: discord.Interaction, button: Button):
        member = interaction.user
        
        # Check account age
        min_age = config['security_settings']['min_account_age_days']
        account_age = (datetime.now() - member.created_at).days
        
        if account_age < min_age:
            await interaction.response.send_message(
                f"Your account is too new. Please wait {min_age - account_age} more day(s).",
                ephemeral=True
            )
            return
        
        # Assign verified role (you can customize this)
        verified_role = discord.utils.get(interaction.guild.roles, name="Verified")
        if verified_role:
            if verified_role not in member.roles:
                await member.add_roles(verified_role, reason="User verified")
                await interaction.response.send_message(
                    "✅ You have been verified!",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "You are already verified.",
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(
                "Verification role not found. Please contact an administrator.",
                ephemeral=True
            )


class Security(commands.Cog):
    """Security and anti-raid commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def has_security_perms(self, member: discord.Member):
        """Check if member has security permissions (staff/admin/moderator roles)."""
        # Check if user is server owner
        if member.guild.owner_id == member.id:
            return True
        
        # Check if user has administrator permission
        if member.guild_permissions.administrator:
            return True
        
        # Check configured roles
        staff_role_id = config['roles'].get('staff', 0)
        admin_role_id = config['roles'].get('admin', 0)
        moderator_role_id = config['roles'].get('moderator', 0)
        
        if staff_role_id and member.get_role(staff_role_id):
            return True
        if admin_role_id and member.get_role(admin_role_id):
            return True
        if moderator_role_id and member.get_role(moderator_role_id):
            return True
        
        return False
    
    @app_commands.command(name='verificationpanel', description='Create the verification panel with Verify button')
    @app_commands.default_permissions(manage_guild=True)
    async def verification_panel_slash(self, interaction: discord.Interaction):
        # Check role permissions
        if not self.has_security_perms(interaction.user):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command. Only staff, admin, or moderator roles can use security commands.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🔐 Server Verification",
            description="Click the button below to verify yourself!\n\n"
                       "**Requirements:**\n"
                       f"- Account must be at least {config['security_settings']['min_account_age_days']} day(s) old",
            color=discord.Color.green()
        )
        view = VerificationView()
        await interaction.response.send_message(embed=embed, view=view)

    @commands.command(name='verificationpanel')
    @commands.has_permissions(manage_guild=True)
    async def verification_panel(self, ctx):
        """Create verification panel."""
        # Check role permissions
        if not self.has_security_perms(ctx.author):
            await ctx.send("❌ You don't have permission to use this command. Only staff, admin, or moderator roles can use security commands.")
            return
        
        embed = discord.Embed(
            title="🔐 Server Verification",
            description="Click the button below to verify yourself!\n\n"
                       "**Requirements:**\n"
                       f"- Account must be at least {config['security_settings']['min_account_age_days']} day(s) old",
            color=discord.Color.green()
        )
        view = VerificationView()
        await ctx.send(embed=embed, view=view)

    @app_commands.command(name='lockdown', description='Lock the server (disable sending in all channels)')
    @app_commands.default_permissions(manage_channels=True)
    async def lockdown_slash(self, interaction: discord.Interaction):
        # Check role permissions
        if not self.has_security_perms(interaction.user):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command. Only staff, admin, or moderator roles can use security commands.",
                ephemeral=True
            )
            return
        
        guild = interaction.guild
        try:
            locked = 0
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    overwrite = channel.overwrites_for(guild.default_role)
                    overwrite.send_messages = False
                    await channel.set_permissions(guild.default_role, overwrite=overwrite)
                    locked += 1
            await interaction.response.send_message(
                f"🔒 Server locked down! {locked} channel(s) locked. Use `/unlock` to unlock."
            )
            log_channel_id = config['channels']['mod_logs']
            if log_channel_id:
                log_channel = self.bot.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(title="Server Lockdown", color=discord.Color.red(), timestamp=datetime.now())
                    embed.add_field(name="Locked by", value=interaction.user.mention, inline=False)
                    embed.add_field(name="Channels locked", value=locked, inline=False)
                    await log_channel.send(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

    @commands.command(name='lockdown')
    @commands.has_permissions(manage_channels=True)
    async def lockdown_server(self, ctx):
        """Lock down the server (disable sending messages for everyone)"""
        # Check role permissions
        if not self.has_security_perms(ctx.author):
            await ctx.send("❌ You don't have permission to use this command. Only staff, admin, or moderator roles can use security commands.")
            return
        
        guild = ctx.guild
        
        try:
            # Lock all channels
            locked_channels = 0
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    overwrite = channel.overwrites_for(guild.default_role)
                    overwrite.send_messages = False
                    await channel.set_permissions(guild.default_role, overwrite=overwrite)
                    locked_channels += 1
            
            await ctx.send(
                f"🔒 Server locked down! {locked_channels} channel(s) locked.\n"
                f"Use `{config['prefix']}unlock` to unlock."
            )
            
            # Log action
            log_channel_id = config['channels']['mod_logs']
            if log_channel_id:
                log_channel = self.bot.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(
                        title="Server Lockdown",
                        color=discord.Color.red(),
                        timestamp=datetime.now()
                    )
                    embed.add_field(name="Locked by", value=ctx.author.mention, inline=False)
                    embed.add_field(name="Channels locked", value=locked_channels, inline=False)
                    await log_channel.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error locking server: {e}")
    
    @app_commands.command(name='unlock', description='Unlock the server')
    @app_commands.default_permissions(manage_channels=True)
    async def unlock_slash(self, interaction: discord.Interaction):
        # Check role permissions
        if not self.has_security_perms(interaction.user):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command. Only staff, admin, or moderator roles can use security commands.",
                ephemeral=True
            )
            return
        
        guild = interaction.guild
        try:
            unlocked = 0
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    overwrite = channel.overwrites_for(guild.default_role)
                    overwrite.send_messages = None
                    await channel.set_permissions(guild.default_role, overwrite=overwrite)
                    unlocked += 1
            await interaction.response.send_message(f"🔓 Server unlocked! {unlocked} channel(s) unlocked.")
            log_channel_id = config['channels']['mod_logs']
            if log_channel_id:
                log_channel = self.bot.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(title="Server Unlocked", color=discord.Color.green(), timestamp=datetime.now())
                    embed.add_field(name="Unlocked by", value=interaction.user.mention, inline=False)
                    await log_channel.send(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

    @commands.command(name='unlock')
    @commands.has_permissions(manage_channels=True)
    async def unlock_server(self, ctx):
        """Unlock the server"""
        # Check role permissions
        if not self.has_security_perms(ctx.author):
            await ctx.send("❌ You don't have permission to use this command. Only staff, admin, or moderator roles can use security commands.")
            return
        
        guild = ctx.guild
        
        try:
            # Unlock all channels
            unlocked_channels = 0
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    overwrite = channel.overwrites_for(guild.default_role)
                    overwrite.send_messages = None  # Reset to default
                    await channel.set_permissions(guild.default_role, overwrite=overwrite)
                    unlocked_channels += 1
            
            await ctx.send(f"🔓 Server unlocked! {unlocked_channels} channel(s) unlocked.")
            
            # Log action
            log_channel_id = config['channels']['mod_logs']
            if log_channel_id:
                log_channel = self.bot.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(
                        title="Server Unlocked",
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    embed.add_field(name="Unlocked by", value=ctx.author.mention, inline=False)
                    await log_channel.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error unlocking server: {e}")
    
    @app_commands.command(name='checkuser', description='Check a user\'s account age and verification status')
    @app_commands.describe(member='User to check (leave empty for yourself)')
    async def checkuser_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        if not member:
            member = interaction.user
        account_age = (datetime.now() - member.created_at).days
        min_age = config['security_settings']['min_account_age_days']
        embed = discord.Embed(
            title=f"User Check: {member.display_name}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d"), inline=False)
        embed.add_field(name="Account Age", value=f"{account_age} day(s)", inline=False)
        embed.add_field(name="Minimum Required", value=f"{min_age} day(s)", inline=False)
        embed.add_field(name="Status", value="✅ Verified" if account_age >= min_age else "⚠️ Too New", inline=False)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "Unknown", inline=False)
        await interaction.response.send_message(embed=embed)

    @commands.command(name='checkuser')
    @commands.has_permissions(moderate_members=True)
    async def check_user(self, ctx, member: discord.Member = None):
        """Check user account age and status"""
        if not member:
            member = ctx.author
        
        account_age = (datetime.now() - member.created_at).days
        min_age = config['security_settings']['min_account_age_days']
        
        embed = discord.Embed(
            title=f"User Check: {member.display_name}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d"), inline=False)
        embed.add_field(name="Account Age", value=f"{account_age} day(s)", inline=False)
        embed.add_field(name="Minimum Required", value=f"{min_age} day(s)", inline=False)
        embed.add_field(name="Status", value="✅ Verified" if account_age >= min_age else "⚠️ Too New", inline=False)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "Unknown", inline=False)
        
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Security(bot))
