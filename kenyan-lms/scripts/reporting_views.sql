-- Optional read-only reporting views. This script is NOT applied by Django
-- migrations; run it deliberately against a database after taking a backup.
-- Unique indexes allow REFRESH MATERIALIZED VIEW CONCURRENTLY, so dashboards
-- can keep reading while the views refresh.

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_enrolment_summary AS
SELECT
    institution_id,
    COUNT(*) AS total_learners,
    COUNT(*) FILTER (WHERE status = 'ACTIVE' AND NOT is_archived) AS active_learners,
    COUNT(*) FILTER (WHERE is_archived) AS archived_learners
FROM learners_learner
GROUP BY institution_id;

CREATE UNIQUE INDEX IF NOT EXISTS mv_enrolment_summary_institution_idx
    ON mv_enrolment_summary (institution_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_fee_collection AS
SELECT
    institution_id,
    COUNT(*) AS payment_count,
    COALESCE(SUM(amount), 0) AS total_collected
FROM fees_payment
GROUP BY institution_id;

CREATE UNIQUE INDEX IF NOT EXISTS mv_fee_collection_institution_idx
    ON mv_fee_collection (institution_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_assessment_completion AS
SELECT
    institution_id,
    COUNT(*) AS attempt_count,
    COUNT(*) FILTER (WHERE status = 'COMPLETED') AS completed_attempts,
    AVG(score) FILTER (WHERE status = 'COMPLETED') AS average_score
FROM assessments_quizattempt
GROUP BY institution_id;

CREATE UNIQUE INDEX IF NOT EXISTS mv_assessment_completion_institution_idx
    ON mv_assessment_completion (institution_id);

CREATE OR REPLACE FUNCTION refresh_reporting_views() RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_enrolment_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_fee_collection;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_assessment_completion;
END;
$$ LANGUAGE plpgsql;

-- Refresh all views:
--   SELECT refresh_reporting_views();
