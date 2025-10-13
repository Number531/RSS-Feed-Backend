"""
Comprehensive database seeding script for RSS News Aggregator.

Seeds:
- RSS Sources (10-15 real news sources)
- Articles (100+ realistic articles)
- Test Users (5 users)
- Comments (50+ comments with threading)
- Votes (200+ votes)
"""
import asyncio
import hashlib
from datetime import datetime, timedelta
from uuid import uuid4
import random

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.rss_source import RSSSource
from app.models.article import Article
from app.models.user import User, pwd_context
from app.models.comment import Comment
from app.models.vote import Vote


# RSS Sources Data
RSS_SOURCES = [
    {
        "name": "TechCrunch - Latest",
        "url": "https://techcrunch.com/feed/",
        "source_name": "TechCrunch",
        "category": "science",
    },
    {
        "name": "Hacker News - Best",
        "url": "https://news.ycombinator.com/rss",
        "source_name": "Hacker News",
        "category": "science",
    },
    {
        "name": "The Verge - All Posts",
        "url": "https://www.theverge.com/rss/index.xml",
        "source_name": "The Verge",
        "category": "science",
    },
    {
        "name": "Ars Technica",
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "source_name": "Ars Technica",
        "category": "science",
    },
    {
        "name": "CNN - Top Stories",
        "url": "http://rss.cnn.com/rss/cnn_topstories.rss",
        "source_name": "CNN",
        "category": "general",
    },
    {
        "name": "BBC News - World",
        "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "source_name": "BBC News",
        "category": "world",
    },
    {
        "name": "Reuters - World News",
        "url": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
        "source_name": "Reuters",
        "category": "world",
    },
    {
        "name": "NPR News",
        "url": "https://feeds.npr.org/1001/rss.xml",
        "source_name": "NPR",
        "category": "general",
    },
    {
        "name": "Politico",
        "url": "https://www.politico.com/rss/politics08.xml",
        "source_name": "Politico",
        "category": "politics",
    },
    {
        "name": "The Hill",
        "url": "https://thehill.com/news/feed/",
        "source_name": "The Hill",
        "category": "politics",
    },
    {
        "name": "ESPN - Top Headlines",
        "url": "https://www.espn.com/espn/rss/news",
        "source_name": "ESPN",
        "category": "general",
    },
    {
        "name": "Wired",
        "url": "https://www.wired.com/feed/rss",
        "source_name": "Wired",
        "category": "science",
    },
]

