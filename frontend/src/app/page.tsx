'use client';

import { useState } from 'react';
import Link from 'next/link';
import styles from './page.module.css';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export default function Home() {
    const [showLogin, setShowLogin] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isRegister, setIsRegister] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const endpoint = isRegister ? '/api/auth/register' : '/api/auth/login';
            const response = await fetch(`${API_URL}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                setError(data.error || 'Something went wrong');
                return;
            }

            // Redirect to dashboard on success
            window.location.href = '/dashboard';
        } catch (err) {
            setError('Network error. Is the backend running?');
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className={styles.main}>
            {/* Hero Section */}
            <section className={styles.hero}>
                <div className={styles.heroContent}>
                    <div className={styles.badge}>
                        <span className={styles.badgeIcon}>✨</span>
                        AI Intelligence Aggregator
                    </div>

                    <h1 className={styles.title}>
                        <span className="text-gradient">Daedalus</span>Signal
                    </h1>

                    <p className={styles.subtitle}>
                        Cut through the noise. Surface the signal. Stay ahead of the AI frontier
                        with curated content from YouTube, X, LinkedIn, and GitHub.
                    </p>

                    <div className={styles.features}>
                        <div className={styles.feature}>
                            <span className={styles.featureIcon}>🎯</span>
                            <span>Keyword Filtering</span>
                        </div>
                        <div className={styles.feature}>
                            <span className={styles.featureIcon}>📊</span>
                            <span>Relevance Scoring</span>
                        </div>
                        <div className={styles.feature}>
                            <span className={styles.featureIcon}>📧</span>
                            <span>Daily Digest</span>
                        </div>
                    </div>

                    {!showLogin ? (
                        <div className={styles.cta}>
                            <button
                                className="btn btn-primary"
                                onClick={() => setShowLogin(true)}
                            >
                                Get Started
                                <span>→</span>
                            </button>
                            <a
                                href="https://ko-fi.com/daedalusapps"
                                target="_blank"
                                rel="noopener noreferrer"
                                className={styles.kofi}
                            >
                                ☕ Support on Ko-fi
                            </a>
                        </div>
                    ) : (
                        <div className={styles.loginCard}>
                            <h3>{isRegister ? 'Create Account' : 'Welcome Back'}</h3>

                            {error && <div className={styles.error}>{error}</div>}

                            <form onSubmit={handleSubmit}>
                                <input
                                    type="email"
                                    placeholder="Email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                />
                                <input
                                    type="password"
                                    placeholder="Password (min 8 characters)"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    minLength={8}
                                    required
                                />
                                <button
                                    type="submit"
                                    className="btn btn-primary"
                                    disabled={loading}
                                >
                                    {loading ? 'Please wait...' : (isRegister ? 'Create Account' : 'Sign In')}
                                </button>
                            </form>

                            <p className={styles.switchAuth}>
                                {isRegister ? 'Already have an account?' : "Don't have an account?"}
                                <button onClick={() => setIsRegister(!isRegister)}>
                                    {isRegister ? 'Sign In' : 'Register'}
                                </button>
                            </p>
                        </div>
                    )}
                </div>

                {/* Decorative elements */}
                <div className={styles.orb1}></div>
                <div className={styles.orb2}></div>
            </section>

            {/* Sources Section */}
            <section className={styles.sources}>
                <h2>Aggregate From</h2>
                <div className={styles.sourceGrid}>
                    <div className={`${styles.sourceCard} ${styles.youtube}`}>
                        <span className={styles.sourceIcon}>▶️</span>
                        <span>YouTube</span>
                    </div>
                    <div className={`${styles.sourceCard} ${styles.twitter}`}>
                        <span className={styles.sourceIcon}>𝕏</span>
                        <span>X (Twitter)</span>
                    </div>
                    <div className={`${styles.sourceCard} ${styles.linkedin}`}>
                        <span className={styles.sourceIcon}>in</span>
                        <span>LinkedIn</span>
                    </div>
                    <div className={`${styles.sourceCard} ${styles.github}`}>
                        <span className={styles.sourceIcon}>⌨️</span>
                        <span>GitHub</span>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className={styles.footer}>
                <p>© {new Date().getFullYear()} DaedalusApps. Built for the AI community.</p>
                <div className={styles.footerLinks}>
                    <Link href="/feedback">Feedback</Link>
                    <span>•</span>
                    <a href="https://ko-fi.com/daedalusapps" target="_blank" rel="noopener noreferrer">
                        Ko-fi
                    </a>
                </div>
            </footer>
        </main>
    );
}
