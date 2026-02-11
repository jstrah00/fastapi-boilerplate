"""
Seed script for demo data: users, profiles, posts, comments, likes, contact requests.

Usage (from inside the backend container):
    docker compose exec backend uv run python scripts/seed_demo_data.py

Or locally with DB running:
    cd backend && uv run python scripts/seed_demo_data.py
"""
import asyncio
import random
import sys
from pathlib import Path
from datetime import datetime, UTC, timedelta
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from app.db.postgres import AsyncSessionLocal
from app.models.postgres.user import User
from app.models.postgres.aretan_profile import AretanProfile
from app.models.postgres.contractor_profile import ContractorProfile
from app.models.postgres.work_experience import WorkExperience
from app.models.postgres.master_tables import (
    MasterIndustry,
    MasterProfession,
    MasterSportAchievement,
)
from app.models.postgres.post import Post
from app.models.postgres.comment import Comment
from app.models.postgres.post_like import PostLike
from app.models.postgres.contact_request import ContactRequest
from app.common.security import get_password_hash

# All demo users share this password
DEMO_PASSWORD = "Demo1234!"

ARETANS = [
    {"first_name": "Luciana", "last_name": "Aymar", "email": "luciana@demo.a2w.com", "phone": "+54 11 5555-0101", "country": "Argentina", "sport_desc": "Former professional field hockey player. Captain of Las Leonas for over a decade, winning multiple Olympic medals and World Cups.", "prof_desc": "Sports commentator and brand ambassador. Passionate about developing the next generation of athletes.", "employment": "independent", "languages": ["Espa\u00f1ol", "English", "Portugu\u00eas"]},
    {"first_name": "Juan Mart\u00edn", "last_name": "Del Potro", "email": "delpo@demo.a2w.com", "phone": "+54 11 5555-0102", "country": "Argentina", "sport_desc": "Former professional tennis player. US Open champion 2009. Known for a devastating forehand.", "prof_desc": "Sports entrepreneur and motivational speaker.", "employment": "independent", "languages": ["Espa\u00f1ol", "English"]},
    {"first_name": "Carolina", "last_name": "Mar\u00edn", "email": "carolina@demo.a2w.com", "phone": "+34 600 555 001", "country": "Espa\u00f1a", "sport_desc": "Olympic gold medalist in badminton (Rio 2016). Three-time World Champion.", "prof_desc": "Sports consultant and keynote speaker on resilience and peak performance.", "employment": "open", "languages": ["Espa\u00f1ol", "English"]},
    {"first_name": "Gerardo", "last_name": "Werthein", "email": "gerardo@demo.a2w.com", "phone": "+54 11 5555-0103", "country": "Argentina", "sport_desc": "Former Olympic Committee member, lifelong equestrian.", "prof_desc": "Business leader with experience in media, telecommunications, and sports management.", "employment": "employed", "languages": ["Espa\u00f1ol", "English", "Fran\u00e7ais"]},
    {"first_name": "Paula", "last_name": "Pareto", "email": "paula@demo.a2w.com", "phone": "+54 11 5555-0104", "country": "Argentina", "sport_desc": "Olympic gold medalist in judo (Rio 2016). First Argentine woman to win an Olympic gold in an individual event.", "prof_desc": "Physician (traumatology) combining medical career with sports mentoring.", "employment": "employed", "languages": ["Espa\u00f1ol", "English", "Japon\u00e9s"]},
    {"first_name": "Diego", "last_name": "Schwartzman", "email": "diego@demo.a2w.com", "phone": "+54 11 5555-0105", "country": "Argentina", "sport_desc": "Professional tennis player, reached ATP Top 10. Known for his incredible speed and court coverage.", "prof_desc": "Tech investor and startup advisor, particularly in sports technology.", "employment": "independent", "languages": ["Espa\u00f1ol", "English", "Italiano"]},
    {"first_name": "Nadia", "last_name": "Podoroska", "email": "nadia@demo.a2w.com", "phone": "+54 11 5555-0106", "country": "Argentina", "sport_desc": "Professional tennis player. First Argentine woman to reach a Grand Slam semifinal in 20 years (Roland Garros 2020).", "prof_desc": "Psychology student exploring sports psychology and athlete wellbeing.", "employment": "open", "languages": ["Espa\u00f1ol", "English"]},
    {"first_name": "Sebasti\u00e1n", "last_name": "Crismanich", "email": "seba@demo.a2w.com", "phone": "+54 11 5555-0107", "country": "Argentina", "sport_desc": "Olympic gold medalist in taekwondo (London 2012).", "prof_desc": "Sports coach and motivational speaker focused on youth development programs.", "employment": "employed", "languages": ["Espa\u00f1ol", "English"]},
    {"first_name": "Delfina", "last_name": "Merino", "email": "delfina@demo.a2w.com", "phone": "+54 11 5555-0108", "country": "Argentina", "sport_desc": "Professional field hockey player. Member of Las Leonas national team.", "prof_desc": "Marketing professional with expertise in sports branding.", "employment": "employed", "languages": ["Espa\u00f1ol", "English"]},
    {"first_name": "Federico", "last_name": "Molinari", "email": "fede@demo.a2w.com", "phone": "+54 11 5555-0109", "country": "Argentina", "sport_desc": "Olympic gymnast, competed in three Olympic Games. Specialist in rings.", "prof_desc": "Fitness consultant and gymnastics academy founder.", "employment": "independent", "languages": ["Espa\u00f1ol", "English"]},
    {"first_name": "Bel\u00e9n", "last_name": "Casetta", "email": "belen@demo.a2w.com", "phone": "+54 11 5555-0110", "country": "Argentina", "sport_desc": "Olympic steeplechase runner. Pan American Games medalist.", "prof_desc": "Nutritionist with focus on high-performance athletes.", "employment": "open", "languages": ["Espa\u00f1ol", "English"]},
    {"first_name": "Braian", "last_name": "Toledo", "email": "braian@demo.a2w.com", "phone": "+54 11 5555-0111", "country": "Argentina", "sport_desc": "Pan American javelin champion. Olympic athlete.", "prof_desc": "Community sports program organizer.", "employment": "open", "languages": ["Espa\u00f1ol"]},
    {"first_name": "Cecilia", "last_name": "Carranza", "email": "cecilia@demo.a2w.com", "phone": "+54 11 5555-0112", "country": "Argentina", "sport_desc": "Olympic gold medalist in sailing (Nacra 17, Tokyo 2020).", "prof_desc": "Environmental advocate and sailing instructor.", "employment": "independent", "languages": ["Espa\u00f1ol", "English", "Fran\u00e7ais"]},
    {"first_name": "Santiago", "last_name": "Lange", "email": "santiago@demo.a2w.com", "phone": "+54 11 5555-0113", "country": "Argentina", "sport_desc": "Olympic gold medalist in sailing at age 54 (Rio 2016). Competed in six Olympic Games.", "prof_desc": "Engineer, boat designer, and inspirational speaker on overcoming adversity.", "employment": "independent", "languages": ["Espa\u00f1ol", "English", "Italiano"]},
]

