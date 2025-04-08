import os
import json
import time
import threading
from typing import Dict, List, Any, Optional
import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory

class MemoryDashboard:
    """
    Web dashboard for visualizing and exploring Aina's memories.
    Provides a web interface for memory visualization, search, and analysis.
    """
    
    def __init__(self, 
                memory_manager, 
                host: str = "127.0.0.1", 
                port: int = 5000,
                template_dir: Optional[str] = None,
                static_dir: Optional[str] = None):
        """
        Initialize memory dashboard.
        
        Args:
            memory_manager: MemoryManager instance
            host: Host address to bind
            port: Port to listen on
            template_dir: Custom template directory
            static_dir: Custom static files directory
        """
        self.memory_manager = memory_manager
        self.host = host
        self.port = port
        
        # Setup Flask app
        if template_dir is None:
            # Use default template directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_dir = os.path.join(current_dir, "templates")
            # Create if it doesn't exist
            os.makedirs(template_dir, exist_ok=True)
        
        if static_dir is None:
            # Use default static directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            static_dir = os.path.join(current_dir, "static")
            # Create if it doesn't exist
            os.makedirs(static_dir, exist_ok=True)
        
        # Save paths
        self.template_dir = template_dir
        self.static_dir = static_dir
        
        # Create Flask app
        self.app = Flask(
            "Aina Memory Dashboard",
            template_folder=template_dir,
            static_folder=static_dir
        )
        
        # Setup routes
        self._setup_routes()
        
        # Server thread
        self.server_thread = None
        self.running = False
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Render the dashboard home page."""
            return render_template('index.html')
        
        @self.app.route('/api/memory/stats')
        def memory_stats():
            """Get memory statistics."""
            try:
                stats = {
                    'core': self.memory_manager.storage.count('core'),
                    'episodic': self.memory_manager.storage.count('episodic'),
                    'semantic': self.memory_manager.storage.count('semantic'),
                    'personal': self.memory_manager.storage.count('personal')
                }
                return jsonify(stats)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory/search')
        def memory_search():
            """Search memories."""
            query = request.args.get('query', '')
            memory_type = request.args.get('type', 'all')
            limit = int(request.args.get('limit', 10))
            
            try:
                results = self.memory_manager.search_memories(
                    query=query,
                    memory_types=memory_type if memory_type != 'all' else 'all',
                    limit=limit
                )
                
                # Format for display
                formatted_results = []
                for result in results:
                    # Format timestamp if available
                    timestamp = result.get('metadata', {}).get('timestamp')
                    if timestamp:
                        timestamp = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    
                    formatted_results.append({
                        'id': result.get('id', ''),
                        'text': result.get('text', ''),
                        'memory_type': result.get('memory_type', ''),
                        'similarity': result.get('similarity', 0),
                        'timestamp': timestamp,
                        'importance': result.get('metadata', {}).get('importance', 0)
                    })
                
                return jsonify(formatted_results)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory/get/<memory_type>/<memory_id>')
        def get_memory(memory_type, memory_id):
            """Get a specific memory by ID."""
            try:
                memory = self.memory_manager.retrieve_memory(memory_type, memory_id)
                
                if memory:
                    # Format timestamp if available
                    if 'metadata' in memory and 'timestamp' in memory['metadata']:
                        memory['metadata']['timestamp_formatted'] = datetime.datetime.fromtimestamp(
                            memory['metadata']['timestamp']
                        ).strftime('%Y-%m-%d %H:%M:%S')
                    
                    return jsonify(memory)
                else:
                    return jsonify({'error': 'Memory not found'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory/types/<memory_type>')
        def get_memory_by_type(memory_type):
            """Get memories by type."""
            limit = int(request.args.get('limit', 50))
            
            try:
                memories = self.memory_manager.retrieve_all_memories(memory_type, limit)
                
                # Format for display
                formatted_memories = []
                for memory in memories:
                    # Format timestamp if available
                    timestamp = memory.get('metadata', {}).get('timestamp')
                    if timestamp:
                        timestamp = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    
                    formatted_memories.append({
                        'id': memory.get('id', ''),
                        'text': memory.get('text', ''),
                        'timestamp': timestamp,
                        'importance': memory.get('metadata', {}).get('importance', 0)
                    })
                
                return jsonify(formatted_memories)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/users')
        def get_users():
            """Get list of users with memories."""
            try:
                # Get all personal memories
                personal_memories = self.memory_manager.retrieve_all_memories('personal', 1000)
                
                # Extract unique user IDs
                user_ids = set()
                for memory in personal_memories:
                    user_id = memory.get('metadata', {}).get('user_id')
                    if user_id:
                        user_ids.add(user_id)
                
                # Get info for each user
                users = []
                for user_id in user_ids:
                    summary = self.memory_manager.personal_memory.get_user_summary(user_id, max_length=100)
                    memories_count = len(self.memory_manager.get_user_memories(user_id, limit=1000))
                    
                    users.append({
                        'id': user_id,
                        'summary': summary,
                        'memories_count': memories_count
                    })
                
                return jsonify(users)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/user/<user_id>')
        def get_user_profile(user_id):
            """Get a user profile."""
            try:
                profile = self.memory_manager.personal_memory.get_user_profile(user_id)
                
                # Format timestamps in interaction summaries
                if 'interaction_summaries' in profile:
                    for summary in profile['interaction_summaries']:
                        if 'timestamp' in summary:
                            summary['timestamp_formatted'] = datetime.datetime.fromtimestamp(
                                summary['timestamp']
                            ).strftime('%Y-%m-%d %H:%M:%S')
                
                return jsonify(profile)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/reflections')
        def get_reflections():
            """Get recent reflections."""
            try:
                # Get daily reflections
                daily_reflections = self.memory_manager.reflection.list_reflections('daily', 10)
                
                # Get weekly reflections
                weekly_reflections = self.memory_manager.reflection.list_reflections('weekly', 5)
                
                # Format timestamps
                for reflection in daily_reflections + weekly_reflections:
                    if 'timestamp' in reflection:
                        reflection['timestamp_formatted'] = datetime.datetime.fromtimestamp(
                            reflection['timestamp']
                        ).strftime('%Y-%m-%d %H:%M:%S')
                
                return jsonify({
                    'daily': daily_reflections,
                    'weekly': weekly_reflections
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/reflection/<reflection_id>')
        def get_reflection(reflection_id):
            """Get a specific reflection."""
            try:
                reflection = self.memory_manager.reflection.get_reflection(reflection_id)
                
                if reflection:
                    # Format timestamp
                    if 'timestamp' in reflection:
                        reflection['timestamp_formatted'] = datetime.datetime.fromtimestamp(
                            reflection['timestamp']
                        ).strftime('%Y-%m-%d %H:%M:%S')
                    
                    return jsonify(reflection)
                else:
                    return jsonify({'error': 'Reflection not found'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/backup', methods=['POST'])
        def create_backup():
            """Create a memory backup."""
            try:
                success = self.memory_manager.backup_memories()
                
                if success:
                    return jsonify({'status': 'success', 'message': 'Backup created successfully'})
                else:
                    return jsonify({'status': 'error', 'message': 'Backup failed'}), 500
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
    
    def start(self, open_browser: bool = False):
        """
        Start the dashboard server.
        
        Args:
            open_browser: Whether to open the browser automatically
        """
        if self.running:
            print("Dashboard already running")
            return
        
        # Generate default templates if they don't exist
        self._ensure_templates_exist()
        
        # Create server thread
        self.server_thread = threading.Thread(
            target=self._run_server,
            daemon=True
        )
        
        # Start server
        self.running = True
        self.server_thread.start()
        
        print(f"✅ Memory dashboard started at http://{self.host}:{self.port}")
        
        # Open browser if requested
        if open_browser:
            self._open_browser()
    
    def _run_server(self):
        """Run the Flask server."""
        self.app.run(
            host=self.host,
            port=self.port,
            debug=False,
            use_reloader=False
        )
    
    def stop(self):
        """Stop the dashboard server."""
        self.running = False
        # Flask doesn't provide a clean way to stop the server from another thread
        # This is a workaround that works in most cases
        try:
            import requests
            requests.get(f"http://{self.host}:{self.port}/shutdown")
        except:
            pass
        
        print("Dashboard stopped")
    
    def _open_browser(self):
        """Open the dashboard in the default browser."""
        import webbrowser
        webbrowser.open(f"http://{self.host}:{self.port}")
    
    def _ensure_templates_exist(self):
        """Ensure the default templates exist."""
        # Create index.html if it doesn't exist
        index_path = os.path.join(self.template_dir, "index.html")
        if not os.path.exists(index_path):
            with open(index_path, "w") as f:
                f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aina Memory Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">Aina Memory Dashboard</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link active" href="#" id="nav-overview">Overview</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#" id="nav-memory-search">Search</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#" id="nav-users">Users</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#" id="nav-reflections">Reflections</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <!-- Overview Section -->
        <div id="section-overview" class="dashboard-section active">
            <h2>Memory Overview</h2>
            <div class="row mt-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5>Memory Statistics</h5>
                        </div>
                        <div class="card-body">
                            <div id="memory-stats-chart" style="height: 300px;"></div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5>Recent Activities</h5>
                        </div>
                        <div class="card-body">
                            <div id="recent-activities"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h5>Memory Management</h5>
                            <button id="create-backup-btn" class="btn btn-primary btn-sm">Create Backup</button>
                        </div>
                        <div class="card-body">
                            <div id="backup-status"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Memory Search Section -->
        <div id="section-memory-search" class="dashboard-section">
            <h2>Memory Search</h2>
            <div class="card">
                <div class="card-body">
                    <div class="row mb-3">
                        <div class="col-md-8">
                            <input type="text" id="search-query" class="form-control" placeholder="Search memories...">
                        </div>
                        <div class="col-md-3">
                            <select id="memory-type-filter" class="form-select">
                                <option value="all">All Types</option>
                                <option value="core">Core</option>
                                <option value="episodic">Episodic</option>
                                <option value="semantic">Semantic</option>
                                <option value="personal">Personal</option>
                            </select>
                        </div>
                        <div class="col-md-1">
                            <button id="search-btn" class="btn btn-primary w-100">Search</button>
                        </div>
                    </div>
                </div>
            </div>
            <div class="mt-4">
                <div id="search-results"></div>
            </div>
        </div>

        <!-- Users Section -->
        <div id="section-users" class="dashboard-section">
            <h2>Users</h2>
            <div class="row">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h5>User List</h5>
                        </div>
                        <div class="card-body">
                            <div id="user-list"></div>
                        </div>
                    </div>
                </div>
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header">
                            <h5>User Profile</h5>
                        </div>
                        <div class="card-body">
                            <div id="user-profile">
                                <p class="text-muted">Select a user to view their profile</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Reflections Section -->
        <div id="section-reflections" class="dashboard-section">
            <h2>Memory Reflections</h2>
            <div class="row">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h5>Recent Reflections</h5>
                        </div>
                        <div class="card-body">
                            <ul class="nav nav-tabs" id="reflectionTabs" role="tablist">
                                <li class="nav-item" role="presentation">
                                    <button class="nav-link active" id="daily-tab" data-bs-toggle="tab" 
                                            data-bs-target="#daily" type="button" role="tab">Daily</button>
                                </li>
                                <li class="nav-item" role="presentation">
                                    <button class="nav-link" id="weekly-tab" data-bs-toggle="tab" 
                                            data-bs-target="#weekly" type="button" role="tab">Weekly</button>
                                </li>
                            </ul>
                            <div class="tab-content mt-3" id="reflectionTabContent">
                                <div class="tab-pane fade show active" id="daily" role="tabpanel">
                                    <div id="daily-reflections-list"></div>
                                </div>
                                <div class="tab-pane fade" id="weekly" role="tabpanel">
                                    <div id="weekly-reflections-list"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header">
                            <h5>Reflection Details</h5>
                        </div>
                        <div class="card-body">
                            <div id="reflection-details">
                                <p class="text-muted">Select a reflection to view details</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
    <script src="/static/js/dashboard.js"></script>
</body>
</html>
""")
            
            # Create CSS directory and file
            css_dir = os.path.join(self.static_dir, "css")
            os.makedirs(css_dir, exist_ok=True)
            
            css_path = os.path.join(css_dir, "style.css")
            if not os.path.exists(css_path):
                with open(css_path, "w") as f:
                    f.write("""
.dashboard-section {
    display: none;
}

.dashboard-section.active {
    display: block;
}

.memory-card {
    margin-bottom: 15px;
    border-left: 4px solid #6c757d;
}

.memory-card.core {
    border-left-color: #0d6efd;
}

.memory-card.episodic {
    border-left-color: #198754;
}

.memory-card.semantic {
    border-left-color: #dc3545;
}

.memory-card.personal {
    border-left-color: #6f42c1;
}

.importance-badge {
    position: absolute;
    top: 10px;
    right: 10px;
}

.user-card {
    cursor: pointer;
    transition: background-color 0.2s;
}

.user-card:hover {
    background-color: #f8f9fa;
}

.user-card.active {
    background-color: #e9ecef;
}

.reflection-item {
    cursor: pointer;
    padding: 10px;
    border-bottom: 1px solid #dee2e6;
    transition: background-color 0.2s;
}

.reflection-item:hover {
    background-color: #f8f9fa;
}

.reflection-item.active {
    background-color: #e9ecef;
}

#create-backup-btn {
    transition: all 0.3s;
}

#create-backup-btn.loading {
    pointer-events: none;
    opacity: 0.7;
}
""")
            
            # Create JS directory and file
            js_dir = os.path.join(self.static_dir, "js")
            os.makedirs(js_dir, exist_ok=True)
            
            js_path = os.path.join(js_dir, "dashboard.js")
            if not os.path.exists(js_path):
                with open(js_path, "w") as f:
                    f.write("""
document.addEventListener('DOMContentLoaded', function() {
    // Navigation
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Update active nav link
            document.querySelectorAll('.navbar-nav .nav-link').forEach(l => {
                l.classList.remove('active');
            });
            this.classList.add('active');
            
            // Show corresponding section
            const sectionId = this.id.replace('nav-', 'section-');
            document.querySelectorAll('.dashboard-section').forEach(section => {
                section.classList.remove('active');
            });
            document.getElementById(sectionId).classList.add('active');
            
            // Load section data
            if (sectionId === 'section-overview') {
                loadOverviewData();
            } else if (sectionId === 'section-users') {
                loadUsers();
            } else if (sectionId === 'section-reflections') {
                loadReflections();
            }
        });
    });
    
    // Search functionality
    document.getElementById('search-btn').addEventListener('click', function() {
        const query = document.getElementById('search-query').value;
        const memoryType = document.getElementById('memory-type-filter').value;
        
        if (query.trim()) {
            searchMemories(query, memoryType);
        }
    });
    
    // Enter key in search box
    document.getElementById('search-query').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            document.getElementById('search-btn').click();
        }
    });
    
    // Backup functionality
    document.getElementById('create-backup-btn').addEventListener('click', createBackup);
    
    // Load initial data
    loadOverviewData();
});

// Load overview data
function loadOverviewData() {
    // Load memory stats
    fetch('/api/memory/stats')
        .then(response => response.json())
        .then(data => {
            renderMemoryStats(data);
            
            // Get recent episodic memories for activities
            return fetch('/api/memory/types/episodic?limit=10');
        })
        .then(response => response.json())
        .then(data => {
            renderRecentActivities(data);
        })
        .catch(error => {
            console.error('Error loading overview data:', error);
        });
}

// Render memory statistics chart
function renderMemoryStats(stats) {
    const memoryTypes = Object.keys(stats);
    const memoryCounts = Object.values(stats);
    
    const options = {
        series: [{
            name: 'Memories',
            data: memoryCounts
        }],
        chart: {
            type: 'bar',
            height: 300
        },
        plotOptions: {
            bar: {
                borderRadius: 4,
                horizontal: false,
                distributed: true
            }
        },
        dataLabels: {
            enabled: false
        },
        xaxis: {
            categories: memoryTypes.map(type => type.charAt(0).toUpperCase() + type.slice(1))
        },
        colors: ['#0d6efd', '#198754', '#dc3545', '#6f42c1']
    };
    
    const chart = new ApexCharts(document.getElementById('memory-stats-chart'), options);
    chart.render();
}

// Render recent activities
function renderRecentActivities(memories) {
    const container = document.getElementById('recent-activities');
    container.innerHTML = '';
    
    if (memories.length === 0) {
        container.innerHTML = '<p class="text-muted">No recent activities found</p>';
        return;
    }
    
    const list = document.createElement('div');
    list.className = 'list-group';
    
    memories.forEach(memory => {
        const item = document.createElement('div');
        item.className = 'list-group-item list-group-item-action';
        
        const title = document.createElement('div');
        title.className = 'd-flex justify-content-between';
        
        const text = document.createElement('h6');
        text.className = 'mb-1';
        text.textContent = memory.text.length > 60 ? memory.text.substring(0, 60) + '...' : memory.text;
        
        const time = document.createElement('small');
        time.textContent = memory.timestamp || 'Unknown time';
        
        title.appendChild(text);
        title.appendChild(time);
        item.appendChild(title);
        
        list.appendChild(item);
    });
    
    container.appendChild(list);
}

// Search memories
function searchMemories(query, memoryType) {
    const resultsContainer = document.getElementById('search-results');
    resultsContainer.innerHTML = '<p class="text-center"><i class="fas fa-spinner fa-spin"></i> Searching...</p>';
    
    fetch(`/api/memory/search?query=${encodeURIComponent(query)}&type=${memoryType}&limit=20`)
        .then(response => response.json())
        .then(data => {
            resultsContainer.innerHTML = '';
            
            if (data.error) {
                resultsContainer.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                return;
            }
            
            if (data.length === 0) {
                resultsContainer.innerHTML = '<div class="alert alert-info">No results found</div>';
                return;
            }
            
            data.forEach(memory => {
                const card = document.createElement('div');
                card.className = `card memory-card mb-3 ${memory.memory_type}`;
                
                const cardBody = document.createElement('div');
                cardBody.className = 'card-body position-relative';
                
                const importance = Math.round(memory.importance * 100) || 0;
                const importanceBadge = document.createElement('span');
                importanceBadge.className = `badge importance-badge bg-${getImportanceColor(memory.importance)}`;
                importanceBadge.textContent = `${importance}%`;
                cardBody.appendChild(importanceBadge);
                
                const title = document.createElement('h5');
                title.className = 'card-title';
                title.textContent = `${memory.memory_type.charAt(0).toUpperCase() + memory.memory_type.slice(1)} Memory`;
                cardBody.appendChild(title);
                
                const text = document.createElement('p');
                text.className = 'card-text';
                text.textContent = memory.text;
                cardBody.appendChild(text);
                
                if (memory.timestamp) {
                    const timestamp = document.createElement('div');
                    timestamp.className = 'text-muted small';
                    timestamp.textContent = memory.timestamp;
                    cardBody.appendChild(timestamp);
                }
                
                card.appendChild(cardBody);
                resultsContainer.appendChild(card);
            });
        })
        .catch(error => {
            console.error('Error searching memories:', error);
            resultsContainer.innerHTML = `<div class="alert alert-danger">Error searching memories: ${error.message}</div>`;
        });
}

// Load users data
function loadUsers() {
    const userList = document.getElementById('user-list');
    userList.innerHTML = '<p class="text-center">Loading users...</p>';
    
    fetch('/api/users')
        .then(response => response.json())
        .then(data => {
            userList.innerHTML = '';
            
            if (data.error) {
                userList.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                return;
            }
            
            if (data.length === 0) {
                userList.innerHTML = '<p class="text-muted">No users found</p>';
                return;
            }
            
            data.forEach(user => {
                const card = document.createElement('div');
                card.className = 'card user-card mb-2';
                card.setAttribute('data-user-id', user.id);
                
                const cardBody = document.createElement('div');
                cardBody.className = 'card-body py-2';
                
                const title = document.createElement('h6');
                title.className = 'card-title mb-1';
                title.textContent = `User ${user.id}`;
                cardBody.appendChild(title);
                
                const memories = document.createElement('div');
                memories.className = 'small text-muted';
                memories.textContent = `${user.memories_count} memories`;
                cardBody.appendChild(memories);
                
                card.appendChild(cardBody);
                userList.appendChild(card);
                
                // Add click event
                card.addEventListener('click', function() {
                    // Remove active class from all cards
                    document.querySelectorAll('.user-card').forEach(c => {
                        c.classList.remove('active');
                    });
                    
                    // Add active class to clicked card
                    this.classList.add('active');
                    
                    // Load user profile
                    loadUserProfile(user.id);
                });
            });
        })
        .catch(error => {
            console.error('Error loading users:', error);
            userList.innerHTML = `<div class="alert alert-danger">Error loading users: ${error.message}</div>`;
        });
}

// Load user profile
function loadUserProfile(userId) {
    const profileContainer = document.getElementById('user-profile');
    profileContainer.innerHTML = '<p class="text-center">Loading profile...</p>';
    
    fetch(`/api/user/${userId}`)
        .then(response => response.json())
        .then(data => {
            profileContainer.innerHTML = '';
            
            if (data.error) {
                profileContainer.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                return;
            }
            
            // Create profile sections
            const sections = [
                { title: 'Traits', data: data.traits || [] },
                { title: 'Preferences', data: data.preferences || [] },
                { title: 'Information', data: data.info || [] },
                { title: 'Recent Interactions', data: data.interaction_summaries || [] }
            ];
            
            sections.forEach(section => {
                if (section.data.length > 0) {
                    const sectionDiv = document.createElement('div');
                    sectionDiv.className = 'mb-4';
                    
                    const title = document.createElement('h5');
                    title.textContent = section.title;
                    sectionDiv.appendChild(title);
                    
                    const list = document.createElement('ul');
                    list.className = 'list-group';
                    
                    section.data.forEach(item => {
                        const listItem = document.createElement('li');
                        listItem.className = 'list-group-item';
                        
                        // For interaction summaries, show date if available
                        if (section.title === 'Recent Interactions' && item.timestamp_formatted) {
                            const date = document.createElement('small');
                            date.className = 'float-end text-muted';
                            date.textContent = item.timestamp_formatted;
                            listItem.appendChild(date);
                        }
                        
                        listItem.appendChild(document.createTextNode(item.text));
                        
                        list.appendChild(listItem);
                    });
                    
                    sectionDiv.appendChild(list);
                    profileContainer.appendChild(sectionDiv);
                }
            });
            
            if (profileContainer.children.length === 0) {
                profileContainer.innerHTML = '<p class="text-muted">No profile information available</p>';
            }
        })
        .catch(error => {
            console.error('Error loading user profile:', error);
            profileContainer.innerHTML = `<div class="alert alert-danger">Error loading profile: ${error.message}</div>`;
        });
}

// Load reflections
function loadReflections() {
    fetch('/api/reflections')
        .then(response => response.json())
        .then(data => {
            // Render daily reflections
            renderReflectionsList(data.daily, 'daily-reflections-list');
            
            // Render weekly reflections
            renderReflectionsList(data.weekly, 'weekly-reflections-list');
        })
        .catch(error => {
            console.error('Error loading reflections:', error);
            document.getElementById('daily-reflections-list').innerHTML = 
                `<div class="alert alert-danger">Error loading reflections: ${error.message}</div>`;
            document.getElementById('weekly-reflections-list').innerHTML = 
                `<div class="alert alert-danger">Error loading reflections: ${error.message}</div>`;
        });
}

// Render reflections list
function renderReflectionsList(reflections, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    if (!reflections || reflections.length === 0) {
        container.innerHTML = '<p class="text-muted">No reflections found</p>';
        return;
    }
    
    reflections.forEach(reflection => {
        const item = document.createElement('div');
        item.className = 'reflection-item';
        item.setAttribute('data-reflection-id', reflection.id);
        
        const title = document.createElement('div');
        title.className = 'fw-bold';
        title.textContent = reflection.file_name || `Reflection ${reflection.id.substring(0, 8)}`;
        
        const date = document.createElement('div');
        date.className = 'small text-muted';
        date.textContent = reflection.timestamp_formatted || 'Unknown date';
        
        item.appendChild(title);
        item.appendChild(date);
        container.appendChild(item);
        
        // Add click event
        item.addEventListener('click', function() {
            // Remove active class from all items
            document.querySelectorAll('.reflection-item').forEach(i => {
                i.classList.remove('active');
            });
            
            // Add active class to clicked item
            this.classList.add('active');
            
            // Load reflection details
            loadReflectionDetails(reflection.id);
        });
    });
}

// Load reflection details
function loadReflectionDetails(reflectionId) {
    const detailsContainer = document.getElementById('reflection-details');
    detailsContainer.innerHTML = '<p class="text-center">Loading reflection...</p>';
    
    fetch(`/api/reflection/${reflectionId}`)
        .then(response => response.json())
        .then(data => {
            detailsContainer.innerHTML = '';
            
            if (data.error) {
                detailsContainer.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                return;
            }
            
            // Date
            const date = document.createElement('div');
            date.className = 'text-muted mb-3';
            date.textContent = data.timestamp_formatted || 'Unknown date';
            detailsContainer.appendChild(date);
            
            // Summary
            if (data.summary) {
                const summaryTitle = document.createElement('h5');
                summaryTitle.textContent = 'Summary';
                detailsContainer.appendChild(summaryTitle);
                
                const summary = document.createElement('div');
                summary.className = 'mb-4';
                summary.textContent = data.summary;
                detailsContainer.appendChild(summary);
            }
            
            // Insights
            if (data.insights && data.insights.length > 0) {
                const insightsTitle = document.createElement('h5');
                insightsTitle.textContent = 'Insights';
                detailsContainer.appendChild(insightsTitle);
                
                const insightsList = document.createElement('ul');
                insightsList.className = 'list-group mb-4';
                
                data.insights.forEach(insight => {
                    const item = document.createElement('li');
                    item.className = 'list-group-item';
                    item.textContent = insight.text;
                    insightsList.appendChild(item);
                });
                
                detailsContainer.appendChild(insightsList);
            }
            
            // Main events
            if (data.main_events && data.main_events.length > 0) {
                const eventsTitle = document.createElement('h5');
                eventsTitle.textContent = 'Key Events';
                detailsContainer.appendChild(eventsTitle);
                
                const eventsList = document.createElement('ul');
                eventsList.className = 'list-group';
                
                data.main_events.forEach(event => {
                    const item = document.createElement('li');
                    item.className = 'list-group-item';
                    
                    const importance = Math.round(event.importance * 100) || 0;
                    const badge = document.createElement('span');
                    badge.className = `badge float-end bg-${getImportanceColor(event.importance)}`;
                    badge.textContent = `${importance}%`;
                    item.appendChild(badge);
                    
                    item.appendChild(document.createTextNode(event.text));
                    eventsList.appendChild(item);
                });
                
                detailsContainer.appendChild(eventsList);
            }
            
            // Memory count
            if (data.memory_count) {
                const memoryCount = document.createElement('div');
                memoryCount.className = 'text-muted mt-3';
                memoryCount.textContent = `Based on ${data.memory_count} memories`;
                detailsContainer.appendChild(memoryCount);
            }
        })
        .catch(error => {
            console.error('Error loading reflection details:', error);
            detailsContainer.innerHTML = `<div class="alert alert-danger">Error loading reflection: ${error.message}</div>`;
        });
}

// Create memory backup
function createBackup() {
    const button = document.getElementById('create-backup-btn');
    const statusContainer = document.getElementById('backup-status');
    
    // Disable button and show loading state
    button.classList.add('loading');
    button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating...';
    statusContainer.innerHTML = '<div class="alert alert-info">Creating backup...</div>';
    
    // Call backup API
    fetch('/api/backup', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            // Reset button
            button.classList.remove('loading');
            button.textContent = 'Create Backup';
            
            // Show status
            if (data.status === 'success') {
                statusContainer.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
            } else {
                statusContainer.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
            }
            
            // Clear status after a delay
            setTimeout(() => {
                statusContainer.innerHTML = '';
            }, 5000);
        })
        .catch(error => {
            console.error('Error creating backup:', error);
            
            // Reset button
            button.classList.remove('loading');
            button.textContent = 'Create Backup';
            
            // Show status
            statusContainer.innerHTML = `<div class="alert alert-danger">Error creating backup: ${error.message}</div>`;
        });
}

// Helper function to get color based on importance
function getImportanceColor(importance) {
    if (!importance) return 'secondary';
    
    if (importance >= 0.8) return 'danger';
    if (importance >= 0.6) return 'warning';
    if (importance >= 0.4) return 'primary';
    if (importance >= 0.2) return 'info';
    return 'secondary';
}
""")