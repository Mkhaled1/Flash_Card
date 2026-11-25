// Frontend entrypoint for the web flashcard app.
// This file defines the React UI, local state management, and
// communication with the Flask backend API.
const { useState, useEffect, useRef } = React;

// ==================== API SERVICE ====================
// Simple API client wrapper around fetch() to communicate with the backend.
// All REST calls are centralized here to keep the UI components clean.
class APIClient {
    constructor(baseURL = window.location.port === '8000'
        ? `${window.location.protocol}//${window.location.hostname}:5000/api`
        : '/api') {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        };
        
        try {
            const response = await fetch(url, config);
            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.error || `HTTP ${response.status}`);
            }
            if (response.status === 204) {
                return null;
            }
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Decks
    getDecks() { return this.request('/decks'); }
    createDeck(name, description) { return this.request('/decks', { method: 'POST', body: JSON.stringify({ name, description }) }); }
    getDeck(id) { return this.request(`/decks/${id}`); }
    updateDeck(id, data) { return this.request(`/decks/${id}`, { method: 'PUT', body: JSON.stringify(data) }); }
    deleteDeck(id) { return this.request(`/decks/${id}`, { method: 'DELETE' }); }
    getDeckStats(id) { return this.request(`/decks/${id}/stats`); }

    // Cards
    getCards(deckId, dueOnly = false) { return this.request(`/decks/${deckId}/cards?due_only=${dueOnly}`); }
    createCard(deckId, word, definition) { return this.request(`/decks/${deckId}/cards`, { method: 'POST', body: JSON.stringify({ word, definition }) }); }
    getCard(id) { return this.request(`/cards/${id}`); }
    updateCard(id, data) { return this.request(`/cards/${id}`, { method: 'PUT', body: JSON.stringify(data) }); }
    deleteCard(id) { return this.request(`/cards/${id}`, { method: 'DELETE' }); }
    rateCard(id, quality) { return this.request(`/cards/${id}/rate`, { method: 'POST', body: JSON.stringify({ quality }) }); }
    resetCard(id) { return this.request(`/cards/${id}/reset`, { method: 'POST' }); }
    getRandomCard(deckId, excludeCardId = null, includeAll = true) {
        const params = new URLSearchParams({ include_all: String(includeAll) });
        if (excludeCardId) params.set('exclude_id', excludeCardId);
        const query = `?${params.toString()}`;
        return this.request(`/decks/${deckId}/random-card${query}`);
    }
    bulkReset(deckId) { return this.request(`/decks/${deckId}/bulk-reset`, { method: 'POST' }); }
    mergeDecks(name, deckIds) {
        return this.request('/decks/merge', {
            method: 'POST',
            body: JSON.stringify({ name, deck_ids: deckIds }),
        });
    }
    getDeckExportUrl(deckId) { return `${this.baseURL}/decks/${deckId}/export.csv`; }
}

const api = new APIClient();

const CSV_HANDLE_DATABASE = 'flashcard-csv-handles';
const CSV_HANDLE_STORE = 'deck-files';

function openCSVHandleDatabase() {
    if (!window.indexedDB) {
        return Promise.reject(new Error('Browser storage is unavailable'));
    }

    return new Promise((resolve, reject) => {
        const request = window.indexedDB.open(CSV_HANDLE_DATABASE, 1);
        request.onupgradeneeded = () => {
            request.result.createObjectStore(CSV_HANDLE_STORE);
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error || new Error('Could not open browser storage'));
    });
}

async function saveCSVFileHandle(deckId, fileHandle) {
    const database = await openCSVHandleDatabase();
    return new Promise((resolve, reject) => {
        const transaction = database.transaction(CSV_HANDLE_STORE, 'readwrite');
        transaction.objectStore(CSV_HANDLE_STORE).put(fileHandle, String(deckId));
        transaction.oncomplete = () => {
            database.close();
            resolve();
        };
        transaction.onerror = () => {
            database.close();
            reject(transaction.error || new Error('Could not save the CSV file link'));
        };
        transaction.onabort = () => {
            database.close();
            reject(transaction.error || new Error('Could not save the CSV file link'));
        };
    });
}

async function getCSVFileHandle(deckId) {
    const database = await openCSVHandleDatabase();
    return new Promise((resolve, reject) => {
        const transaction = database.transaction(CSV_HANDLE_STORE, 'readonly');
        const request = transaction.objectStore(CSV_HANDLE_STORE).get(String(deckId));
        request.onsuccess = () => {
            database.close();
            resolve(request.result || null);
        };
        request.onerror = () => {
            database.close();
            reject(request.error || new Error('Could not read the CSV file link'));
        };
    });
}

async function writeDeckProgressToCSV(deckId) {
    const fileHandle = await getCSVFileHandle(deckId);
    if (!fileHandle) {
        return false;
    }

    const permission = await fileHandle.queryPermission({ mode: 'readwrite' });
    if (permission !== 'granted') {
        throw new Error('CSV write access is not enabled. Enable CSV updates and try again.');
    }

    const response = await fetch(api.getDeckExportUrl(deckId));
    if (!response.ok) {
        throw new Error(`Could not export CSV progress (HTTP ${response.status})`);
    }

    const writable = await fileHandle.createWritable();
    try {
        await writable.write(await response.blob());
        await writable.close();
    } catch (error) {
        await writable.abort();
        throw error;
    }
    return true;
}

