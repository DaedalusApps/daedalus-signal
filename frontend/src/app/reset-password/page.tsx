'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import styles from '../forgot-password/page.module.css';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://signal.daedalusapps.com';

function ResetPasswordForm() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const token = searchParams.get('token');

    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [validating, setValidating] = useState(true);
    const [tokenValid, setTokenValid] = useState(false);
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        if (!token) {
            setValidating(false);
            setError('No reset token provided');
            return;
        }

        // Validate the token
        const validateToken = async () => {
            try {
                const response = await fetch(`${API_URL}/api/auth/reset-password/${token}`, {
                    method: 'GET',
                });
                const data = await response.json();
                setTokenValid(data.valid);
                if (!data.valid) {
                    setError('This reset link is invalid or has expired. Please request a new one.');
                }
            } catch (err) {
                setError('Failed to validate reset link. Please try again.');
            } finally {
                setValidating(false);
            }
        };

        validateToken();
    }, [token]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (password.length < 8) {
            setError('Password must be at least 8 characters');
            return;
        }

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        setLoading(true);

        try {
            const response = await fetch(`${API_URL}/api/auth/reset-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                setError(data.error || 'Something went wrong');
                return;
            }

            setSuccess(true);
            // Redirect to login after 3 seconds
            setTimeout(() => {
                router.push('/');
            }, 3000);
        } catch (err) {
            setError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    if (validating) {
        return (
            <main className={styles.main}>
                <div className={styles.card}>
                    <div className={styles.icon}>🔄</div>
                    <h1>Validating...</h1>
                    <p className={styles.description}>
                        Please wait while we verify your reset link.
                    </p>
                </div>
            </main>
        );
    }

    if (success) {
        return (
            <main className={styles.main}>
                <div className={styles.card}>
                    <div className={styles.icon}>✅</div>
                    <h1>Password Reset!</h1>
                    <div className={styles.successBox}>
                        <p>Your password has been successfully reset.</p>
                        <p className={styles.successNote}>
                            Redirecting you to login...
                        </p>
                    </div>
                    <Link href="/" className={styles.backLink}>
                        Go to login now
                    </Link>
                </div>
            </main>
        );
    }

    if (!tokenValid) {
        return (
            <main className={styles.main}>
                <div className={styles.card}>
                    <div className={styles.icon}>⚠️</div>
                    <h1>Invalid Link</h1>
                    <div className={styles.error}>{error}</div>
                    <Link href="/forgot-password" className="btn btn-primary" style={{ display: 'block', marginBottom: '1rem' }}>
                        Request New Reset Link
                    </Link>
                    <Link href="/" className={styles.backLink}>
                        Back to login
                    </Link>
                </div>
            </main>
        );
    }

    return (
        <main className={styles.main}>
            <div className={styles.card}>
                <div className={styles.icon}>🔐</div>
                <h1>Set New Password</h1>
                <p className={styles.description}>
                    Enter your new password below.
                </p>

                {error && <div className={styles.error}>{error}</div>}

                <form onSubmit={handleSubmit}>
                    <input
                        type="password"
                        placeholder="New password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        disabled={loading}
                        minLength={8}
                    />
                    <input
                        type="password"
                        placeholder="Confirm new password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                        disabled={loading}
                        minLength={8}
                    />
                    <button
                        type="submit"
                        className="btn btn-primary"
                        disabled={loading || !password || !confirmPassword}
                    >
                        {loading ? 'Resetting...' : 'Reset Password'}
                    </button>
                </form>

                <Link href="/" className={styles.backLink}>
                    Back to login
                </Link>
            </div>
        </main>
    );
}

export default function ResetPasswordPage() {
    return (
        <Suspense fallback={
            <main className={styles.main}>
                <div className={styles.card}>
                    <div className={styles.icon}>🔄</div>
                    <h1>Loading...</h1>
                </div>
            </main>
        }>
            <ResetPasswordForm />
        </Suspense>
    );
}
