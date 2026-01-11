'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Sidebar from '@/components/Sidebar';
import { User } from '@/types';
import { getAuthHeaders } from '@/lib/auth';
import styles from '../dashboard.module.css';
import pageStyles from './admin.module.css';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
const DREAMHOST_WORKER_URL = process.env.NEXT_PUBLIC_DREAMHOST_WORKER_URL || '';

interface Stats {
    users: number;
    sources: number;
    tags: number;
    contents: number;
    feedback_pending: number;
}

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
    const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'feedback' | 'logs'>('overview');
    const [testEmailLoading, setTestEmailLoading] = useState(false);
    const [testEmailMessage, setTestEmailMessage] = useState('');
    const [scraperLoading, setScraperLoading] = useState(false);
    const [scraperMessage, setScraperMessage] = useState('');
    const [mailerLoading, setMailerLoading] = useState(false);
    const [mailerMessage, setMailerMessage] = useState('');
    const [logContent, setLogContent] = useState('');
    const [logType, setLogType] = useState<'scraper' | 'mailer'>('scraper');
    const [logLoading, setLogLoading] = useState(false);
    const [logInfo, setLogInfo] = useState('');


    useEffect(() => {
        loadAdminData();
    }, []);

    const loadAdminData = async () => {
        try {
            const headers = getAuthHeaders();
            const [statsRes, usersRes, feedbackRes] = await Promise.all([
                fetch(`${API_URL}/api/admin/stats`, { headers }),
                fetch(`${API_URL}/api/admin/users`, { headers }),
                fetch(`${API_URL}/api/admin/feedback`, { headers }),
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
            // If DreamHost worker is configured, use 2-step flow
            if (DREAMHOST_WORKER_URL) {
                // Step 1: Get signed payload from PythonAnywhere
                const payloadRes = await fetch(`${API_URL}/api/admin/test-email-payload`, {
                    headers: getAuthHeaders(),
                });

                if (!payloadRes.ok) {
                    const data = await payloadRes.json();
                    setTestEmailMessage(`❌ ${data.error || 'Failed to get email payload'}`);
                    return;
                }

                const { payload, payload_json, signature } = await payloadRes.json();

                // Step 2: Send to DreamHost worker
                // Include payload_json to ensure exact string matching for HMAC verification
                const dhRes = await fetch(`${DREAMHOST_WORKER_URL}/web_shim.php`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ payload, payload_json, signature }),
                });

                const dhData = await dhRes.json();
                if (dhRes.ok) {
                    setTestEmailMessage(`✅ ${dhData.message}`);
                } else {
                    setTestEmailMessage(`❌ ${dhData.error || 'DreamHost worker failed'}`);
                }
            } else {
                // Fallback to direct PA send if DreamHost not configured
                const res = await fetch(`${API_URL}/api/admin/test-email`, {
                    method: 'POST',
                    headers: getAuthHeaders(),
                });
                const data = await res.json();
                if (res.ok) {
                    setTestEmailMessage(`✅ ${data.message}`);
                } else {
                    setTestEmailMessage(`❌ ${data.error}`);
                }
            }
        } catch (err) {
            setTestEmailMessage('❌ Failed to send test email');
        } finally {
            setTestEmailLoading(false);
        }
    };

    const triggerScrape = async () => {
        setScraperLoading(true);
        setScraperMessage('');

        try {
            if (!DREAMHOST_WORKER_URL) {
                setScraperMessage('❌ DreamHost worker URL not configured');
                return;
            }

            // Step 1: Get signed payload from PythonAnywhere
            const payloadRes = await fetch(`${API_URL}/api/admin/trigger-scrape-payload`, {
                headers: getAuthHeaders(),
            });

            if (!payloadRes.ok) {
                const data = await payloadRes.json();
                setScraperMessage(`❌ ${data.error || 'Failed to get scrape payload'}`);
                return;
            }

            const { payload, payload_json, signature } = await payloadRes.json();

            // Step 2: Send to DreamHost worker
            const dhRes = await fetch(`${DREAMHOST_WORKER_URL}/web_shim.php`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ payload, payload_json, signature }),
            });

            const dhData = await dhRes.json();
            if (dhRes.ok) {
                setScraperMessage(`✅ ${dhData.message}`);
            } else {
                setScraperMessage(`❌ ${dhData.error || 'DreamHost worker failed'}`);
            }
        } catch (err) {
            setScraperMessage('❌ Failed to trigger scraper');
        } finally {
            setScraperLoading(false);
        }
    };

    const triggerMailer = async () => {
        setMailerLoading(true);
        setMailerMessage('');

        try {
            if (!DREAMHOST_WORKER_URL) {
                setMailerMessage('❌ DreamHost worker URL not configured');
                return;
            }

            // Step 1: Get signed payload from PythonAnywhere
            const payloadRes = await fetch(`${API_URL}/api/admin/trigger-mailer-payload`, {
                headers: getAuthHeaders(),
            });

            if (!payloadRes.ok) {
                const data = await payloadRes.json();
                setMailerMessage(`❌ ${data.error || 'Failed to get mailer payload'}`);
                return;
            }

            const { payload, payload_json, signature } = await payloadRes.json();

            // Step 2: Send to DreamHost worker
            const dhRes = await fetch(`${DREAMHOST_WORKER_URL}/web_shim.php`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ payload, payload_json, signature }),
            });

            const dhData = await dhRes.json();
            if (dhRes.ok) {
                setMailerMessage(`✅ ${dhData.message}`);
            } else {
                setMailerMessage(`❌ ${dhData.error || 'DreamHost worker failed'}`);
            }
        } catch (err) {
            setMailerMessage('❌ Failed to trigger mailer');
        } finally {
            setMailerLoading(false);
        }
    };

    const fetchLogs = async (type: 'scraper' | 'mailer') => {
        setLogLoading(true);
        setLogType(type);
        setLogContent('');
        setLogInfo('');

        try {
            if (!DREAMHOST_WORKER_URL) {
                setLogContent('DreamHost worker URL not configured');
                return;
            }

            // Step 1: Get signed payload from PythonAnywhere
            const payloadRes = await fetch(`${API_URL}/api/admin/get-logs-payload?log_type=${type}`, {
                headers: getAuthHeaders(),
            });

            if (!payloadRes.ok) {
                const data = await payloadRes.json();
                setLogContent(`Error: ${data.error || 'Failed to get logs payload'}`);
                return;
            }

            const { payload, payload_json, signature } = await payloadRes.json();

            // Step 2: Send to DreamHost worker
            const dhRes = await fetch(`${DREAMHOST_WORKER_URL}/web_shim.php`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ payload, payload_json, signature }),
            });

            const dhData = await dhRes.json();
            if (dhRes.ok) {
                setLogContent(dhData.content || '(Empty log)');
                setLogInfo(`Showing ${dhData.lines} of ${dhData.total_lines || dhData.lines} lines`);
            } else {
                setLogContent(`Error: ${dhData.error || 'DreamHost worker failed'}`);
            }
        } catch (err) {
            setLogContent('Failed to fetch logs');
        } finally {
            setLogLoading(false);
        }
    };

    const deleteUser = async (userId: number, email: string) => {
        if (!confirm(`Are you sure you want to delete user ${email}? This cannot be undone.`)) {
            return;
        }
        try {
            const res = await fetch(`${API_URL}/api/admin/users/${userId}`, {
                method: 'DELETE',
                headers: getAuthHeaders(),
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
                    <button
                        className={`${pageStyles.tab} ${activeTab === 'logs' ? pageStyles.active : ''}`}
                        onClick={() => setActiveTab('logs')}
                    >
                        Logs
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
                        <div className={pageStyles.statCard}>
                            <span className={pageStyles.statIcon}>🔄</span>
                            <div className={pageStyles.statInfo}>
                                <button
                                    onClick={triggerScrape}
                                    disabled={scraperLoading}
                                    className={pageStyles.testEmailBtn}
                                >
                                    {scraperLoading ? 'Running...' : 'Run Scrapers'}
                                </button>
                                {scraperMessage && <p className={pageStyles.testEmailMsg}>{scraperMessage}</p>}
                            </div>
                        </div>
                        <div className={pageStyles.statCard}>
                            <span className={pageStyles.statIcon}>📨</span>
                            <div className={pageStyles.statInfo}>
                                <button
                                    onClick={triggerMailer}
                                    disabled={mailerLoading}
                                    className={pageStyles.testEmailBtn}
                                >
                                    {mailerLoading ? 'Sending...' : 'Send Digests'}
                                </button>
                                {mailerMessage && <p className={pageStyles.testEmailMsg}>{mailerMessage}</p>}
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

                {/* Logs Tab */}
                {activeTab === 'logs' && (
                    <div className={pageStyles.logsContainer}>
                        <div className={pageStyles.logsButtons}>
                            <button
                                onClick={() => fetchLogs('scraper')}
                                disabled={logLoading}
                                className={`${pageStyles.logBtn} ${logType === 'scraper' ? pageStyles.active : ''}`}
                            >
                                {logLoading && logType === 'scraper' ? 'Loading...' : '🔄 Scraper Log'}
                            </button>
                            <button
                                onClick={() => fetchLogs('mailer')}
                                disabled={logLoading}
                                className={`${pageStyles.logBtn} ${logType === 'mailer' ? pageStyles.active : ''}`}
                            >
                                {logLoading && logType === 'mailer' ? 'Loading...' : '📨 Mailer Log'}
                            </button>
                        </div>
                        {logInfo && <p className={pageStyles.logInfo}>{logInfo}</p>}
                        <pre className={pageStyles.logContent}>
                            {logContent || 'Click a button above to load logs'}
                        </pre>
                    </div>
                )}
            </main>
        </div>
    );
}
