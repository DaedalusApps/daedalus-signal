'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { setToken } from '@/lib/auth';
import { API_BASE } from '@/lib/api';
import styles from './page.module.css';

const TURNSTILE_SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY || '';

declare global {
    interface Window {
        turnstile?: {
            render: (container: string | HTMLElement, options: {
                sitekey: string;
                callback: (token: string) => void;
                'error-callback'?: () => void;
                'expired-callback'?: () => void;
            }) => string;
            reset: (widgetId: string) => void;
            remove: (widgetId: string) => void;
        };
    }
}

export default function Home() {
    const [showLogin, setShowLogin] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isRegister, setIsRegister] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [turnstileToken, setTurnstileToken] = useState('');
    const turnstileRef = useRef<HTMLDivElement>(null);
    const widgetIdRef = useRef<string | null>(null);

    // Load Turnstile script
    useEffect(() => {
        if (!TURNSTILE_SITE_KEY) return;

        const script = document.createElement('script');
        script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js';
        script.async = true;
        script.defer = true;
        document.head.appendChild(script);

        return () => {
            document.head.removeChild(script);
        };
    }, []);

    // Pre-warm the backend when login form is shown (prevents cold-start errors)
    useEffect(() => {
        if (showLogin) {
            // Fire-and-forget ping to wake up the backend
            fetch(`${API_BASE}/api/health`).catch(() => { });
        }
    }, [showLogin]);

    // Render Turnstile widget when in register mode
    useEffect(() => {
        if (!TURNSTILE_SITE_KEY || !isRegister || !showLogin) {
            // Clean up widget when not in register mode
            if (widgetIdRef.current && window.turnstile) {
                window.turnstile.remove(widgetIdRef.current);
                widgetIdRef.current = null;
            }
            setTurnstileToken('');
            return;
        }

        const renderWidget = () => {
            if (turnstileRef.current && window.turnstile && !widgetIdRef.current) {
                widgetIdRef.current = window.turnstile.render(turnstileRef.current, {
                    sitekey: TURNSTILE_SITE_KEY,
                    callback: (token: string) => {
                        setTurnstileToken(token);
                    },
                    'error-callback': () => {
                        setError('CAPTCHA error. Please try again.');
                        setTurnstileToken('');
                    },
                    'expired-callback': () => {
                        setTurnstileToken('');
                    }
                });
            }
        };

        // Wait for script to load
        const checkTurnstile = setInterval(() => {
            if (window.turnstile) {
                clearInterval(checkTurnstile);
                renderWidget();
            }
        }, 100);

        return () => {
            clearInterval(checkTurnstile);
            if (widgetIdRef.current && window.turnstile) {
                window.turnstile.remove(widgetIdRef.current);
                widgetIdRef.current = null;
            }
        };
    }, [isRegister, showLogin]);

    const handleSubmit = async (e: React.FormEvent, retryCount = 0) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        // Check Turnstile token for registration
        if (isRegister && TURNSTILE_SITE_KEY && !turnstileToken) {
            setError('Please complete the CAPTCHA verification');
            setLoading(false);
            return;
        }

        const endpoint = isRegister ? '/api/auth/register' : '/api/auth/login';
        const body: Record<string, string> = { email, password };
        if (isRegister && turnstileToken) {
            body.turnstile_token = turnstileToken;
        }

        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });

            const data = await response.json();

            if (!response.ok) {
                setError(data.error || 'Something went wrong');
                // Reset Turnstile on error
                if (widgetIdRef.current && window.turnstile) {
                    window.turnstile.reset(widgetIdRef.current);
                    setTurnstileToken('');
                }
                setLoading(false);
                return;
            }

            // Store JWT token
            if (data.token) {
                setToken(data.token);
            }

            // Redirect to dashboard on success
            window.location.href = '/dashboard';
        } catch (err) {
            // Retry once on network error (handles cold-start delays)
            if (retryCount < 1) {
                setError('Connecting to server...');
                setTimeout(() => {
                    handleSubmit(e, retryCount + 1);
                }, 1000);
                return;
            }
            setError('Network error. Is the backend running?');
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
                        Intelligence Aggregator
                    </div>

                    <h1 className={styles.title}>
                        <span className="text-gradient">Daedalus</span>Signal
                    </h1>

                    <p className={styles.subtitle}>
                        Cut through the noise. Surface the signal. Stay ahead of the frontier
                        with curated content from YouTube and X.
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

                                {/* Turnstile CAPTCHA - only shown for registration */}
                                {isRegister && TURNSTILE_SITE_KEY && (
                                    <div
                                        ref={turnstileRef}
                                        className={styles.turnstile}
                                    />
                                )}

                                <button
                                    type="submit"
                                    className="btn btn-primary"
                                    disabled={loading || (isRegister && !!TURNSTILE_SITE_KEY && !turnstileToken)}
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

                            {!isRegister && (
                                <p className={styles.forgotPassword}>
                                    <Link href="/forgot-password">Forgot password?</Link>
                                </p>
                            )}
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
                    <div className={`${styles.sourceCard} ${styles.linkedin} ${styles.comingSoon}`}>
                        <span className={styles.sourceIcon}>in</span>
                        <span>LinkedIn</span>
                        <span className={styles.badge}>Coming Soon</span>
                    </div>
                    <div className={`${styles.sourceCard} ${styles.github} ${styles.comingSoon}`}>
                        <span className={styles.sourceIcon}>⌨️</span>
                        <span>GitHub</span>
                        <span className={styles.badge}>Coming Soon</span>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className={styles.footer}>
                <p>© {new Date().getFullYear()} DaedalusApps. Built for the tech community.</p>
                <div className={styles.footerLinks}>
                    <Link href="/feedback">Feedback</Link>
                </div>
            </footer>
        </main>
    );
}
