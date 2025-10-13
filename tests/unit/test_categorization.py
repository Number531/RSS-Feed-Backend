"""
Unit tests for article categorization and tagging.
"""
import pytest
from app.utils.categorization import (
    categorize_article,
    extract_tags,
    get_political_leaning,
    CATEGORY_KEYWORDS,
    POLITICAL_KEYWORDS
)


class TestCategorizeArticle:
    """Test article categorization based on content."""
    
    def test_categorize_politics(self):
        """Test that political keywords trigger politics category."""
        title = "Senate passes new healthcare legislation"
        description = "Congress votes on important bill"
        category = categorize_article(title, description, "general")
        assert category == "politics"
    
    def test_categorize_technology(self):
        """Test that tech keywords trigger technology category."""
        title = "New AI breakthrough in machine learning"
        description = "Researchers develop advanced algorithm"
        category = categorize_article(title, description, "general")
        assert category == "technology"
    
    def test_categorize_sports(self):
        """Test that sports keywords trigger sports category."""
        title = "Lakers win championship in overtime thriller"
        description = "NBA finals conclude with exciting game"
        category = categorize_article(title, description, "general")
        assert category == "sports"
    
    def test_categorize_business(self):
        """Test that business keywords trigger business category."""
        title = "Stock market reaches new high as investors react"
        description = "Wall Street trading shows strong economic indicators"
        category = categorize_article(title, description, "general")
        assert category == "business"
    
    def test_categorize_entertainment(self):
        """Test that entertainment keywords trigger entertainment category."""
        title = "New movie breaks box office records"
        description = "Hollywood blockbuster exceeds expectations"
        category = categorize_article(title, description, "general")
        assert category == "entertainment"
    
    def test_categorize_science(self):
        """Test that science keywords trigger science category."""
        title = "Scientists discover new particle in physics experiment"
        description = "Research breakthrough in quantum mechanics"
        category = categorize_article(title, description, "general")
        assert category == "science"
    
    def test_categorize_health(self):
        """Test that health keywords trigger health category."""
        title = "New vaccine shows promising results in clinical trials"
        description = "Medical breakthrough could prevent disease"
        category = categorize_article(title, description, "general")
        assert category == "health"
    
    def test_fallback_to_feed_category(self):
        """Test that feed category is used when no keywords match."""
        title = "Random article about nothing specific"
        description = "This doesn't match any category keywords"
        category = categorize_article(title, description, "world")
        assert category == "world"
    
    def test_case_insensitive_matching(self):
        """Test that keyword matching is case-insensitive."""
        title = "SENATE PASSES LEGISLATION"
        description = "CONGRESS VOTES"
        category = categorize_article(title, description, "general")
        assert category == "politics"
    
    def test_multiple_category_keywords(self):
        """Test that multiple keywords in same category strengthen match."""
        title = "President signs bill after Senate and Congress vote"
        description = "Political legislation passes with bipartisan support"
        category = categorize_article(title, description, "general")
        assert category == "politics"
    
    def test_conflicting_categories(self):
        """Test behavior when article matches multiple categories."""
        # Article with both tech and business keywords
        title = "Tech startup raises millions in investment funding"
        description = "Silicon Valley company attracts venture capital"
        category = categorize_article(title, description, "general")
        # Should match one of them (order depends on implementation)
        assert category in ["technology", "business"]


class TestExtractTags:
    """Test tag extraction from article content."""
    
    def test_extract_single_tag(self):
        """Test extracting a single tag."""
        title = "New iPhone release announced"
        description = "Apple unveils latest smartphone"
        tags = extract_tags(title, description)
        assert "iphone" in tags
    
    def test_extract_multiple_tags(self):
        """Test extracting multiple tags."""
        title = "Trump and Biden debate on healthcare"
        description = "Presidential candidates discuss policy"
        tags = extract_tags(title, description)
        assert "trump" in tags
        assert "biden" in tags
        assert "healthcare" in tags
    
    def test_tags_from_title_and_description(self):
        """Test that tags are extracted from both title and description."""
        title = "Climate change discussion"
        description = "Global warming affects environment"
        tags = extract_tags(title, description)
        assert "climate" in tags or "environment" in tags
    
    def test_case_insensitive_extraction(self):
        """Test that tag extraction is case-insensitive."""
        title = "COVID-19 Pandemic Updates"
        description = "Latest news on coronavirus"
        tags = extract_tags(title, description)
        assert "covid" in tags or "pandemic" in tags
    
    def test_no_duplicate_tags(self):
        """Test that duplicate tags are not added."""
        title = "Biden discusses Biden's healthcare plan"
        description = "President Biden announces policy"
        tags = extract_tags(title, description)
        # Count occurrences of 'biden'
        assert tags.count("biden") == 1
    
    def test_empty_input(self):
        """Test handling of empty title and description."""
        tags = extract_tags("", "")
        assert tags == []
    
    def test_tag_limit(self):
        """Test that tag extraction has a reasonable limit."""
        # Create content with many potential tags
        title = "Trump Biden Harris Sanders Warren Politics Election"
        description = "Congress Senate House Representatives Government"
        tags = extract_tags(title, description)
        # Should have a reasonable number of tags (not unlimited)
        assert len(tags) <= 20