# Sample Article Templates
ARTICLE_TEMPLATES = {
    "science": [
        {
            "title": "New AI Model Achieves Human-Level Performance on Complex Reasoning Tasks",
            "description": "Researchers unveil breakthrough artificial intelligence system capable of solving advanced mathematical problems and logical puzzles.",
            "content": "A team of researchers has developed a new AI model that demonstrates unprecedented capabilities in complex reasoning tasks. The model, trained on diverse datasets, shows promise for applications in scientific research and problem-solving.",
        },
        {
            "title": "Quantum Computer Breakthrough Could Revolutionize Drug Discovery",
            "description": "Scientists achieve major milestone in quantum computing with potential applications in pharmaceutical research.",
            "content": "A new quantum computing breakthrough announced today could accelerate drug discovery processes by orders of magnitude. The advancement allows for more accurate molecular simulations.",
        },
        {
            "title": "SpaceX Successfully Launches Next Generation Satellite Constellation",
            "description": "Latest rocket launch deploys advanced communication satellites into orbit.",
            "content": "SpaceX has successfully launched its next-generation satellite constellation, marking another milestone in global internet coverage expansion.",
        },
        {
            "title": "Major Breakthrough in Fusion Energy Research Announced",
            "description": "Scientists achieve net positive energy gain in nuclear fusion experiment.",
            "content": "Researchers at a national laboratory have achieved a major breakthrough in fusion energy, successfully generating more energy than was consumed in the reaction.",
        },
        {
            "title": "New Programming Language Promises 10x Performance Improvements",
            "description": "Developers release open-source language designed for high-performance computing.",
            "content": "A new programming language designed for systems programming has been released, promising significant performance improvements over existing solutions.",
        },
    ],
    "general": [
        {
            "title": "Global Leaders Gather for Climate Summit in Major City",
            "description": "World leaders meet to discuss urgent climate action and sustainability initiatives.",
            "content": "Leaders from over 100 countries have gathered for a critical climate summit aimed at addressing the global climate crisis and establishing new emissions targets.",
        },
        {
            "title": "Major Tech Company Announces Significant Layoffs Amid Economic Concerns",
            "description": "Technology giant reduces workforce as part of restructuring efforts.",
            "content": "In response to economic pressures, a major technology company announced plans to reduce its workforce by thousands of positions.",
        },
        {
            "title": "Historic Peace Agreement Signed Between Long-Standing Rivals",
            "description": "Diplomatic breakthrough ends decades of conflict between neighboring nations.",
            "content": "After years of negotiations, two rival nations have signed a historic peace agreement, marking the end of decades of hostilities.",
        },
        {
            "title": "New Study Reveals Surprising Benefits of Mediterranean Diet",
            "description": "Research shows diet rich in olive oil and vegetables reduces disease risk.",
            "content": "A comprehensive study has found that adherence to a Mediterranean diet significantly reduces the risk of heart disease and other chronic conditions.",
        },
    ],
    "politics": [
        {
            "title": "Congress Passes Landmark Infrastructure Bill with Bipartisan Support",
            "description": "Major legislation allocates funding for roads, bridges, and broadband expansion.",
            "content": "In a rare show of bipartisan cooperation, Congress has passed a comprehensive infrastructure bill that addresses critical national needs.",
        },
        {
            "title": "Supreme Court to Hear Arguments on Major Constitutional Case",
            "description": "High court will review controversial law affecting millions of citizens.",
            "content": "The Supreme Court has agreed to hear oral arguments in a case that could have far-reaching implications for constitutional law.",
        },
        {
            "title": "Election Results Show Shifting Political Landscape in Key States",
            "description": "Recent elections indicate changing voter preferences across multiple regions.",
            "content": "Analysis of recent election results reveals significant shifts in political allegiances, particularly in swing states.",
        },
        {
            "title": "President Announces New Foreign Policy Initiative",
            "description": "Administration unveils strategy for international relations and trade.",
            "content": "The president has announced a comprehensive foreign policy initiative aimed at strengthening international partnerships.",
        },
    ],
    "world": [
        {
            "title": "Earthquake Strikes Major Metropolitan Area, Rescue Operations Underway",
            "description": "Powerful tremor causes widespread damage, emergency services respond.",
            "content": "A major earthquake has struck a densely populated urban area, triggering emergency response efforts and international aid.",
        },
        {
            "title": "International Trade Agreement Reached After Years of Negotiations",
            "description": "Multiple nations finalize historic trade pact affecting global commerce.",
            "content": "After extensive negotiations, several countries have reached agreement on a comprehensive trade deal that will reshape international commerce.",
        },
        {
            "title": "United Nations Warns of Humanitarian Crisis in Conflict Zone",
            "description": "International organization calls for immediate action to assist affected populations.",
            "content": "The United Nations has issued an urgent appeal for humanitarian assistance as conditions deteriorate in a region affected by ongoing conflict.",
        },
        {
            "title": "Major Archaeological Discovery Sheds Light on Ancient Civilization",
            "description": "Researchers uncover artifacts providing new insights into historical society.",
            "content": "Archaeologists have made a significant discovery that provides new understanding of an ancient civilization's culture and daily life.",
        },
    ],
}

# Test Users Data
TEST_USERS = [
    {
        "username": "tech_enthusiast",
        "email": "tech@example.com",
        "password": "TechPass123!",
        "full_name": "Alex Johnson",
    },
    {
        "username": "news_reader",
        "email": "reader@example.com",
        "password": "ReadPass123!",
        "full_name": "Jordan Smith",
    },
    {
        "username": "science_fan",
        "email": "science@example.com",
        "password": "SciPass123!",
        "full_name": "Taylor Brown",
    },
    {
        "username": "politics_watcher",
        "email": "politics@example.com",
        "password": "PolPass123!",
        "full_name": "Morgan Davis",
    },
    {
        "username": "world_observer",
        "email": "world@example.com",
        "password": "WorldPass123!",
        "full_name": "Casey Wilson",
    },
]

# Comment Templates
COMMENT_TEMPLATES = [
    "This is a really interesting article! Thanks for sharing.",
    "I have some concerns about the methodology used in this research.",
    "Great writeup! Looking forward to seeing how this develops.",
    "Does anyone have more information about this topic?",
    "This contradicts what I read in another article. Can someone clarify?",
    "Fascinating development. This could change everything.",
    "I'm skeptical about these claims. Need to see more evidence.",
    "Finally, some good news in this area!",
    "The implications of this are huge for the industry.",
    "Well-written and informative. Appreciate the detailed analysis.",
    "I disagree with the conclusion drawn here.",
    "This aligns with what experts have been predicting.",
    "Thanks for posting this! Very relevant to my work.",
    "Could this technology be applied to other fields?",
    "Interesting perspective. Haven't thought about it that way.",
]


