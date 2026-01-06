'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import styles from '../dashboard.module.css';
import pageStyles from './tags.module.css';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

interface Tag {
    id: number;
    name: string;
    category: string | null;
    is_default: boolean;
}

export default function TagsPage() {
    const [tags, setTags] = useState<Tag[]>([]);
    const [defaults, setDefaults] = useState<Tag[]>([]);
    const [loading, setLoading] = useState(true);
    const [newTag, setNewTag] = useState('');
    const [error, setError] = useState('');

    useEffect(() => {
        loadTags();
    }, []);

    const loadTags = async () => {
        try {
            const [userRes, defaultRes] = await Promise.all([
                fetch(`${API_URL}/api/tags`, { credentials: 'include' }),
                fetch(`${API_URL}/api/tags/defaults`, { credentials: 'include' }),
            ]);

            if (userRes.ok) {
                const data = await userRes.json();
                setTags(data.tags || []);
            }

            if (defaultRes.ok) {
                const data = await defaultRes.json();
                setDefaults(data.tags || []);
            }
        } catch (err) {
            console.error('Failed to load tags:', err);
        } finally {
            setLoading(false);
        }
    };

    const addTag = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (!newTag.trim()) return;

        const res = await fetch(`${API_URL}/api/tags`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ name: newTag }),
        });

        const data = await res.json();

        if (!res.ok) {
            setError(data.error || 'Failed to add tag');
            return;
        }

        setTags([...tags, data.tag]);
        setNewTag('');
    };

    const removeTag = async (id: number) => {
        const res = await fetch(`${API_URL}/api/tags/${id}`, {
            method: 'DELETE',
            credentials: 'include',
        });

        if (res.ok) {
            setTags(tags.filter(t => t.id !== id));
        }
    };

    const addDefaultTag = async (tag: Tag) => {
        const res = await fetch(`${API_URL}/api/tags`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ name: tag.name, category: tag.category }),
        });

        if (res.ok) {
            const data = await res.json();
            setTags([...tags, data.tag]);
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
                    <Link href="/dashboard/sources" className={styles.navItem}>
                        <span>🔗</span> Sources
                    </Link>
                    <Link href="/dashboard/tags" className={`${styles.navItem} ${styles.active}`}>
                        <span>🏷️</span> Tags
                    </Link>
                </nav>
            </aside>

            <main className={styles.main}>
                <header className={styles.header}>
                    <div>
                        <h1>Tags</h1>
                        <p>Keywords used to filter and score content (max 20)</p>
                    </div>
                </header>

                <div className={pageStyles.addSection}>
                    <form onSubmit={addTag} className={pageStyles.form}>
                        <input
                            type="text"
                            placeholder="Add a new tag (e.g., machine learning)"
                            value={newTag}
                            onChange={(e) => setNewTag(e.target.value)}
                        />
                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={tags.length >= 20}
                        >
                            Add Tag
                        </button>
                    </form>
                    {error && <div className={pageStyles.error}>{error}</div>}
                </div>

                <section className={pageStyles.section}>
                    <h2>Your Tags ({tags.length}/20)</h2>
                    {tags.length === 0 ? (
                        <p className={pageStyles.empty}>No tags added. Add tags to filter content.</p>
                    ) : (
                        <div className={pageStyles.tagGrid}>
                            {tags.map((tag) => (
                                <div key={tag.id} className={pageStyles.tag}>
                                    <span>#{tag.name}</span>
                                    <button onClick={() => removeTag(tag.id)}>×</button>
                                </div>
                            ))}
                        </div>
                    )}
                </section>

                <section className={pageStyles.section}>
                    <h2>Suggested Tags</h2>
                    <p className={pageStyles.sectionDesc}>Popular tags in the AI community</p>
                    <div className={pageStyles.tagGrid}>
                        {defaults
                            .filter(d => !tags.find(t => t.name === d.name))
                            .map((tag) => (
                                <button
                                    key={tag.id}
                                    className={pageStyles.suggestedTag}
                                    onClick={() => addDefaultTag(tag)}
                                    disabled={tags.length >= 20}
                                >
                                    <span>#{tag.name}</span>
                                    <span className={pageStyles.plus}>+</span>
                                </button>
                            ))}
                    </div>
                </section>
            </main>
        </div>
    );
}
