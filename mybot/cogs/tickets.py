"""
Ticket System Cog
Handles ticket creation, management, and closing
Skill role applications use a button that opens a modal form
"""

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import json
import asyncio
from datetime import datetime

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

# Store ticket data
ticket_data = {}
ticket_questions = {}
# Store skill role applications: {ticket_id: {user_id, skill, experience, portfolio, status, applied_at}}
skill_applications = {}


class SkillRoleApplicationModal(Modal, title='⭐ Skill Role Application'):
    """Modal form for skill role applications."""
    
    skill_input = TextInput(
        label='Skill/Role Name',
        placeholder='e.g., Web Developer, Graphic Designer, Python Developer',
        required=True,
        max_length=100
    )
    
    experience_input = TextInput(
        label='Experience Level',
        placeholder='Describe your experience, years of experience, projects worked on...',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )
    
    portfolio_input = TextInput(
        label='Portfolio/Examples',
        placeholder='Links to your work, GitHub, portfolio site, screenshots, etc.',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )
    
    def __init__(self, ticket_id: str):
        super().__init__()
        self.ticket_id = ticket_id
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        ticket = ticket_data.get(self.ticket_id)
        if not ticket or ticket['status'] != 'open':
            await interaction.response.send_message(
                "This ticket is no longer open.", ephemeral=True
            )
            return
        
        # Store application
        skill_applications[self.ticket_id] = {
            'user_id': str(interaction.user.id),
            'skill': self.skill_input.value,
            'experience': self.experience_input.value,
            'portfolio': self.portfolio_input.value,
            'status': 'pending',
            'applied_at': datetime.now().isoformat()
        }
        
        # Update ticket data
        ticket['application'] = skill_applications[self.ticket_id]
        
        # Send application summary to ticket channel
        embed = discord.Embed(
            title="⭐ Skill Role Application Submitted",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Skill", value=self.skill_input.value, inline=False)
        embed.add_field(name="Experience", value=self.experience_input.value[:500] + ("..." if len(self.experience_input.value) > 500 else ""), inline=False)
        embed.add_field(name="Portfolio/Examples", value=self.portfolio_input.value[:500] + ("..." if len(self.portfolio_input.value) > 500 else ""), inline=False)
        embed.set_footer(text="Staff will review your application soon!")
        
        await interaction.response.send_message(
            "✅ Your application has been submitted! Staff will review it soon.",
            ephemeral=True
        )
        
        # Send to ticket channel
        ticket_channel = interaction.client.get_channel(ticket['channel_id'])
        if ticket_channel:
            await ticket_channel.send(
                f"{interaction.user.mention} has submitted their skill role application:",
                embed=embed
            )
            
            # Notify staff
            staff_role_id = config['roles'].get('staff', 0)
            if staff_role_id:
                staff_role = interaction.guild.get_role(staff_role_id)
                if staff_role:
                    await ticket_channel.send(
                        f"{staff_role.mention} - New skill role application ready for review!\n"
                        f"Use `/approve {interaction.user.mention} {self.skill_input.value}` to approve."
                    )


class SkillApplicationView(View):
    """View with button to start skill role application."""
    
    def __init__(self, ticket_id: str):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
    
    @discord.ui.button(label="Start Application", style=discord.ButtonStyle.primary, emoji="⭐")
    async def start_application_button(self, interaction: discord.Interaction, button: Button):
        ticket = ticket_data.get(self.ticket_id)
        if not ticket:
            await interaction.response.send_message("Ticket not found.", ephemeral=True)
            return
        
        # Check if user owns this ticket
        if ticket['user_id'] != str(interaction.user.id):
            await interaction.response.send_message(
                "This application form is only for the ticket creator.",
                ephemeral=True
            )
            return
        
        # Check if already applied
        if self.ticket_id in skill_applications:
            await interaction.response.send_message(
                "You have already submitted an application for this ticket.",
                ephemeral=True
            )
            return
        
        # Show modal
        modal = SkillRoleApplicationModal(self.ticket_id)
        await interaction.response.send_modal(modal)


class TicketTypeSelect(discord.ui.Select):
    """Select menu for choosing ticket type"""
    
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Bug Report",
                description="Report a bug or issue",
                emoji="🐛",
                value="bug"
            ),
            discord.SelectOption(
                label="Skill Role Application",
                description="Apply for a skill role",
                emoji="⭐",
                value="skill"
            )
        ]
        super().__init__(placeholder="Choose ticket type...", options=options)
    
    async def callback(self, interaction: discord.Interaction):
        ticket_type = self.values[0]
        user = interaction.user
        guild = interaction.guild
        
        # Check ticket limit
        user_id = str(user.id)
        user_tickets = [t for t in ticket_data.values() if t['user_id'] == user_id and t['status'] == 'open']
        
        max_tickets = config['ticket_settings']['max_tickets_per_user']
        if len(user_tickets) >= max_tickets:
            await interaction.response.send_message(
                f"You already have {len(user_tickets)} open ticket(s). "
                f"Please close existing tickets before creating new ones.",
                ephemeral=True
            )
            return
        
        # Create ticket channel
        category_id = config['channels']['ticket_category']
        category = discord.utils.get(guild.categories, id=category_id) if category_id else None
        
        ticket_num = len(ticket_data) + 1
        channel_name = f"{ticket_type}-{user.name.lower()}-{ticket_num}"
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        # Add staff permissions
        staff_role_id = config['roles'].get('staff', 0)
        if staff_role_id:
            staff_role = guild.get_role(staff_role_id)
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True
                )
        
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            reason=f"Ticket created by {user}"
        )
        
        # Store ticket data
        ticket_id = f"{user_id}-{ticket_num}"
        ticket_data[ticket_id] = {
            'user_id': user_id,
            'channel_id': ticket_channel.id,
            'type': ticket_type,
            'status': 'open',
            'created_at': datetime.now().isoformat()
        }
        
        # Send initial message based on type
        if ticket_type == "bug":
            await ticket_channel.send(
                f"{user.mention} Welcome to your bug report ticket!\n\n"
                f"Please provide the following information:\n"
                f"1. **Description**: What is the bug?\n"
                f"2. **Steps to Reproduce**: How can we reproduce it?\n"
                f"3. **Screenshots**: Attach any relevant screenshots\n\n"
                f"Use the button below to close this ticket when done."
            )
        elif ticket_type == "skill":
            embed = discord.Embed(
                title="⭐ Skill Role Application",
                description=f"{user.mention} Welcome to your skill role application ticket!\n\n"
                           f"Click the button below to start your application.\n"
                           f"You'll fill out a form with:\n"
                           f"• **Skill/Role Name**\n"
                           f"• **Experience Level**\n"
                           f"• **Portfolio/Examples**\n\n"
                           f"Staff will review your application and assign the role if approved.",
                color=discord.Color.blue()
            )
            await ticket_channel.send(embed=embed)
            
            # Add application button
            application_view = SkillApplicationView(ticket_id)
            await ticket_channel.send(view=application_view)
        
        # Add close button
        close_view = CloseTicketView(ticket_id)
        await ticket_channel.send(view=close_view)
        
        # Log ticket creation
        log_channel_id = config['channels']['ticket_logs']
        if log_channel_id:
            log_channel = interaction.client.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="Ticket Created",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=False)
                embed.add_field(name="Type", value=ticket_type.title(), inline=False)
                embed.add_field(name="Channel", value=ticket_channel.mention, inline=False)
                await log_channel.send(embed=embed)
        
        await interaction.response.send_message(
            f"Ticket created! {ticket_channel.mention}",
            ephemeral=True
        )