async def create_url_hash(url: str) -> str:
    """Generate SHA-256 hash of URL for deduplication."""
    return hashlib.sha256(url.encode()).hexdigest()


async def seed_rss_sources(session: AsyncSession):
    """Seed RSS sources."""
    print("Seeding RSS sources...")
    sources = []
    
    for source_data in RSS_SOURCES:
        source = RSSSource(
            id=uuid4(),
            name=source_data["name"],
            url=source_data["url"],
            source_name=source_data["source_name"],
            category=source_data["category"],
            is_active=True,
            fetch_success_count=random.randint(50, 200),
            fetch_failure_count=random.randint(0, 10),
            consecutive_failures=0,
            last_fetched=datetime.utcnow() - timedelta(hours=random.randint(1, 24)),
            last_successful_fetch=datetime.utcnow() - timedelta(hours=random.randint(1, 24)),
        )
        session.add(source)
        sources.append(source)
    
    await session.commit()
    print(f"✅ Created {len(sources)} RSS sources")
    return sources


async def seed_articles(session: AsyncSession, sources: list[RSSSource]):
    """Seed articles from various sources."""
    print("Seeding articles...")
    articles = []
    
    # Generate articles for each category
    for source in sources:
        category = source.category
        templates = ARTICLE_TEMPLATES.get(category, ARTICLE_TEMPLATES["general"])
        
        # Create 8-12 articles per source
        num_articles = random.randint(8, 12)
        
        for i in range(num_articles):
            template = random.choice(templates)
            
            # Add variation to titles and content
            title_suffix = random.choice(["", " - Updated", " [Analysis]", " (Breaking)", ""])
            title = f"{template['title']}{title_suffix}"
            
            # Generate unique URL
            url = f"https://{source.source_name.lower().replace(' ', '')}.com/articles/{uuid4().hex[:12]}"
            
            # Random publication date within last 30 days
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            pub_date = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago)
            
            article = Article(
                id=uuid4(),
                rss_source_id=source.id,
                title=title,
                url=url,
                url_hash=await create_url_hash(url),
                description=template["description"],
                content=template["content"] + f"\n\n[Article from {source.source_name}]",
                author=random.choice([
                    "Staff Writer",
                    "Editorial Team",
                    "Senior Reporter",
                    "Contributing Author",
                    None
                ]),
                published_date=pub_date,
                category=category,
                tags=random.sample([
                    "breaking", "analysis", "opinion", "research", 
                    "technology", "innovation", "policy", "global"
                ], k=random.randint(2, 4)),
                vote_score=random.randint(-5, 50),
                vote_count=random.randint(0, 60),
                comment_count=random.randint(0, 25),
                trending_score=random.uniform(0, 100),
                created_at=pub_date,
                updated_at=pub_date,
            )
            
            session.add(article)
            articles.append(article)
    
    await session.commit()
    print(f"✅ Created {len(articles)} articles")
    return articles


async def seed_users(session: AsyncSession):
    """Seed test users."""
    print("Seeding users...")
    users = []
    
    for user_data in TEST_USERS:
        user = User(
            id=uuid4(),
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=pwd_context.hash(user_data["password"]),
            full_name=user_data.get("full_name"),
            is_active=True,
            is_verified=random.choice([True, True, True, False]),  # 75% verified
            created_at=datetime.utcnow() - timedelta(days=random.randint(30, 365)),
            last_login_at=datetime.utcnow() - timedelta(hours=random.randint(1, 72)),
        )
        session.add(user)
        users.append(user)
    
    await session.commit()
    print(f"✅ Created {len(users)} test users")
    return users


