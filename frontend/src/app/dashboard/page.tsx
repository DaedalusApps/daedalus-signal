'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Sidebar from '@/components/Sidebar';
import { getAuthHeaders, isAuthenticated } from '@/lib/auth';
import styles from './dashboard.module.css';
import { Content } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://signal.daedalusapps.com';

export default function Dashboard() {
    const [content, setContent] = useState<Content[]>([]);
    const [sourcesCount, setSourcesCount] = useState<number>(0);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>('all');

    useEffect(() => {
        // Redirect to login if not authenticated
        if (!isAuthenticated()) {
            window.location.href = '/';
            return;
        }

        const loadData = async () => {
            try {
                const headers = getAuthHeaders();
                // Fetch content feed and sources count in parallel
                const [contentRes, sourcesRes] = await Promise.all([
                    fetch(`${API_URL}/api/content/feed`, { headers }),
                    fetch(`${API_URL}/api/sources`, { headers }),
                ]);

                if (contentRes.ok) {
                    const contentData = await contentRes.json();
                    setContent(contentData.feed || []);
                }

                if (sourcesRes.ok) {
                    const sourcesData = await sourcesRes.json();
                    setSourcesCount((sourcesData.sources || []).length);
                }
            } catch (err) {
                console.error('Failed to load data:', err);
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

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

    const filteredContent = (filter === 'all'
        ? content
        : content.filter(c => c.source?.source_type === filter)
    ).sort((a, b) => b.relevance_score - a.relevance_score);

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
            <Sidebar activePage="feed" />

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
                            className={`${styles.filterBtn} ${filter === 'twitter' ? styles.active : ''}`}
                            onClick={() => setFilter('twitter')}
                        >
                            X
                        </button>
                        <button
                            className={`${styles.filterBtn} ${filter === 'youtube' ? styles.active : ''}`}
                            onClick={() => setFilter('youtube')}
                        >
                            YouTube
                        </button>
                        <button
                            className={`${styles.filterBtn} ${styles.disabled}`}
                            title="Coming Soon"
                            disabled
                        >
                            LinkedIn
                        </button>
                        <button
                            className={`${styles.filterBtn} ${styles.disabled}`}
                            title="Coming Soon"
                            disabled
                        >
                            GitHub
                        </button>
                    </div>
                </header>

                {filteredContent.length === 0 ? (
                    <div className={styles.empty}>
                        {sourcesCount > 0 ? (
                            <>
                                <span className={styles.emptyIcon}>⏳</span>
                                <h3>Feed pending</h3>
                                <p>
                                    You have {sourcesCount} source{sourcesCount !== 1 ? 's' : ''} configured.
                                    Your feed will populate on the next ingestion cycle.
                                </p>
                                <p className={styles.cycleInfo}>
                                    Content is fetched every 6 hours. Check back soon!
                                </p>
                            </>
                        ) : (
                            <>
                                <span className={styles.emptyIcon}>📭</span>
                                <h3>No content yet</h3>
                                <p>Add some sources to start seeing content in your feed.</p>
                                <Link href="/dashboard/sources" className="btn btn-primary">
                                    Add Sources
                                </Link>
                            </>
                        )}
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
