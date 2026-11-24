// IndexedDB-backed queue for changes attempted while offline.
// Only mutations are queued. Reads are served by the service worker cache.
// An in-memory fallback keeps the app working if IndexedDB is unavailable.

const DB_NAME = "klb_offline";
const DB_VERSION = 1;
const STORE = "mutations";

let memoryStore = [];
let nextMemoryId = 1;

function open() {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === "undefined") return resolve(null);
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        const store = db.createObjectStore(STORE, { keyPath: "id", autoIncrement: true });
        store.createIndex("createdAt", "createdAt", { unique: false });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export async function enqueue(item) {
  const record = {
    path: item.path,
    method: item.method,
    body: item.body ?? null,
    headers: item.headers ?? {},
    createdAt: Date.now(),
    attempts: 0,
    lastError: null,
  };
  const db = await open();
  if (!db) {
    const row = { ...record, id: nextMemoryId++ };
    memoryStore.push(row);
    return row;
  }
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    const req = tx.objectStore(STORE).add(record);
    let id;
    req.onsuccess = () => { id = req.result; };
    tx.oncomplete = () => { db.close(); resolve({ ...record, id }); };
    tx.onerror = () => { db.close(); reject(tx.error); };
  });
}

export async function all() {
  const db = await open();
  if (!db) return [...memoryStore];
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const req = tx.objectStore(STORE).getAll();
    let rows = [];
    req.onsuccess = () => { rows = req.result || []; };
    tx.oncomplete = () => { db.close(); resolve(rows); };
    tx.onerror = () => { db.close(); reject(tx.error); };
  });
}

// Rows flagged by syncPending() for manual review. No schema change needed:
// conflict metadata is stored as ordinary fields on the existing records.
export async function conflicted() {
  return (await all()).filter((row) => row.conflict);
}

export async function update(id, patch) {
  const db = await open();
  if (!db) {
    const i = memoryStore.findIndex((r) => r.id === id);
    if (i >= 0) memoryStore[i] = { ...memoryStore[i], ...patch };
    return memoryStore[i];
  }
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    const store = tx.objectStore(STORE);
    let merged;
    const getReq = store.get(id);
    getReq.onsuccess = () => {
      if (!getReq.result) return;
      merged = { ...getReq.result, ...patch };
      store.put(merged);
    };
    tx.oncomplete = () => { db.close(); resolve(merged); };
    tx.onerror = () => { db.close(); reject(tx.error); };
  });
}

export async function remove(id) {
  const db = await open();
  if (!db) { memoryStore = memoryStore.filter((r) => r.id !== id); return; }
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).delete(id);
    tx.oncomplete = () => { db.close(); resolve(); };
    tx.onerror = () => { db.close(); reject(tx.error); };
  });
}

export async function clear() {
  const db = await open();
  if (!db) { memoryStore = []; return; }
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).clear();
    tx.oncomplete = () => { db.close(); resolve(); };
    tx.onerror = () => { db.close(); reject(tx.error); };
  });
}

export async function count() {
  return (await all()).length;
}
