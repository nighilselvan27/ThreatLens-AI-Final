-- =====================================================================
-- ThreatLens AI - Sample Database Seed Data
-- Insert Initial Admin & Security Analyst Users
-- =====================================================================

-- Note: Passwords are hashed using bcrypt
-- Admin Password: AdminPassword123!
-- Analyst Password: AnalystPassword123!

INSERT INTO users (full_name, email, password, role, is_active)
VALUES 
(
    'ThreatLens Administrator',
    'admin@threatlens.ai',
    '$2b$12$p9ICNuSh1Kj3i4yTQwti4e/BKS5JjsOfBsauR0UBul9iiJbZFVjfy',
    'Admin',
    TRUE
),
(
    'Senior Security Analyst',
    'analyst.senior@threatlens.ai',
    '$2b$12$AXUb3FOJYtVdf/RY.pwjuOmBVkcF.9VQ5SsV4U9cR0gvLrGt19HiC',
    'Security Analyst',
    TRUE
),
(
    'Junior Security Analyst',
    'analyst.junior@threatlens.ai',
    '$2b$12$AXUb3FOJYtVdf/RY.pwjuOmBVkcF.9VQ5SsV4U9cR0gvLrGt19HiC',
    'Security Analyst',
    TRUE
)
ON CONFLICT (email) DO NOTHING;
