-- Fix existing synthesis articles by setting has_synthesis = true
-- Run this if you manually populated synthesis_article but forgot to set the flag

-- Update articles that have synthesis_article content but has_synthesis is not true
UPDATE articles
SET has_synthesis = true
WHERE synthesis_article IS NOT NULL
  AND synthesis_article != ''
  AND (has_synthesis IS NULL OR has_synthesis = false);

-- Verify the update
SELECT 
    COUNT(*) FILTER (WHERE has_synthesis = true) as with_synthesis_flag,
    COUNT(*) FILTER (WHERE synthesis_article IS NOT NULL) as with_synthesis_content,
    COUNT(*) as total_articles
FROM articles;
