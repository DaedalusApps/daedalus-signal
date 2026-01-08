'use client';

import { useState } from 'react';
import Link from 'next/link';
import styles from './page.module.css';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export default function ForgotPasswordPage() {
    const [email, setEmail] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);
    const [submitted, setSubmitted] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setLoading(true);

        try {
            const response = await fetch(`${API_URL}/api/auth/forgot-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ email, message }),
            });

            const data = await response.json();

            if (!response.ok) {
                setError(data.error || 'Something went wrong');
                return;
            }

            setSuccess(data.message);
            setSubmitted(true);
        } catch (err) {
            setError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className={styles.main}>
            <div className={styles.card}>
                <div className={styles.icon}>🔑</div>
                <h1>Password Reset Request</h1>

                {!submitted ? (
                    <>
                        <p className={styles.description}>
                            Submit a request to reset your password. An administrator will review your request and assist you.
                        </p>

                        <div className={styles.notice}>
                            <strong>Note:</strong> Automated password reset via email is planned for a future update.
                            For now, requests are handled manually by our team.
                        </div>

                        {error && <div className={styles.error}>{error}</div>}

                        <form onSubmit={handleSubmit}>
                            <input
                                type="email"
                                placeholder="Email address"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                disabled={loading}
                            />
                            <textarea
                                placeholder="Additional information (optional) - e.g., when you created the account, any details that might help verify your identity"
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                rows={3}
                                disabled={loading}
                                className={styles.textarea}
                            />
                            <button
                                type="submit"
                                className="btn btn-primary"
                                disabled={loading || !email}
                            >
                                {loading ? 'Submitting...' : 'Submit Request'}
                            </button>
                        </form>
                    </>
                ) : (
                    <>
                        <div className={styles.successBox}>
                            <p>{success}</p>
                            <p className={styles.successNote}>
                                We typically respond within 24-48 hours. Please check your email for further instructions.
                            </p>
                        </div>
                    </>
                )}

                <Link href="/" className={styles.backLink}>
                    Back to login
                </Link>
            </div>
        </main>
    );
}
