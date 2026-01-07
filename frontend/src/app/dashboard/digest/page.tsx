'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import styles from '../dashboard.module.css';
import pageStyles from './digest.module.css';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

import { User } from '@/types';

export default function DigestPage() {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        loadUser();
    }, []);

    const loadUser = async () => {
        try {
            const res = await fetch(`${API_URL}/api/auth/me`, {
                credentials: 'include',
            });
            if (res.ok) {
                const data = await res.json();
                setUser(data.user);
            }
        } catch (err) {
            console.error('Failed to load user:', err);
        } finally {
            setLoading(false);
        }
    };

    const toggleDigest = async () => {
        if (!user) return;
        setSaving(true);

        try {
            const res = await fetch(`${API_URL}/api/auth/me`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ digest_enabled: !user.digest_enabled }),
            });

            if (res.ok) {
                const data = await res.json();
                setUser(data.user);
            }
        } catch (err) {
            console.error('Failed to update digest setting:', err);
        } finally {
            setSaving(false);
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
            <Sidebar activePage="digest" />

            <main className={styles.main}>
                <header className={styles.header}>
                    <div>
                        <h1>Email Digest</h1>
                        <p>Configure your daily email digest preferences</p>
                    </div>
                </header>

                <div className={pageStyles.digestCard}>
                    <div className={pageStyles.cardHeader}>
                        <div>
                            <h3>Daily Digest Email</h3>
                            <p>Receive a curated summary of the day&apos;s top content in your inbox.</p>
                        </div>
                        <button
                            className={`${pageStyles.toggle} ${user?.digest_enabled ? pageStyles.enabled : ''}`}
                            onClick={toggleDigest}
                            disabled={saving}
                        >
                            <span className={pageStyles.toggleSwitch}></span>
                        </button>
                    </div>

                    <div className={pageStyles.status}>
                        <span className={pageStyles.statusIcon}>
                            {user?.digest_enabled ? '✅' : '⏸️'}
                        </span>
                        <span>
                            {user?.digest_enabled
                                ? 'Digest is enabled. You\'ll receive emails at 8:00 AM.'
                                : 'Digest is paused. Enable to receive daily updates.'}
                        </span>
                    </div>
                </div>

                <div className={pageStyles.infoCard}>
                    <h4>What&apos;s included in your digest?</h4>
                    <ul>
                        <li><span>📊</span> Top 10 highest-scoring content items from the past 24 hours</li>
                        <li><span>🏷️</span> Content filtered by your selected tags</li>
                        <li><span>🔗</span> Only from your subscribed sources</li>
                        <li><span>📅</span> Delivered daily at 8:00 AM your local time</li>
                    </ul>
                </div>
            </main>
        </div>
    );
}
