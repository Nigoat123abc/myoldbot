"""
Moderation Cog
Handles ban, kick, mute, warn commands and message logging
"""

import discord
from discord import app_commands
from discord.ext import commands
import json
import asyncio
from datetime import datetime, timedelta

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

# Store warnings
warnings = {}


class Moderation(commands.Cog):
    """Moderation commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def has_mod_perms(self, member: discord.Member):
        """Check if member has moderation permissions"""
        staff_role_id = config['roles'].get('staff', 0)
        mod_role_id = config['roles'].get('moderator', 0)
        admin_role_id = config['roles'].get('admin', 0)
        
        if member.guild_permissions.administrator:
            return True
        
        if staff_role_id and member.get_role(staff_role_id):
            return True
        if mod_role_id and member.get_role(mod_role_id):
            return True
        if admin_role_id and member.get_role(admin_role_id):
            return True
        
        return False
    
    async def log_action(self, action: str, moderator: discord.Member, 
                        target: discord.Member, reason: str = None):
        """Log moderation action"""
        log_channel_id = config['channels']['mod_logs']
        if not log_channel_id:
            return
        
        log_channel = self.bot.get_channel(log_channel_id)
        if not log_channel:
            return
        
        embed = discord.Embed(
            title=f"Moderation Action: {action}",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Moderator", value=f"{moderator.mention} ({moderator.id})", inline=False)
        embed.add_field(name="Target", value=f"{target.mention} ({target.id})", inline=False)
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
        
        await log_channel.send(embed=embed)
    
    @app_commands.command(name='ban', description='Ban a user from the server')
    @app_commands.describe(member='User to ban', reason='Reason for the ban')
    @app_commands.default_permissions(ban_members=True)
    async def ban_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if member.id == interaction.user.id:
            await interaction.response.send_message("You cannot ban yourself.", ephemeral=True)
            return
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("You cannot ban someone with equal or higher roles.", ephemeral=True)
            return
        try:
            await member.ban(reason=f"{reason} | Banned by {interaction.user}")
            await interaction.response.send_message(f"✅ {member.mention} has been banned. Reason: {reason}")
            await self.log_action("Ban", interaction.user, member, reason)
        except Exception as e:
            await interaction.response.send_message(f"Error banning user: {e}", ephemeral=True)

    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban_user(self, ctx, member: discord.Member = None, *, reason: str = "No reason provided"):
        """Ban a user from the server"""
        if not member:
            await ctx.send("Usage: `!ban @user [reason]`")
            return
        
        if member.id == ctx.author.id:
            await ctx.send("You cannot ban yourself.")
            return
        
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send("You cannot ban someone with equal or higher roles.")
            return
        
        try:
            await member.ban(reason=f"{reason} | Banned by {ctx.author}")
            await ctx.send(f"✅ {member.mention} has been banned. Reason: {reason}")
            await self.log_action("Ban", ctx.author, member, reason)
        except Exception as e:
            await ctx.send(f"Error banning user: {e}")
    
    @app_commands.command(name='kick', description='Kick a user from the server')
    @app_commands.describe(member='User to kick', reason='Reason for the kick')
    @app_commands.default_permissions(kick_members=True)
    async def kick_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if member.id == interaction.user.id:
            await interaction.response.send_message("You cannot kick yourself.", ephemeral=True)
            return
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("You cannot kick someone with equal or higher roles.", ephemeral=True)
            return
        try:
            await member.kick(reason=f"{reason} | Kicked by {interaction.user}")
            await interaction.response.send_message(f"✅ {member.mention} has been kicked. Reason: {reason}")
            await self.log_action("Kick", interaction.user, member, reason)
        except Exception as e:
            await interaction.response.send_message(f"Error kicking user: {e}", ephemeral=True)

    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick_user(self, ctx, member: discord.Member = None, *, reason: str = "No reason provided"):
        """Kick a user from the server"""
        if not member:
            await ctx.send("Usage: `!kick @user [reason]`")
            return
        
        if member.id == ctx.author.id:
            await ctx.send("You cannot kick yourself.")
            return
        
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send("You cannot kick someone with equal or higher roles.")
            return
        
        try:
            await member.kick(reason=f"{reason} | Kicked by {ctx.author}")
            await ctx.send(f"✅ {member.mention} has been kicked. Reason: {reason}")
            await self.log_action("Kick", ctx.author, member, reason)
        except Exception as e:
            await ctx.send(f"Error kicking user: {e}")
    
    @app_commands.command(name='mute', description='Mute a user for a number of minutes')
    @app_commands.describe(member='User to mute', duration_minutes='Duration in minutes', reason='Reason for mute')
    @app_commands.default_permissions(manage_roles=True)
    async def mute_slash(self, interaction: discord.Interaction, member: discord.Member,
                        duration_minutes: int = 10, reason: str = "No reason provided"):
        if member.id == interaction.user.id:
            await interaction.response.send_message("You cannot mute yourself.", ephemeral=True)
            return
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("You cannot mute someone with equal or higher roles.", ephemeral=True)
            return
        mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
        if not mute_role:
            mute_role = await interaction.guild.create_role(name="Muted", reason="Auto-created for mute system")
            for ch in interaction.guild.channels:
                try:
                    await ch.set_permissions(mute_role, send_messages=False, speak=False)
                except Exception:
                    pass
        try:
            await member.add_roles(mute_role, reason=f"{reason} | Muted by {interaction.user}")
            await interaction.response.send_message(
                f"✅ {member.mention} has been muted for {duration_minutes} minute(s). Reason: {reason}"
            )
            await self.log_action("Mute", interaction.user, member, f"{reason} | Duration: {duration_minutes} minutes")
            await asyncio.sleep(duration_minutes * 60)
            if mute_role in member.roles:
                await member.remove_roles(mute_role, reason="Mute duration expired")
        except Exception as e:
            await interaction.response.send_message(f"Error muting user: {e}", ephemeral=True)

    @commands.command(name='mute')
    @commands.has_permissions(manage_roles=True)
    async def mute_user(self, ctx, member: discord.Member = None, 
                       duration: str = "10", *, reason: str = "No reason provided"):
        """Mute a user for specified duration (in minutes)"""
        if not member:
            await ctx.send("Usage: `!mute @user <duration_minutes> [reason]`")
            return
        
        if member.id == ctx.author.id:
            await ctx.send("You cannot mute yourself.")
            return
        
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send("You cannot mute someone with equal or higher roles.")
            return
        
        try:
            duration_minutes = int(duration)
        except ValueError:
            await ctx.send("Duration must be a number (minutes).")
            return
        
        # Get or create mute role
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not mute_role:
            mute_role = await ctx.guild.create_role(
                name="Muted",
                reason="Auto-created for mute system"
            )
            # Apply to all channels
            for channel in ctx.guild.channels:
                try:
                    await channel.set_permissions(mute_role, send_messages=False, speak=False)
                except:
                    pass
        
        try:
            await member.add_roles(mute_role, reason=f"{reason} | Muted by {ctx.author}")
            await ctx.send(
                f"✅ {member.mention} has been muted for {duration_minutes} minute(s). "
                f"Reason: {reason}"
            )
            await self.log_action("Mute", ctx.author, member, f"{reason} | Duration: {duration_minutes} minutes")
            
            # Auto-unmute after duration
            await asyncio.sleep(duration_minutes * 60)
            if mute_role in member.roles:
                await member.remove_roles(mute_role, reason="Mute duration expired")
        except Exception as e:
            await ctx.send(f"Error muting user: {e}")
    
    @app_commands.command(name='unmute', description='Remove mute from a user')
    @app_commands.describe(member='User to unmute')
    @app_commands.default_permissions(manage_roles=True)
    async def unmute_slash(self, interaction: discord.Interaction, member: discord.Member):
        mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
        if not mute_role:
            await interaction.response.send_message("Mute role not found.", ephemeral=True)
            return
        if mute_role not in member.roles:
            await interaction.response.send_message(f"{member.mention} is not muted.", ephemeral=True)
            return
        try:
            await member.remove_roles(mute_role, reason=f"Unmuted by {interaction.user}")
            await interaction.response.send_message(f"✅ {member.mention} has been unmuted.")
            await self.log_action("Unmute", interaction.user, member)
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

    @commands.command(name='unmute')
    @commands.has_permissions(manage_roles=True)
    async def unmute_user(self, ctx, member: discord.Member = None):
        """Unmute a user"""
        if not member:
            await ctx.send("Usage: `!unmute @user`")
            return
        
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not mute_role:
            await ctx.send("Mute role not found.")
            return
        
        if mute_role not in member.roles:
            await ctx.send(f"{member.mention} is not muted.")
            return
        
        try:
            await member.remove_roles(mute_role, reason=f"Unmuted by {ctx.author}")
            await ctx.send(f"✅ {member.mention} has been unmuted.")
            await self.log_action("Unmute", ctx.author, member)
        except Exception as e:
            await ctx.send(f"Error unmuting user: {e}")
    
    @app_commands.command(name='warn', description='Warn a user')
    @app_commands.describe(member='User to warn', reason='Reason for the warning')
    @app_commands.default_permissions(moderate_members=True)
    async def warn_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if member.id == interaction.user.id:
            await interaction.response.send_message("You cannot warn yourself.", ephemeral=True)
            return
        user_id = str(member.id)
        if user_id not in warnings:
            warnings[user_id] = []
        warnings[user_id].append({
            'moderator': str(interaction.user.id),
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
        count = len(warnings[user_id])
        await interaction.response.send_message(
            f"⚠️ {member.mention} has been warned. Total warnings: {count}\nReason: {reason}"
        )
        await self.log_action("Warn", interaction.user, member, reason)
        try:
            await member.send(f"You have been warned in {interaction.guild.name}\nReason: {reason}\nTotal warnings: {count}")
        except Exception:
            pass

    @commands.command(name='warn')
    @commands.has_permissions(manage_messages=True)
    async def warn_user(self, ctx, member: discord.Member = None, *, reason: str = "No reason provided"):
        """Warn a user"""
        if not member:
            await ctx.send("Usage: `!warn @user [reason]`")
            return
        
        if member.id == ctx.author.id:
            await ctx.send("You cannot warn yourself.")
            return
        
        # Store warning
        user_id = str(member.id)
        if user_id not in warnings:
            warnings[user_id] = []
        
        warnings[user_id].append({
            'moderator': str(ctx.author.id),
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
        
        warning_count = len(warnings[user_id])
        
        await ctx.send(
            f"⚠️ {member.mention} has been warned. "
            f"Total warnings: {warning_count}\n"
            f"Reason: {reason}"
        )
        await self.log_action("Warn", ctx.author, member, reason)
        
        # DM user
        try:
            await member.send(
                f"You have been warned in {ctx.guild.name}\n"
                f"Reason: {reason}\n"
                f"Total warnings: {warning_count}"
            )
        except:
            pass
    
    @app_commands.command(name='warnings', description='View warnings for a user')
    @app_commands.describe(member='User to check (leave empty for yourself)')
    async def warnings_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        if not member:
            member = interaction.user
        user_id = str(member.id)
        user_warnings = warnings.get(user_id, [])
        if not user_warnings:
            await interaction.response.send_message(f"{member.mention} has no warnings.", ephemeral=True)
            return
        embed = discord.Embed(
            title=f"Warnings for {member.display_name}",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        for i, w in enumerate(user_warnings, 1):
            mod = self.bot.get_user(int(w['moderator']))
            mod_name = mod.name if mod else "Unknown"
            ts = datetime.fromisoformat(w['timestamp']).strftime("%Y-%m-%d %H:%M")
            embed.add_field(name=f"Warning #{i}", value=f"**Moderator:** {mod_name}\n**Reason:** {w['reason']}\n**Date:** {ts}", inline=False)
        embed.set_footer(text=f"Total: {len(user_warnings)}")
        await interaction.response.send_message(embed=embed)

    @commands.command(name='warnings')
    async def view_warnings(self, ctx, member: discord.Member = None):
        """View warnings for a user"""
        if not member:
            member = ctx.author
        
        user_id = str(member.id)
        user_warnings = warnings.get(user_id, [])
        
        if not user_warnings:
            await ctx.send(f"{member.mention} has no warnings.")
            return
        
        embed = discord.Embed(
            title=f"Warnings for {member.display_name}",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        
        for i, warning in enumerate(user_warnings, 1):
            moderator = self.bot.get_user(int(warning['moderator']))
            mod_name = moderator.name if moderator else "Unknown"
            timestamp = datetime.fromisoformat(warning['timestamp']).strftime("%Y-%m-%d %H:%M")
            
            embed.add_field(
                name=f"Warning #{i}",
                value=f"**Moderator:** {mod_name}\n"
                      f"**Reason:** {warning['reason']}\n"
                      f"**Date:** {timestamp}",
                inline=False
            )
        
        embed.set_footer(text=f"Total warnings: {len(user_warnings)}")
        await ctx.send(embed=embed)
    
    @app_commands.command(name='clearwarnings', description="Clear all warnings for a user")
    @app_commands.describe(member='User to clear warnings for')
    @app_commands.default_permissions(moderate_members=True)
    async def clearwarnings_slash(self, interaction: discord.Interaction, member: discord.Member):
        user_id = str(member.id)
        if user_id in warnings:
            count = len(warnings[user_id])
            del warnings[user_id]
            await interaction.response.send_message(f"✅ Cleared {count} warning(s) for {member.mention}")
            await self.log_action("Clear Warnings", interaction.user, member)
        else:
            await interaction.response.send_message(f"{member.mention} has no warnings to clear.", ephemeral=True)

    @commands.command(name='clearwarnings')
    @commands.has_permissions(manage_messages=True)
    async def clear_warnings(self, ctx, member: discord.Member = None):
        """Clear all warnings for a user"""
        if not member:
            await ctx.send("Usage: `!clearwarnings @user`")
            return
        
        user_id = str(member.id)
        if user_id in warnings:
            count = len(warnings[user_id])
            del warnings[user_id]
            await ctx.send(f"✅ Cleared {count} warning(s) for {member.mention}")
            await self.log_action("Clear Warnings", ctx.author, member)
        else:
            await ctx.send(f"{member.mention} has no warnings to clear.")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
