'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import styles from './page.module.css';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

function VerifyContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const email = searchParams.get('email') || '';

    const [code, setCode] = useState(['', '', '', '', '', '']);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);
    const [resendCooldown, setResendCooldown] = useState(0);
    const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

    // Countdown for resend cooldown
    useEffect(() => {
        if (resendCooldown > 0) {
            const timer = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000);
            return () => clearTimeout(timer);
        }
    }, [resendCooldown]);

    // Redirect if no email provided
    useEffect(() => {
        if (!email) {
            router.push('/');
        }
    }, [email, router]);

    const handleInputChange = (index: number, value: string) => {
        // Only allow digits
        if (value && !/^\d$/.test(value)) return;

        const newCode = [...code];
        newCode[index] = value;
        setCode(newCode);

        // Auto-focus next input
        if (value && index < 5) {
            inputRefs.current[index + 1]?.focus();
        }

        // Auto-submit when all digits entered
        if (value && index === 5 && newCode.every(d => d !== '')) {
            handleVerify(newCode.join(''));
        }
    };

    const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
        if (e.key === 'Backspace' && !code[index] && index > 0) {
            inputRefs.current[index - 1]?.focus();
        }
    };

    const handlePaste = (e: React.ClipboardEvent) => {
        e.preventDefault();
        const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
        if (pasted.length === 6) {
            const newCode = pasted.split('');
            setCode(newCode);
            inputRefs.current[5]?.focus();
            handleVerify(pasted);
        }
    };

    const handleVerify = async (verifyCode?: string) => {
        const codeToVerify = verifyCode || code.join('');
        if (codeToVerify.length !== 6) {
            setError('Please enter the 6-digit code');
            return;
        }

        setError('');
        setSuccess('');
        setLoading(true);

        try {
            const response = await fetch(`${API_URL}/api/auth/verify-email`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ email, code: codeToVerify }),
            });

            const data = await response.json();

            if (!response.ok) {
                setError(data.error || 'Verification failed');
                setCode(['', '', '', '', '', '']);
                inputRefs.current[0]?.focus();
                return;
            }

            setSuccess('Email verified successfully! Redirecting...');
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);
        } catch (err) {
            setError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleResend = async () => {
        if (resendCooldown > 0) return;

        setError('');
        setSuccess('');

        try {
            const response = await fetch(`${API_URL}/api/auth/resend-verification`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ email }),
            });

            const data = await response.json();

            if (!response.ok) {
                setError(data.error || 'Failed to resend code');
                return;
            }

            setSuccess('New verification code sent!');
            setResendCooldown(60);
            setCode(['', '', '', '', '', '']);
            inputRefs.current[0]?.focus();
        } catch (err) {
            setError('Network error. Please try again.');
        }
    };

    if (!email) {
        return null;
    }

    return (
        <main className={styles.main}>
            <div className={styles.card}>
                <div className={styles.icon}>📧</div>
                <h1>Verify Your Email</h1>
                <p className={styles.description}>
                    We sent a 6-digit verification code to<br />
                    <strong>{email}</strong>
                </p>

                {error && <div className={styles.error}>{error}</div>}
                {success && <div className={styles.success}>{success}</div>}

                <div className={styles.codeInputs} onPaste={handlePaste}>
                    {code.map((digit, index) => (
                        <input
                            key={index}
                            ref={el => { inputRefs.current[index] = el; }}
                            type="text"
                            inputMode="numeric"
                            maxLength={1}
                            value={digit}
                            onChange={(e) => handleInputChange(index, e.target.value)}
                            onKeyDown={(e) => handleKeyDown(index, e)}
                            className={styles.codeInput}
                            disabled={loading}
                            autoFocus={index === 0}
                        />
                    ))}
                </div>

                <button
                    className="btn btn-primary"
                    onClick={() => handleVerify()}
                    disabled={loading || code.some(d => d === '')}
                >
                    {loading ? 'Verifying...' : 'Verify Email'}
                </button>

                <div className={styles.resend}>
                    <p>Didn't receive the code?</p>
                    <button
                        onClick={handleResend}
                        disabled={resendCooldown > 0}
                        className={styles.resendButton}
                    >
                        {resendCooldown > 0
                            ? `Resend in ${resendCooldown}s`
                            : 'Resend Code'
                        }
                    </button>
                </div>

                <Link href="/" className={styles.backLink}>
                    Back to login
                </Link>
            </div>
        </main>
    );
}

export default function VerifyPage() {
    return (
        <Suspense fallback={<div className={styles.main}><div className={styles.card}>Loading...</div></div>}>
            <VerifyContent />
        </Suspense>
    );
}