async def seed_comments(session: AsyncSession, articles: list[Article], users: list[User]):
    """Seed comments on articles."""
    print("Seeding comments...")
    comments = []
    
    # Select random articles to comment on (about 40% of articles)
    articles_to_comment = random.sample(articles, k=int(len(articles) * 0.4))
    
    for article in articles_to_comment:
        # Create 1-5 top-level comments per article
        num_comments = random.randint(1, 5)
        
        for _ in range(num_comments):
            user = random.choice(users)
            content = random.choice(COMMENT_TEMPLATES)
            
            # Add more natural variation
            if random.random() > 0.5:
                content += f" #{random.choice(['interesting', 'important', 'breaking'])}"
            
            created_at = article.created_at + timedelta(
                hours=random.randint(1, 48),
                minutes=random.randint(0, 59)
            )
            
            comment = Comment(
                id=uuid4(),
                article_id=article.id,
                user_id=user.id,
                content=content,
                is_deleted=False,
                created_at=created_at,
                updated_at=created_at,
            )
            
            session.add(comment)
            comments.append(comment)
            
            # 30% chance of reply to this comment
            if random.random() < 0.3:
                reply_user = random.choice([u for u in users if u.id != user.id])
                reply_content = random.choice([
                    "I agree with your point.",
                    "Interesting perspective!",
                    "Can you elaborate on that?",
                    "Thanks for sharing this insight.",
                    "I see it differently...",
                ])
                
                reply = Comment(
                    id=uuid4(),
                    article_id=article.id,
                    user_id=reply_user.id,
                    parent_comment_id=comment.id,
                    content=reply_content,
                    is_deleted=False,
                    created_at=created_at + timedelta(hours=random.randint(1, 12)),
                    updated_at=created_at + timedelta(hours=random.randint(1, 12)),
                )
                
                session.add(reply)
                comments.append(reply)
    
    await session.commit()
    print(f"✅ Created {len(comments)} comments")
    return comments


async def seed_votes(session: AsyncSession, articles: list[Article], users: list[User]):
    """Seed votes on articles."""
    print("Seeding votes...")
    votes = []
    
    # Each user votes on 30-50% of articles
    for user in users:
        articles_to_vote = random.sample(articles, k=int(len(articles) * random.uniform(0.3, 0.5)))
        
        for article in articles_to_vote:
            # 70% upvote, 30% downvote
            vote_value = 1 if random.random() < 0.7 else -1
            
            vote = Vote(
                id=uuid4(),
                article_id=article.id,
                user_id=user.id,
                vote_value=vote_value,
                created_at=article.created_at + timedelta(
                    hours=random.randint(0, 72),
                    minutes=random.randint(0, 59)
                ),
            )
            
            session.add(vote)
            votes.append(vote)
    
    await session.commit()
    print(f"✅ Created {len(votes)} votes")
    return votes


async def update_article_metrics(session: AsyncSession):
    """Update article vote_score and comment_count based on actual data."""
    print("Updating article metrics...")
    
    from sqlalchemy import select, func
    
    # Update vote scores
    result = await session.execute(
        select(Article.id, func.sum(Vote.vote_value).label("total_score"))
        .join(Vote, Article.id == Vote.article_id)
        .group_by(Article.id)
    )
    
    vote_scores = {article_id: score for article_id, score in result}
    
    # Update comment counts
    result = await session.execute(
        select(Article.id, func.count(Comment.id).label("comment_count"))
        .join(Comment, Article.id == Comment.article_id)
        .group_by(Article.id)
    )
    
    comment_counts = {article_id: count for article_id, count in result}
    
    # Apply updates
    articles = await session.execute(select(Article))
    for article in articles.scalars():
        article.vote_score = vote_scores.get(article.id, 0)
        article.comment_count = comment_counts.get(article.id, 0)
        article.vote_count = abs(vote_scores.get(article.id, 0))
    
    await session.commit()
    print("✅ Updated article metrics")


async def main():
    """Main seeding function."""
    print("\n" + "="*60)
    print("🌱 RSS News Aggregator - Database Seeding")
    print("="*60 + "\n")
    
    # Create async engine and session
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            # Seed in order
            sources = await seed_rss_sources(session)
            articles = await seed_articles(session, sources)
            users = await seed_users(session)
            comments = await seed_comments(session, articles, users)
            votes = await seed_votes(session, articles, users)
            await update_article_metrics(session)
            
            print("\n" + "="*60)
            print("✅ Database Seeding Complete!")
            print("="*60)
            print(f"\n📊 Summary:")
            print(f"   • RSS Sources: {len(sources)}")
            print(f"   • Articles: {len(articles)}")
            print(f"   • Users: {len(users)}")
            print(f"   • Comments: {len(comments)}")
            print(f"   • Votes: {len(votes)}")
            print(f"\n🔐 Test User Credentials:")
            for user_data in TEST_USERS:
                print(f"   • {user_data['email']} / {user_data['password']}")
            print("\n" + "="*60 + "\n")
            
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
