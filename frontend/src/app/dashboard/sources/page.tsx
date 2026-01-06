'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import styles from '../dashboard.module.css';
import pageStyles from './sources.module.css';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

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
    const [newSource, setNewSource] = useState({ name: '', url: '', source_type: 'youtube' });
    const [error, setError] = useState('');

    useEffect(() => {
        loadSources();
    }, []);

    const loadSources = async () => {
        try {
            const [userRes, defaultRes] = await Promise.all([
                fetch(`${API_URL}/api/sources`, { credentials: 'include' }),
                fetch(`${API_URL}/api/sources/defaults`, { credentials: 'include' }),
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

        const res = await fetch(`${API_URL}/api/sources`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(newSource),
        });

        const data = await res.json();

        if (!res.ok) {
            setError(data.error || 'Failed to add source');
            return;
        }

        setSources([...sources, data.source]);
        setNewSource({ name: '', url: '', source_type: 'youtube' });
        setShowAdd(false);
    };

    const removeSource = async (id: number) => {
        const res = await fetch(`${API_URL}/api/sources/${id}`, {
            method: 'DELETE',
            credentials: 'include',
        });

        if (res.ok) {
            setSources(sources.filter(s => s.id !== id));
        }
    };

    const addDefault = async (source: Source) => {
        const res = await fetch(`${API_URL}/api/sources`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
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
            <aside className={styles.sidebar}>
                <div className={styles.logo}>
                    <span className="text-gradient">Daedalus</span>Signal
                </div>
                <nav className={styles.nav}>
                    <Link href="/dashboard" className={styles.navItem}>
                        <span>📊</span> Feed
                    </Link>
                    <Link href="/dashboard/sources" className={`${styles.navItem} ${styles.active}`}>
                        <span>🔗</span> Sources
                    </Link>
                    <Link href="/dashboard/tags" className={styles.navItem}>
                        <span>🏷️</span> Tags
                    </Link>
                </nav>
            </aside>

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
                            <select
                                value={newSource.source_type}
                                onChange={(e) => setNewSource({ ...newSource, source_type: e.target.value })}
                            >
                                <option value="youtube">YouTube Channel</option>
                                <option value="twitter">X (Twitter) Account</option>
                                <option value="github">GitHub Repository</option>
                                <option value="linkedin">LinkedIn Profile</option>
                            </select>
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
