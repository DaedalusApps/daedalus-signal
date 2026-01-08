const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

interface ApiResponse<T> {
    data?: T;
    error?: string;
}

async function request<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<ApiResponse<T>> {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            credentials: 'include',
        });

        const data = await response.json();

        if (!response.ok) {
            return { error: data.error || 'Request failed' };
        }

        return { data };
    } catch (error) {
        return { error: 'Network error' };
    }
}

// Auth
export const auth = {
    register: (email: string, password: string, turnstile_token?: string) =>
        request('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, password, turnstile_token }),
        }),

    login: (email: string, password: string) =>
        request('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        }),

    logout: () =>
        request('/api/auth/logout', { method: 'POST' }),

    me: () => request('/api/auth/me'),

    update: (data: { digest_enabled?: boolean; onboarding_complete?: boolean }) =>
        request('/api/auth/me', {
            method: 'PATCH',
            body: JSON.stringify(data),
        }),

    verifyEmail: (email: string, code: string) =>
        request('/api/auth/verify-email', {
            method: 'POST',
            body: JSON.stringify({ email, code }),
        }),

    resendVerification: (email: string) =>
        request('/api/auth/resend-verification', {
            method: 'POST',
            body: JSON.stringify({ email }),
        }),

    forgotPassword: (email: string) =>
        request('/api/auth/forgot-password', {
            method: 'POST',
            body: JSON.stringify({ email }),
        }),

    resetPassword: (email: string, code: string, new_password: string) =>
        request('/api/auth/reset-password', {
            method: 'POST',
            body: JSON.stringify({ email, code, new_password }),
        }),
};

// Sources
export const sources = {
    list: () => request('/api/sources'),

    defaults: () => request('/api/sources/defaults'),

    add: (name: string, url: string, source_type: string) =>
        request('/api/sources', {
            method: 'POST',
            body: JSON.stringify({ name, url, source_type }),
        }),

    remove: (id: number) =>
        request(`/api/sources/${id}`, { method: 'DELETE' }),
};

// Tags
export const tags = {
    list: () => request('/api/tags'),

    defaults: () => request('/api/tags/defaults'),

    add: (name: string, category?: string) =>
        request('/api/tags', {
            method: 'POST',
            body: JSON.stringify({ name, category }),
        }),

    remove: (id: number) =>
        request(`/api/tags/${id}`, { method: 'DELETE' }),
};

// Content
export const content = {
    list: (page = 1, perPage = 20, sourceType?: string) => {
        const params = new URLSearchParams({
            page: String(page),
            per_page: String(perPage),
        });
        if (sourceType) params.append('source_type', sourceType);
        return request(`/api/content?${params}`);
    },

    feed: (limit = 10) =>
        request(`/api/content/feed?limit=${limit}`),

    digest: () => request('/api/content/digest'),
};

// Admin
export const admin = {
    stats: () => request('/api/admin/stats'),

    users: () => request('/api/admin/users'),

    sources: () => request('/api/admin/sources'),

    approveSource: (id: number) =>
        request(`/api/admin/sources/${id}/approve`, { method: 'POST' }),

    tags: () => request('/api/admin/tags'),

    approveTag: (id: number) =>
        request(`/api/admin/tags/${id}/approve`, { method: 'POST' }),

    feedback: (status?: string) => {
        const params = status ? `?status=${status}` : '';
        return request(`/api/admin/feedback${params}`);
    },
};

// Feedback
export const feedback = {
    submit: (email: string, message: string, feedback_type = 'general') =>
        request('/api/feedback', {
            method: 'POST',
            body: JSON.stringify({ email, message, feedback_type }),
        }),
};