// ==================== MAIN APP ====================
// Top-level application component. Controls page navigation and deck loading.
function App() {
    const [currentPage, setCurrentPage] = useState('menu');
    const [decks, setDecks] = useState([]);
    const [currentDeck, setCurrentDeck] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [darkMode, setDarkMode] = useState(() => localStorage.getItem('darkMode') === 'true');

    useEffect(() => {
        loadDecks();
    }, []);

    useEffect(() => {
        document.body.classList.toggle('dark-mode', darkMode);
        localStorage.setItem('darkMode', String(darkMode));
    }, [darkMode]);

    async function loadDecks() {
        try {
            setLoading(true);
            const data = await api.getDecks();
            setDecks(data);
            setError(null);
        } catch (err) {
            setError('Failed to load decks: ' + err.message);
        } finally {
            setLoading(false);
        }
    }

    function handleSelectDeck(deck) {
        setCurrentDeck(deck);
        setCurrentPage('study');
    }

    function handleBackToMenu() {
        setCurrentPage('menu');
        setCurrentDeck(null);
        loadDecks();
    }

    return (
        <div className="container">
            <div className="app-toolbar">
                <button className="btn btn-secondary" onClick={() => setDarkMode(!darkMode)}>
                    {darkMode ? '☀️ Light mode' : '🌙 Dark mode'}
                </button>
            </div>
            {error && <div className="alert alert-danger">{error}</div>}
            
            {currentPage === 'menu' && (
                <MainMenu 
                    decks={decks} 
                    loading={loading}
                    onSelectDeck={handleSelectDeck}
                    onRefresh={loadDecks}
                    setCurrentPage={setCurrentPage}
                />
            )}
            
            {currentPage === 'study' && currentDeck && (
                <StudyPage 
                    deck={currentDeck}
                    onBack={handleBackToMenu}
                    setCurrentPage={setCurrentPage}
                />
            )}
            
            {currentPage === 'editor' && currentDeck && (
                <EditorPage 
                    deck={currentDeck}
                    onBack={handleBackToMenu}
                />
            )}

            {currentPage === 'status' && currentDeck && (
                <CardStatusPage
                    deck={currentDeck}
                    onBack={() => setCurrentPage('study')}
                />
            )}
            
            {currentPage === 'stats' && currentDeck && (
                <StatsPage 
                    deck={currentDeck}
                    darkMode={darkMode}
                    onBack={handleBackToMenu}
                />
            )}
            
            {currentPage === 'deck-manager' && (
                <DeckManagerPage 
                    decks={decks}
                    onRefresh={loadDecks}
                    onBack={handleBackToMenu}
                />
            )}
        </div>
    );
}

