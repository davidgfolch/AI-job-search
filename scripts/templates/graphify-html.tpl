<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>graphify - __TITLE__</title>
<script src="https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js"
        integrity="sha384-Ux6phic9PEHJ38YtrijhkzyJ8yQlH8i/+buBR8s3mAZOJrP1gwyvAcIYl3GWtpX1"
        crossorigin="anonymous"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0f0f1a; color: #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; display: flex; height: 100vh; overflow: hidden; }
  #graph { flex: 1; }
  #sidebar { width: 280px; background: #1a1a2e; border-left: 1px solid #2a2a4e; display: flex; flex-direction: column; overflow: hidden; }
  #search-wrap { padding: 12px; border-bottom: 1px solid #2a2a4e; }
  #search { width: 100%; background: #0f0f1a; border: 1px solid #3a3a5e; color: #e0e0e0; padding: 7px 10px; border-radius: 6px; font-size: 13px; outline: none; }
  #search:focus { border-color: #4E79A7; }
  #search-results { max-height: 140px; overflow-y: auto; padding: 4px 12px; border-bottom: 1px solid #2a2a4e; display: none; }
  .search-item { padding: 4px 6px; cursor: pointer; border-radius: 4px; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .search-item:hover { background: #2a2a4e; }
  #info-panel { padding: 14px; border-bottom: 1px solid #2a2a4e; min-height: 140px; }
  #info-panel h3 { font-size: 13px; color: #aaa; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em; }
  #info-content { font-size: 13px; color: #ccc; line-height: 1.6; }
  #info-content .field { margin-bottom: 5px; }
  #info-content .field b { color: #e0e0e0; }
  #info-content .empty { color: #555; font-style: italic; }
  .neighbor-link { display: block; padding: 2px 6px; margin: 2px 0; border-radius: 3px; cursor: pointer; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border-left: 3px solid #333; }
  .neighbor-link:hover { background: #2a2a4e; }
  #neighbors-list { max-height: 160px; overflow-y: auto; margin-top: 4px; }
  #legend-wrap { flex: 1; overflow-y: auto; padding: 12px; }
  #legend-wrap h3 { font-size: 13px; color: #aaa; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.05em; }
  .legend-module { display: flex; align-items: center; gap: 8px; padding: 8px 0 4px; margin-top: 4px; cursor: pointer; border-radius: 4px; font-size: 12px; font-weight: 700; color: #e0e0e0; border-top: 1px solid #2a2a4e; }
  .legend-module:first-child { border-top: none; }
  .legend-module:hover { background: #2a2a4e; padding-left: 4px; }
  .legend-module.dimmed { opacity: 0.35; }
  .legend-module-communities { padding-left: 10px; }
  .legend-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; cursor: pointer; border-radius: 4px; font-size: 12px; }
  .legend-item:hover { background: #2a2a4e; padding-left: 4px; }
  .legend-item.dimmed { opacity: 0.35; }
  .legend-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
  .legend-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .legend-count { color: #666; font-size: 11px; }
  #stats { padding: 10px 14px; border-top: 1px solid #2a2a4e; font-size: 11px; color: #555; }
  #legend-controls { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding: 4px 0; }
  #legend-controls label { display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 12px; color: #aaa; user-select: none; }
  #legend-controls label:hover { color: #e0e0e0; }
  .legend-cb, #select-all-cb { appearance: none; -webkit-appearance: none; width: 14px; height: 14px; border: 1.5px solid #3a3a5e; border-radius: 3px; background: #0f0f1a; cursor: pointer; position: relative; flex-shrink: 0; }
  .legend-cb:checked, #select-all-cb:checked { background: #4E79A7; border-color: #4E79A7; }
  .legend-cb:checked::after, #select-all-cb:checked::after { content: ''; position: absolute; left: 3.5px; top: 1px; width: 4px; height: 7px; border: solid #fff; border-width: 0 2px 2px 0; transform: rotate(45deg); }
  #external-cb:checked { background: #77778a; border-color: #77778a; }
  .legend-ext { font-size: 11px; color: #666; font-style: italic; margin-top: 6px; }
  #select-all-cb:indeterminate { background: #4E79A7; border-color: #4E79A7; }
  #select-all-cb:indeterminate::after { content: ''; position: absolute; left: 2px; top: 5px; width: 8px; height: 2px; background: #fff; border: none; transform: none; }
</style>
</head>
<body>
<div id="graph"></div>
<div id="sidebar">
  <div id="search-wrap">
    <input id="search" type="text" placeholder="Search nodes..." autocomplete="off">
    <div id="search-results"></div>
  </div>
  <div id="info-panel">
    <h3>Node Info</h3>
    <div id="info-content"><span class="empty">Click a node to inspect it</span></div>
  </div>
  <div id="legend-wrap">
    <h3>Communities by module</h3>
    <div id="legend-controls">
      <label><input type="checkbox" id="select-all-cb" checked onchange="toggleAllCommunities(!this.checked)">Select All</label>
      <label><input type="checkbox" id="external-cb" class="legend-cb" onchange="toggleExternal()">Show external/library nodes</label>
    </div>
    <div id="legend"></div>
  </div>
  <div id="stats">__STATS__</div>
</div>
<script>
const RAW_NODES = __NODES_JSON__;
const RAW_EDGES = __EDGES_JSON__;
const MODULES = __MODULES_JSON__;
const TOTAL_COMMUNITIES = __TOTAL_COMMUNITIES__;

// HTML-escape helper — prevents XSS when injecting graph data into innerHTML
function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

// External/library nodes have no source file (imported modules, symbols, type annotations)
const EXTERNAL_COLOR = '#77778a';
function isExternal(n) { return !n.source_file; }

// Build vis datasets
const nodesDS = new vis.DataSet(RAW_NODES.map(n => {
  const ext = isExternal(n);
  return {
    id: n.id, label: n.label,
    color: ext ? { background: EXTERNAL_COLOR, border: EXTERNAL_COLOR, highlight: { background: '#ffffff', border: EXTERNAL_COLOR } } : n.color,
    size: n.size,
    font: n.font, title: n.title,
    _community: n.community, _community_name: n.community_name,
    _module: n.module, _source_file: n.source_file, _file_type: n.file_type, _degree: n.degree,
    _external: ext,
  };
}));

const edgesDS = new vis.DataSet(RAW_EDGES.map((e, i) => ({
  id: i, from: e.from, to: e.to,
  label: '',
  title: e.title,
  dashes: e.dashes,
  width: e.width,
  color: e.color,
  arrows: { to: { enabled: true, scaleFactor: 0.5 } },
})));

const container = document.getElementById('graph');
const network = new vis.Network(container, { nodes: nodesDS, edges: edgesDS }, {
  physics: {
    enabled: true,
    solver: 'forceAtlas2Based',
    forceAtlas2Based: {
      gravitationalConstant: -60,
      centralGravity: 0.005,
      springLength: 120,
      springConstant: 0.08,
      damping: 0.4,
      avoidOverlap: 0.8,
    },
    stabilization: { iterations: 200, fit: true },
  },
  interaction: {
    hover: true,
    tooltipDelay: 100,
    hideEdgesOnDrag: true,
    navigationButtons: false,
    keyboard: false,
  },
  nodes: { shape: 'dot', borderWidth: 1.5 },
  edges: { smooth: { type: 'continuous', roundness: 0.2 }, selectionWidth: 3 },
});

network.once('stabilizationIterationsDone', () => {
  network.setOptions({ physics: { enabled: false } });
});

function showInfo(nodeId) {
  const n = nodesDS.get(nodeId);
  if (!n) return;
  const neighborIds = network.getConnectedNodes(nodeId);
  const neighborItems = neighborIds.map(nid => {
    const nb = nodesDS.get(nid);
    const color = nb ? nb.color.background : '#555';
    return `<span class="neighbor-link" style="border-left-color:${esc(color)}" data-nid="${esc(nid)}">${esc(nb ? nb.label : nid)}</span>`;
  }).join('');
  document.getElementById('info-content').innerHTML = `
    <div class="field"><b>${esc(n.label)}</b>${n._external ? ' <span class="legend-ext">(external)</span>' : ''}</div>
    <div class="field">Module: ${esc(n._module || '-')}</div>
    <div class="field">Type: ${esc(n._file_type || 'unknown')}</div>
    <div class="field">Community: ${esc(n._community_name)}</div>
    <div class="field">Source: ${esc(n._source_file || '-')}</div>
    <div class="field">Degree: ${n._degree}</div>
    ${neighborIds.length ? `<div class="field" style="margin-top:8px;color:#aaa;font-size:11px">Neighbors (${neighborIds.length})</div><div id="neighbors-list">${neighborItems}</div>` : ''}
  `;
}

function focusNode(nodeId) {
  network.focus(nodeId, { scale: 1.4, animation: true });
  network.selectNodes([nodeId]);
  showInfo(nodeId);
}

document.addEventListener('click', e => {
  const el = e.target.closest('.neighbor-link');
  if (el && el.dataset.nid !== undefined) focusNode(el.dataset.nid);
});

let hoveredNodeId = null;
network.on('hoverNode', params => {
  hoveredNodeId = params.node;
  container.style.cursor = 'pointer';
});
network.on('blurNode', () => {
  hoveredNodeId = null;
  container.style.cursor = 'default';
});
container.addEventListener('click', () => {
  if (hoveredNodeId !== null) {
    showInfo(hoveredNodeId);
    network.selectNodes([hoveredNodeId]);
  }
});
network.on('click', params => {
  if (params.nodes.length > 0) {
    showInfo(params.nodes[0]);
  } else if (hoveredNodeId === null) {
    document.getElementById('info-content').innerHTML = '<span class="empty">Click a node to inspect it</span>';
  }
});

const searchInput = document.getElementById('search');
const searchResults = document.getElementById('search-results');
searchInput.addEventListener('input', () => {
  const q = searchInput.value.toLowerCase().trim();
  searchResults.innerHTML = '';
  if (!q) { searchResults.style.display = 'none'; return; }
  const matches = RAW_NODES.filter(n => n.label.toLowerCase().includes(q) && !isNodeHidden(n)).slice(0, 20);
  if (!matches.length) { searchResults.style.display = 'none'; return; }
  searchResults.style.display = 'block';
  matches.forEach(n => {
    const el = document.createElement('div');
    el.className = 'search-item';
    el.textContent = n.label;
    el.style.borderLeft = `3px solid ${n.color.background}`;
    el.style.paddingLeft = '8px';
    el.onclick = () => {
      network.focus(n.id, { scale: 1.5, animation: true });
      network.selectNodes([n.id]);
      showInfo(n.id);
      searchResults.style.display = 'none';
      searchInput.value = '';
    };
    searchResults.appendChild(el);
  });
});
document.addEventListener('click', e => {
  if (!searchResults.contains(e.target) && e.target !== searchInput)
    searchResults.style.display = 'none';
});

const hiddenCommunities = new Set();
const selectAllCb = document.getElementById('select-all-cb');
const externalCb = document.getElementById('external-cb');

function cidsForModule(moduleName) {
  const m = MODULES.find(x => x.module === moduleName);
  return m ? m.communities.map(c => c.cid) : [];
}

function isNodeHidden(n) {
  return hiddenCommunities.has(n.community) || (isExternal(n) && !externalCb.checked);
}

function refreshNodes() {
  const updates = RAW_NODES.map(n => ({ id: n.id, hidden: isNodeHidden(n) }));
  nodesDS.update(updates);
  updateSelectAllState();
}

function toggleExternal() {
  refreshNodes();
}

function updateSelectAllState() {
  const hidden = hiddenCommunities.size;
  selectAllCb.checked = hidden === 0;
  selectAllCb.indeterminate = hidden > 0 && hidden < TOTAL_COMMUNITIES;
}

function syncModuleCheckbox(moduleName) {
  const m = MODULES.find(x => x.module === moduleName);
  if (!m) return;
  const hidden = m.communities.filter(c => hiddenCommunities.has(c.cid)).length;
  const cb = document.querySelector(`[data-module="${moduleName}"] .legend-cb-module`);
  if (!cb) return;
  cb.checked = hidden === 0;
  cb.indeterminate = hidden > 0 && hidden < m.communities.length;
}

function toggleAllCommunities(hide) {
  document.querySelectorAll('.legend-item, .legend-module').forEach(el => {
    hide ? el.classList.add('dimmed') : el.classList.remove('dimmed');
  });
  document.querySelectorAll('.legend-cb').forEach(cb => {
    cb.checked = !hide;
  });
  hiddenCommunities.clear();
  if (hide) MODULES.forEach(m => m.communities.forEach(c => hiddenCommunities.add(c.cid)));
  refreshNodes();
}

const legendEl = document.getElementById('legend');
MODULES.forEach(m => {
  const header = document.createElement('div');
  header.className = 'legend-module';
  header.setAttribute('data-module', m.module);
  const mcb = document.createElement('input');
  mcb.type = 'checkbox';
  mcb.className = 'legend-cb legend-cb-module';
  mcb.checked = true;
  mcb.addEventListener('change', (e) => {
    e.stopPropagation();
    const cids = cidsForModule(m.module);
    cids.forEach(cid => {
      if (mcb.checked) hiddenCommunities.delete(cid); else hiddenCommunities.add(cid);
    });
    document.querySelectorAll(`[data-module="${m.module}"] .legend-item`).forEach(item => {
      const icb = item.querySelector('.legend-cb-community');
      if (icb) { icb.checked = mcb.checked; item.classList.toggle('dimmed', !mcb.checked); }
    });
    refreshNodes();
  });
  header.innerHTML = `<span class="legend-dot" style="background:${m.color}"></span>
    <span class="legend-label">${esc(m.module)}</span>
    <span class="legend-count">${m.count}</span>`;
  header.prepend(mcb);
  header.onclick = (e) => {
    if (e.target === mcb) return;
    mcb.checked = !mcb.checked;
    mcb.dispatchEvent(new Event('change'));
  };
  legendEl.appendChild(header);

  const group = document.createElement('div');
  group.className = 'legend-module-communities';
  group.setAttribute('data-module', m.module);
  m.communities.forEach(c => {
    const item = document.createElement('div');
    item.className = 'legend-item';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.className = 'legend-cb legend-cb-community';
    cb.checked = true;
    cb.addEventListener('change', (e) => {
      e.stopPropagation();
      if (cb.checked) hiddenCommunities.delete(c.cid); else hiddenCommunities.add(c.cid);
      item.classList.toggle('dimmed', !cb.checked);
      refreshNodes();
      syncModuleCheckbox(m.module);
    });
    item.innerHTML = `<span class="legend-dot" style="background:${c.color}"></span>
      <span class="legend-label">${esc(c.label)}</span>
      <span class="legend-count">${c.count}</span>`;
    item.prepend(cb);
    item.onclick = (e) => {
      if (e.target === cb) return;
      cb.checked = !cb.checked;
      cb.dispatchEvent(new Event('change'));
    };
    group.appendChild(item);
  });
  legendEl.appendChild(group);
});

const extCount = RAW_NODES.filter(isExternal).length;
const extStats = document.createElement('span');
extStats.textContent = ` · ${extCount} external`;
document.getElementById('stats').appendChild(extStats);
refreshNodes();
</script>
</body>
</html>