CONTRACTORS = [
    {"first_name": "Mar\u00eda", "last_name": "Gonz\u00e1lez", "email": "maria@acme.com", "company": "Acme Sports Group", "size": "50-200", "entity": "company", "desc": "Leading sports management agency in Latin America. We connect brands with athletes for sponsorship deals, events, and media campaigns.", "website": "https://acmesports.example.com"},
    {"first_name": "Roberto", "last_name": "Fern\u00e1ndez", "email": "roberto@talentpro.com", "company": "TalentPro HR", "size": "200-500", "entity": "company", "desc": "HR consulting firm specializing in placing former athletes in corporate roles. We value discipline, leadership, and teamwork.", "website": "https://talentpro.example.com"},
    {"first_name": "Ana", "last_name": "Mart\u00ednez", "email": "ana@fitbrand.com", "company": "FitBrand Agency", "size": "10-50", "entity": "company", "desc": "Digital marketing agency specialized in fitness and sports brands. Looking for athletes to endorse health and wellness products.", "website": "https://fitbrand.example.com"},
    {"first_name": "Carlos", "last_name": "L\u00f3pez", "email": "carlos@sportech.io", "company": "SporTech", "size": "10-50", "entity": "company", "desc": "Sports technology startup building wearable devices and analytics platforms. We hire athletes as product testers and brand ambassadors.", "website": "https://sportech.example.io"},
    {"first_name": "Laura", "last_name": "Ruiz", "email": "laura@consultora.ar", "company": "", "size": "", "entity": "individual", "desc": "Independent consultant specializing in corporate wellness programs. I help companies integrate sports culture into their work environment.", "website": ""},
    {"first_name": "Miguel", "last_name": "Torres", "email": "miguel@eventosarg.com", "company": "Eventos Deportivos Argentina", "size": "50-200", "entity": "company", "desc": "Event management company organizing sports tournaments, charity runs, and corporate team-building activities across South America.", "website": "https://eventosarg.example.com"},
]

