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
        
        # Calculate coverage factor based on size and complexity
        coverage_factor = 0.3  # Base coverage (SMALL/EASY)
        if size == "MEDIUM":
            coverage_factor = 0.4
        elif size == "LARGE":
            coverage_factor = 0.6
            
        # Adjust based on complexity
        if complexity == "NORMAL":
            coverage_factor *= 1.2
        elif complexity == "HARD":
            coverage_factor *= 1.5
        
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
                is_final_floor=is_final_floor,
                coverage_factor=coverage_factor
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
                    is_final_floor: bool = False,
                    **kwargs) -> Dict[str, Any]:
        """
        Generate a single floor of the dungeon using proper maze generation
        
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
        # Initialize grid with ALL walls
        grid = np.full((height, width), self.cell_types["WALL"], dtype=int)
        
        # Leave only a 1-cell border around the edges
        effective_width = width - 2
        effective_height = height - 2
        
        # Make sure maze dimensions are odd (for proper corridors)
        effective_width = effective_width - 1 if effective_width % 2 == 0 else effective_width
        effective_height = effective_height - 1 if effective_height % 2 == 0 else effective_height
        
        # Calculate start position - closer to top-left corner
        # Ensure coordinates are odd for proper grid alignment
        start_x = random.randrange(1, max(3, effective_width // 4), 2)
        start_y = random.randrange(1, max(3, effective_height // 4), 2)
        start_pos = (start_y, start_x)
        
        # Calculate end position - closer to bottom-right corner
        end_x = random.randrange(min(effective_width - 2, 3 * effective_width // 4), effective_width, 2)
        end_y = random.randrange(min(effective_height - 2, 3 * effective_height // 4), effective_height, 2)
        end_pos = (end_y, end_x)
        
        # Generate maze using recursive backtracker that fills the whole area
        self._generate_full_maze(grid, 1, 1, effective_width, effective_height)
        
        # Ensure start and end positions are paths
        grid[start_pos[0], start_pos[1]] = self.cell_types["PATH"]
        grid[end_pos[0], end_pos[1]] = self.cell_types["PATH"]
        
        # Ensure there's a path between start and end
        self._ensure_path_between(grid, start_pos, end_pos)
        
        # Add more connections to make the maze less perfect (based on branch_factor)
        num_extra_connections = int(effective_width * effective_height * branch_factor * 0.02)
        self._add_extra_connections(grid, num_extra_connections)
        
        # Remove some dead ends to create more loops
        num_dead_ends_to_remove = dead_ends * 2  # Increase number to create more loops
        self._remove_dead_ends(grid, num_dead_ends_to_remove)
        
        # Mark start and end positions
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
            "revealed": np.zeros((height, width), dtype=bool).tolist(),
            "elements": self._extract_elements(grid),
            "player_positions": {}
        }
        
        return floor

    def _generate_full_maze(self, grid, start_y, start_x, width, height):
        """
        Generate a maze that fills the entire available space
        
        Args:
            grid: The grid to modify
            start_y: Starting Y coordinate
            start_x: Starting X coordinate
            width: Width of the effective area
            height: Height of the effective area
        """
        # Create a grid to track visited cells
        visited = np.zeros((height + 1, width + 1), dtype=bool)
        
        # Queue for cell processing - start with full grid of cells
        cells = []
        for y in range(start_y, start_y + height, 2):
            for x in range(start_x, start_x + width, 2):
                if y < grid.shape[0] and x < grid.shape[1]:
                    cells.append((y, x))
        
        # Shuffle the cells for more randomness
        random.shuffle(cells)
        
        # Process each cell
        for y, x in cells:
            # Mark the cell as a path
            if 0 <= y < grid.shape[0] and 0 <= x < grid.shape[1]:
                grid[y, x] = self.cell_types["PATH"]
                visited[y - start_y, x - start_x] = True
        
        # Connect the path cells with a spanning tree algorithm
        self._connect_maze_cells(grid, start_y, start_x, visited)

    def _connect_maze_cells(self, grid, start_y, start_x, visited):
        """
        Connect the path cells to form a connected maze
        
        Args:
            grid: The grid to modify
            start_y: Starting Y coordinate
            start_x: Starting X coordinate
            visited: Grid of visited cells
        """
        height, width = visited.shape
        
        # Use a spanning tree algorithm to connect all cells
        # Start with a random cell
        cells_to_connect = []
        connected_cells = set()
        
        # Find all path cells
        for y in range(visited.shape[0]):
            for x in range(visited.shape[1]):
                if visited[y, x]:
                    real_y, real_x = y + start_y, x + start_x
                    if 0 <= real_y < grid.shape[0] and 0 <= real_x < grid.shape[1]:
                        if len(connected_cells) == 0:
                            # Start with one cell
                            connected_cells.add((real_y, real_x))
                        else:
                            # Add others to the list of cells to connect
                            cells_to_connect.append((real_y, real_x))
        
        # Shuffle to randomize connections
        random.shuffle(cells_to_connect)
        
        # Connect all cells
        while cells_to_connect:
            # Find a cell that can connect to our existing connected set
            for i, (y, x) in enumerate(cells_to_connect):
                # Check if this cell can connect to any connected cell
                can_connect = False
                connect_y, connect_x = None, None
                
                # Check all possible connections
                for dy, dx in [(0, 2), (2, 0), (0, -2), (-2, 0)]:
                    ny, nx = y + dy, x + dx
                    if (ny, nx) in connected_cells:
                        # Can connect here
                        can_connect = True
                        connect_y, connect_x = ny, nx
                        break
                
                if can_connect:
                    # Connect the cells
                    wall_y = (y + connect_y) // 2
                    wall_x = (x + connect_x) // 2
                    
                    if 0 <= wall_y < grid.shape[0] and 0 <= wall_x < grid.shape[1]:
                        grid[wall_y, wall_x] = self.cell_types["PATH"]
                    
                    # Add this cell to connected set
                    connected_cells.add((y, x))
                    
                    # Remove from cells to connect
                    cells_to_connect.pop(i)
                    break
            else:
                # If we can't connect any more cells, break
                break
            
    def _generate_true_maze(self, grid, width, height):
        """
        Generate a proper maze using the Recursive Backtracker algorithm
        
        Args:
            grid: The grid to modify
            width: The effective width
            height: The effective height
            
        Returns:
            The modified grid with a proper maze
        """
        # Create a grid of cells to track visited cells during maze generation
        # We work with odd coordinates (1, 3, 5, etc) to leave walls between paths
        visited = np.zeros((height, width), dtype=bool)
        
        # Start at a random cell (odd coordinates)
        start_y = random.randrange(1, height, 2)
        start_x = random.randrange(1, width, 2)
        
        # Mark the starting cell as a path
        grid[start_y, start_x] = self.cell_types["PATH"]
        visited[start_y, start_x] = True
        
        # Create a stack for backtracking and add the starting cell
        stack = [(start_y, start_x)]
        
        # Continue until the stack is empty
        while stack:
            current_y, current_x = stack[-1]
            
            # Get unvisited neighbors (with walls between them)
            neighbors = []
            for dy, dx in [(0, 2), (2, 0), (0, -2), (-2, 0)]:  # Right, Down, Left, Up
                ny, nx = current_y + dy, current_x + dx
                
                # Check if the neighbor is within bounds and not visited
                if (1 <= ny < height - 1 and 1 <= nx < width - 1 and 
                    not visited[ny, nx]):
                    neighbors.append((ny, nx, dy, dx))
            
            if neighbors:
                # Choose a random unvisited neighbor
                next_y, next_x, dy, dx = random.choice(neighbors)
                
                # Remove the wall between current cell and the chosen neighbor
                wall_y = current_y + dy // 2
                wall_x = current_x + dx // 2
                grid[wall_y, wall_x] = self.cell_types["PATH"]
                
                # Mark the new cell as a path and visited
                grid[next_y, next_x] = self.cell_types["PATH"]
                visited[next_y, next_x] = True
                
                # Push the new cell to the stack
                stack.append((next_y, next_x))
            else:
                # Backtrack - no unvisited neighbors
                stack.pop()
        
        return grid

    def _ensure_path_between(self, grid, start_pos, end_pos):
        """
        Ensure there's a valid path between start and end positions
        
        Args:
            grid: The grid to modify
            start_pos: The starting position
            end_pos: The ending position
        """
        height, width = grid.shape
        
        # Use A* pathfinding to find the shortest path
        # Initialize the open and closed sets
        open_set = [start_pos]
        closed_set = set()
        
        # Track the path with a parent dictionary
        came_from = {}
        
        # G score is the distance from start to current position
        g_score = {start_pos: 0}
        
        # F score is the estimated total cost (g_score + heuristic)
        f_score = {start_pos: self._manhattan_distance(start_pos, end_pos)}
        
        while open_set:
            # Get the node with the lowest f_score
            current = min(open_set, key=lambda pos: f_score.get(pos, float('inf')))
            
            if current == end_pos:
                # We've reached the end - ensure the path is marked
                while current in came_from:
                    current = came_from[current]
                    # Mark as path if not already
                    if grid[current[0], current[1]] == self.cell_types["WALL"]:
                        grid[current[0], current[1]] = self.cell_types["PATH"]
                return
            
            open_set.remove(current)
            closed_set.add(current)
            
            # Check each neighbor
            y, x = current
            for dy, dx in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                ny, nx = y + dy, x + dx
                
                # Check if position is valid
                if not (0 <= ny < height and 0 <= nx < width):
                    continue
                
                # If wall, check if we can add a path here
                if grid[ny, nx] == self.cell_types["WALL"]:
                    # Check if we'd create a 2x2 open space (avoid this for maze structure)
                    creates_2x2 = False
                    for cy, cx in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                        check_y, check_x = ny - cy, nx - cx
                        if (0 <= check_y < height - 1 and 0 <= check_x < width - 1):
                            # Count PATH cells in a 2x2 region
                            path_count = 0
                            for py, px in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                                if grid[check_y + py, check_x + px] == self.cell_types["PATH"] or (check_y + py == ny and check_x + px == nx):
                                    path_count += 1
                            if path_count >= 3:  # Would create a 2x2 open area
                                creates_2x2 = True
                                break
                    
                    if creates_2x2:
                        continue
                
                # Skip if the neighbor is in the closed set
                if (ny, nx) in closed_set:
                    continue
                
                # Calculate the tentative g_score
                tentative_g_score = g_score[current] + 1
                
                # If this path is better than any previous one
                if (ny, nx) not in open_set or tentative_g_score < g_score.get((ny, nx), float('inf')):
                    # Update the path
                    came_from[(ny, nx)] = current
                    g_score[(ny, nx)] = tentative_g_score
                    f_score[(ny, nx)] = tentative_g_score + self._manhattan_distance((ny, nx), end_pos)
                    
                    # Add to open set if not already there
                    if (ny, nx) not in open_set:
                        open_set.append((ny, nx))

    def _manhattan_distance(self, pos1, pos2):
        """Calculate Manhattan distance between two positions"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def _add_extra_connections(self, grid, count):
        """
        Add extra connections to make the maze less perfect (loops)
        
        Args:
            grid: The grid to modify
            count: Number of extra connections to add
        """
        height, width = grid.shape
        
        walls_added = 0
        attempts = 0
        max_attempts = count * 10  # Avoid infinite loops
        
        while walls_added < count and attempts < max_attempts:
            attempts += 1
            
            # Choose a random wall that's not on the boundary
            y = random.randint(1, height - 2)
            x = random.randint(1, width - 2)
            
            if grid[y, x] != self.cell_types["WALL"]:
                continue
            
            # Check if this wall separates two passages
            passages = 0
            passage_coords = []
            
            for dy, dx in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                ny, nx = y + dy, x + dx
                if (0 <= ny < height and 0 <= nx < width and 
                    grid[ny, nx] != self.cell_types["WALL"]):
                    passages += 1
                    passage_coords.append((ny, nx))
            
            # If exactly two passages on opposite sides, this is a good candidate
            if passages == 2 and abs(passage_coords[0][0] - passage_coords[1][0]) + abs(passage_coords[0][1] - passage_coords[1][1]) == 2:
                # Remove the wall to create a loop
                grid[y, x] = self.cell_types["PATH"]
                walls_added += 1

    def _remove_dead_ends(self, grid, count):
        """
        Remove some dead ends to create more loops
        
        Args:
            grid: The grid to modify
            count: Number of dead ends to remove
        """
        height, width = grid.shape
        
        for _ in range(count):
            # Find dead ends (path cells with exactly 3 wall neighbors)
            dead_ends = []
            
            for y in range(1, height - 1):
                for x in range(1, width - 1):
                    if grid[y, x] != self.cell_types["WALL"]:
                        # Count wall neighbors
                        wall_count = 0
                        for dy, dx in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            ny, nx = y + dy, x + dx
                            if (0 <= ny < height and 0 <= nx < width and 
                                grid[ny, nx] == self.cell_types["WALL"]):
                                wall_count += 1
                        
                        # Dead end has 3 walls around it
                        if wall_count == 3:
                            dead_ends.append((y, x))
            
            if not dead_ends:
                break
            
            # Choose a random dead end
            y, x = random.choice(dead_ends)
            
            # Find a wall to remove
            for dy, dx in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                ny, nx = y + dy, x + dx
                if (0 <= ny < height and 0 <= nx < width and 
                    grid[ny, nx] == self.cell_types["WALL"]):
                    # Check if the wall is not on the boundary
                    if 0 < ny < height - 1 and 0 < nx < width - 1:
                        # Make sure removing this wall connects to another path
                        connects_to_path = False
                        for ndy, ndx in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            nny, nnx = ny + ndy, nx + ndx
                            if (0 <= nny < height and 0 <= nnx < width and
                                grid[nny, nnx] != self.cell_types["WALL"] and
                                (nny != y or nnx != x)):
                                connects_to_path = True
                                break
                        
                        if connects_to_path:
                            grid[ny, nx] = self.cell_types["PATH"]
                            break
  
    def _add_elements(self, grid, trap_chance, is_final_floor):
        """
        Add elements to the dungeon (better distributed)
        
        Args:
            grid: The grid to modify
            trap_chance: Chance of traps being placed
            is_final_floor: If True, this is the final floor
        """
        height, width = grid.shape
        
        # Find all path cells (excluding special cells)
        path_cells = []
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if grid[y, x] == self.cell_types["PATH"]:
                    path_cells.append((y, x))
        
        # Skip if no path cells
        if not path_cells:
            return
        
        # Calculate number of each element based on grid size
        num_path_cells = len(path_cells)
        num_chests = max(1, num_path_cells // 25)  # More chests
        num_traps = max(1, int(num_path_cells * trap_chance * 0.15))  # More traps
        num_enemies = max(2, num_path_cells // 15)  # More enemies
        
        # Adjust for final floor
        if is_final_floor:
            num_chests = max(2, num_chests)
            num_enemies = max(3, num_enemies)
        
        # Create a copy of path cells to avoid duplicates
        available_cells = path_cells.copy()
        random.shuffle(available_cells)
        
        # Divide the grid into regions to ensure even distribution
        regions = []
        region_size = 5  # Size of each region
        
        for region_y in range(0, height, region_size):
            for region_x in range(0, width, region_size):
                region_cells = []
                for y, x in available_cells:
                    if (region_y <= y < region_y + region_size and 
                        region_x <= x < region_x + region_size):
                        region_cells.append((y, x))
                
                if region_cells:
                    regions.append(region_cells)
        
        # Place elements throughout different regions
        elements_placed = 0
        
        # Place chests
        for _ in range(num_chests):
            if not regions:
                break
            
            region_idx = random.randint(0, len(regions) - 1)
            if not regions[region_idx]:
                regions.pop(region_idx)
                continue
                
            y, x = random.choice(regions[region_idx])
            grid[y, x] = self.cell_types["CHEST"]
            
            # Remove cell from available cells
            regions[region_idx].remove((y, x))
            if (y, x) in available_cells:
                available_cells.remove((y, x))
            
            elements_placed += 1
        
        # Place traps
        for _ in range(num_traps):
            if not regions:
                break
            
            region_idx = random.randint(0, len(regions) - 1)
            if not regions[region_idx]:
                regions.pop(region_idx)
                continue
                
            y, x = random.choice(regions[region_idx])
            grid[y, x] = self.cell_types["TRAP"]
            
            # Remove cell from available cells
            regions[region_idx].remove((y, x))
            if (y, x) in available_cells:
                available_cells.remove((y, x))
            
            elements_placed += 1
        
        # Place enemies
        for _ in range(num_enemies):
            if not regions:
                break
            
            region_idx = random.randint(0, len(regions) - 1)
            if not regions[region_idx]:
                regions.pop(region_idx)
                continue
                
            y, x = random.choice(regions[region_idx])
            grid[y, x] = self.cell_types["ENEMY"]
            
            # Remove cell from available cells
            regions[region_idx].remove((y, x))
            if (y, x) in available_cells:
                available_cells.remove((y, x))
            
            elements_placed += 1
                    
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
        
    def _count_path_cells(self, grid: np.ndarray) -> int:
        """Count the number of non-wall cells in the grid"""
        return np.sum(grid != self.cell_types["WALL"])

    def _add_more_branches(self, grid: np.ndarray, branch_factor: float, dead_end_count: int) -> None:
        """Add more branches to increase coverage"""
        height, width = grid.shape
        
        # Find all existing path cells to branch from
        path_cells = []
        for y in range(1, height-1):
            for x in range(1, width-1):
                if grid[y, x] != self.cell_types["WALL"]:
                    path_cells.append((y, x))
        
        if not path_cells:
            return
            
        # Choose random starting points
        branching_points = random.sample(path_cells, min(len(path_cells), 5))
        
        for start_y, start_x in branching_points:
            # Random direction
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            random.shuffle(directions)
            
            # Try to make a branch in a random direction
            for dy, dx in directions:
                # Branch length (longer for higher complexity)
                branch_length = random.randint(3, 3 + int(branch_factor * 7))
                
                # Create branch
                current_y, current_x = start_y, start_x
                
                for _ in range(branch_length):
                    next_y, next_x = current_y + dy, current_x + dx
                    
                    # Check boundaries and if it's a wall
                    if (1 <= next_y < height-1 and 1 <= next_x < width-1 and 
                        grid[next_y, next_x] == self.cell_types["WALL"]):
                        
                        # Make this cell a path
                        grid[next_y, next_x] = self.cell_types["PATH"]
                        current_y, current_x = next_y, next_x
                        
                        # Randomly change direction (with low probability)
                        if random.random() < 0.2:
                            # Turn left or right
                            if dy == 0:  # Moving horizontally
                                dy = random.choice([-1, 1])
                                dx = 0
                            else:  # Moving vertically
                                dy = 0
                                dx = random.choice([-1, 1])
                    else:
                        break  # Stop branch if we hit a non-wall

    def _generate_maze_dfs(self, grid, y, x, end_pos):
        """Generate a maze using depth-first search algorithm"""
        height, width = grid.shape
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        # Shuffle directions for randomness
        random.shuffle(directions)
        
        for dy, dx in directions:
            # Check two cells away (to maintain walls between paths)
            ny, nx = y + dy * 2, x + dx * 2
            
            # Check if this cell is within bounds and is a wall
            if (0 < ny < height-1 and 0 < nx < width-1 and
                grid[ny][nx] == self.cell_types["WALL"]):
                
                # Connect by making both cells a path
                grid[y + dy][x + dx] = self.cell_types["PATH"]
                grid[ny][nx] = self.cell_types["PATH"]
                
                # Recursively continue from the new cell
                self._generate_maze_dfs(grid, ny, nx, end_pos)
                
                # If we're near the end position, make sure to connect to it
                if abs(ny - end_pos[0]) <= 2 and abs(nx - end_pos[1]) <= 2:
                    ey, ex = end_pos
                    if abs(ny - ey) + abs(nx - ex) == 2:  # If one cell away (diagonal)
                        # Connect horizontally or vertically
                        if ny == ey:
                            grid[ny][min(nx, ex) + 1] = self.cell_types["PATH"]
                        else:
                            grid[min(ny, ey) + 1][nx] = self.cell_types["PATH"]
                    elif abs(ny - ey) + abs(nx - ex) <= 3:  # If close
                        # Draw direct path
                        if ny == ey:
                            for x_pos in range(min(nx, ex) + 1, max(nx, ex)):
                                grid[ny][x_pos] = self.cell_types["PATH"]
                        elif nx == ex:
                            for y_pos in range(min(ny, ey) + 1, max(ny, ey)):
                                grid[y_pos][nx] = self.cell_types["PATH"]

    def _ensure_path_to_end(self, grid, start_pos, end_pos):
        """Make sure there's a path connecting start and end positions"""
        sy, sx = start_pos
        ey, ex = end_pos
        
        # Find closest path cell to end position
        height, width = grid.shape
        closest_dist = float('inf')
        closest_pos = None
        
        for y in range(1, height-1):
            for x in range(1, width-1):
                if grid[y][x] == self.cell_types["PATH"]:
                    dist = abs(y - ey) + abs(x - ex)
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_pos = (y, x)
        
        if closest_pos:
            y, x = closest_pos
            
            # Create a twisty path from closest path to end
            current_pos = (y, x)
            target_pos = end_pos
            
            while current_pos != target_pos:
                cy, cx = current_pos
                
                # Determine direction (prefer moving toward target)
                if cy < ey and random.random() < 0.7:
                    next_pos = (cy + 1, cx)
                elif cy > ey and random.random() < 0.7:
                    next_pos = (cy - 1, cx)
                elif cx < ex and random.random() < 0.7:
                    next_pos = (cy, cx + 1)
                elif cx > ex and random.random() < 0.7:
                    next_pos = (cy, cx - 1)
                else:
                    # Sometimes move in random direction for twisty paths
                    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                    dy, dx = random.choice(directions)
                    next_pos = (cy + dy, cx + dx)
                
                ny, nx = next_pos
                
                # Check boundaries and avoid connecting paths (maintain maze structure)
                if (0 < ny < height-1 and 0 < nx < width-1 and
                    grid[ny][nx] == self.cell_types["WALL"]):
                    
                    # Count neighboring path cells
                    path_neighbors = 0
                    for dy, dx in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        if (0 <= ny+dy < height and 0 <= nx+dx < width and
                            grid[ny+dy][nx+dx] == self.cell_types["PATH"] and
                            (ny+dy, nx+dx) != current_pos):
                            path_neighbors += 1
                    
                    # Only add if it won't create loops (maintain maze property)
                    if path_neighbors <= 0 or (ny, nx) == end_pos:
                        grid[ny][nx] = self.cell_types["PATH"]
                        current_pos = (ny, nx)
                    else:
                        # Try a different direction next time
                        continue
                else:
                    # If we can't move there, try a different direction next iteration
                    continue
                
                # If we're at the end, we're done
                if current_pos == target_pos:
                    break

    def _add_maze_branch(self, grid):
        """Add a branch to the existing maze"""
        height, width = grid.shape
        
        # Find a suitable starting point (a path with a wall nearby)
        path_cells = []
        for y in range(1, height-1):
            for x in range(1, width-1):
                if grid[y][x] == self.cell_types["PATH"]:
                    # Check if there's at least one wall two cells away
                    for dy, dx in [(0, 2), (2, 0), (0, -2), (-2, 0)]:
                        ny, nx = y + dy, x + dx
                        if (0 < ny < height-1 and 0 < nx < width-1 and
                            grid[ny][nx] == self.cell_types["WALL"]):
                            # Middle cell must also be a wall
                            if grid[y + dy//2][x + dx//2] == self.cell_types["WALL"]:
                                path_cells.append((y, x, dy, dx))
        
        if not path_cells:
            return
        
        # Choose a random starting point and direction
        y, x, dy, dx = random.choice(path_cells)
        
        # Create the branch
        my, mx = y + dy//2, x + dx//2  # Middle cell
        ny, nx = y + dy, x + dx        # New path cell
        
        grid[my][mx] = self.cell_types["PATH"]
        grid[ny][nx] = self.cell_types["PATH"]
        
        # Continue the branch with DFS
        self._generate_maze_dfs(grid, ny, nx, (0, 0))  # Dummy end pos

    def _add_dead_end(self, grid):
        """Add a dead-end branch to the maze"""
        height, width = grid.shape
        
        # Find path cells with at least one adjacent wall
        path_cells = []
        for y in range(1, height-1):
            for x in range(1, width-1):
                if grid[y][x] == self.cell_types["PATH"]:
                    for dy, dx in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        ny, nx = y + dy, x + dx
                        if (0 < ny < height-1 and 0 < nx < width-1 and
                            grid[ny][nx] == self.cell_types["WALL"]):
                            path_cells.append((y, x, dy, dx))
        
        if not path_cells:
            return
        
        # Choose a random cell and direction
        y, x, dy, dx = random.choice(path_cells)
        
        # Create the dead end
        ny, nx = y + dy, x + dx
        grid[ny][nx] = self.cell_types["PATH"]