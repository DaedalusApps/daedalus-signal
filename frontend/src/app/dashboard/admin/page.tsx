'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Sidebar from '@/components/Sidebar';
import styles from '../dashboard.module.css';
import pageStyles from './admin.module.css';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

interface Stats {
    users: number;
    sources: number;
    tags: number;
    contents: number;
    feedback_pending: number;
}

import { User } from '@/types';

interface Feedback {
    id: number;
    email: string;
    message: string;
    feedback_type: string;
    status: string;
    created_at: string;
}

export default function AdminPage() {
    const [stats, setStats] = useState<Stats | null>(null);
    const [users, setUsers] = useState<User[]>([]);
    const [feedback, setFeedback] = useState<Feedback[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'feedback'>('overview');
    const [testEmailLoading, setTestEmailLoading] = useState(false);
    const [testEmailMessage, setTestEmailMessage] = useState('');


    useEffect(() => {
        loadAdminData();
    }, []);

    const loadAdminData = async () => {
        try {
            const [statsRes, usersRes, feedbackRes] = await Promise.all([
                fetch(`${API_URL}/api/admin/stats`, { credentials: 'include' }),
                fetch(`${API_URL}/api/admin/users`, { credentials: 'include' }),
                fetch(`${API_URL}/api/admin/feedback`, { credentials: 'include' }),
            ]);

            if (!statsRes.ok) {
                setError('Access denied. Admin privileges required.');
                setLoading(false);
                return;
            }

            const statsData = await statsRes.json();
            setStats(statsData.stats);

            if (usersRes.ok) {
                const usersData = await usersRes.json();
                setUsers(usersData.users || []);
            }

            if (feedbackRes.ok) {
                const feedbackData = await feedbackRes.json();
                setFeedback(feedbackData.feedback || []);
            }
        } catch (err) {
            console.error('Failed to load admin data:', err);
            setError('Failed to load admin data');
        } finally {
            setLoading(false);
        }
    };

    const sendTestEmail = async () => {
        setTestEmailLoading(true);
        setTestEmailMessage('');
        try {
            const res = await fetch(`${API_URL}/api/admin/test-email`, {
                method: 'POST',
                credentials: 'include',
            });
            const data = await res.json();
            if (res.ok) {
                setTestEmailMessage(`✅ ${data.message}`);
            } else {
                setTestEmailMessage(`❌ ${data.error}`);
            }
        } catch (err) {
            setTestEmailMessage('❌ Failed to send test email');
        } finally {
            setTestEmailLoading(false);
        }
    };

    const deleteUser = async (userId: number, email: string) => {
        if (!confirm(`Are you sure you want to delete user ${email}? This cannot be undone.`)) {
            return;
        }
        try {
            const res = await fetch(`${API_URL}/api/admin/users/${userId}`, {
                method: 'DELETE',
                credentials: 'include',
            });
            if (res.ok) {
                setUsers(users.filter(u => u.id !== userId));
            } else {
                const data = await res.json();
                alert(data.error || 'Failed to delete user');
            }
        } catch (err) {
            alert('Failed to delete user');
        }
    };

    if (loading) {
        return (
            <div className={styles.loading}>
                <div className={styles.spinner}></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className={styles.dashboard}>
                <Sidebar activePage="feed" />
                <main className={styles.main}>
                    <div className={pageStyles.error}>
                        <h2>⚠️ Access Denied</h2>
                        <p>{error}</p>
                        <Link href="/dashboard" className="btn btn-primary">
                            Back to Dashboard
                        </Link>
                    </div>
                </main>
            </div>
        );
    }

    return (
        <div className={styles.dashboard}>
            <Sidebar activePage="admin" />

            <main className={styles.main}>
                <header className={styles.header}>
                    <div>
                        <h1>Admin Dashboard</h1>
                        <p>System overview and management</p>
                    </div>
                </header>

                {/* Tab Navigation */}
                <div className={pageStyles.tabs}>
                    <button
                        className={`${pageStyles.tab} ${activeTab === 'overview' ? pageStyles.active : ''}`}
                        onClick={() => setActiveTab('overview')}
                    >
                        Overview
                    </button>
                    <button
                        className={`${pageStyles.tab} ${activeTab === 'users' ? pageStyles.active : ''}`}
                        onClick={() => setActiveTab('users')}
                    >
                        Users ({users.length})
                    </button>
                    <button
                        className={`${pageStyles.tab} ${activeTab === 'feedback' ? pageStyles.active : ''}`}
                        onClick={() => setActiveTab('feedback')}
                    >
                        Feedback ({stats?.feedback_pending || 0} pending)
                    </button>
                </div>

                {/* Overview Tab */}
                {activeTab === 'overview' && stats && (
                    <div className={pageStyles.statsGrid}>
                        <div className={pageStyles.statCard}>
                            <span className={pageStyles.statIcon}>👥</span>
                            <div className={pageStyles.statInfo}>
                                <h3>{stats.users}</h3>
                                <p>Total Users</p>
                            </div>
                        </div>
                        <div className={pageStyles.statCard}>
                            <span className={pageStyles.statIcon}>🔗</span>
                            <div className={pageStyles.statInfo}>
                                <h3>{stats.sources}</h3>
                                <p>Sources</p>
                            </div>
                        </div>
                        <div className={pageStyles.statCard}>
                            <span className={pageStyles.statIcon}>🏷️</span>
                            <div className={pageStyles.statInfo}>
                                <h3>{stats.tags}</h3>
                                <p>Tags</p>
                            </div>
                        </div>
                        <div className={pageStyles.statCard}>
                            <span className={pageStyles.statIcon}>📄</span>
                            <div className={pageStyles.statInfo}>
                                <h3>{stats.contents}</h3>
                                <p>Content Items</p>
                            </div>
                        </div>
                        <div className={pageStyles.statCard}>
                            <span className={pageStyles.statIcon}>💬</span>
                            <div className={pageStyles.statInfo}>
                                <h3>{stats.feedback_pending}</h3>
                                <p>Pending Feedback</p>
                            </div>
                        </div>
                        <div className={pageStyles.statCard}>
                            <span className={pageStyles.statIcon}>📧</span>
                            <div className={pageStyles.statInfo}>
                                <button
                                    onClick={sendTestEmail}
                                    disabled={testEmailLoading}
                                    className={pageStyles.testEmailBtn}
                                >
                                    {testEmailLoading ? 'Sending...' : 'Send Test Email'}
                                </button>
                                {testEmailMessage && <p className={pageStyles.testEmailMsg}>{testEmailMessage}</p>}
                            </div>
                        </div>
                    </div>
                )}

                {/* Users Tab */}
                {activeTab === 'users' && (
                    <div className={pageStyles.tableWrapper}>
                        <table className={pageStyles.table}>
                            <thead>
                                <tr>
                                    <th>Email</th>
                                    <th>Admin</th>
                                    <th>Digest</th>
                                    <th>Onboarded</th>
                                    <th>Joined</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {users.map((user) => (
                                    <tr key={user.id}>
                                        <td>{user.email}</td>
                                        <td>
                                            <span className={user.is_admin ? pageStyles.badgeSuccess : pageStyles.badgeMuted}>
                                                {user.is_admin ? 'Yes' : 'No'}
                                            </span>
                                        </td>
                                        <td>
                                            <span className={user.digest_enabled ? pageStyles.badgeSuccess : pageStyles.badgeMuted}>
                                                {user.digest_enabled ? 'On' : 'Off'}
                                            </span>
                                        </td>
                                        <td>
                                            <span className={user.onboarding_complete ? pageStyles.badgeSuccess : pageStyles.badgeMuted}>
                                                {user.onboarding_complete ? 'Yes' : 'No'}
                                            </span>
                                        </td>
                                        <td>{user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}</td>
                                        <td>
                                            {!user.is_admin && (
                                                <button
                                                    onClick={() => deleteUser(user.id, user.email)}
                                                    className={pageStyles.deleteBtn}
                                                >
                                                    Delete
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Feedback Tab */}
                {activeTab === 'feedback' && (
                    <div className={pageStyles.feedbackList}>
                        {feedback.length === 0 ? (
                            <p className={pageStyles.empty}>No feedback yet.</p>
                        ) : (
                            feedback.map((item) => (
                                <div key={item.id} className={pageStyles.feedbackCard}>
                                    <div className={pageStyles.feedbackHeader}>
                                        <span className={pageStyles.feedbackEmail}>{item.email}</span>
                                        <span className={`${pageStyles.badge} ${pageStyles[item.status]}`}>
                                            {item.status}
                                        </span>
                                    </div>
                                    <p className={pageStyles.feedbackMessage}>{item.message}</p>
                                    <div className={pageStyles.feedbackFooter}>
                                        <span className={pageStyles.feedbackType}>{item.feedback_type}</span>
                                        <span className={pageStyles.feedbackDate}>
                                            {new Date(item.created_at).toLocaleString()}
                                        </span>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                )}
            </main>
        </div>
    );
}