POST_CONTENTS = [
    "Just finished an incredible training session. The key to improvement is consistency and showing up every single day, even when you don\u2019t feel like it. **Discipline beats motivation** every time.",
    "Excited to announce I'll be speaking at the Latin American Sports Summit next month! Will be sharing insights on transitioning from competitive sports to the business world.",
    "Reading _Atomic Habits_ by James Clear and finding so many parallels with elite sports training. Small daily improvements really do compound over time.",
    "Had a great meeting with a tech startup today. They\u2019re building AI-powered training analytics \u2014 the future of sports performance is here! [Check it out](https://example.com/sports-ai)",
    "To all young athletes out there: **your sport career will end someday**. Start thinking about your post-sport career now. It\u2019s never too early to build skills outside of your discipline.",
    "Great panel discussion today about mental health in sports. We need to normalize asking for help. _Strength is not just physical_.",
    "Looking for recommendations on sports management courses. Has anyone done the FIFA/CIES program? Would love to hear about your experience.",
    "Three things I learned from 15 years of competitive sports:\n1. **Failure is the best teacher**\n2. Teamwork makes everything possible\n3. Recovery is just as important as training",
    "Just wrapped up an amazing charity event! We raised over $50,000 for youth sports programs in underserved communities. Sport changes lives!",
    "The corporate world values the same skills we develop as athletes: discipline, resilience, time management, and the ability to perform under pressure. Don\u2019t underestimate your transferable skills!",
    "Missing the Olympic Village vibes today. There\u2019s nothing quite like being surrounded by the world\u2019s best athletes, all pushing their limits together.",
    "Announced my new role as brand ambassador for a major sportswear company! Grateful for the opportunity to represent values I believe in: hard work, authenticity, and inclusion.",
    "Had an incredible conversation with a group of students about career transitions. Their questions reminded me why sharing our experiences matters.",
    "Weekend training camp done! Nothing beats the feeling of pushing past your limits and discovering what you\u2019re truly capable of.",
    "Investing in yourself is the best investment you\u2019ll ever make. Whether it\u2019s education, health, or relationships \u2014 **compound interest applies to personal growth too**.",
    "So proud of my colleague who just landed a C-suite position after retiring from professional sports. Proof that athletic discipline translates directly to business success.",
    "Reminder: networking isn\u2019t about collecting contacts. It\u2019s about _building genuine relationships_. Quality over quantity, always.",
    "Just completed a sports marketing certification! Never stop learning, no matter where you are in your career.",
    "Beautiful morning run along the river. Sometimes the best strategy sessions happen when you\u2019re moving your body.",
    "Five years ago I had no idea what I\u2019d do after sports. Today I run my own consulting firm. The journey wasn\u2019t easy, but it was worth every step.",
    "Thrilled to join the advisory board of a new sports academy! Education and athletics go hand in hand.",
    "To the hirers on this platform: athletes bring **unmatched dedication** to the table. Give us a chance \u2014 you won\u2019t be disappointed.",
    "Just finished mentoring a young athlete through her first contract negotiation. So rewarding to see the next generation empowered!",
    "The best teams I\u2019ve been on had one thing in common: **trust**. Whether it\u2019s on the field or in the boardroom, trust is everything.",
    "Had my first investor meeting today. Nervous but excited. Taking the entrepreneurial leap!",
    "Grateful for this community. Connecting with fellow athletes and professionals who understand the unique challenges of career transition is invaluable.",
    "Training update: back to 90% after my injury. Patience and consistency are everything in recovery. Same applies to career setbacks.",
    "Just signed up for a public speaking workshop. Communication skills are so underrated in the sports world.",
    "Proud moment: our foundation\u2019s scholarship program just sent its 100th athlete-student to university!",
    "Monday motivation: _\u201cThe only way to do great work is to love what you do.\u201d_ \u2014 Find that passion in your next career chapter.",
    "Great feedback from my first corporate training workshop! Teaching teams about high-performance mindset through sports analogies.",
    "Reflecting on my career: the medals are nice, but the friendships and life lessons are what truly last.",
    "Anyone else transitioning into the tech world? Would love to connect and share resources!",
    "Just completed a marathon for charity! Proving that competitive spirit never dies \u2014 it just finds new outlets.",
    "Hot take: companies should actively recruit retired athletes. The ROI on hiring someone with Olympic-level work ethic is incredible.",
    "Excited about a new partnership between our sports foundation and a major tech company. Big things coming!",
    "The discipline of training 6 hours a day for 20 years teaches you something no MBA can: **relentless execution**.",
    "Had coffee with a fellow Olympian today. We talked about how the hardest competition isn\u2019t in the arena \u2014 it\u2019s reinventing yourself afterward.",
    "Launching my podcast next month! Will interview athletes about their life after sports. Stay tuned!",
    "Year-end reflection: made the leap from sports to business, built amazing connections on this platform, and started giving back. What a journey!",
]

