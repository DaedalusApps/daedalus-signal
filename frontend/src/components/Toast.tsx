'use client';

import { useEffect, useState } from 'react';
import styles from './Toast.module.css';

interface ToastProps {
    message: string;
    type?: 'info' | 'success' | 'warning';
    duration?: number;
    onClose?: () => void;
}

export default function Toast({ message, type = 'info', duration = 5000, onClose }: ToastProps) {
    const [visible, setVisible] = useState(true);

    useEffect(() => {
        const timer = setTimeout(() => {
            setVisible(false);
            onClose?.();
        }, duration);

        return () => clearTimeout(timer);
    }, [duration, onClose]);

    if (!visible) return null;

    const icons = {
        info: '🔔',
        success: '✅',
        warning: '⚠️',
    };

    return (
        <div className={`${styles.toast} ${styles[type]}`}>
            <span className={styles.icon}>{icons[type]}</span>
            <span className={styles.message}>{message}</span>
            <button className={styles.close} onClick={() => { setVisible(false); onClose?.(); }}>
                ×
            </button>
        </div>
    );
}
