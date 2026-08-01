'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useTheme } from '@/hooks/useTheme';
import { getAuthHeaders, clearToken } from '@/lib/auth';
import styles from './Sidebar.module.css';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://signal.daedalusapps.com';

import { User } from '@/types';

interface SidebarProps {
    activePage: 'feed' | 'sources' | 'tags' | 'digest' | 'admin';
}

export default function Sidebar({ activePage }: SidebarProps) {
    const [user, setUser] = useState<User | null>(null);
    const [newCount, setNewCount] = useState(0);
    const { theme, toggleTheme } = useTheme();

    useEffect(() => {
        loadUser();
        checkNewContent();
    }, []);

    const loadUser = async () => {
        try {
            const res = await fetch(`${API_URL}/api/auth/me`, {
                headers: getAuthHeaders(),
            });
            if (res.ok) {
                const data = await res.json();
                setUser(data.user);
            }
        } catch (err) {
            console.error('Failed to load user:', err);
        }
    };

    const handleLogout = () => {
        clearToken();
        window.location.href = '/';
    };

    const checkNewContent = async () => {
        const lastChecked = localStorage.getItem('lastContentCheck');
        if (!lastChecked) {
            localStorage.setItem('lastContentCheck', new Date().toISOString());
            return;
        }
        try {
            const res = await fetch(
                `${API_URL}/api/content/new-count?since=${encodeURIComponent(lastChecked)}`,
                { headers: getAuthHeaders() }
            );
            if (res.ok) {
                const data = await res.json();
                setNewCount(data.count);
            }
        } catch (err) {
            console.error('Failed to check new content:', err);
        }
    };

    const clearNewCount = () => {
        setNewCount(0);
        localStorage.setItem('lastContentCheck', new Date().toISOString());
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
                        onClick={item.id === 'feed' ? clearNewCount : undefined}
                    >
                        <span>{item.icon}</span> {item.label}
                        {item.id === 'feed' && newCount > 0 && (
                            <span className={styles.badge}>{newCount > 99 ? '99+' : newCount}</span>
                        )}
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