class TestGetPoliticalLeaning:
    """Test political leaning detection."""
    
    def test_left_leaning(self):
        """Test detection of left-leaning content."""
        title = "Progressive policies gain support"
        description = "Liberal agenda moves forward with social justice reforms"
        leaning = get_political_leaning(title, description)
        assert leaning == "left"
    
    def test_right_leaning(self):
        """Test detection of right-leaning content."""
        title = "Conservative values upheld in new legislation"
        description = "Traditional family values protected by law"
        leaning = get_political_leaning(title, description)
        assert leaning == "right"
    
    def test_neutral_content(self):
        """Test that non-political content is neutral."""
        title = "Weather forecast for tomorrow"
        description = "Sunny skies expected with mild temperatures"
        leaning = get_political_leaning(title, description)
        assert leaning == "neutral"
    
    def test_balanced_content(self):
        """Test content with both left and right keywords."""
        title = "Progressive conservatives debate liberal traditional values"
        description = "Bipartisan discussion on policy"
        leaning = get_political_leaning(title, description)
        assert leaning == "neutral"  # Balanced keywords should result in neutral
    
    def test_case_insensitive(self):
        """Test that political leaning detection is case-insensitive."""
        title = "PROGRESSIVE LIBERAL POLICIES"
        description = "LEFT-WING AGENDA"
        leaning = get_political_leaning(title, description)
        assert leaning == "left"


class TestCategoryKeywords:
    """Test that category keyword dictionaries are properly structured."""
    
    def test_all_categories_exist(self):
        """Test that all expected categories have keywords."""
        expected_categories = [
            "politics", "technology", "sports", "business",
            "entertainment", "science", "health"
        ]
        for category in expected_categories:
            assert category in CATEGORY_KEYWORDS
            assert len(CATEGORY_KEYWORDS[category]) > 0
    
    def test_keywords_are_lowercase(self):
        """Test that all keywords are stored in lowercase."""
        for category, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                assert keyword == keyword.lower()
    
    def test_no_duplicate_keywords_in_category(self):
        """Test that there are no duplicate keywords within categories."""
        for category, keywords in CATEGORY_KEYWORDS.items():
            assert len(keywords) == len(set(keywords))


class TestPoliticalKeywords:
    """Test that political keyword dictionaries are properly structured."""
    
    def test_left_right_keywords_exist(self):
        """Test that left and right political keywords are defined."""
        assert "left" in POLITICAL_KEYWORDS
        assert "right" in POLITICAL_KEYWORDS
        assert len(POLITICAL_KEYWORDS["left"]) > 0
        assert len(POLITICAL_KEYWORDS["right"]) > 0
    
    def test_political_keywords_lowercase(self):
        """Test that political keywords are lowercase."""
        for side, keywords in POLITICAL_KEYWORDS.items():
            for keyword in keywords:
                assert keyword == keyword.lower()
    
    def test_no_overlapping_keywords(self):
        """Test that left and right don't share keywords."""
        left_keywords = set(POLITICAL_KEYWORDS["left"])
        right_keywords = set(POLITICAL_KEYWORDS["right"])
        overlap = left_keywords.intersection(right_keywords)
        assert len(overlap) == 0, f"Found overlapping keywords: {overlap}"


class TestRealWorldScenarios:
    """Test categorization with real-world article examples."""
    
    def test_covid_article(self):
        """Test categorization of COVID-19 article."""
        title = "CDC updates COVID-19 guidelines for vaccinated individuals"
        description = "Health officials announce new recommendations"
        category = categorize_article(title, description, "general")
        assert category == "health"
        
        tags = extract_tags(title, description)
        assert "covid" in tags or "vaccine" in tags
    
    def test_sports_championship(self):
        """Test categorization of sports championship article."""
        title = "Super Bowl LVIII: Chiefs defeat 49ers in overtime"
        description = "Patrick Mahomes leads Kansas City to victory"
        category = categorize_article(title, description, "general")
        assert category == "sports"
        
        tags = extract_tags(title, description)
        assert "super bowl" in tags or "nfl" in tags or "football" in tags
    
    def test_tech_product_launch(self):
        """Test categorization of tech product launch."""
        title = "Apple announces new M3 MacBook Pro with AI features"
        description = "Latest laptop includes advanced machine learning capabilities"
        category = categorize_article(title, description, "general")
        assert category == "technology"
        
        tags = extract_tags(title, description)
        assert "apple" in tags or "ai" in tags
    
    def test_political_election(self):
        """Test categorization of political election article."""
        title = "Presidential candidates prepare for Iowa caucus"
        description = "Democratic and Republican hopefuls campaign heavily"
        category = categorize_article(title, description, "general")
        assert category == "politics"
        
        tags = extract_tags(title, description)
        assert "election" in tags or "campaign" in tags
    
    def test_climate_science(self):
        """Test categorization of climate science article."""
        title = "Climate scientists warn of accelerating global warming"
        description = "New research shows environmental impact exceeds predictions"
        category = categorize_article(title, description, "general")
        # Could be categorized as either science or environment
        assert category in ["science", "environment"]
