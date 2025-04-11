import discord
from discord.ext import commands
import os
from PIL import Image, ImageDraw
import io
import asyncio
import random

class Dungeons(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_dungeons = {}  # Store active dungeon sessions
        self.dungeon_dir = "assets/images/dungeons"
        
        # Create directories if they don't exist
        os.makedirs(self.dungeon_dir, exist_ok=True)
        
        # Player colors (for different players in the dungeon)
        self.player_colors = [
            (255, 0, 0),    # Red
            (0, 0, 255),    # Blue
            (0, 255, 0),    # Green
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (255, 165, 0),  # Orange
            (128, 0, 128)   # Purple
        ]
    
    @commands.command()
    async def test_grid(self, ctx, dungeon_name="default_dungeon"):
        """Test command to create a grid overlay on a dungeon image"""
        # Check if dungeon image exists or create a sample one
        dungeon_path = os.path.join(self.dungeon_dir, f"{dungeon_name}.png")
        
        if not os.path.exists(dungeon_path):
            # Create a blank image if no dungeon image exists
            img = Image.new('RGB', (800, 600), color=(200, 200, 200))
            img.save(dungeon_path)
            await ctx.send(f"Created sample dungeon image at {dungeon_path}")
        
        # Create a new dungeon session
        dungeon_id = str(ctx.channel.id)
        self.active_dungeons[dungeon_id] = {
            'image_path': dungeon_path,
            'players': {ctx.author.id: {'x': 0, 'y': 0, 'color_index': 0}},
            'width': 20,
            'height': 30,
            'message_id': None,
            'player_count': 1
        }
        
        # Generate and send the dungeon image
        dungeon_image = self.generate_dungeon_image(dungeon_id)
        message = await ctx.send(file=discord.File(fp=dungeon_image, filename="dungeon.png"))
        self.active_dungeons[dungeon_id]['message_id'] = message.id
        
        # Add movement controls
        await message.add_reaction("⬆️")  # Up
        await message.add_reaction("⬇️")  # Down
        await message.add_reaction("⬅️")  # Left
        await message.add_reaction("➡️")  # Right
        
        await ctx.send(f"Dungeon started! Use the arrow reactions to move your character.")
    
    def generate_dungeon_image(self, dungeon_id):
        """Generate the dungeon image with grid and player positions"""
        dungeon = self.active_dungeons[dungeon_id]
        
        # Open the base dungeon image
        with Image.open(dungeon['image_path']) as img:
            # Create a copy of the image to work with
            img = img.copy()
            
            # Calculate cell dimensions
            img_width, img_height = img.size
            cell_width = img_width // dungeon['width']
            cell_height = img_height // dungeon['height']
            
            # Create drawing context
            draw = ImageDraw.Draw(img)
            
            # Draw grid lines
            for x in range(0, img_width + 1, cell_width):
                draw.line([(x, 0), (x, img_height)], fill=(0, 0, 0), width=2)
            
            for y in range(0, img_height + 1, cell_height):
                draw.line([(0, y), (img_width, y)], fill=(0, 0, 0), width=2)
            
            # Draw players
            for player_id, player_data in dungeon['players'].items():
                x = player_data['x'] * cell_width + cell_width // 2
                y = player_data['y'] * cell_height + cell_height // 2
                radius = min(cell_width, cell_height) // 3
                
                # Get player color
                color_index = player_data.get('color_index', 0)
                player_color = self.player_colors[color_index % len(self.player_colors)]
                
                # Draw circle representing player
                draw.ellipse((x - radius, y - radius, x + radius, y + radius), 
                            fill=player_color, outline=(0, 0, 0), width=2)
            
            # Convert to bytes for discord.File
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            
            return buffer
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle movement reactions"""
        # Ignore bot's own reactions
        if user.bot:
            return
        
        # Check if this is a dungeon message
        dungeon_id = str(reaction.message.channel.id)
        if dungeon_id not in self.active_dungeons:
            return
            
        dungeon = self.active_dungeons[dungeon_id]
        if reaction.message.id != dungeon['message_id']:
            return
            
        # Check if user is in the dungeon
        if user.id not in dungeon['players']:
            # Add new player with a unique color
            color_index = dungeon['player_count'] % len(self.player_colors)
            dungeon['players'][user.id] = {'x': 0, 'y': 0, 'color_index': color_index}
            dungeon['player_count'] += 1
        
        # Get current position
        position = dungeon['players'][user.id]
        x, y = position['x'], position['y']
        
        # Handle movement
        moved = False
        if reaction.emoji == "⬆️" and y > 0:  # Up
            position['y'] -= 1
            moved = True
        elif reaction.emoji == "⬇️" and y < dungeon['height'] - 1:  # Down
            position['y'] += 1
            moved = True
        elif reaction.emoji == "⬅️" and x > 0:  # Left
            position['x'] -= 1
            moved = True
        elif reaction.emoji == "➡️" and x < dungeon['width'] - 1:  # Right
            position['x'] += 1
            moved = True
            
        # Remove the user's reaction so they can react again
        try:
            await reaction.remove(user)
        except discord.errors.Forbidden:
            # Bot doesn't have permission to remove reactions
            pass
        
        # Update the dungeon image if moved
        if moved:
            dungeon_image = self.generate_dungeon_image(dungeon_id)
            # Using edit with attachments for Discord.py v2.0+
            await reaction.message.edit(attachments=[discord.File(fp=dungeon_image, filename="dungeon.png")])
    
    @commands.command()
    async def join_dungeon(self, ctx):
        """Join the active dungeon in this channel"""
        dungeon_id = str(ctx.channel.id)
        if dungeon_id not in self.active_dungeons:
            return await ctx.send("❌ No active dungeon in this channel!")
            
        # Add player to dungeon at starting position
        dungeon = self.active_dungeons[dungeon_id]
        if ctx.author.id not in dungeon['players']:
            # Assign the next available color
            color_index = dungeon['player_count'] % len(self.player_colors)
            dungeon['players'][ctx.author.id] = {'x': 0, 'y': 0, 'color_index': color_index}
            dungeon['player_count'] += 1
            
            # Update the dungeon image
            dungeon_image = self.generate_dungeon_image(dungeon_id)
            message = await ctx.channel.fetch_message(dungeon['message_id'])
            await message.edit(attachments=[discord.File(fp=dungeon_image, filename="dungeon.png")])
            
            await ctx.send(f"✅ {ctx.author.mention} joined the dungeon!")
        else:
            await ctx.send(f"⚠️ {ctx.author.mention} is already in the dungeon!")
    
    @commands.command()
    async def end_dungeon(self, ctx):
        """End the active dungeon in this channel"""
        dungeon_id = str(ctx.channel.id)
        if dungeon_id not in self.active_dungeons:
            return await ctx.send("❌ No active dungeon in this channel!")
            
        # Remove the dungeon
        del self.active_dungeons[dungeon_id]
        await ctx.send("✅ Dungeon ended!")
    
    @commands.command()
    async def teleport(self, ctx, x: int, y: int):
        """Teleport your character to a specific position (for testing)"""
        dungeon_id = str(ctx.channel.id)
        if dungeon_id not in self.active_dungeons:
            return await ctx.send("❌ No active dungeon in this channel!")
        
        dungeon = self.active_dungeons[dungeon_id]
        
        # Check boundaries
        if x < 0 or x >= dungeon['width'] or y < 0 or y >= dungeon['height']:
            return await ctx.send(f"❌ Position out of bounds! Must be within 0-{dungeon['width']-1} (x) and 0-{dungeon['height']-1} (y)")
        
        # Check if player is in the dungeon
        if ctx.author.id not in dungeon['players']:
            color_index = dungeon['player_count'] % len(self.player_colors)
            dungeon['players'][ctx.author.id] = {'x': x, 'y': y, 'color_index': color_index}
            dungeon['player_count'] += 1
        else:
            # Update player position
            dungeon['players'][ctx.author.id]['x'] = x
            dungeon['players'][ctx.author.id]['y'] = y
        
        # Update the dungeon image
        dungeon_image = self.generate_dungeon_image(dungeon_id)
        message = await ctx.channel.fetch_message(dungeon['message_id'])
        await message.edit(attachments=[discord.File(fp=dungeon_image, filename="dungeon.png")])
        
        await ctx.send(f"✅ {ctx.author.mention} teleported to position ({x}, {y})")

async def setup(bot):
    await bot.add_cog(Dungeons(bot))