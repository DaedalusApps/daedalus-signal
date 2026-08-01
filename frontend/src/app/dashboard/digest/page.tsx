'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import { getAuthHeaders, clearToken } from '@/lib/auth';
import styles from '../dashboard.module.css';
import pageStyles from './digest.module.css';
import { API_BASE } from '@/lib/api';

import { User } from '@/types';

export default function DigestPage() {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [deleting, setDeleting] = useState(false);

    useEffect(() => {
        loadUser();
    }, []);

    const loadUser = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/auth/me`, {
                headers: getAuthHeaders(),
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
            const res = await fetch(`${API_BASE}/api/auth/me`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
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

    const deleteAccount = async () => {
        if (!confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
            return;
        }

        if (!confirm('FINAL WARNING: This will permanently delete all your data including sources, tags, and preferences. Are you absolutely sure?')) {
            return;
        }

        setDeleting(true);
        try {
            const res = await fetch(`${API_BASE}/api/auth/me`, {
                method: 'DELETE',
                headers: getAuthHeaders(),
            });

            if (res.ok) {
                clearToken();
                alert('Account deleted successfully.');
                window.location.href = '/';
            } else {
                const data = await res.json();
                alert(data.error || 'Failed to delete account');
            }
        } catch (err) {
            console.error('Failed to delete account:', err);
            alert('Failed to delete account. Please try again.');
        } finally {
            setDeleting(false);
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
                        <li><span>📊</span> Top 10 content items from the past 24 hours</li>
                        <li><span>🔗</span> Only from your subscribed sources</li>
                        <li><span>📅</span> Delivered daily at 8:00 AM your local time</li>
                    </ul>
                </div>

                <div className={pageStyles.dangerZone}>
                    <h4>⚠️ Danger Zone</h4>
                    <div className={pageStyles.dangerContent}>
                        <div>
                            <h5>Delete Account</h5>
                            <p>Permanently delete your account and all associated data. This cannot be undone.</p>
                        </div>
                        <button
                            className={pageStyles.deleteBtn}
                            onClick={deleteAccount}
                            disabled={deleting}
                        >
                            {deleting ? 'Deleting...' : 'Delete Account'}
                        </button>
                    </div>
                </div>
            </main>
        </div>
    );
}