COMMENT_TEXTS = [
    "Couldn't agree more! This resonates so much with my own experience.",
    "Great post! Thanks for sharing your perspective.",
    "So inspiring! Keep it up.",
    "This is exactly what I needed to hear today.",
    "Would love to connect and chat more about this!",
    "Well said! Athletes bring unique skills to any field.",
    "Thanks for the motivation!",
    "Absolutely true. Discipline is everything.",
    "Love this! Sharing with my network.",
    "So proud of this community.",
    "This is why A2W exists \u2014 connecting talented people!",
    "Can you share more details about this?",
    "Congrats! Well deserved.",
    "Your journey is truly inspirational.",
    "**This!** 100% agree.",
    "The sports-to-business transition is real. Great advice!",
    "Following your work closely. Keep going!",
    "Really needed this today. Thank you.",
]

WORK_EXPERIENCES = [
    ("Brand Ambassador", "Nike Argentina"),
    ("Sports Commentator", "ESPN Latinoam\u00e9rica"),
    ("Performance Coach", "Club Atl\u00e9tico River Plate"),
    ("Fitness Consultant", "Body Tech"),
    ("Youth Coach", "CENARD"),
    ("Sports Marketing Manager", "Grupo Clar\u00edn"),
    ("Events Coordinator", "Comit\u00e9 Ol\u00edmpico Argentino"),
    ("Personal Trainer", "Independent"),
    ("Sports Director", "Club Universitario de Buenos Aires"),
    ("Motivational Speaker", "TEDx Buenos Aires"),
]


