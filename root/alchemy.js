const { useState } = React;

// Icon components
const Home = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
    <polyline points="9 22 9 12 15 12 15 22"/>
  </svg>
);

const HexGame = () => {
  // Hex grid layout - axial coordinates (q, r)
  const TILE_DATA = {
    '0,0': { type: 'home', color: '#8B4513', icon: 'home', resources: {} },
    
    // Ring 1 (immediate neighbors)
    '0,-1': { type: 'plain', color: '#F0E68C', icon: 'plain', resources: { wood: 3, herbs: 1 } },
    '1,-1': { type: 'plain', color: '#F0E68C', icon: 'plain', resources: { stone: 2, iron: 1 } },
    '1,0': { type: 'plain', color: '#F0E68C', icon: 'plain', resources: { wood: 3, herbs: 1 } },
    '0,1': { type: 'plain', color: '#F0E68C', icon: 'plain', resources: { wood: 3, herbs: 1 } },
    '-1,1': { type: 'plain', color: '#F0E68C', icon: 'plain', resources: { stone: 2, iron: 1 } },
    '-1,0': { type: 'plain', color: '#F0E68C', icon: 'plain', resources: { wood: 3, herbs: 1 } },
    
    // Ring 2
    '0,-2': { type: 'forest', color: '#228B22', icon: 'tree', resources: { stone: 2, iron: 1 } },
    '1,-2': { type: 'forest', color: '#228B22', icon: 'tree', resources: { fish: 2, water: 3 } },
    '2,-2': { type: 'forest', color: '#228B22', icon: 'tree', resources: { stone: 2, iron: 1 } },
    '2,-1': { type: 'forest', color: '#228B22', icon: 'tree', resources: { fish: 2, water: 3 } },
    '2,0': { type: 'forest', color: '#228B22', icon: 'tree', resources: { stone: 2, iron: 1 } },
    '1,1': { type: 'forest', color: '#228B22', icon: 'tree', resources: { stone: 2, iron: 1 } },
    '0,2': { type: 'forest', color: '#228B22', icon: 'tree', resources: { stone: 2, iron: 1 } },
    '-1,2': { type: 'forest', color: '#228B22', icon: 'tree', resources: { fish: 2, water: 3 } },
    '-2,2': { type: 'forest', color: '#228B22', icon: 'tree', resources: { stone: 2, iron: 1 } },
    '-2,1': { type: 'forest', color: '#228B22', icon: 'tree', resources: { fish: 2, water: 3 } },
    '-2,0': { type: 'forest', color: '#228B22', icon: 'tree', resources: { stone: 2, iron: 1 } },
    '-1,-1': { type: 'forest', color: '#228B22', icon: 'tree', resources: { stone: 2, iron: 1 } },
    
    // Ring 3
    '0,-3': { type: 'mountain', color: '#CD853F', icon: 'mountain', resources: { wheat: 2 } },
    '1,-3': { type: 'water', color: '#4682B4', icon: 'water', resources: { fish: 2, water: 3 } },
    '2,-3': { type: 'water', color: '#4682B4', icon: 'water', resources: { wheat: 2 } },
    '3,-3': { type: 'mountain', color: '#CD853F', icon: 'mountain', resources: { wheat: 2 } },
    '3,-2': { type: 'water', color: '#4682B4', icon: 'water', resources: { wheat: 2 } },
    '3,-1': { type: 'water', color: '#4682B4', icon: 'water', resources: { wheat: 2 } },
    '3,0': { type: 'mountain', color: '#CD853F', icon: 'mountain', resources: { wheat: 2 } },
    '2,1': { type: 'water', color: '#4682B4', icon: 'water', resources: { wheat: 2 } },
    '1,2': { type: 'water', color: '#4682B4', icon: 'water', resources: { wheat: 2 } },
    '0,3': { type: 'mountain', color: '#CD853F', icon: 'mountain', resources: { wheat: 2 } },
    '-1,3': { type: 'water', color: '#4682B4', icon: 'water', resources: { fish: 2, water: 3 } },
    '-2,3': { type: 'water', color: '#4682B4', icon: 'water', resources: { wheat: 2 } },
    '-3,3': { type: 'mountain', color: '#CD853F', icon: 'mountain', resources: { wheat: 2 } },
    '-3,2': { type: 'water', color: '#4682B4', icon: 'water', resources: { wheat: 2 } },
    '-3,1': { type: 'water', color: '#4682B4', icon: 'water', resources: { wheat: 2 } },
    '-3,0': { type: 'mountain', color: '#CD853F', icon: 'mountain', resources: { wheat: 2 } },
    '-2,-1': { type: 'water', color: '#4682B4', icon: 'water', resources: { wheat: 2 } },
    '-1,-2': { type: 'water', color: '#4682B4', icon: 'water', resources: { wheat: 2 } },
    
    // Ring 4
    '0,-4': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '1,-4': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '2,-4': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '3,-4': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '4,-4': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '4,-3': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '4,-2': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '4,-1': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '4,0': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '3,1': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '2,2': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '1,3': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '0,4': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '-1,4': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '-2,4': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '-3,4': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '-4,4': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '-4,3': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '-4,2': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '-4,1': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '-4,0': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '-3,-1': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '-2,-2': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
    '-1,-3': { type: 'plains', color: '#F0E68C', icon: 'plains', resources: { wheat: 2 } },
  };

  // Movement directions in axial coordinates
  const DIRECTIONS = {
    'N': { q: 0, r: -1 },
    'NE': { q: 1, r: -1 },
    'SE': { q: 1, r: 0 },
    'S': { q: 0, r: 1 },
    'SW': { q: -1, r: 1 },
    'NW': { q: -1, r: 0 },
  };

  const [playerPos, setPlayerPos] = useState({ q: 0, r: 0 });
  const [ap, setAp] = useState(8);
  const [inventory, setInventory] = useState({});
  const [message, setMessage] = useState('Welcome! Move around and gather resources.');

  const showMessage = (msg) => {
    setMessage(msg);
    setTimeout(() => setMessage(''), 3000);
  };

  const move = (direction) => {
    if (ap < 1) {
      showMessage('Not enough AP!');
      return;
    }

    const dir = DIRECTIONS[direction];
    const newPos = { q: playerPos.q + dir.q, r: playerPos.r + dir.r };
    const key = `${newPos.q},${newPos.r}`;

    if (TILE_DATA[key]) {
      setPlayerPos(newPos);
      setAp(ap - 1);
      showMessage(`Moved ${direction}. AP: ${ap - 1}`);
    } else {
      showMessage('Cannot move there!');
    }
  };

  const gather = () => {
    if (ap < 2) {
      showMessage('Not enough AP! (Need 2 AP)');
      return;
    }

    const key = `${playerPos.q},${playerPos.r}`;
    const tile = TILE_DATA[key];

    if (tile.type === 'home') {
      showMessage('Nothing to gather at home base!');
      return;
    }

    const resources = tile.resources;
    if (Object.keys(resources).length === 0) {
      showMessage('Nothing to gather here!');
      return;
    }

    const newInventory = { ...inventory };
    Object.entries(resources).forEach(([resource, amount]) => {
      newInventory[resource] = (newInventory[resource] || 0) + amount;
    });

    setInventory(newInventory);
    setAp(ap - 2);
    
    const resourceStr = Object.entries(resources)
      .map(([r, a]) => `${r} +${a}`)
      .join(', ');
    showMessage(`Gathered: ${resourceStr}`);
  };

  const alchemy = () => {
    if (ap < 2) {
      showMessage('Not enough AP! (Need 2 AP)');
      return;
    }

    if (playerPos.q !== 0 || playerPos.r !== 0) {
      showMessage('Must be at home base to use alchemy!');
      return;
    }

    setAp(ap - 2);
    showMessage('Alchemy performed! (Function not yet implemented)');
  };

  const restoreAP = () => {
    setAp(8);
    showMessage('AP restored to 8!');
  };

  // Hex drawing functions
  const hexToPixel = (q, r, size) => {
    const x = size * (3/2 * q);
    const y = size * (Math.sqrt(3)/2 * q + Math.sqrt(3) * r);
    return { x, y };
  };

  const drawHexagon = (x, y, size) => {
    const points = [];
    for (let i = 0; i < 6; i++) {
      const angle = (Math.PI / 3) * i - Math.PI / 6;
      points.push({
        x: x + size * Math.cos(angle),
        y: y + size * Math.sin(angle)
      });
    }
    return points.map(p => `${p.x},${p.y}`).join(' ');
  };

  const HEX_SIZE = 30;
  const centerX = 400;
  const centerY = 350;

  const currentTile = TILE_DATA[`${playerPos.q},${playerPos.r}`];
  const atHome = playerPos.q === 0 && playerPos.r === 0;
  const canGather = !atHome && ap >= 2 && Object.keys(currentTile.resources).length > 0;
  const canAlchemy = atHome && ap >= 2;

  return (
    <div className="flex flex-col items-center gap-4 p-6 bg-gray-100 min-h-screen">
      <h1 className="text-3xl font-bold text-gray-800">Hexagon Resource Game</h1>
      
      <div className="flex gap-6 text-lg">
        <div className="bg-blue-500 text-white px-4 py-2 rounded-lg font-bold">
          AP: {ap} / 8
        </div>
        <div className="bg-green-500 text-white px-4 py-2 rounded-lg">
          Position: ({playerPos.q}, {playerPos.r})
        </div>
        <div className="bg-purple-500 text-white px-4 py-2 rounded-lg">
          {currentTile.type.charAt(0).toUpperCase() + currentTile.type.slice(1)}
        </div>
      </div>

      {message && (
        <div className="bg-yellow-100 border border-yellow-400 text-yellow-800 px-4 py-2 rounded-lg">
          {message}
        </div>
      )}

      <div className="bg-white p-4 rounded-lg shadow-lg">
        <svg width="800" height="700" className="border-2 border-gray-300 rounded">
          {Object.entries(TILE_DATA).map(([key, tile]) => {
            const [q, r] = key.split(',').map(Number);
            const pos = hexToPixel(q, r, HEX_SIZE);
            const x = centerX + pos.x;
            const y = centerY + pos.y;
            const isPlayer = q === playerPos.q && r === playerPos.r;

            return (
              <g key={key}>
                <polygon
                  points={drawHexagon(x, y, HEX_SIZE)}
                  fill={tile.color}
                  stroke={isPlayer ? '#FF0000' : '#000'}
                  strokeWidth={isPlayer ? 4 : 2}
                  opacity={0.8}
                />
                <text
                  x={x}
                  y={y}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  className="text-xs font-bold"
                  fill="#000"
                >
                  {tile.icon === 'mountain' && 'M'}
                  {tile.icon === 'tree' && 'A'}
                  {tile.icon === 'water' && '~'}
                  {tile.icon === 'home' && 'H'}
                </text>
                {isPlayer && (
                  <circle cx={x} cy={y} r={8} fill="#FF0000" stroke="#FFF" strokeWidth={2} />
                )}
              </g>
            );
          })}
        </svg>
      </div>

      <div className="flex flex-col items-center gap-4">
        <div className="text-lg font-semibold">Movement (1 AP each)</div>
        <div className="grid grid-cols-3 gap-2">
          <div></div>
          <button onClick={() => move('N')} className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded font-bold">
            N
          </button>
          <div></div>
          
          <button onClick={() => move('NW')} className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded font-bold">
            NW
          </button>
          <div className="flex items-center justify-center">
            <Home />
          </div>
          <button onClick={() => move('NE')} className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded font-bold">
            NE
          </button>
          
          <button onClick={() => move('SW')} className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded font-bold">
            SW
          </button>
          <div></div>
          <button onClick={() => move('SE')} className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded font-bold">
            SE
          </button>
          
          <div></div>
          <button onClick={() => move('S')} className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded font-bold">
            S
          </button>
          <div></div>
        </div>
      </div>

      <div className="flex gap-4">
        <button
          onClick={gather}
          disabled={!canGather}
          className={`px-8 py-4 rounded-lg font-bold text-lg ${
            canGather
              ? 'bg-green-600 hover:bg-green-700 text-white'
              : 'bg-gray-400 text-gray-700 cursor-not-allowed'
          }`}
        >
          Gather (2 AP)
        </button>
        
        <button
          onClick={alchemy}
          disabled={!canAlchemy}
          className={`px-8 py-4 rounded-lg font-bold text-lg ${
            canAlchemy
              ? 'bg-purple-600 hover:bg-purple-700 text-white'
              : 'bg-gray-400 text-gray-700 cursor-not-allowed'
          }`}
        >
          Alchemy (2 AP)
        </button>
        
        <button
          onClick={restoreAP}
          className="bg-orange-600 hover:bg-orange-700 text-white px-8 py-4 rounded-lg font-bold text-lg"
        >
          Restore AP
        </button>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-2xl">
        <h2 className="text-2xl font-bold mb-4">Inventory</h2>
        {Object.keys(inventory).length === 0 ? (
          <p className="text-gray-600">No resources yet. Go gather some!</p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(inventory).map(([resource, amount]) => (
              <div key={resource} className="bg-gray-100 p-3 rounded-lg text-center">
                <div className="font-bold capitalize">{resource}</div>
                <div className="text-2xl text-green-600">{amount}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-white p-4 rounded-lg shadow-lg">
        <h3 className="font-bold mb-2">Legend</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded" style={{backgroundColor: '#8B4513'}}></div>
            <span>H - Home Base</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded" style={{backgroundColor: '#228B22'}}></div>
            <span>A - Forest</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded" style={{backgroundColor: '#CD853F'}}></div>
            <span>M - Mountain</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded" style={{backgroundColor: '#4682B4'}}></div>
            <span>~ - Water</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Render the app
ReactDOM.render(<HexGame />, document.getElementById('root'));