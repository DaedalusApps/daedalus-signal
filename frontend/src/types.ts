export interface User {
    id: number;
    email: string;
    is_admin: boolean;
    digest_enabled: boolean;
    onboarding_complete: boolean;
    created_at?: string;
}

export interface Content {
    id: number;
    title: string;
    description: string;
    url: string;
    content_type: string;
    relevance_score: number;
    source: {
        name: string;
        source_type: string;
    };
    scraped_at: string;
}
