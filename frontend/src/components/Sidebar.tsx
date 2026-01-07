'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useTheme } from '@/hooks/useTheme';
import styles from './Sidebar.module.css';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

import { User } from '@/types';

interface SidebarProps {
    activePage: 'feed' | 'sources' | 'tags' | 'digest' | 'admin';
}

export default function Sidebar({ activePage }: SidebarProps) {
    const [user, setUser] = useState<User | null>(null);
    const { theme, toggleTheme } = useTheme();

    useEffect(() => {
        loadUser();
    }, []);

    const loadUser = async () => {
        try {
            const res = await fetch(`${API_URL}/api/auth/me`, { credentials: 'include' });
            if (res.ok) {
                const data = await res.json();
                setUser(data.user);
            }
        } catch (err) {
            console.error('Failed to load user:', err);
        }
    };

    const handleLogout = async () => {
        await fetch(`${API_URL}/api/auth/logout`, {
            method: 'POST',
            credentials: 'include',
        });
        window.location.href = '/';
    };

    const navItems = [
        { id: 'feed', href: '/dashboard', icon: '📊', label: 'Feed' },
        { id: 'sources', href: '/dashboard/sources', icon: '🔗', label: 'Sources' },
        { id: 'tags', href: '/dashboard/tags', icon: '🏷️', label: 'Tags' },
        { id: 'digest', href: '/dashboard/digest', icon: '📧', label: 'Digest' },
    ];

    return (
        <aside className={styles.sidebar}>
            <div className={styles.logo}>
                <span className="text-gradient">Daedalus</span>Signal
            </div>

            <nav className={styles.nav}>
                {navItems.map((item) => (
                    <Link
                        key={item.id}
                        href={item.href}
                        className={`${styles.navItem} ${activePage === item.id ? styles.active : ''}`}
                    >
                        <span>{item.icon}</span> {item.label}
                    </Link>
                ))}
            </nav>

            {activePage === 'admin' && (
                <div className={styles.adminBadge}>
                    <span>⚙️</span> Admin Panel
                </div>
            )}

            <button onClick={toggleTheme} className={styles.themeToggle}>
                <span>{theme === 'dark' ? '☀️' : '🌙'}</span>
                {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
            </button>

            <div className={styles.userSection}>
                <div className={styles.userInfo}>
                    <div className={styles.avatar}>
                        {user?.email?.charAt(0).toUpperCase() || '?'}
                    </div>
                    <div>
                        <p className={styles.userEmail}>{user?.email || 'Loading...'}</p>
                        {user?.is_admin && <span className={styles.userAdminBadge}>Admin</span>}
                    </div>
                </div>
                <button onClick={handleLogout} className={styles.logoutBtn}>
                    Logout
                </button>
            </div>
        </aside>
    );
}
