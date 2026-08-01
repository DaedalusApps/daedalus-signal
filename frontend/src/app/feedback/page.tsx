'use client';

import { useState } from 'react';
import Link from 'next/link';
import styles from './feedback.module.css';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://signal.daedalusapps.com';

export default function FeedbackPage() {
    const [email, setEmail] = useState('');
    const [message, setMessage] = useState('');
    const [type, setType] = useState('general');
    const [submitted, setSubmitted] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const res = await fetch(`${API_URL}/api/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, message, feedback_type: type }),
            });

            const data = await res.json();

            if (!res.ok) {
                setError(data.error || 'Failed to submit feedback');
                return;
            }

            setSubmitted(true);
        } catch (err) {
            setError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className={styles.main}>
            <Link href="/" className={styles.backLink}>
                ← Back to Home
            </Link>

            <div className={styles.container}>
                <h1 className="text-gradient">Feedback</h1>
                <p className={styles.subtitle}>
                    Help us improve DaedalusSignal. We'd love to hear from you!
                </p>

                {submitted ? (
                    <div className={styles.success}>
                        <span className={styles.successIcon}>✓</span>
                        <h2>Thank you!</h2>
                        <p>Your feedback has been submitted. We appreciate your input!</p>
                        <Link href="/" className="btn btn-primary">
                            Back to Home
                        </Link>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} className={styles.form}>
                        {error && <div className={styles.error}>{error}</div>}

                        <div className={styles.field}>
                            <label>Feedback Type</label>
                            <select value={type} onChange={(e) => setType(e.target.value)}>
                                <option value="general">General Feedback</option>
                                <option value="feature">Feature Request</option>
                                <option value="bug">Bug Report</option>
                            </select>
                        </div>

                        <div className={styles.field}>
                            <label>Email</label>
                            <input
                                type="email"
                                placeholder="your@email.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>

                        <div className={styles.field}>
                            <label>Message</label>
                            <textarea
                                placeholder="Tell us what you think..."
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                rows={5}
                                required
                            />
                        </div>

                        <button type="submit" className="btn btn-primary" disabled={loading}>
                            {loading ? 'Submitting...' : 'Submit Feedback'}
                        </button>
                    </form>
                )}
            </div>
        </main>
    );
}
