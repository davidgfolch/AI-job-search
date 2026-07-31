const fs = require('fs');
const html = fs.readFileSync('graphify-out/graph.html', 'utf8');

const placeholders = ['__NODES_JSON__', '__EDGES_JSON__', '__MODULES_JSON__', '__TITLE__', '__STATS__', '__TOTAL_COMMUNITIES__']
  .filter(p => html.includes(p));
if (placeholders.length) { console.error('FAIL: placeholders remain', placeholders); process.exit(1); }

const mNodes = html.match(/const RAW_NODES = (.*);\r?\nconst RAW_EDGES/);
const mModules = html.match(/const MODULES = (.*);\r?\nconst TOTAL_COMMUNITIES/);
if (!mNodes || !mModules) { console.error('FAIL: could not extract JSON'); process.exit(1); }
const RAW_NODES = JSON.parse(mNodes[1]);
const MODULES = JSON.parse(mModules[1]);

const layoutSection = html.match(/\/\/ --- Matrix layout[\s\S]*?\r?\n}\r?\n\r?\n\/\/ Build vis datasets/);
if (!layoutSection) { console.error('FAIL: layout section not found'); process.exit(1); }

function isExternal(n) { return !n.source_file; }
const fn = new Function('RAW_NODES', 'MODULES', 'isExternal',
  layoutSection[0] + '\nconst _pos = computeLayout(); return { pos: _pos, nodeKind, isPrivate, isFile, moduleBands, layerBands, totalHeight, totalWidth };');
const api = fn(RAW_NODES, MODULES, isExternal);

const kinds = {};
RAW_NODES.forEach(n => { kinds[n.id] = api.nodeKind(n); });
const kindCount = {};
Object.values(kinds).forEach(k => { kindCount[k] = (kindCount[k] || 0) + 1; });
console.log('kind counts:', kindCount);

const pos = api.pos;
const missing = RAW_NODES.filter(n => !pos[n.id] || typeof pos[n.id].x !== 'number' || typeof pos[n.id].y !== 'number');
console.log('nodes without numeric position:', missing.length);
if (missing.length) { console.error('FAIL: missing positions'); process.exit(1); }

const internal = RAW_NODES.filter(n => !isExternal(n));
const distinctBands = new Set(internal.map(n => `${n.module}\u0001${(() => { const d = (n.source_file || '').split('/').slice(0, -1); return d.length ? d.slice(0, 2).join('/') : '(root)'; })()}`));
console.log('layerBands:', api.layerBands.length, '| distinct module/layer:', distinctBands.size);
console.log('moduleBands:', api.moduleBands.length, '| totalHeight:', api.totalHeight, '| totalWidth:', api.totalWidth);
console.log('aspect ratio (W/H):', (api.totalWidth / api.totalHeight).toFixed(2));
if (api.layerBands.length !== distinctBands.size) { console.error('FAIL: band count mismatch'); process.exit(1); }
if (api.moduleBands.length !== new Set(internal.map(n => n.module)).size) { console.error('FAIL: module band count mismatch'); process.exit(1); }

const privateCount = RAW_NODES.filter(api.isPrivate).length;
const hiddenOnLoad = RAW_NODES.filter(n => isExternal(n) || api.isFile(n) || api.isPrivate(n)).length;
console.log('private:', privateCount, '| file:', RAW_NODES.filter(api.isFile).length, '| hidden on load:', hiddenOnLoad);
if (privateCount !== 242 || kindCount.file !== 631 || kindCount.external !== 643) { console.error('FAIL: counts'); process.exit(1); }

const xs = Object.values(pos).map(p => p.x), ys = Object.values(pos).map(p => p.y);
const extX = Math.max(...RAW_NODES.filter(isExternal).map(n => pos[n.id].x));
const intMaxX = Math.max(...internal.map(n => pos[n.id].x));
console.log('internal max x:', intMaxX.toFixed(0), '| external x:', extX.toFixed(0));
if (extX <= intMaxX) { console.error('FAIL: external column not rightmost'); process.exit(1); }

const ratio = api.totalWidth / api.totalHeight;
if (ratio < 0.8 || ratio > 1.25) { console.error('FAIL: aspect not near-square', ratio); process.exit(1); }
console.log('ALL CHECKS PASSED');
