'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import styles from './dashboard.module.css';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

interface Content {
    id: number;
    title: string;
    description: string;
    url: string;
    content_type: string;
    relevance_score: number;
    source: {
        name: string;
        source_type: string;
    };
    scraped_at: string;
}

interface User {
    id: number;
    email: string;
    is_admin: boolean;
    digest_enabled: boolean;
    onboarding_complete: boolean;
}

export default function Dashboard() {
    const [user, setUser] = useState<User | null>(null);
    const [content, setContent] = useState<Content[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>('all');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            // Fetch user
            const userRes = await fetch(`${API_URL}/api/auth/me`, {
                credentials: 'include',
            });

            if (!userRes.ok) {
                window.location.href = '/';
                return;
            }

            const userData = await userRes.json();
            setUser(userData.user);

            // Fetch content
            const contentRes = await fetch(`${API_URL}/api/content/feed?limit=50`, {
                credentials: 'include',
            });

            if (contentRes.ok) {
                const contentData = await contentRes.json();
                setContent(contentData.feed || []);
            }
        } catch (err) {
            console.error('Failed to load data:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = async () => {
        await fetch(`${API_URL}/api/auth/logout`, {
            method: 'POST',
            credentials: 'include',
        });
        window.location.href = '/';
    };

    const getSourceIcon = (type: string) => {
        switch (type) {
            case 'youtube': return '▶️';
            case 'twitter': return '𝕏';
            case 'linkedin': return '💼';
            case 'github': return '⌨️';
            default: return '📄';
        }
    };

    const getTypeColor = (type: string) => {
        switch (type) {
            case 'youtube': return '#ff0000';
            case 'twitter': return '#1da1f2';
            case 'linkedin': return '#0077b5';
            case 'github': return '#6e5494';
            default: return '#6366f1';
        }
    };

    const filteredContent = filter === 'all'
        ? content
        : content.filter(c => c.source?.source_type === filter);

    if (loading) {
        return (
            <div className={styles.loading}>
                <div className={styles.spinner}></div>
                <p>Loading your feed...</p>
            </div>
        );
    }

    return (
        <div className={styles.dashboard}>
            {/* Sidebar */}
            <aside className={styles.sidebar}>
                <div className={styles.logo}>
                    <span className="text-gradient">Daedalus</span>Signal
                </div>

                <nav className={styles.nav}>
                    <Link href="/dashboard" className={`${styles.navItem} ${styles.active}`}>
                        <span>📊</span> Feed
                    </Link>
                    <Link href="/dashboard/sources" className={styles.navItem}>
                        <span>🔗</span> Sources
                    </Link>
                    <Link href="/dashboard/tags" className={styles.navItem}>
                        <span>🏷️</span> Tags
                    </Link>
                    <Link href="/dashboard/digest" className={styles.navItem}>
                        <span>📧</span> Digest
                    </Link>
                    {user?.is_admin && (
                        <Link href="/dashboard/admin" className={styles.navItem}>
                            <span>⚙️</span> Admin
                        </Link>
                    )}
                </nav>

                <div className={styles.userSection}>
                    <div className={styles.userInfo}>
                        <div className={styles.avatar}>
                            {user?.email.charAt(0).toUpperCase()}
                        </div>
                        <div>
                            <p className={styles.userEmail}>{user?.email}</p>
                            {user?.is_admin && <span className={styles.adminBadge}>Admin</span>}
                        </div>
                    </div>
                    <button onClick={handleLogout} className={styles.logoutBtn}>
                        Logout
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className={styles.main}>
                <header className={styles.header}>
                    <div>
                        <h1>Your Feed</h1>
                        <p>Latest curated content from your sources</p>
                    </div>

                    <div className={styles.filters}>
                        <button
                            className={`${styles.filterBtn} ${filter === 'all' ? styles.active : ''}`}
                            onClick={() => setFilter('all')}
                        >
                            All
                        </button>
                        <button
                            className={`${styles.filterBtn} ${filter === 'youtube' ? styles.active : ''}`}
                            onClick={() => setFilter('youtube')}
                        >
                            YouTube
                        </button>
                        <button
                            className={`${styles.filterBtn} ${filter === 'twitter' ? styles.active : ''}`}
                            onClick={() => setFilter('twitter')}
                        >
                            X
                        </button>
                        <button
                            className={`${styles.filterBtn} ${filter === 'github' ? styles.active : ''}`}
                            onClick={() => setFilter('github')}
                        >
                            GitHub
                        </button>
                    </div>
                </header>

                {filteredContent.length === 0 ? (
                    <div className={styles.empty}>
                        <span className={styles.emptyIcon}>📭</span>
                        <h3>No content yet</h3>
                        <p>Add some sources to start seeing content in your feed.</p>
                        <Link href="/dashboard/sources" className="btn btn-primary">
                            Add Sources
                        </Link>
                    </div>
                ) : (
                    <div className={styles.contentGrid}>
                        {filteredContent.map((item, index) => (
                            <article
                                key={item.id || index}
                                className={styles.contentCard}
                                style={{ animationDelay: `${index * 0.05}s` }}
                            >
                                <div className={styles.cardHeader}>
                                    <span
                                        className={styles.sourceType}
                                        style={{ color: getTypeColor(item.source?.source_type || 'default') }}
                                    >
                                        {getSourceIcon(item.source?.source_type || 'default')}
                                        {item.source?.name}
                                    </span>
                                    <span className={styles.score}>
                                        {item.relevance_score}%
                                    </span>
                                </div>

                                <h3 className={styles.cardTitle}>
                                    <a href={item.url} target="_blank" rel="noopener noreferrer">
                                        {item.title}
                                    </a>
                                </h3>

                                {item.description && (
                                    <p className={styles.cardDescription}>
                                        {item.description.slice(0, 150)}
                                        {item.description.length > 150 && '...'}
                                    </p>
                                )}

                                <div className={styles.cardFooter}>
                                    <span className={styles.contentType}>{item.content_type}</span>
                                    <a
                                        href={item.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className={styles.viewLink}
                                    >
                                        View →
                                    </a>
                                </div>
                            </article>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}