class CloseTicketView(View):
    """View with close ticket button"""
    
    def __init__(self, ticket_id):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
    
    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close_button(self, interaction: discord.Interaction, button: Button):
        # Check permissions
        if not (interaction.user.guild_permissions.manage_channels or 
                ticket_data.get(self.ticket_id, {}).get('user_id') == str(interaction.user.id)):
            await interaction.response.send_message(
                "You don't have permission to close this ticket.",
                ephemeral=True
            )
            return
        
        ticket = ticket_data.get(self.ticket_id)
        if not ticket or ticket['status'] != 'open':
            await interaction.response.send_message(
                "This ticket is already closed.",
                ephemeral=True
            )
            return
        
        # Mark as closed
        ticket['status'] = 'closed'
        ticket['closed_by'] = str(interaction.user.id)
        ticket['closed_at'] = datetime.now().isoformat()
        
        channel = interaction.channel
        
        # Log closure
        log_channel_id = config['channels']['ticket_logs']
        if log_channel_id:
            log_channel = interaction.client.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="Ticket Closed",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                embed.add_field(name="Closed by", value=interaction.user.mention, inline=False)
                embed.add_field(name="Channel", value=channel.mention, inline=False)
                await log_channel.send(embed=embed)
        
        await interaction.response.send_message("Ticket is being closed...")
        await asyncio.sleep(2)
        await channel.delete(reason=f"Ticket closed by {interaction.user}")


