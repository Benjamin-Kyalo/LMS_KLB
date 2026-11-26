-- Create a least-privilege application role.
-- Replace APP_PASSWORD with a strong secret supplied through your secret manager.
-- Run as a PostgreSQL superuser.

CREATE ROLE lms_app LOGIN PASSWORD 'APP_PASSWORD';

GRANT CONNECT ON DATABASE lms TO lms_app;
GRANT USAGE ON SCHEMA public TO lms_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO lms_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO lms_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO lms_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT ON SEQUENCES TO lms_app;

-- Review and revoke any unnecessary table permissions before production use.