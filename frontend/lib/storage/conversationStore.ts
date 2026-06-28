import { openDB, DBSchema, IDBPDatabase } from 'idb';
import { ChatMessage, Citation } from '../types/models';

export interface StoredConversation {
  sessionId: string;
  title: string;
  messages: ChatMessage[];
  citations: Citation[];
  updatedAt: number;
}

export interface ConversationSummary {
  sessionId: string;
  title: string;
  updatedAt: number;
}

interface ChatDB extends DBSchema {
  conversations: {
    key: string;
    value: StoredConversation;
    indexes: { 'by-updatedAt': number };
  };
}

const DB_NAME = 'rag-chat-db';
const DB_VERSION = 1;

let dbPromise: Promise<IDBPDatabase<ChatDB>> | null = null;

function getDB() {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('IndexedDB not available in SSR'));
  }
  if (!dbPromise) {
    dbPromise = openDB<ChatDB>(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains('conversations')) {
          const store = db.createObjectStore('conversations', { keyPath: 'sessionId' });
          store.createIndex('by-updatedAt', 'updatedAt');
        }
      },
    }).catch(err => {
      console.warn("Failed to open IndexedDB", err);
      // Reset dbPromise on failure so next call tries again or degrades gracefully
      dbPromise = null;
      throw err;
    });
  }
  return dbPromise;
}

export async function listConversations(): Promise<ConversationSummary[]> {
  try {
    const db = await getDB();
    const tx = db.transaction('conversations', 'readonly');
    const index = tx.store.index('by-updatedAt');
    // Fetch all, they come sorted by index (ascending). We reverse to get descending.
    const all = await index.getAll();
    return all.reverse().map((c) => ({
      sessionId: c.sessionId,
      title: c.title,
      updatedAt: c.updatedAt,
    }));
  } catch (e) {
    console.warn("listConversations failed:", e);
    return [];
  }
}

export async function getConversation(sessionId: string): Promise<StoredConversation | null> {
  try {
    const db = await getDB();
    const result = await db.get('conversations', sessionId);
    return result || null;
  } catch (e) {
    console.warn(`getConversation(${sessionId}) failed:`, e);
    return null;
  }
}

export async function saveConversation(conversation: StoredConversation): Promise<void> {
  try {
    const db = await getDB();
    await db.put('conversations', conversation);
  } catch (e) {
    console.warn("saveConversation failed:", e);
  }
}

export async function deleteConversation(sessionId: string): Promise<void> {
  try {
    const db = await getDB();
    await db.delete('conversations', sessionId);
  } catch (e) {
    console.warn(`deleteConversation(${sessionId}) failed:`, e);
  }
}