class OpenTicketView(View):
    """View with button to open ticket"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.primary, emoji="🎫")
    async def open_ticket_button(self, interaction: discord.Interaction, button: Button):
        view = View()
        view.add_item(TicketTypeSelect())
        await interaction.response.send_message(
            "Please select the type of ticket you want to create:",
            view=view,
            ephemeral=True
        )


class Tickets(commands.Cog):
    """Ticket system commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='ticketpanel', description='Create the ticket panel with Open Ticket button')
    @app_commands.default_permissions(manage_channels=True)
    async def ticket_panel_slash(self, interaction: discord.Interaction):
        """Slash: Create a ticket panel with button."""
        embed = discord.Embed(
            title="🎫 Ticket System",
            description="Click the button below to create a ticket!\n\n"
                       "**Available Ticket Types:**\n"
                       "🐛 **Bug Report** - Report bugs or issues\n"
                       "⭐ **Skill Role Application** - Apply for a skill role",
            color=discord.Color.blue()
        )
        view = OpenTicketView()
        await interaction.response.send_message(embed=embed, view=view)

    @commands.command(name='ticketpanel')
    @commands.has_permissions(manage_channels=True)
    async def ticket_panel(self, ctx):
        """Create a ticket panel with button."""
        embed = discord.Embed(
            title="🎫 Ticket System",
            description="Click the button below to create a ticket!\n\n"
                       "**Available Ticket Types:**\n"
                       "🐛 **Bug Report** - Report bugs or issues\n"
                       "⭐ **Skill Role Application** - Apply for a skill role",
            color=discord.Color.blue()
        )
        view = OpenTicketView()
        await ctx.send(embed=embed, view=view)

    @app_commands.command(name='approve', description='Approve a skill role application and assign the role')
    @app_commands.describe(member='The user to approve', role_name='Exact name of the role to assign')
    @app_commands.default_permissions(manage_roles=True)
    async def approve_slash(self, interaction: discord.Interaction, member: discord.Member, role_name: str):
        """Slash: Approve skill role and assign role."""
        # Find role by name
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if not role:
            await interaction.response.send_message(
                f"Role '{role_name}' not found. Please specify a valid role name.",
                ephemeral=True
            )
            return
        
        # Check if there's a pending application for this user
        user_id = str(member.id)
        pending_app = None
        ticket_id = None
        
        for tid, app in skill_applications.items():
            if app['user_id'] == user_id and app['status'] == 'pending':
                pending_app = app
                ticket_id = tid
                break
        
        try:
            await member.add_roles(role, reason=f"Skill role approved by {interaction.user}")
            
            # Update application status
            if pending_app:
                pending_app['status'] = 'approved'
                pending_app['approved_by'] = str(interaction.user.id)
                pending_app['approved_at'] = datetime.now().isoformat()
                pending_app['role_assigned'] = role_name
                
                # Notify in ticket channel if ticket exists
                ticket = ticket_data.get(ticket_id)
                if ticket and ticket['status'] == 'open':
                    ticket_channel = self.bot.get_channel(ticket['channel_id'])
                    if ticket_channel:
                        embed = discord.Embed(
                            title="✅ Application Approved!",
                            description=f"{member.mention} has been assigned the **{role.mention}** role!",
                            color=discord.Color.green(),
                            timestamp=datetime.now()
                        )
                        embed.add_field(name="Approved by", value=interaction.user.mention, inline=False)
                        await ticket_channel.send(embed=embed)
            
            await interaction.response.send_message(
                f"✅ {member.mention} has been assigned the {role.mention} role!"
            )
            
            # Log action
            log_channel_id = config['channels']['ticket_logs']
            if log_channel_id:
                log_channel = self.bot.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(
                        title="Skill Role Approved",
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    embed.add_field(name="User", value=member.mention, inline=False)
                    embed.add_field(name="Role", value=role.mention, inline=False)
                    embed.add_field(name="Approved by", value=interaction.user.mention, inline=False)
                    if pending_app:
                        embed.add_field(name="Skill", value=pending_app.get('skill', 'N/A'), inline=False)
                    await log_channel.send(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Error assigning role: {e}", ephemeral=True)

    @commands.command(name='approve')
    @commands.has_permissions(manage_roles=True)
    async def approve_skill(self, ctx, member: discord.Member = None, *, role_name: str = None):
        """Approve a skill role application and assign role."""
        if not member:
            await ctx.send("Usage: `!approve @user <role_name>`")
            return
        
        role = discord.utils.get(ctx.guild.roles, name=role_name) if role_name else None
        if not role:
            await ctx.send(f"Role '{role_name}' not found. Please specify a valid role name.")
            return
        
        # Check if there's a pending application
        user_id = str(member.id)
        pending_app = None
        ticket_id = None
        
        for tid, app in skill_applications.items():
            if app['user_id'] == user_id and app['status'] == 'pending':
                pending_app = app
                ticket_id = tid
                break
        
        try:
            await member.add_roles(role, reason=f"Skill role approved by {ctx.author}")
            
            # Update application status
            if pending_app:
                pending_app['status'] = 'approved'
                pending_app['approved_by'] = str(ctx.author.id)
                pending_app['approved_at'] = datetime.now().isoformat()
                pending_app['role_assigned'] = role_name
                
                # Notify in ticket channel
                ticket = ticket_data.get(ticket_id)
                if ticket and ticket['status'] == 'open':
                    ticket_channel = self.bot.get_channel(ticket['channel_id'])
                    if ticket_channel:
                        embed = discord.Embed(
                            title="✅ Application Approved!",
                            description=f"{member.mention} has been assigned the **{role.mention}** role!",
                            color=discord.Color.green(),
                            timestamp=datetime.now()
                        )
                        embed.add_field(name="Approved by", value=ctx.author.mention, inline=False)
                        await ticket_channel.send(embed=embed)
            
            await ctx.send(f"✅ {member.mention} has been assigned the {role.mention} role!")
            
            # Log action
            log_channel_id = config['channels']['ticket_logs']
            if log_channel_id:
                log_channel = self.bot.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(
                        title="Skill Role Approved",
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    embed.add_field(name="User", value=member.mention, inline=False)
                    embed.add_field(name="Role", value=role.mention, inline=False)
                    embed.add_field(name="Approved by", value=ctx.author.mention, inline=False)
                    if pending_app:
                        embed.add_field(name="Skill", value=pending_app.get('skill', 'N/A'), inline=False)
                    await log_channel.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error assigning role: {e}")


async def setup(bot):
    await bot.add_cog(Tickets(bot))