// ==================== MAIN MENU ====================
// Displays deck selection, creation, and import options.
function MainMenu({ decks, loading, onSelectDeck, onRefresh, setCurrentPage }) {
    const [showNewDeck, setShowNewDeck] = useState(false);
    const [showImportCSV, setShowImportCSV] = useState(false);
    const [importNotice, setImportNotice] = useState(null);

    return (
        <div className="page">
            <div className="header">
                <h1>German Flashcard App</h1>
                <p>Master German vocabulary with spaced repetition</p>
            </div>

            {importNotice && <div className="alert alert-warning">{importNotice}</div>}

            {showNewDeck && (
                <NewDeckModal 
                    onClose={() => setShowNewDeck(false)}
                    onSuccess={() => {
                        setShowNewDeck(false);
                        onRefresh();
                    }}
                />
            )}

            {showImportCSV && (
                <ImportCSVModal 
                    onClose={() => setShowImportCSV(false)}
                    onSuccess={notice => {
                        setShowImportCSV(false);
                        setImportNotice(notice);
                        onRefresh();
                    }}
                />
            )}

            <div className="main-grid">
                <button className="btn btn-primary btn-lg" onClick={() => setShowNewDeck(true)}>
                    ➕ New Deck
                </button>
                <button className="btn btn-primary btn-lg" onClick={() => setShowImportCSV(true)}>
                    📥 Import CSV
                </button>
                <button className="btn btn-primary btn-lg" onClick={() => setCurrentPage('deck-manager')}>
                    📚 Deck Manager
                </button>
            </div>

            <h2 style={{marginTop: '30px', marginBottom: '15px'}}>Your Decks</h2>
            
            {loading ? (
                <div className="spinner"></div>
            ) : decks.length === 0 ? (
                <div className="card">
                    <p style={{textAlign: 'center', color: '#9CA3AF'}}>No decks yet. Create one to get started!</p>
                </div>
            ) : (
                <div className="main-grid">
                    {decks.map(deck => (
                        <div key={deck.id} className="card" style={{cursor: 'pointer'}} onClick={() => onSelectDeck(deck)}>
                            <div className="card-title">{deck.name}</div>
                            <div className="card-subtitle">{deck.description}</div>
                            <div className="stat-value">{deck.card_count}</div>
                            <div className="stat-label">Cards</div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// ==================== NEW DECK MODAL ====================
// Modal dialog for creating a new deck with a name and optional description.
function NewDeckModal({ onClose, onSuccess }) {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    async function handleSubmit(e) {
        e.preventDefault();
        if (!name.trim()) {
            setError('Deck name is required');
            return;
        }
        
        try {
            setLoading(true);
            await api.createDeck(name, description);
            onSuccess();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="modal open">
            <div className="modal-content">
                <h2 style={{marginBottom: '20px'}}>Create New Deck</h2>
                {error && <div className="alert alert-danger">{error}</div>}
                
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Deck Name *</label>
                        <input 
                            type="text" 
                            value={name}
                            onChange={e => setName(e.target.value)}
                            placeholder="e.g., German Verbs"
                            autoFocus
                        />
                    </div>
                    
                    <div className="form-group">
                        <label>Description</label>
                        <textarea 
                            value={description}
                            onChange={e => setDescription(e.target.value)}
                            placeholder="Optional description"
                        ></textarea>
                    </div>
                    
                    <div className="btn-group">
                        <button type="submit" className="btn btn-success btn-block" disabled={loading}>
                            {loading ? 'Creating...' : 'Create Deck'}
                        </button>
                        <button type="button" className="btn btn-secondary btn-block" onClick={onClose}>
                            Cancel
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

// ==================== IMPORT CSV MODAL ====================
// Modal dialog for uploading a CSV file and creating a deck from its contents.
function ImportCSVModal({ onClose, onSuccess }) {
    const [deckName, setDeckName] = useState('');
    const [file, setFile] = useState(null);
    const [fileHandle, setFileHandle] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [preview, setPreview] = useState([]);
    const fileInputRef = useRef(null);

    function handleSelectedFile(selectedFile, selectedHandle = null) {
        if (!selectedFile) return;

        if (!selectedFile.name.toLowerCase().endsWith('.csv')) {
            setError('Please select a CSV file');
            return;
        }

        setFile(selectedFile);
        setFileHandle(selectedHandle);
        const suggestedName = selectedFile.name.replace(/\.csv$/i, '').trim();
        setDeckName(suggestedName);
        setError(null);

        // Read and preview file
        const reader = new FileReader();
        reader.onload = (event) => {
            const content = event.target.result;
            const lines = content.split('\n').slice(0, 3); // Show first 3 rows
            setPreview(lines.map(line => line.split(',').slice(0, 2))); // Show first 2 columns
        };
        reader.readAsText(selectedFile);
    }

    function handleFileSelect(e) {
        handleSelectedFile(e.target.files[0]);
    }

    async function chooseCSVFile() {
        try {
            const [selectedHandle] = await window.showOpenFilePicker({
                multiple: false,
                types: [{ description: 'CSV files', accept: { 'text/csv': ['.csv'] } }],
            });
            const permission = await selectedHandle.requestPermission({ mode: 'readwrite' });
            if (permission !== 'granted') {
                setError('Write access is required to update this CSV with study progress.');
                return;
            }
            handleSelectedFile(await selectedHandle.getFile(), selectedHandle);
        } catch (err) {
            if (err.name !== 'AbortError') {
                setError('Could not open the CSV file: ' + err.message);
            }
        }
    }

    async function handleSubmit(e) {
        e.preventDefault();

        if (!deckName.trim()) {
            setError('Deck name is required');
            return;
        }

        if (!file) {
            setError('Please select a CSV file');
            return;
        }

        try {
            setLoading(true);

            // Read file as base64
            const reader = new FileReader();
            reader.onload = async (event) => {
                const fileContent = event.target.result;

                try {
                    const importedDeck = await api.request('/decks/import-csv', {
                        method: 'POST',
                        body: JSON.stringify({
                            deck_name: deckName,
                            file_content: fileContent
                        })
                    });
                    let notice = null;
                    if (fileHandle) {
                        try {
                            await saveCSVFileHandle(importedDeck.deck_id, fileHandle);
                        } catch (err) {
                            notice = 'Deck imported, but automatic CSV updates could not be enabled: ' + err.message;
                        }
                    } else {
                        notice = 'This browser cannot write to the selected CSV directly. Progress is saved in the app; use Deck Manager → Export CSV to save it to a file.';
                    }
                    onSuccess(notice);
                } catch (err) {
                    setError(err.message);
                } finally {
                    setLoading(false);
                }
            };
            reader.readAsDataURL(file);
        } catch (err) {
            setError(err.message);
            setLoading(false);
        }
    }

    return (
        <div className="modal open">
            <div className="modal-content">
                <h2 style={{marginBottom: '20px'}}>Import CSV File</h2>
                {error && <div className="alert alert-danger">{error}</div>}
                
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Deck Name *</label>
                        <input 
                            type="text" 
                            value={deckName}
                            onChange={e => setDeckName(e.target.value)}
                            placeholder="e.g., German Verbs"
                            autoFocus
                        />
                    </div>
                    
                    <div className="form-group">
                        <label>CSV File * (German word | English definition)</label>
                        {typeof window.showOpenFilePicker === 'function' ? (
                            <button type="button" className="btn btn-secondary" onClick={chooseCSVFile}>
                                Choose CSV and enable progress write-back
                            </button>
                        ) : (
                            <>
                                <input
                                    type="file"
                                    ref={fileInputRef}
                                    accept=".csv"
                                    onChange={handleFileSelect}
                                    style={{padding: '10px', border: '2px dashed #06B6D4', borderRadius: '8px', cursor: 'pointer'}}
                                />
                                <p className="card-subtitle">
                                    Direct CSV updates are not supported in this browser; use Deck Manager → Export CSV to save progress.
                                </p>
                            </>
                        )}
                    </div>

                    {preview.length > 0 && (
                        <div className="card" style={{marginBottom: '15px', backgroundColor: '#F0F9FF'}}>
                            <div className="card-title">Preview</div>
                            <table style={{fontSize: '12px'}}>
                                <thead>
                                    <tr>
                                        <th>German</th>
                                        <th>English</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {preview.map((row, idx) => (
                                        <tr key={idx}>
                                            <td>{row[0]?.trim()}</td>
                                            <td>{row[1]?.trim()}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                    
                    <div className="btn-group">
                        <button type="submit" className="btn btn-success btn-block" disabled={loading || !file}>
                            {loading ? 'Importing...' : 'Import Deck'}
                        </button>
                        <button type="button" className="btn btn-secondary btn-block" onClick={onClose}>
                            Cancel
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

// ==================== STUDY PAGE ====================
// Main study interface: shows flashcards, flips the card, and records ratings.
function StudyPage({ deck, onBack, setCurrentPage }) {
    const [card, setCard] = useState(null);
    const [flipped, setFlipped] = useState(false);
    const [loading, setLoading] = useState(false);
    const [stats, setStats] = useState(null);
    const [completed, setCompleted] = useState(false);
    const [direction, setDirection] = useState('de-en');
    const [includeAll, setIncludeAll] = useState(true);
    const [completionMessage, setCompletionMessage] = useState('');
    const [studyError, setStudyError] = useState(null);
    const [csvSyncStatus, setCSVSyncStatus] = useState('checking');

    useEffect(() => {
        loadRandomCard(null, true);
        loadStats();
        loadCSVSyncStatus();
    }, [deck.id]);

    async function loadRandomCard(excludeCardId = null, allCards = includeAll) {
        try {
            setLoading(true);
            const data = await api.getRandomCard(deck.id, excludeCardId, allCards);
            const cardData = data && Object.prototype.hasOwnProperty.call(data, 'card')
                ? data.card
                : data;
            setStudyError(null);
            if (cardData) {
                setCard(cardData);
                setFlipped(false);
                setCompleted(false);
                setStudyError(null);
            } else {
                setCard(null);
                setCompleted(true);
                setCompletionMessage(data?.message || 'There are no cards available to study.');
            }
        } catch (err) {
            setStudyError('Failed to load a card: ' + err.message);
            setCard(null);
        } finally {
            setLoading(false);
        }
    }

    async function loadStats() {
        try {
            const data = await api.getDeckStats(deck.id);
            setStats(data);
        } catch (err) {
            setStudyError('Failed to load deck statistics: ' + err.message);
        }
    }

    async function loadCSVSyncStatus() {
        try {
            const fileHandle = await getCSVFileHandle(deck.id);
            if (!fileHandle) {
                setCSVSyncStatus('unlinked');
                return;
            }
            const permission = await fileHandle.queryPermission({ mode: 'readwrite' });
            setCSVSyncStatus(permission === 'granted' ? 'ready' : 'permission-needed');
        } catch (err) {
            setCSVSyncStatus('error');
            setStudyError('Failed to check CSV write access: ' + err.message);
        }
    }

    async function enableCSVWriteBack() {
        try {
            const fileHandle = await getCSVFileHandle(deck.id);
            if (!fileHandle) {
                throw new Error('No source CSV is linked to this deck.');
            }
            const permission = await fileHandle.requestPermission({ mode: 'readwrite' });
            if (permission !== 'granted') {
                throw new Error('Write access was not granted.');
            }
            await writeDeckProgressToCSV(deck.id);
            setCSVSyncStatus('ready');
            setStudyError(null);
        } catch (err) {
            setCSVSyncStatus('error');
            setStudyError('Could not save progress to the CSV: ' + err.message);
        }
    }

    // Rate the current card and immediately load the next due card.
    async function handleRate(quality) {
        if (!card || !flipped) {
            return;
        }

        try {
            setLoading(true);
            await api.rateCard(card.id, quality);
            let csvWriteError = null;
            try {
                const csvUpdated = await writeDeckProgressToCSV(deck.id);
                if (csvUpdated) {
                    setCSVSyncStatus('ready');
                }
            } catch (err) {
                csvWriteError = err;
                setCSVSyncStatus('permission-needed');
            }
            await loadRandomCard(card.id, includeAll);
            await loadStats();
            if (csvWriteError) {
                setStudyError('Rating was saved, but progress could not be written to the CSV: ' + csvWriteError.message);
            }
        } catch (err) {
            setStudyError('Failed to save your rating: ' + err.message);
        } finally {
            setLoading(false);
        }
    }

    function changeStudyMode(allCards) {
        setIncludeAll(allCards);
        setCompleted(false);
        loadRandomCard(null, allCards);
    }

    return (
        <div className="page">
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px'}}>
                <h1>{deck.name}</h1>
                <button className="btn btn-secondary" onClick={onBack}>← Back to Menu</button>
            </div>

            <div style={{display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '20px'}}>
                <button
                    className={"btn " + (includeAll ? 'btn-primary' : 'btn-secondary')}
                    onClick={() => changeStudyMode(true)}
                >
                    Study all cards
                </button>
                <button
                    className={"btn " + (!includeAll ? 'btn-primary' : 'btn-secondary')}
                    onClick={() => changeStudyMode(false)}
                >
                    Study due cards only
                </button>
            </div>

            <div style={{display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '20px'}}>
                <button
                    className={"btn " + (direction === 'de-en' ? 'btn-primary' : 'btn-secondary')}
                    onClick={() => { setDirection('de-en'); setFlipped(false); }}
                >
                    German to English
                </button>
                <button
                    className={"btn " + (direction === 'en-de' ? 'btn-primary' : 'btn-secondary')}
                    onClick={() => { setDirection('en-de'); setFlipped(false); }}
                >
                    English to German
                </button>
            </div>

            {stats && (
                <div className="stats-grid">
                    <div className="stat-box">
                        <div className="stat-value">{stats.total_cards}</div>
                        <div className="stat-label">Total Cards</div>
                    </div>
                    <div className="stat-box">
                        <div className="stat-value">{stats.cards_due}</div>
                        <div className="stat-label">Due Today</div>
                    </div>
                    <div className="stat-box">
                        <div className="stat-value">{stats.mastery_percentage}%</div>
                        <div className="stat-label">Mastery</div>
                    </div>
                </div>
            )}

            {studyError && <div className="alert alert-danger">{studyError}</div>}
            {csvSyncStatus === 'ready' && (
                <div className="alert alert-info">Study progress is written to the source CSV after each rating.</div>
            )}
            {(csvSyncStatus === 'permission-needed' || csvSyncStatus === 'error') && (
                <div className="alert alert-warning">
                    <p>CSV write access is needed to sync study progress.</p>
                    <button className="btn btn-warning" disabled={loading} onClick={enableCSVWriteBack}>
                        Enable or retry CSV updates
                    </button>
                </div>
            )}

            {completed ? (
                <div className="card" style={{textAlign: 'center', padding: '40px'}}>
                    <h2 style={{color: 'var(--success)', marginBottom: '10px'}}>
                        {includeAll && completionMessage === 'All cards are mastered'
                            ? '🎉 Deck mastered!'
                            : includeAll ? '🎉 No cards to study yet' : '🎉 All done for today!'}
                    </h2>
                    <p>{completionMessage}</p>
                    {!includeAll && (
                        <button
                            className="btn btn-primary btn-lg"
                            style={{marginTop: '20px'}}
                            onClick={() => changeStudyMode(true)}
                        >
                            Study all cards
                        </button>
                    )}
                    <div className="btn-group">
                        <button className="btn btn-secondary" onClick={onBack}>← Back to Menu</button>
                        <button className="btn btn-primary" onClick={() => setCurrentPage('editor')}>✏️ Edit Deck</button>
                    </div>
                </div>
            ) : card ? (
                <>
                    <div className="flashcard-container">
                        <div className={`flashcard ${flipped ? 'flipped' : ''}`} onClick={() => setFlipped(!flipped)}>
                            <div className="flashcard-inner">
                                <div className="flashcard-front">
                                    <div className="flashcard-label">{direction === 'de-en' ? 'German Word' : 'English Word'}</div>
                                    <div>{direction === 'de-en' ? card.word : card.definition}</div>
                                </div>
                                <div className="flashcard-back">
                                    <div className="flashcard-label">{direction === 'de-en' ? 'English Definition' : 'German Translation'}</div>
                                    <div>{direction === 'de-en' ? card.definition : card.word}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <p style={{textAlign: 'center', color: '#9CA3AF', marginBottom: '20px'}}>
                        {flipped ? 'Choose a rating for this card' : 'Click the card to reveal the definition'}
                    </p>

                    {flipped && <div className="rating-buttons">
                        <button 
                            className="rating-btn unknown" 
                            onClick={() => handleRate(0)}
                            disabled={loading}
                        >
                            😤 Unknown
                        </button>
                        <button 
                            className="rating-btn hard" 
                            onClick={() => handleRate(1)}
                            disabled={loading}
                        >
                            😐 Hard
                        </button>
                        <button 
                            className="rating-btn medium" 
                            onClick={() => handleRate(2)}
                            disabled={loading}
                        >
                            😊 Medium
                        </button>
                        <button 
                            className="rating-btn memorized" 
                            onClick={() => handleRate(3)}
                            disabled={loading}
                        >
                            😄 Memorized
                        </button>
                        <button 
                            className="rating-btn perfect" 
                            onClick={() => handleRate(5)}
                            disabled={loading}
                        >
                            🤩 Perfect
                        </button>
                    </div>}

                    <div style={{display: 'flex', gap: '10px', marginTop: '20px'}}>
                        <button className="btn btn-secondary" onClick={onBack}>← Back to Menu</button>
                        <button className="btn btn-primary" onClick={() => setCurrentPage('editor')}>✏️ Edit Deck</button>
                        <button className="btn btn-primary" onClick={() => setCurrentPage('stats')}>📊 View Stats</button>
                        <button className="btn btn-primary" onClick={() => setCurrentPage('status')}>📋 Show Status</button>
                    </div>
                </>
            ) : studyError ? (
                <button
                    className="btn btn-primary"
                    onClick={() => { loadRandomCard(null, includeAll); loadStats(); }}
                >
                    Retry
                </button>
            ) : (
                <div className="spinner"></div>
            )}
        </div>
    );
}

// ==================== EDITOR PAGE ====================
// Deck editor for adding, viewing, and deleting individual flashcards.
function EditorPage({ deck, onBack }) {
    const [cards, setCards] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showForm, setShowForm] = useState(false);
    const [editingCard, setEditingCard] = useState(null);
    const [newWord, setNewWord] = useState('');
    const [newDef, setNewDef] = useState('');
    const [error, setError] = useState(null);

    useEffect(() => {
        loadCards();
    }, [deck.id]);

    async function loadCards() {
        try {
            setLoading(true);
            const data = await api.getCards(deck.id);
            setCards(data);
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    function startAddingCard() {
        setEditingCard(null);
        setNewWord('');
        setNewDef('');
        setShowForm(true);
    }

    function startEditingCard(card) {
        setEditingCard(card);
        setNewWord(card.word);
        setNewDef(card.definition || '');
        setShowForm(true);
    }

    function cancelForm() {
        setShowForm(false);
        setEditingCard(null);
        setNewWord('');
        setNewDef('');
    }

    async function handleSaveCard(e) {
        e.preventDefault();
        if (!newWord.trim() || !newDef.trim()) {
            setError('Word and definition are required');
            return;
        }

        try {
            setLoading(true);
            if (editingCard) {
                await api.updateCard(editingCard.id, {
                    word: newWord.trim(),
                    definition: newDef.trim(),
                });
            } else {
                await api.createCard(deck.id, newWord.trim(), newDef.trim());
            }
            cancelForm();
            await loadCards();
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    async function handleDeleteCard(cardId) {
        if (!confirm('Delete this card?')) return;
        
        try {
            setLoading(true);
            await api.deleteCard(cardId);
            await loadCards();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="page">
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px'}}>
                <h1>Edit {deck.name}</h1>
                <button className="btn btn-secondary" onClick={onBack}>← Back to Menu</button>
            </div>

            {error && <div className="alert alert-danger">{error}</div>}

            <button
                className="btn btn-primary btn-lg btn-block"
                onClick={showForm ? cancelForm : startAddingCard}
            >
                {showForm ? '✕ Cancel' : '➕ Add Card'}
            </button>

            {showForm && (
                <form onSubmit={handleSaveCard} className="card" style={{marginTop: '15px'}}>
                    <h2>{editingCard ? 'Edit Card' : 'New Card'}</h2>
                    <div className="form-group">
                        <label>German Word</label>
                        <input 
                            type="text"
                            value={newWord}
                            onChange={e => setNewWord(e.target.value)}
                            placeholder="Enter German word"
                        />
                    </div>
                    <div className="form-group">
                        <label>English Definition</label>
                        <textarea 
                            value={newDef}
                            onChange={e => setNewDef(e.target.value)}
                            placeholder="Enter English definition"
                        ></textarea>
                    </div>
                    <div className="btn-group">
                        <button type="submit" className="btn btn-success" disabled={loading}>
                            {loading ? 'Saving...' : editingCard ? 'Save Changes' : 'Add Card'}
                        </button>
                        {editingCard && (
                            <button type="button" className="btn btn-secondary" onClick={cancelForm}>
                                Cancel
                            </button>
                        )}
                    </div>
                </form>
            )}

            <h2 style={{marginTop: '30px', marginBottom: '15px'}}>Cards ({cards.length})</h2>
            
            {loading && !showForm ? (
                <div className="spinner"></div>
            ) : cards.length === 0 ? (
                <div className="card">
                    <p style={{textAlign: 'center', color: '#9CA3AF'}}>No cards in this deck yet</p>
                </div>
            ) : (
                <div className="table-scroll">
                    <table>
                        <thead>
                            <tr>
                                <th>Word</th>
                                <th>Definition</th>
                                <th>Status</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {cards.map(card => (
                                <tr key={card.id}>
                                    <td><strong>{card.word}</strong></td>
                                    <td>{card.definition}</td>
                                    <td><span className={`badge badge-${card.rating.toLowerCase().replace(' ', '-')}`}>{card.rating}</span></td>
                                    <td>
                                        <button
                                            className="btn btn-secondary"
                                            style={{padding: '5px 10px', fontSize: '12px', marginRight: '5px'}}
                                            onClick={() => startEditingCard(card)}
                                        >
                                            Edit
                                        </button>
                                        <button
                                            className="btn btn-danger"
                                            style={{padding: '5px 10px', fontSize: '12px'}}
                                            onClick={() => handleDeleteCard(card.id)}
                                        >
                                            Delete
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

function CardStatusPage({ deck, onBack }) {
    const [cards, setCards] = useState([]);
    const [selectedCardId, setSelectedCardId] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadCards();
    }, [deck.id]);

    async function loadCards() {
        try {
            setLoading(true);
            setCards(await api.getCards(deck.id));
            setError(null);
        } catch (err) {
            setError('Failed to load card statuses: ' + err.message);
        } finally {
            setLoading(false);
        }
    }

    async function handleResetCard(cardId) {
        try {
            setLoading(true);
            await api.resetCard(cardId);
            await loadCards();
        } catch (err) {
            setError('Failed to reset card: ' + err.message);
        } finally {
            setLoading(false);
        }
    }

    async function handleResetSelected() {
        if (!selectedCardId) return;
        await handleResetCard(selectedCardId);
    }

    async function handleResetAll() {
        if (!confirm(`Reset all cards in "${deck.name}"?`)) return;
        try {
            setLoading(true);
            await api.bulkReset(deck.id);
            setSelectedCardId(null);
            await loadCards();
        } catch (err) {
            setError('Failed to reset cards: ' + err.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="page">
            <div className="page-heading">
                <h1>Status - {deck.name}</h1>
                <button className="btn btn-secondary" onClick={onBack}>← Back to Study</button>
            </div>

            {error && <div className="alert alert-danger">{error}</div>}
            <div className="btn-group">
                <button className="btn btn-warning" disabled={!selectedCardId || loading} onClick={handleResetSelected}>
                    Reset Selected
                </button>
                <button className="btn btn-danger" disabled={!cards.length || loading} onClick={handleResetAll}>
                    Reset All
                </button>
            </div>

            {loading ? (
                <div className="spinner"></div>
            ) : cards.length === 0 ? (
                <div className="card"><p>No cards in this deck.</p></div>
            ) : (
                <div className="table-scroll">
                    <table>
                        <thead>
                            <tr>
                                <th>Select</th>
                                <th>Word</th>
                                <th>Status</th>
                                <th>Next Review</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {cards.map(card => (
                                <tr
                                    key={card.id}
                                    className={selectedCardId === card.id ? 'selected-row' : ''}
                                    onClick={() => setSelectedCardId(card.id)}
                                >
                                    <td>
                                        <input
                                            type="radio"
                                            name="selected-card"
                                            checked={selectedCardId === card.id}
                                            onChange={() => setSelectedCardId(card.id)}
                                            aria-label={`Select ${card.word}`}
                                        />
                                    </td>
                                    <td>{card.word}</td>
                                    <td><span className={`badge badge-${card.rating.toLowerCase().replace(/\s/g, '-')}`}>{card.rating}</span></td>
                                    <td>{card.next_due}</td>
                                    <td>
                                        <button className="btn btn-warning" onClick={() => handleResetCard(card.id)}>
                                            Reset
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

// ==================== STATS PAGE ====================
// Displays deck statistics and renders a progress chart based on card ratings.
function StatsPage({ deck, darkMode, onBack }) {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(false);
    const chartRef = useRef(null);
    const chartInstance = useRef(null);

    useEffect(() => {
        loadStats();
    }, [deck.id]);

    useEffect(() => {
        if (stats && !loading && chartRef.current) {
            drawChart();
        }
    }, [stats, darkMode, loading]);

    async function loadStats() {
        try {
            setLoading(true);
            const data = await api.getDeckStats(deck.id);
            setStats(data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }

    function drawChart() {
        if (!window.Chart || !stats) return;
        
        const ctx = chartRef.current?.getContext('2d');
        if (!ctx) return;

        if (chartInstance.current) {
            chartInstance.current.destroy();
        }

        const labels = Object.keys(stats.ratings);
        const data = Object.values(stats.ratings);
        const colors = ['#E0E7FF', '#FED7AA', '#FEDCDC', '#FEF3C7', '#D1FAE5', '#CCFBF1'];

        chartInstance.current = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderColor: '#FFFFFF',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: darkMode ? '#F9FAFB' : '#111827',
                            font: { size: 12 },
                            padding: 15,
                        }
                    }
                }
            }
        });
    }

    return (
        <div className="page">
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px'}}>
                <h1>Stats - {deck.name}</h1>
                <button className="btn btn-secondary" onClick={onBack}>← Back to Menu</button>
            </div>

            {loading ? (
                <div className="spinner"></div>
            ) : stats ? (
                <>
                    <div className="stats-grid">
                        <div className="stat-box">
                            <div className="stat-value">{stats.total_cards}</div>
                            <div className="stat-label">Total Cards</div>
                        </div>
                        <div className="stat-box">
                            <div className="stat-value">{stats.cards_due}</div>
                            <div className="stat-label">Due Today</div>
                        </div>
                        <div className="stat-box">
                            <div className="stat-value">{stats.cards_learned}</div>
                            <div className="stat-label">Learned</div>
                        </div>
                        <div className="stat-box">
                            <div className="stat-value">{stats.mastery_percentage}%</div>
                            <div className="stat-label">Mastery</div>
                        </div>
                    </div>

                    <div className="card" style={{marginTop: '30px'}}>
                        <h2 style={{marginBottom: '20px'}}>Progress Chart</h2>
                        <canvas ref={chartRef} style={{maxHeight: '400px'}}></canvas>
                    </div>

                    <div className="card" style={{marginTop: '20px'}}>
                        <h3>By Status</h3>
                        <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '15px', marginTop: '15px'}}>
                            <div className="stat-box">
                                <div className="stat-value">{stats.status_counts.new}</div>
                                <div className="stat-label">New</div>
                            </div>
                            <div className="stat-box">
                                <div className="stat-value">{stats.status_counts.learning}</div>
                                <div className="stat-label">Learning</div>
                            </div>
                            <div className="stat-box">
                                <div className="stat-value">{stats.status_counts.mastered}</div>
                                <div className="stat-label">Mastered</div>
                            </div>
                        </div>
                    </div>
                </>
            ) : null}
        </div>
    );
}

// ==================== DECK MANAGER ====================
// Deck management view for resetting or deleting entire decks.
function DeckManagerPage({ decks, onRefresh, onBack }) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [showMerge, setShowMerge] = useState(false);

    async function handleDeleteDeck(deckId, deckName) {
        if (!confirm(`Delete deck "${deckName}" and all its cards?`)) return;

        try {
            setLoading(true);
            await api.deleteDeck(deckId);
            onRefresh();
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    async function handleResetDeck(deckId, deckName) {
        if (!confirm(`Reset all cards in "${deckName}"?`)) return;

        try {
            setLoading(true);
            await api.bulkReset(deckId);
            onRefresh();
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="page">
            {showMerge && (
                <MergeDecksModal
                    decks={decks}
                    onClose={() => setShowMerge(false)}
                    onSuccess={async () => {
                        setShowMerge(false);
                        await onRefresh();
                    }}
                />
            )}

            <div className="page-heading">
                <h1>Deck Manager</h1>
                <div className="btn-group">
                    <button className="btn btn-primary" disabled={decks.length < 2} onClick={() => setShowMerge(true)}>
                        Merge Decks
                    </button>
                    <button className="btn btn-secondary" onClick={onBack}>← Back to Menu</button>
                </div>
            </div>

            {error && <div className="alert alert-danger">{error}</div>}

            {loading ? (
                <div className="spinner"></div>
            ) : decks.length === 0 ? (
                <div className="card">
                    <p style={{textAlign: 'center', color: '#9CA3AF'}}>No decks to manage</p>
                </div>
            ) : (
                <div className="table-scroll">
                    <table>
                        <thead>
                            <tr>
                                <th>Deck Name</th>
                                <th>Description</th>
                                <th>Cards</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {decks.map(deck => (
                                <tr key={deck.id}>
                                    <td><strong>{deck.name}</strong></td>
                                    <td>{deck.description || '—'}</td>
                                    <td>{deck.card_count}</td>
                                    <td>
                                        <div className="btn-group deck-actions" style={{gap: '5px'}}>
                                            <button
                                                className="btn btn-warning"
                                                style={{padding: '5px 10px', fontSize: '12px'}}
                                                onClick={() => handleResetDeck(deck.id, deck.name)}
                                            >
                                                Reset
                                            </button>
                                            <a
                                                className="btn btn-primary"
                                                style={{padding: '5px 10px', fontSize: '12px'}}
                                                href={api.getDeckExportUrl(deck.id)}
                                            >
                                                Export CSV
                                            </a>
                                            <button
                                                className="btn btn-danger"
                                                style={{padding: '5px 10px', fontSize: '12px'}}
                                                onClick={() => handleDeleteDeck(deck.id, deck.name)}
                                            >
                                                Delete
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

function MergeDecksModal({ decks, onClose, onSuccess }) {
    const [name, setName] = useState('');
    const [selectedDeckIds, setSelectedDeckIds] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    function toggleDeck(deckId) {
        setSelectedDeckIds(current => current.includes(deckId)
            ? current.filter(id => id !== deckId)
            : [...current, deckId]);
    }

    async function handleSubmit(e) {
        e.preventDefault();
        if (!name.trim()) {
            setError('Enter a name for the merged deck.');
            return;
        }
        if (selectedDeckIds.length < 2) {
            setError('Choose at least two decks to merge.');
            return;
        }

        try {
            setLoading(true);
            await api.mergeDecks(name.trim(), selectedDeckIds);
            await onSuccess();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="modal open">
            <div className="modal-content">
                <h2>Merge Decks</h2>
                {error && <div className="alert alert-danger">{error}</div>}
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="merged-deck-name">New deck name</label>
                        <input
                            id="merged-deck-name"
                            value={name}
                            onChange={event => setName(event.target.value)}
                            autoFocus
                        />
                    </div>
                    <fieldset className="merge-deck-list">
                        <legend>Select at least two source decks</legend>
                        {decks.map(deck => (
                            <label className="merge-deck-option" key={deck.id}>
                                <input
                                    type="checkbox"
                                    checked={selectedDeckIds.includes(deck.id)}
                                    onChange={() => toggleDeck(deck.id)}
                                />
                                <span>{deck.name} ({deck.card_count} cards)</span>
                            </label>
                        ))}
                    </fieldset>
                    <div className="btn-group">
                        <button className="btn btn-success" type="submit" disabled={loading}>
                            {loading ? 'Merging...' : 'Create Merged Deck'}
                        </button>
                        <button className="btn btn-secondary" type="button" onClick={onClose}>
                            Cancel
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

// ==================== RENDER APP ====================
// Mount the root React application into the page.
ReactDOM.render(<App />, document.getElementById('root'));
