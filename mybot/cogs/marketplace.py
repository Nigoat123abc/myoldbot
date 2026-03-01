"""
Marketplace System Cog
Handles hiring and hirable posts with format enforcement.
Uses modals (forms) for easy input - no manual formatting needed!
"""

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput
import json
from datetime import datetime

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

# Track user cooldowns
user_cooldowns = {}


class HiringModal(Modal, title='💼 Create Hiring Post'):
    """Modal form for hiring posts."""
    
    title_input = TextInput(
        label='Project Title',
        placeholder='e.g., Website Developer Needed',
        required=True,
        max_length=100
    )
    
    description_input = TextInput(
        label='Description',
        placeholder='Describe what you need in detail...',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )
    
    budget_input = TextInput(
        label='Budget',
        placeholder='e.g., $500-$1000 or Negotiable',
        required=True,
        max_length=100
    )
    
    requirements_input = TextInput(
        label='Requirements',
        placeholder='List specific skills, experience level, etc.',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )
    
    contact_input = TextInput(
        label='Contact Information',
        placeholder='How to contact you (Discord, email, etc.)',
        required=True,
        max_length=200
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        # Get the cog instance
        cog = interaction.client.get_cog('Marketplace')
        if not cog:
            await interaction.response.send_message("Error: Marketplace cog not found.", ephemeral=True)
            return
        
        # Format the post content
        formatted_content = (
            f"**Title:** {self.title_input.value}\n\n"
            f"**Description:** {self.description_input.value}\n\n"
            f"**Budget:** {self.budget_input.value}\n\n"
            f"**Requirements:** {self.requirements_input.value}\n\n"
            f"**Contact:** {self.contact_input.value}"
        )
        
        # Use the existing posting logic
        await interaction.response.defer(ephemeral=True)
        async def reply(content, ephemeral=False):
            await interaction.followup.send(content, ephemeral=True)
        
        await cog._do_hiring(
            interaction.user,
            formatted_content,
            reply,
            interaction.channel_id,
            is_slash=True
        )


class HirableModal(Modal, title='👤 Create Hirable Post'):
    """Modal form for hirable posts."""
    
    title_input = TextInput(
        label='Your Title/Name',
        placeholder='e.g., Professional Web Developer',
        required=True,
        max_length=100
    )
    
    skills_input = TextInput(
        label='Skills',
        placeholder='List your skills and expertise...',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )
    
    experience_input = TextInput(
        label='Experience',
        placeholder='Describe your experience level and years of experience',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )
    
    portfolio_input = TextInput(
        label='Portfolio/Examples',
        placeholder='Links to your work, GitHub, portfolio site, etc.',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )
    
    contact_input = TextInput(
        label='Contact Information',
        placeholder='How to contact you (Discord, email, etc.)',
        required=True,
        max_length=200
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        # Get the cog instance
        cog = interaction.client.get_cog('Marketplace')
        if not cog:
            await interaction.response.send_message("Error: Marketplace cog not found.", ephemeral=True)
            return
        
        # Format the post content
        formatted_content = (
            f"**Title:** {self.title_input.value}\n\n"
            f"**Skills:** {self.skills_input.value}\n\n"
            f"**Experience:** {self.experience_input.value}\n\n"
            f"**Portfolio:** {self.portfolio_input.value}\n\n"
            f"**Contact:** {self.contact_input.value}"
        )
        
        # Use the existing posting logic
        await interaction.response.defer(ephemeral=True)
        async def reply(content, ephemeral=False):
            await interaction.followup.send(content, ephemeral=True)
        
        await cog._do_hirable(
            interaction.user,
            formatted_content,
            reply,
            interaction.channel_id,
            is_slash=True
        )


class Marketplace(commands.Cog):
    """Marketplace commands (slash and prefix)."""

    def __init__(self, bot):
        self.bot = bot

    def check_cooldown(self, user_id):
        """Check if user is on cooldown."""
        cooldown_seconds = config['marketplace_settings']['cooldown_seconds']
        if user_id in user_cooldowns:
            time_passed = (datetime.now() - user_cooldowns[user_id]).seconds
            if time_passed < cooldown_seconds:
                remaining = cooldown_seconds - time_passed
                return False, remaining
        return True, 0

    def _get_target_channel(self, channel_id, post_type):
        """
        Determine where to post based on current channel and post type.
        Returns (target_channel, is_from_cmds)
        post_type: 'hiring' or 'hirable'
        """
        cmds_id = config['channels'].get('cmds', 0)
        hiring_posts_id = config['channels'].get('hiring_posts', 0)
        hirable_posts_id = config['channels'].get('hirable_posts', 0)
        
        # If user is in cmds channel, post to the appropriate channel
        if cmds_id and channel_id == cmds_id:
            if post_type == 'hiring':
                target_id = hiring_posts_id
            else:  # hirable
                target_id = hirable_posts_id
            target_channel = self.bot.get_channel(target_id) if target_id else None
            return target_channel, True
        
        # If user is in hiring_posts channel and posting hiring
        if post_type == 'hiring' and channel_id == hiring_posts_id:
            return self.bot.get_channel(hiring_posts_id), False
        
        # If user is in hirable_posts channel and posting hirable
        if post_type == 'hirable' and channel_id == hirable_posts_id:
            return self.bot.get_channel(hirable_posts_id), False
        
        # Not in allowed channel
        return None, False

    def _allowed_channel(self, channel_id, post_type):
        """Check if command is allowed in this channel."""
        cmds_id = config['channels'].get('cmds', 0)
        hiring_posts_id = config['channels'].get('hiring_posts', 0)
        hirable_posts_id = config['channels'].get('hirable_posts', 0)
        
        # Can use in cmds channel
        if cmds_id and channel_id == cmds_id:
            return True
        
        # Can use in hiring_posts for hiring
        if post_type == 'hiring' and channel_id == hiring_posts_id:
            return True
        
        # Can use in hirable_posts for hirable
        if post_type == 'hirable' and channel_id == hirable_posts_id:
            return True
        
        return False

    async def _do_hiring(self, author, description, reply_fn, channel_id, is_slash=False):
        """Shared logic for hiring post (slash or prefix)."""
        # Check if allowed in this channel
        if not self._allowed_channel(channel_id, 'hiring'):
            cmds_id = config['channels'].get('cmds', 0)
            hiring_posts_id = config['channels'].get('hiring_posts', 0)
            cmds_mention = f"<#{cmds_id}>" if cmds_id else "#cmds"
            hiring_mention = f"<#{hiring_posts_id}>" if hiring_posts_id else "#hiring-posts"
            await reply_fn(
                f"Use `/hiring` in {cmds_mention} or {hiring_mention}.",
                ephemeral=is_slash
            )
            return

        # Get target channel (where to post)
        target_channel, is_from_cmds = self._get_target_channel(channel_id, 'hiring')
        
        if not target_channel:
            await reply_fn("Hiring posts channel is not configured.", ephemeral=is_slash)
            return

        can_post, remaining = self.check_cooldown(author.id)
        if not can_post:
            minutes = remaining // 60
            await reply_fn(f"You're on cooldown. Wait {minutes} more minute(s).", ephemeral=is_slash)
            return

        embed = discord.Embed(
            title="💼 Hiring Post",
            description=description,
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.set_author(name=author.display_name, icon_url=author.display_avatar.url)
        embed.set_footer(text=f"Posted by {author.name}")

        # Post to target channel
        msg = await target_channel.send(embed=embed)
        user_cooldowns[author.id] = datetime.now()

        if is_from_cmds:
            await reply_fn(f"✅ Your hiring post was created in {target_channel.mention}: {msg.jump_url}", ephemeral=is_slash)
        else:
            await reply_fn(f"✅ Your hiring post has been created! {msg.jump_url}", ephemeral=is_slash)

    async def _do_hirable(self, author, description, reply_fn, channel_id, is_slash=False):
        """Shared logic for hirable post (slash or prefix)."""
        # Check if allowed in this channel
        if not self._allowed_channel(channel_id, 'hirable'):
            cmds_id = config['channels'].get('cmds', 0)
            hirable_posts_id = config['channels'].get('hirable_posts', 0)
            cmds_mention = f"<#{cmds_id}>" if cmds_id else "#cmds"
            hirable_mention = f"<#{hirable_posts_id}>" if hirable_posts_id else "#hirable-posts"
            await reply_fn(
                f"Use `/hirable` in {cmds_mention} or {hirable_mention}.",
                ephemeral=is_slash
            )
            return

        # Get target channel (where to post)
        target_channel, is_from_cmds = self._get_target_channel(channel_id, 'hirable')
        
        if not target_channel:
            await reply_fn("Hirable posts channel is not configured.", ephemeral=is_slash)
            return

        can_post, remaining = self.check_cooldown(author.id)
        if not can_post:
            minutes = remaining // 60
            await reply_fn(f"You're on cooldown. Wait {minutes} more minute(s).", ephemeral=is_slash)
            return

        embed = discord.Embed(
            title="👤 Available for Hire",
            description=description,
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_author(name=author.display_name, icon_url=author.display_avatar.url)
        embed.set_footer(text=f"Posted by {author.name}")

        # Post to target channel
        msg = await target_channel.send(embed=embed)
        user_cooldowns[author.id] = datetime.now()

        if is_from_cmds:
            await reply_fn(f"✅ Your hirable post was created in {target_channel.mention}: {msg.jump_url}", ephemeral=is_slash)
        else:
            await reply_fn(f"✅ Your hirable post has been created! {msg.jump_url}", ephemeral=is_slash)

    # ---------- Slash commands ----------
    @app_commands.command(name='hiring', description='Create a hiring post (opens a form)')
    async def hiring_slash(self, interaction: discord.Interaction):
        """Open hiring post modal form."""
        # Check if allowed in this channel
        if not self._allowed_channel(interaction.channel_id, 'hiring'):
            cmds_id = config['channels'].get('cmds', 0)
            hiring_posts_id = config['channels'].get('hiring_posts', 0)
            cmds_mention = f"<#{cmds_id}>" if cmds_id else "#cmds"
            hiring_mention = f"<#{hiring_posts_id}>" if hiring_posts_id else "#hiring-posts"
            await interaction.response.send_message(
                f"Use `/hiring` in {cmds_mention} or {hiring_mention}.",
                ephemeral=True
            )
            return
        
        # Check cooldown
        can_post, remaining = self.check_cooldown(interaction.user.id)
        if not can_post:
            minutes = remaining // 60
            await interaction.response.send_message(
                f"You're on cooldown. Wait {minutes} more minute(s).",
                ephemeral=True
            )
            return
        
        # Show the modal
        modal = HiringModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(name='hirable', description='Create a hirable post (opens a form)')
    async def hirable_slash(self, interaction: discord.Interaction):
        """Open hirable post modal form."""
        # Check if allowed in this channel
        if not self._allowed_channel(interaction.channel_id, 'hirable'):
            cmds_id = config['channels'].get('cmds', 0)
            hirable_posts_id = config['channels'].get('hirable_posts', 0)
            cmds_mention = f"<#{cmds_id}>" if cmds_id else "#cmds"
            hirable_mention = f"<#{hirable_posts_id}>" if hirable_posts_id else "#hirable-posts"
            await interaction.response.send_message(
                f"Use `/hirable` in {cmds_mention} or {hirable_mention}.",
                ephemeral=True
            )
            return
        
        # Check cooldown
        can_post, remaining = self.check_cooldown(interaction.user.id)
        if not can_post:
            minutes = remaining // 60
            await interaction.response.send_message(
                f"You're on cooldown. Wait {minutes} more minute(s).",
                ephemeral=True
            )
            return
        
        # Show the modal
        modal = HirableModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(name='marketplaceformat', description='Show required format for hiring and hirable posts')
    async def marketplace_format_slash(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📋 Marketplace Post Formats",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="💼 Hiring Post",
            value="Use `/hiring` to open a form with fields for:\n"
                  "• Title\n• Description\n• Budget\n• Requirements\n• Contact",
            inline=False
        )
        embed.add_field(
            name="👤 Hirable Post",
            value="Use `/hirable` to open a form with fields for:\n"
                  "• Title/Name\n• Skills\n• Experience\n• Portfolio\n• Contact",
            inline=False
        )
        cmds_id = config['channels'].get('cmds', 0)
        hiring_posts_id = config['channels'].get('hiring_posts', 0)
        hirable_posts_id = config['channels'].get('hirable_posts', 0)
        cmds_mention = f"<#{cmds_id}>" if cmds_id else "#cmds"
        hiring_mention = f"<#{hiring_posts_id}>" if hiring_posts_id else "#hiring-posts"
        hirable_mention = f"<#{hirable_posts_id}>" if hirable_posts_id else "#hirable-posts"
        embed.add_field(
            name="Where to post",
            value=f"Use `/hiring` or `/hirable` in {cmds_mention}.\n"
                  f"Posts will appear in {hiring_mention} or {hirable_mention} respectively.",
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ---------- Prefix commands (kept for backward compatibility) ----------
    @commands.command(name='hiring')
    async def hiring_post(self, ctx, *, description: str = None):
        """Post a hiring advertisement (use in #cmds or #hiring-posts)."""
        if not description:
            await ctx.send(
                "**Hiring Post Format:**\n"
                "Title, Description, Budget, Requirements, Contact.\n"
                "Or use `/hiring` for an easier form!"
            )
            return
        
        async def reply(content, ephemeral=False):
            await ctx.send(content, delete_after=10 if "cooldown" in content or "format" in content or "Use" in content else 5)
        try:
            await self._do_hiring(ctx.author, description, reply, ctx.channel.id, is_slash=False)
            cmds_id = config['channels'].get('cmds', 0)
            if ctx.message and ctx.channel.id != cmds_id:
                try:
                    await ctx.message.delete()
                except Exception:
                    pass
        except Exception as e:
            await ctx.send(str(e))

    @commands.command(name='hirable')
    async def hirable_post(self, ctx, *, description: str = None):
        """Post a hirable advertisement (use in #cmds or #hirable-posts)."""
        if not description:
            await ctx.send(
                "**Hirable Post Format:**\n"
                "Title, Skills, Experience, Portfolio, Contact.\n"
                "Or use `/hirable` for an easier form!"
            )
            return
        
        async def reply(content, ephemeral=False):
            await ctx.send(content, delete_after=10 if "cooldown" in content or "format" in content or "Use" in content else 5)
        try:
            await self._do_hirable(ctx.author, description, reply, ctx.channel.id, is_slash=False)
            cmds_id = config['channels'].get('cmds', 0)
            if ctx.message and ctx.channel.id != cmds_id:
                try:
                    await ctx.message.delete()
                except Exception:
                    pass
        except Exception as e:
            await ctx.send(str(e))

    @commands.command(name='marketplaceformat')
    async def marketplace_format(self, ctx):
        """Show marketplace post formats."""
        embed = discord.Embed(
            title="📋 Marketplace Post Formats",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="💼 Hiring Post",
            value="Use `/hiring` for an easy form, or include:\n"
                  "Title, Description, Budget, Requirements, Contact",
            inline=False
        )
        embed.add_field(
            name="👤 Hirable Post",
            value="Use `/hirable` for an easy form, or include:\n"
                  "Title, Skills, Experience, Portfolio, Contact",
            inline=False
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Marketplace(bot))
