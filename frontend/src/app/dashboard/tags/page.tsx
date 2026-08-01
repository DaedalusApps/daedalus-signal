'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import { getAuthHeaders } from '@/lib/auth';
import styles from '../dashboard.module.css';
import pageStyles from './tags.module.css';
import { API_BASE } from '@/lib/api';

const MAX_TAGS = 50;

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
            const headers = getAuthHeaders();
            const [userRes, defaultRes] = await Promise.all([
                fetch(`${API_BASE}/api/tags`, { headers }),
                fetch(`${API_BASE}/api/tags/defaults`, { headers }),
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

        const res = await fetch(`${API_BASE}/api/tags`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
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
        const res = await fetch(`${API_BASE}/api/tags/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders(),
        });

        if (res.ok) {
            setTags(tags.filter(t => t.id !== id));
        }
    };

    const addDefaultTag = async (tag: Tag) => {
        const res = await fetch(`${API_BASE}/api/tags`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
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
            <Sidebar activePage="tags" />

            <main className={styles.main}>
                <header className={styles.header}>
                    <div>
                        <h1>Tags</h1>
                        <p>Keywords to personalize your feed (max {MAX_TAGS})</p>
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
                            disabled={tags.length >= MAX_TAGS}
                        >
                            Add Tag
                        </button>
                    </form>
                    {error && <div className={pageStyles.error}>{error}</div>}
                </div>

                <section className={pageStyles.section}>
                    <h2>Your Tags ({tags.length}/{MAX_TAGS})</h2>
                    {tags.length === 0 ? (
                        <p className={pageStyles.empty}>No tags added. Add tags to personalize your feed.</p>
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
                    <p className={pageStyles.sectionDesc}>Popular tags in the tech community</p>
                    <div className={pageStyles.tagGrid}>
                        {defaults
                            .filter(d => !tags.find(t => t.name === d.name))
                            .map((tag) => (
                                <button
                                    key={tag.id}
                                    className={pageStyles.suggestedTag}
                                    onClick={() => addDefaultTag(tag)}
                                    disabled={tags.length >= MAX_TAGS}
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
