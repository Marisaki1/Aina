import random
import numpy as np
from typing import Tuple, List, Dict, Any, Optional
import os
import json
from datetime import datetime

# Import settings
import settings

class DungeonGenerator:
    def __init__(self):
        """Initialize the dungeon generator"""
        self.settings = settings.DUNGEON_SETTINGS
        self.cell_types = settings.CELL_TYPES
        
    def generate_dungeon(self, 
                         size: str = "MEDIUM", 
                         complexity: str = "NORMAL", 
                         floors_type: str = "SMALL", 
                         difficulty: str = "NORMAL") -> Dict[str, Any]:
        """
        Generate a complete dungeon with multiple floors
        
        Args:
            size: Size of the dungeon (SMALL, MEDIUM, LARGE)
            complexity: Complexity of the dungeon (EASY, NORMAL, HARD)
            floors_type: Number of floors (SMALL, MEDIUM, LARGE, EXTREME)
            difficulty: Difficulty of encounters (EASY, NORMAL, HARD, LUNATIC)
            
        Returns:
            Dict containing the full dungeon data
        """
        # Get settings for the specified parameters
        size_config = self.settings["SIZES"][size]
        complexity_config = self.settings["COMPLEXITY"][complexity]
        floors_config = self.settings["FLOORS"][floors_type]
        difficulty_config = self.settings["DIFFICULTY"][difficulty]
        
        # Determine number of floors
        num_floors = random.randint(floors_config["min"], floors_config["max"])
        
        # Generate dungeon data structure
        dungeon = {
            "id": f"dungeon_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
            "name": f"{size_config['name']} ({complexity} Complexity)",
            "created_at": datetime.now().isoformat(),
            "size": size,
            "complexity": complexity,
            "floors_type": floors_type,
            "difficulty": difficulty,
            "num_floors": num_floors,
            "current_floor": 0,
            "floors": []
        }
        
        # Generate each floor
        for floor_num in range(num_floors):
            # Last floor always has a boss/endpoint instead of stairs
            is_final_floor = floor_num == num_floors - 1
            
            floor = self._generate_floor(
                floor_num=floor_num,
                width=size_config["width"],
                height=size_config["height"],
                branch_factor=complexity_config["branch_factor"],
                dead_ends=complexity_config["dead_ends"],
                trap_chance=difficulty_config["trap_chance"],
                is_final_floor=is_final_floor
            )
            
            dungeon["floors"].append(floor)
        
        return dungeon
    
    def _generate_floor(self, 
                        floor_num: int, 
                        width: int, 
                        height: int,
                        branch_factor: float,
                        dead_ends: int,
                        trap_chance: float,
                        is_final_floor: bool = False) -> Dict[str, Any]:
        """
        Generate a single floor of the dungeon
        
        Args:
            floor_num: The floor number
            width: Width of the grid
            height: Height of the grid
            branch_factor: How branched the paths are (0.0 to 1.0)
            dead_ends: Number of dead ends to add
            trap_chance: Chance of traps being placed
            is_final_floor: If True, this is the final floor
            
        Returns:
            Dict containing the floor data
        """
        # Initialize grid with walls - EVERYTHING starts as a wall
        grid = np.zeros((height, width), dtype=int)
        
        # Fill the entire grid with walls
        for y in range(height):
            for x in range(width):
                grid[y, x] = self.cell_types["WALL"]
        
        # Generate start and end positions (not too close to edges)
        start_pos = (random.randint(2, height-3), random.randint(2, width-3))
        
        # For the final floor, place end on opposite side of the grid from start
        if is_final_floor:
            end_pos = self._get_opposite_position(start_pos, height, width)
        else:
            # For non-final floors, place stairs at a good distance from start
            potential_end_spots = []
            min_distance = min(width, height) // 2  # At least half the grid away
            
            for y in range(2, height-2):
                for x in range(2, width-2):
                    dist = abs(start_pos[0] - y) + abs(start_pos[1] - x)
                    if dist >= min_distance:
                        potential_end_spots.append((y, x))
            
            if potential_end_spots:
                end_pos = random.choice(potential_end_spots)
            else:
                end_pos = (
                    (start_pos[0] + height // 2) % (height - 4) + 2,
                    (start_pos[1] + width // 2) % (width - 4) + 2
                )
        
        # Create a single-width path from start to end
        self._generate_single_width_path(grid, start_pos, end_pos)
        
        # Add branch points
        self._add_single_width_branches(grid, branch_factor, dead_ends)
        
        # Mark start and end points
        grid[start_pos[0], start_pos[1]] = self.cell_types["START"]
        
        if is_final_floor:
            grid[end_pos[0], end_pos[1]] = self.cell_types["END"]
        else:
            grid[end_pos[0], end_pos[1]] = self.cell_types["STAIRS_UP"]
        
        # Add elements to the grid (chests, traps, enemies)
        self._add_elements(grid, trap_chance, is_final_floor)
        
        # Create floor data structure
        floor = {
            "number": floor_num,
            "width": width,
            "height": height,
            "grid": grid.tolist(),
            "start_pos": start_pos,
            "end_pos": end_pos,
            "is_final_floor": is_final_floor,
            "revealed": np.zeros((height, width), dtype=bool).tolist(),  # Fog of war tracking
            "elements": self._extract_elements(grid),
            "player_positions": {}  # Will store player positions
        }
        
        return floor

    def _generate_single_width_path(self, grid: np.ndarray, start: Tuple[int, int], end: Tuple[int, int]) -> None:
        """
        Generate a path from start to end that is exactly 1 cell wide
        
        Args:
            grid: The grid array to modify
            start: Starting position (y, x)
            end: Ending position (y, x)
        """
        # Set start and potentially visited positions
        y, x = start
        grid[y, x] = self.cell_types["PATH"]
        
        # Keep track of cells we've tried
        visited = set([start])
        
        # Simple A* implementation
        queue = [(start, [])]  # (position, path)
        
        while queue:
            (y, x), path = queue.pop(0)
            
            # Check if we reached the end
            if (y, x) == end:
                # Mark the final path
                for py, px in path:
                    grid[py, px] = self.cell_types["PATH"]
                return
            
            # Try each direction
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            random.shuffle(directions)  # Randomize directions for more interesting paths
            
            for dy, dx in directions:
                ny, nx = y + dy, x + dx
                
                # Check if within bounds and not visited
                if (0 < ny < grid.shape[0]-1 and 0 < nx < grid.shape[1]-1 and
                    (ny, nx) not in visited):
                    
                    # Mark as visited
                    visited.add((ny, nx))
                    
                    # Add to queue
                    new_path = path + [(ny, nx)]
                    queue.append(((ny, nx), new_path))
        
        # If we can't find a path, create a direct one
        self._create_direct_single_width_path(grid, start, end)

    def _create_direct_single_width_path(self, grid: np.ndarray, start: Tuple[int, int], end: Tuple[int, int]) -> None:
        """
        Create a direct 1-cell-wide path between two points
        
        Args:
            grid: The grid array to modify
            start: Starting position (y, x)
            end: Ending position (y, x)
        """
        y, x = start
        end_y, end_x = end
        
        # Choose to go horizontal or vertical first (randomly)
        if random.choice([True, False]):
            # Move horizontally first, then vertically
            while x != end_x:
                x += 1 if end_x > x else -1
                grid[y, x] = self.cell_types["PATH"]
            
            while y != end_y:
                y += 1 if end_y > y else -1
                grid[y, x] = self.cell_types["PATH"]
        else:
            # Move vertically first, then horizontally
            while y != end_y:
                y += 1 if end_y > y else -1
                grid[y, x] = self.cell_types["PATH"]
            
            while x != end_x:
                x += 1 if end_x > x else -1
                grid[y, x] = self.cell_types["PATH"]

    def _add_single_width_branches(self, grid: np.ndarray, branch_factor: float, dead_end_count: int) -> None:
        """
        Add 1-cell-wide branches to the main path
        
        Args:
            grid: The grid array to modify
            branch_factor: How branched the paths are (0.0 to 1.0)
            dead_end_count: Number of additional dead ends to add
        """
        height, width = grid.shape
        
        # Find all existing path cells
        path_cells = []
        for y in range(1, height-1):
            for x in range(1, width-1):
                if grid[y, x] == self.cell_types["PATH"]:
                    path_cells.append((y, x))
        
        # Shuffle to randomize branch starting points
        random.shuffle(path_cells)
        
        # Calculate number of branches based on branch factor
        num_branches = int(len(path_cells) * branch_factor) + dead_end_count
        num_branches = min(num_branches, len(path_cells) * 2)  # Cap to reasonable number
        
        branches_added = 0
        
        for y, x in path_cells:
            if branches_added >= num_branches:
                break
                
            # Find available directions to add a branch
            directions = []
            for dy, dx in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                ny, nx = y + dy, x + dx
                
                # Check if there's a wall we can turn into a path
                if (1 < ny < height-2 and 1 < nx < width-2 and 
                    grid[ny, nx] == self.cell_types["WALL"]):
                    
                    # Check if the next cell in that direction is also a wall
                    # (to ensure we don't connect to another path right away)
                    ny2, nx2 = ny + dy, nx + dx
                    if (0 < ny2 < height-1 and 0 < nx2 < width-1 and
                        grid[ny2, nx2] == self.cell_types["WALL"]):
                        directions.append((dy, dx))
            
            if directions:
                # Choose a random direction
                dy, dx = random.choice(directions)
                
                # Create a branch
                branch_length = random.randint(2, 5)  # Length of 2-5 cells
                
                # First cell of branch
                y1, x1 = y + dy, x + dx
                grid[y1, x1] = self.cell_types["PATH"]
                
                # Continue branch
                current_y, current_x = y1, x1
                
                for _ in range(1, branch_length):
                    # Try to continue straight with high probability
                    if random.random() < 0.7:
                        next_dy, next_dx = dy, dx
                    else:
                        # Try to turn (perpendicular to current direction)
                        turn_options = [(dx, -dy), (-dx, dy)]
                        next_dy, next_dx = random.choice(turn_options)
                    
                    next_y, next_x = current_y + next_dy, current_x + next_dx
                    
                    # Check if valid position for continuing branch
                    if (1 < next_y < height-2 and 1 < next_x < width-2 and
                        grid[next_y, next_x] == self.cell_types["WALL"]):
                        
                        # Also check if we're not connecting to another path
                        connected_to_path = False
                        for check_dy, check_dx in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            if check_dy == -next_dy and check_dx == -next_dx:
                                # Skip checking the cell we just came from
                                continue
                                
                            check_y, check_x = next_y + check_dy, next_x + check_dx
                            if (0 <= check_y < height and 0 <= check_x < width and
                                grid[check_y, check_x] == self.cell_types["PATH"]):
                                connected_to_path = True
                                break
                        
                        if not connected_to_path:
                            grid[next_y, next_x] = self.cell_types["PATH"]
                            current_y, current_x = next_y, next_x
                            # Update direction for next iteration if we turned
                            dy, dx = next_dy, next_dx
                        else:
                            # Stop if we would connect to another path
                            break
                    else:
                        # Stop if we reached an edge or another path
                        break
                
                branches_added += 1
    
    def _add_elements(self, grid: np.ndarray, trap_chance: float, is_final_floor: bool) -> None:
        """
        Add elements like chests, traps, and enemies to the dungeon
        
        Args:
            grid: The grid array to modify
            trap_chance: Chance of traps being placed (0.0 to 1.0)
            is_final_floor: If True, this is the final floor
        """
        # Find all plain path cells (candidates for elements)
        path_cells = []
        for y in range(1, grid.shape[0]-1):
            for x in range(1, grid.shape[1]-1):
                if grid[y, x] == self.cell_types["PATH"]:
                    # Check surrounding cells - better to place elements in interesting spots
                    wall_neighbors = 0
                    for ny, nx in [(y-1, x), (y+1, x), (y, x-1), (y, x+1)]:
                        if 0 <= ny < grid.shape[0] and 0 <= nx < grid.shape[1] and grid[ny, nx] == self.cell_types["WALL"]:
                            wall_neighbors += 1
                    
                    # Cells with 2 or 3 wall neighbors make good element locations
                    if 2 <= wall_neighbors <= 3:
                        path_cells.append((y, x))
        
        # Shuffle cells to randomize element placement
        random.shuffle(path_cells)
        
        # Calculate number of each element based on grid size
        num_cells = len(path_cells)
        num_chests = max(1, num_cells // 15)
        num_traps = max(1, int(num_cells * trap_chance))
        num_enemies = max(2, num_cells // 10)
        
        # Adjust for final floor
        if is_final_floor:
            num_chests += 1  # Extra reward
            num_enemies += 2  # More challenge
        
        # Place chests
        for i in range(min(num_chests, len(path_cells))):
            y, x = path_cells.pop(0)
            grid[y, x] = self.cell_types["CHEST"]
        
        # Place traps
        for i in range(min(num_traps, len(path_cells))):
            y, x = path_cells.pop(0)
            grid[y, x] = self.cell_types["TRAP"]
        
        # Place enemies
        for i in range(min(num_enemies, len(path_cells))):
            y, x = path_cells.pop(0)
            grid[y, x] = self.cell_types["ENEMY"]
    
    def _extract_elements(self, grid: np.ndarray) -> Dict[str, List[Tuple[int, int]]]:
        """Extract element positions from the grid
        
        Args:
            grid: The dungeon grid
            
        Returns:
            Dictionary of elements and their positions
        """
        elements = {
            "chests": [],
            "traps": [],
            "enemies": [],
            "stairs_up": [],
            "stairs_down": [],
            "start": None,
            "end": None
        }
        
        # Scan grid for elements
        for y in range(grid.shape[0]):
            for x in range(grid.shape[1]):
                cell_type = grid[y, x]
                
                if cell_type == self.cell_types["CHEST"]:
                    elements["chests"].append((y, x))
                elif cell_type == self.cell_types["TRAP"]:
                    elements["traps"].append((y, x))
                elif cell_type == self.cell_types["ENEMY"]:
                    elements["enemies"].append((y, x))
                elif cell_type == self.cell_types["STAIRS_UP"]:
                    elements["stairs_up"].append((y, x))
                elif cell_type == self.cell_types["STAIRS_DOWN"]:
                    elements["stairs_down"].append((y, x))
                elif cell_type == self.cell_types["START"]:
                    elements["start"] = (y, x)
                elif cell_type == self.cell_types["END"]:
                    elements["end"] = (y, x)
        
        return elements
    
    def _get_opposite_position(self, pos: Tuple[int, int], height: int, width: int) -> Tuple[int, int]:
        """
        Get a position roughly opposite to the given position in the grid
        
        Args:
            pos: Original position (y, x)
            height: Grid height
            width: Grid width
            
        Returns:
            Position tuple (y, x) on opposite side of grid
        """
        y, x = pos
        
        # Determine which quadrant the original position is in
        quadrant_y = 0 if y < height // 2 else 1
        quadrant_x = 0 if x < width // 2 else 1
        
        # Calculate opposite quadrant
        opposite_y = 1 - quadrant_y
        opposite_x = 1 - quadrant_x
        
        # Generate a position in the opposite quadrant
        if opposite_y == 0:
            new_y = random.randint(1, height // 2 - 1)
        else:
            new_y = random.randint(height // 2 + 1, height - 2)
            
        if opposite_x == 0:
            new_x = random.randint(1, width // 2 - 1)
        else:
            new_x = random.randint(width // 2 + 1, width - 2)
        
        return (new_y, new_x)
    
    def save_dungeon(self, dungeon: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Save a dungeon to disk
        
        Args:
            dungeon: The dungeon data to save
            filename: Optional filename (defaults to dungeon ID)
            
        Returns:
            The path where the dungeon was saved
        """
        if filename is None:
            filename = f"{dungeon['id']}.json"
        
        save_path = os.path.join(self.settings["SAVE"]["SAVE_DIR"], filename)
        
        with open(save_path, 'w') as f:
            json.dump(dungeon, f)
        
        return save_path
    
    def load_dungeon(self, dungeon_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a dungeon from disk
        
        Args:
            dungeon_id: The ID of the dungeon to load
            
        Returns:
            The dungeon data or None if not found
        """
        save_path = os.path.join(self.settings["SAVE"]["SAVE_DIR"], f"{dungeon_id}.json")
        
        if not os.path.exists(save_path):
            return None
        
        with open(save_path, 'r') as f:
            return json.load(f)