async def main() -> None:
    """Seed demo data."""
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(func.count(User.id)).where(User.email.like("%@demo.a2w.com")))
        count = result.scalar()
        if count and count > 0:
            print("\n  Demo data already seeded. To re-seed, delete demo users first.\n")
            return

        print("\n  Seeding demo data...\n")

        # Load master data IDs
        industries = (await session.execute(select(MasterIndustry).where(MasterIndustry.is_active == True))).scalars().all()
        professions = (await session.execute(select(MasterProfession).where(MasterProfession.is_active == True))).scalars().all()
        achievements = (await session.execute(select(MasterSportAchievement).where(MasterSportAchievement.is_active == True))).scalars().all()

        if not industries or not professions or not achievements:
            print("  ERROR: Master data not seeded. Run init_db.py first.\n")
            return

        hashed = get_password_hash(DEMO_PASSWORD)
        all_users: list[User] = []
        aretan_users: list[User] = []
        contractor_users: list[User] = []

        # --- Create Aretan Users ---
        print(f"  Creating {len(ARETANS)} aretan users...")
        for i, a in enumerate(ARETANS):
            user = User(
                id=uuid4(),
                email=a["email"],
                first_name=a["first_name"],
                last_name=a["last_name"],
                password_hash=hashed,
                role="aretan",
                status="active",
                phone=a["phone"],
                country=a["country"],
            )
            session.add(user)
            await session.flush()

            profile = AretanProfile(
                user_id=user.id,
                industry_ids=[ind.id for ind in random.sample(industries, k=random.randint(1, min(3, len(industries))))],
                profession_ids=[pro.id for pro in random.sample(professions, k=random.randint(1, min(2, len(professions))))],
                max_achievement_id=random.choice(achievements).id,
                sport_description=a["sport_desc"],
                professional_description=a["prof_desc"],
                employment_status=a["employment"],
                languages=a["languages"],
                social_networks={"linkedin": f"https://linkedin.com/in/{a['first_name'].lower().replace(' ', '')}"},
            )
            session.add(profile)
            await session.flush()

            # Add 1-2 work experiences
            for _ in range(random.randint(1, 2)):
                title, company = random.choice(WORK_EXPERIENCES)
                we = WorkExperience(
                    aretan_profile_id=profile.id,
                    title=title,
                    company=company,
                    start_date=datetime.now(UTC) - timedelta(days=random.randint(365, 2000)),
                    end_date=datetime.now(UTC) - timedelta(days=random.randint(0, 364)) if random.random() > 0.4 else None,
                )
                session.add(we)

            all_users.append(user)
            aretan_users.append(user)

        # --- Create Contractor Users ---
        print(f"  Creating {len(CONTRACTORS)} contractor users...")
        for c in CONTRACTORS:
            user = User(
                id=uuid4(),
                email=c["email"],
                first_name=c["first_name"],
                last_name=c["last_name"],
                password_hash=hashed,
                role="contratante",
                status="active",
                country="Argentina",
            )
            session.add(user)
            await session.flush()

            profile = ContractorProfile(
                user_id=user.id,
                entity_type=c["entity"],
                company_name=c["company"] or None,
                company_size=c["size"] or None,
                website=c["website"] or None,
                industry_id=random.choice(industries).id,
                description=c["desc"],
            )
            session.add(profile)

            all_users.append(user)
            contractor_users.append(user)

        await session.flush()

        # --- Create Posts ---
        print(f"  Creating {len(POST_CONTENTS)} posts...")
        posts: list[Post] = []
        base_time = datetime.now(UTC) - timedelta(days=30)

        for i, content in enumerate(POST_CONTENTS):
            author = random.choice(all_users)
            # Occasionally add mentions
            if random.random() > 0.7:
                mentioned = random.choice([u for u in all_users if u.id != author.id])
                content += f" @[{mentioned.first_name} {mentioned.last_name}]({mentioned.id})"

            post = Post(
                id=uuid4(),
                author_id=author.id,
                content=content,
                created_at=base_time + timedelta(hours=i * 12 + random.randint(0, 6)),
            )
            session.add(post)
            posts.append(post)

        await session.flush()

        # --- Create Comments ---
        comment_count = 0
        print("  Creating comments...")
        for post in posts:
            num_comments = random.randint(0, 4)
            for _ in range(num_comments):
                commenter = random.choice(all_users)
                text = random.choice(COMMENT_TEXTS)
                comment = Comment(
                    id=uuid4(),
                    post_id=post.id,
                    author_id=commenter.id,
                    content=text,
                    created_at=post.created_at + timedelta(minutes=random.randint(5, 1440)),
                )
                session.add(comment)
                comment_count += 1
            post.comments_count = num_comments

        await session.flush()

        # --- Create Likes ---
        like_count = 0
        print("  Creating likes...")
        for post in posts:
            likers = random.sample(all_users, k=random.randint(0, min(8, len(all_users))))
            for liker in likers:
                like = PostLike(
                    id=uuid4(),
                    post_id=post.id,
                    user_id=liker.id,
                )
                session.add(like)
                like_count += 1
            post.likes_count = len(likers)

        await session.flush()

        # --- Create Contact Requests ---
        cr_count = 0
        print("  Creating contact requests...")
        for contractor in contractor_users:
            targets = random.sample(aretan_users, k=random.randint(1, 3))
            for target in targets:
                status = random.choice(["pending", "accepted", "accepted", "rejected"])
                cr = ContactRequest(
                    id=uuid4(),
                    requester_id=contractor.id,
                    target_id=target.id,
                    message=f"Hi {target.first_name}, I'd love to connect regarding potential opportunities.",
                    status=status,
                )
                session.add(cr)
                cr_count += 1

        await session.commit()

        print(f"\n  Done! Created:")
        print(f"    {len(aretan_users)} aretans")
        print(f"    {len(contractor_users)} contractors")
        print(f"    {len(posts)} posts")
        print(f"    {comment_count} comments")
        print(f"    {like_count} likes")
        print(f"    {cr_count} contact requests")
        print(f"\n  All demo users share password: {DEMO_PASSWORD}")
        print(f"  Aretan emails: *@demo.a2w.com")
        print(f"  Contractor emails: see CONTRACTORS list\n")


if __name__ == "__main__":
    asyncio.run(main())
