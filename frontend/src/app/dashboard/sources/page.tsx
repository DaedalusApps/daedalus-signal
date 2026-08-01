'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import { getAuthHeaders } from '@/lib/auth';
import styles from '../dashboard.module.css';
import pageStyles from './sources.module.css';
import { API_BASE } from '@/lib/api';

interface Source {
    id: number;
    name: string;
    url: string;
    source_type: string;
    is_default: boolean;
    last_scraped: string | null;
}

export default function SourcesPage() {
    const [sources, setSources] = useState<Source[]>([]);
    const [defaults, setDefaults] = useState<Source[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAdd, setShowAdd] = useState(false);
    const [newSource, setNewSource] = useState({ name: '', url: '', source_type: 'twitter' });
    const [error, setError] = useState('');

    useEffect(() => {
        loadSources();
    }, []);

    const loadSources = async () => {
        try {
            const headers = getAuthHeaders();
            const [userRes, defaultRes] = await Promise.all([
                fetch(`${API_BASE}/api/sources`, { headers }),
                fetch(`${API_BASE}/api/sources/defaults`, { headers }),
            ]);

            if (userRes.ok) {
                const data = await userRes.json();
                setSources(data.sources || []);
            }

            if (defaultRes.ok) {
                const data = await defaultRes.json();
                setDefaults(data.sources || []);
            }
        } catch (err) {
            console.error('Failed to load sources:', err);
        } finally {
            setLoading(false);
        }
    };

    const addSource = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        const res = await fetch(`${API_BASE}/api/sources`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
            body: JSON.stringify(newSource),
        });

        const data = await res.json();

        if (!res.ok) {
            setError(data.error || 'Failed to add source');
            return;
        }

        setSources([...sources, data.source]);
        setNewSource({ name: '', url: '', source_type: 'twitter' });
        setShowAdd(false);
    };

    const removeSource = async (id: number) => {
        const res = await fetch(`${API_BASE}/api/sources/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders(),
        });

        if (res.ok) {
            setSources(sources.filter(s => s.id !== id));
        }
    };

    const addDefault = async (source: Source) => {
        const res = await fetch(`${API_BASE}/api/sources`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
            body: JSON.stringify({
                name: source.name,
                url: source.url,
                source_type: source.source_type,
            }),
        });

        if (res.ok) {
            const data = await res.json();
            setSources([...sources, data.source]);
        }
    };

    const getIcon = (type: string) => {
        switch (type) {
            case 'youtube': return '▶️';
            case 'twitter': return '𝕏';
            case 'linkedin': return '💼';
            case 'github': return '⌨️';
            default: return '🔗';
        }
    };

    if (loading) {
        return (
            <div className={styles.loading}>
                <div className={styles.spinner}></div>
            </div>
        );
    }

    return (
        <div className={styles.dashboard}>
            <Sidebar activePage="sources" />

            <main className={styles.main}>
                <header className={styles.header}>
                    <div>
                        <h1>Sources</h1>
                        <p>Manage your content sources (max 10)</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => setShowAdd(!showAdd)}>
                        {showAdd ? 'Cancel' : '+ Add Source'}
                    </button>
                </header>

                {showAdd && (
                    <div className={pageStyles.addCard}>
                        <h3>Add New Source</h3>
                        {error && <div className={pageStyles.error}>{error}</div>}
                        <form onSubmit={addSource} className={pageStyles.form}>
                            <div className={pageStyles.sourceTypeGroup}>
                                <button
                                    type="button"
                                    className={`${pageStyles.sourceTypeBtn} ${newSource.source_type === 'twitter' ? pageStyles.active : ''}`}
                                    onClick={() => setNewSource({ ...newSource, source_type: 'twitter' })}
                                >
                                    𝕏 X (Twitter)
                                </button>
                                <button
                                    type="button"
                                    className={`${pageStyles.sourceTypeBtn} ${newSource.source_type === 'youtube' ? pageStyles.active : ''}`}
                                    onClick={() => setNewSource({ ...newSource, source_type: 'youtube' })}
                                >
                                    ▶️ YouTube
                                </button>
                                <div className={pageStyles.disabledWrapper} title="Future feature">
                                    <button
                                        type="button"
                                        className={`${pageStyles.sourceTypeBtn} ${pageStyles.disabled}`}
                                        disabled
                                    >
                                        ⌨️ GitHub
                                    </button>
                                </div>
                                <div className={pageStyles.disabledWrapper} title="Future feature">
                                    <button
                                        type="button"
                                        className={`${pageStyles.sourceTypeBtn} ${pageStyles.disabled}`}
                                        disabled
                                    >
                                        💼 LinkedIn
                                    </button>
                                </div>
                            </div>
                            <input
                                type="text"
                                placeholder="Source name"
                                value={newSource.name}
                                onChange={(e) => setNewSource({ ...newSource, name: e.target.value })}
                                required
                            />
                            <input
                                type="url"
                                placeholder="Source URL"
                                value={newSource.url}
                                onChange={(e) => setNewSource({ ...newSource, url: e.target.value })}
                                required
                            />
                            <button type="submit" className="btn btn-primary">Add Source</button>
                        </form>
                    </div>
                )}

                <section className={pageStyles.section}>
                    <h2>Your Sources ({sources.length}/10)</h2>
                    {sources.length === 0 ? (
                        <p className={pageStyles.empty}>No sources added yet.</p>
                    ) : (
                        <div className={pageStyles.grid}>
                            {sources.map((source) => (
                                <div key={source.id} className={pageStyles.sourceCard}>
                                    <span className={pageStyles.icon}>{getIcon(source.source_type)}</span>
                                    <div className={pageStyles.info}>
                                        <h4>{source.name}</h4>
                                        <a href={source.url} target="_blank" rel="noopener noreferrer">
                                            {source.url.slice(0, 40)}...
                                        </a>
                                    </div>
                                    <button
                                        className={pageStyles.removeBtn}
                                        onClick={() => removeSource(source.id)}
                                    >
                                        ×
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </section>

                <section className={pageStyles.section}>
                    <h2>Suggested Sources</h2>
                    <p className={pageStyles.sectionDesc}>Quick add from our curated defaults</p>
                    <div className={pageStyles.grid}>
                        {defaults
                            .filter(d => !sources.find(s => s.url === d.url))
                            .slice(0, 8)
                            .map((source) => (
                                <div key={source.id} className={pageStyles.sourceCard}>
                                    <span className={pageStyles.icon}>{getIcon(source.source_type)}</span>
                                    <div className={pageStyles.info}>
                                        <h4>{source.name}</h4>
                                        <span className="badge">{source.source_type}</span>
                                    </div>
                                    <button
                                        className="btn btn-secondary"
                                        onClick={() => addDefault(source)}
                                        disabled={sources.length >= 10}
                                    >
                                        + Add
                                    </button>
                                </div>
                            ))}
                    </div>
                </section>
            </main>
        </div>
    );
}
