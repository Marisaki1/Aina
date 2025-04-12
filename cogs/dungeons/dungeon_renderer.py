import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import io
from typing import Dict, List, Tuple, Any, Optional

# Import settings
import settings

class DungeonRenderer:
    def __init__(self):
        """Initialize the dungeon renderer"""
        self.settings = settings.DUNGEON_SETTINGS
        self.cell_types = settings.CELL_TYPES
        
        # Store player colors for consistent player coloring
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
    
    def render_dungeon(self, 
                       dungeon: Dict[str, Any], 
                       floor_num: int = 0, 
                       show_fog: bool = True) -> io.BytesIO:
        """
        Render the current floor of the dungeon as an image
        
        Args:
            dungeon: The dungeon data
            floor_num: The floor number to render
            show_fog: Whether to apply fog of war
            
        Returns:
            BytesIO containing the image data
        """
        # Make sure the requested floor exists
        if floor_num < 0 or floor_num >= len(dungeon["floors"]):
            floor_num = 0
        
        # Get the floor data
        floor = dungeon["floors"][floor_num]
        
        # Get dimensions
        height = floor["height"]
        width = floor["width"]
        
        # Create base image
        cell_size = 32  # pixels per cell
        img_width = width * cell_size
        img_height = height * cell_size
        img = Image.new('RGB', (img_width, img_height), color=(100, 100, 100))
        draw = ImageDraw.Draw(img)
        
        # Get the grid and convert to numpy if it's a list
        grid = floor["grid"]
        if isinstance(grid, list):
            grid = np.array(grid)
        
        # Get the revealed cells (for fog of war)
        revealed = floor["revealed"]
        if isinstance(revealed, list):
            revealed = np.array(revealed)
        
        # Apply fog of war if requested
        visible = np.ones_like(grid, dtype=bool)
        if show_fog and self.settings["FOG_OF_WAR"]["ENABLED"]:
            visible = self._calculate_visibility(floor, revealed)
        
        # Draw each cell
        for y in range(height):
            for x in range(width):
                cell_type = grid[y][x]
                
                # Skip if not visible due to fog of war
                if not visible[y][x] and show_fog:
                    self._draw_cell(draw, x, y, cell_size, self.cell_types["FOG"])
                    continue
                
                # Draw the appropriate cell
                self._draw_cell(draw, x, y, cell_size, cell_type)
        
        # Draw the grid lines
        for x in range(width + 1):
            draw.line([(x * cell_size, 0), (x * cell_size, img_height)], 
                      fill=(0, 0, 0), width=1)
        
        for y in range(height + 1):
            draw.line([(0, y * cell_size), (img_width, y * cell_size)], 
                      fill=(0, 0, 0), width=1)
        
        # Draw players
        for player_id, pos in floor["player_positions"].items():
            y, x = pos
            color_index = int(player_id) % len(self.player_colors)
            player_color = self.player_colors[color_index]
            
            # Calculate player position in pixels
            px = x * cell_size + cell_size // 2
            py = y * cell_size + cell_size // 2
            radius = cell_size // 3
            
            # Draw player circle
            draw.ellipse((px - radius, py - radius, px + radius, py + radius), 
                         fill=player_color, outline=(0, 0, 0), width=2)
        
        # Draw floor information
        self._draw_floor_info(draw, img_width, img_height, dungeon, floor_num)
        
        # Convert to bytes for discord.File
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        return buffer
    
    def _draw_cell(self, draw: ImageDraw.Draw, x: int, y: int, cell_size: int, cell_type: int) -> None:
        """
        Draw a single cell on the image
        
        Args:
            draw: PIL ImageDraw object
            x: X grid coordinate
            y: Y grid coordinate
            cell_size: Size of cell in pixels
            cell_type: Type of cell to draw
        """
        # Calculate pixel coordinates
        px = x * cell_size
        py = y * cell_size
        
        # Choose color based on cell type
        if cell_type == self.cell_types["WALL"]:
            color = self.settings["COLORS"]["WALL"]
        elif cell_type == self.cell_types["PATH"]:
            color = self.settings["COLORS"]["PATH"]
        elif cell_type == self.cell_types["START"]:
            color = self.settings["COLORS"]["START"]
        elif cell_type == self.cell_types["END"]:
            color = self.settings["COLORS"]["END"]
        elif cell_type == self.cell_types["STAIRS_UP"] or cell_type == self.cell_types["STAIRS_DOWN"]:
            color = self.settings["COLORS"]["STAIRS"]
        elif cell_type == self.cell_types["CHEST"]:
            color = self.settings["COLORS"]["CHEST"]
        elif cell_type == self.cell_types["TRAP"]:
            color = self.settings["COLORS"]["TRAP"]
        elif cell_type == self.cell_types["ENEMY"]:
            color = (220, 100, 100)  # Reddish for enemy
        elif cell_type == self.cell_types["FOG"]:
            color = self.settings["COLORS"]["FOG"]
        else:
            color = (150, 150, 150)  # Default gray
        
        # Draw the cell
        draw.rectangle([px, py, px + cell_size, py + cell_size], fill=color)
        
        # Add icon or text for special cells
        if cell_type == self.cell_types["START"]:
            self._draw_text(draw, "S", px, py, cell_size)
        elif cell_type == self.cell_types["END"]:
            self._draw_text(draw, "E", px, py, cell_size)
        elif cell_type == self.cell_types["STAIRS_UP"]:
            self._draw_text(draw, "↑", px, py, cell_size)
        elif cell_type == self.cell_types["STAIRS_DOWN"]:
            self._draw_text(draw, "↓", px, py, cell_size)
        elif cell_type == self.cell_types["CHEST"]:
            self._draw_text(draw, "C", px, py, cell_size)
        elif cell_type == self.cell_types["TRAP"]:
            self._draw_text(draw, "T", px, py, cell_size)
        elif cell_type == self.cell_types["ENEMY"]:
            self._draw_text(draw, "X", px, py, cell_size)
    
    def _draw_text(self, draw: ImageDraw.Draw, text: str, x: int, y: int, cell_size: int) -> None:
        """
        Draw text centered in a cell
        
        Args:
            draw: PIL ImageDraw object
            text: Text to draw
            x: X pixel coordinate of top-left corner
            y: Y pixel coordinate of top-left corner
            cell_size: Size of cell in pixels
        """
        # Try to get a font
        font = None
        try:
            font = ImageFont.truetype("arial.ttf", cell_size // 2)
        except:
            try:
                font = ImageFont.load_default()
            except:
                pass
        
        # Calculate text position (centered)
        text_width = cell_size // 2
        text_height = cell_size // 2
        
        text_x = x + (cell_size - text_width) // 2
        text_y = y + (cell_size - text_height) // 2
        
        # Draw text
        draw.text((text_x, text_y), text, fill=(0, 0, 0), font=font)
    
    def _draw_floor_info(self, 
                         draw: ImageDraw.Draw, 
                         img_width: int, 
                         img_height: int, 
                         dungeon: Dict[str, Any], 
                         floor_num: int) -> None:
        """
        Draw floor information at the bottom of the image
        
        Args:
            draw: PIL ImageDraw object
            img_width: Width of the image in pixels
            img_height: Height of the image in pixels
            dungeon: Dungeon data
            floor_num: Current floor number
        """
        # Try to get a font
        font = None
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            try:
                font = ImageFont.load_default()
            except:
                pass
        
        # Create floor info text
        floor_text = f"Floor {floor_num + 1}/{dungeon['num_floors']}"
        
        # Draw semi-transparent background for text
        draw.rectangle([0, img_height - 20, img_width, img_height],
                      fill=(0, 0, 0, 128))
        
        # Draw text
        draw.text((10, img_height - 15), floor_text, fill=(255, 255, 255), font=font)
        
        # Draw additional info on right side
        difficulty = dungeon["difficulty"]
        info_text = f"Difficulty: {difficulty}"
        
        # Calculate position to right-align text
        text_width = 100  # Estimate
        draw.text((img_width - text_width - 10, img_height - 15), 
                 info_text, fill=(255, 255, 255), font=font)
    
    def _calculate_visibility(self, floor: Dict[str, Any], revealed: np.ndarray) -> np.ndarray:
        """
        Calculate which cells are visible based on player positions and revealed history
        
        Args:
            floor: The floor data
            revealed: Boolean array of previously revealed cells
            
        Returns:
            Boolean array of visible cells
        """
        height = floor["height"]
        width = floor["width"]
        
        # Start with the previously revealed cells
        visible = revealed.copy()
        
        # Get visibility radius from settings
        radius = self.settings["FOG_OF_WAR"]["VISIBILITY_RADIUS"]
        
        # For each player, reveal cells around them
        for player_id, pos in floor["player_positions"].items():
            y, x = pos
            
            # Calculate visible area (square around player)
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    ny, nx = y + dy, x + dx
                    
                    # Check bounds
                    if 0 <= ny < height and 0 <= nx < width:
                        visible[ny][nx] = True
        
        return visible
    
    def update_revealed_cells(self, dungeon: Dict[str, Any], floor_num: int) -> None:
        """
        Update the revealed cells based on current player positions
        
        Args:
            dungeon: The dungeon data
            floor_num: The floor number
        """
        floor = dungeon["floors"][floor_num]
        
        # Get visibility radius from settings
        radius = self.settings["FOG_OF_WAR"]["VISIBILITY_RADIUS"]
        
        # Get the revealed array
        revealed = floor["revealed"]
        if isinstance(revealed, list):
            revealed = np.array(revealed)
        
        # For each player, reveal cells around them
        for player_id, pos in floor["player_positions"].items():
            y, x = pos
            
            # Calculate visible area (square around player)
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    ny, nx = y + dy, x + dx
                    
                    # Check bounds
                    if 0 <= ny < floor["height"] and 0 <= nx < floor["width"]:
                        revealed[ny][nx] = True
        
        # Update the floor's revealed cells
        floor["revealed"] = revealed.tolist()