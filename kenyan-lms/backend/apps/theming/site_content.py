"""Default public-site wording and validation for admin-managed overrides.

The object below is the server-side source of truth for the editable public
site. It mirrors the frontend fallback so the site still renders when the API
is temporarily unavailable. All wording is original. Reference sites informed
the topics, not the copy.
"""
from urllib.parse import urlparse

from rest_framework.exceptions import ValidationError

from apps.theming.contrast import HEX_COLOUR, MIN_TEXT_CONTRAST, contrast_ratio

PUBLIC_SITE_KEY = "public"

# Allowlisted, section-scoped appearance controls. Empty values inherit the
# active palette or the shipped section design. There is deliberately no raw
# CSS field: an administrator can change one section without affecting another.
STYLE_SECTION_KEYS = (
    "header",
    "footer",
    "hero",
    "announcement",
    "quick-links",
    "trust",
    "workspaces",
    "routines",
    "access",
    "workspace-learning",
    "workspace-school",
    "workspace-publishing",
    "journey",
    "insights",
    "accessibility",
    "info",
    "spotlight",
    "roles",
    "support",
    "faq",
    "library",
    "login",
    "register",
    "invite",
    "tutor",
)
STYLE_COLOUR_KEYS = ("background", "text", "accent", "border")
STYLE_CHOICES = {
    "radius": ("", "0px", "8px", "16px", "24px"),
    "spacing": ("", "compact", "comfortable", "relaxed"),
}
STYLE_FIELDS = STYLE_COLOUR_KEYS + tuple(STYLE_CHOICES)


def default_site_styles():
    """Return fresh per-section style controls with no overrides applied."""
    return {
        section: {field: "" for field in STYLE_FIELDS}
        for section in STYLE_SECTION_KEYS
    }


DEFAULT_SITE_CONTENT = {
    "header": {
        "brand": {
            "mark": "KLB",
            "name": "Elimu",
            "subtitle": "Every lesson opens a door.",
        },
        "links": [
            {"label": "Home", "href": "/"},
            {"label": "For Schools", "href": "/for-schools"},
            {"label": "For Teachers", "href": "/for-teachers"},
            {"label": "For Learners", "href": "/for-learners"},
            {"label": "Digital Library", "href": "/library"},
            {"label": "About KLB Elimu", "href": "/about"},
            {"label": "Help Centre", "href": "/help"},
        ],
        "signInLabel": "Sign In",
        "signInHref": "/login",
        "primaryCtaLabel": "Get Your School Started",
        "primaryCtaHref": "/contact?category=School%20registration",
        "authLinks": [{"label": "Sign In", "href": "/login"}],
        "adminLinks": [
            {"label": "Admin sign in", "href": "/admin/login"},
            {"label": "User registration", "href": "/register"},
        ],
    },
    "footer": {
        "name": "KLB Elimu",
        "tagline": (
            "KLB Elimu brings schools, teachers, learners, parents and educational "
            "resources closer together through one digital learning environment."
        ),
        "contactTitle": "Contact",
        "lines": [
            "Kenya Literature Bureau PLC, Nairobi, Kenya",
            "School registration support: use the enquiry form",
            "Technical support: contact your school administrator first",
        ],
        "exploreTitle": "Platform",
        "exploreLinks": [
            {"label": "About KLB Elimu", "href": "/about"},
            {"label": "For Schools", "href": "/for-schools"},
            {"label": "For Teachers", "href": "/for-teachers"},
            {"label": "For Learners", "href": "/for-learners"},
            {"label": "For Parents", "href": "/for-parents"},
        ],
        "learnTitle": "Resources",
        "learnLinks": [
            {"label": "Digital Library", "href": "/library"},
            {"label": "Learning Resources", "href": "/library#resources"},
            {"label": "Help Centre", "href": "/help"},
            {"label": "Frequently Asked Questions", "href": "/faq"},
        ],
        "infoTitle": "Information",
        "infoLinks": [
            {"label": "Privacy Notice", "href": "/privacy"},
            {"label": "Terms of Use", "href": "/terms"},
            {"label": "Acceptable Use Policy", "href": "/acceptable-use"},
            {"label": "Accessibility Statement", "href": "/accessibility-statement"},
        ],
        "supportTitle": "Contact",
        "supportLinks": [
            {"label": "Contact KLB", "href": "/contact"},
            {
                "label": "School Registration Support",
                "href": "/contact?category=School%20registration",
            },
            {
                "label": "Technical Support",
                "href": "/contact?category=Technical%20assistance",
            },
        ],
        "credit": {
            "prefix": "Photography via ",
            "linkLabel": "Unsplash",
            "linkHref": "https://unsplash.com/license",
            "suffix": " and illustration by KLB",
        },
        "closingLine": "Every lesson opens a door.",
        "disclaimer": (
            "A proposed digital learning initiative associated with Kenya "
            "Literature Bureau PLC, subject to organisational approval."
        ),
    },
    "hero": {
        "overline": "KLB Elimu",
        "eyebrow": "A proposed digital learning ecosystem",
        "title": "Give every lesson somewhere to go.",
        "description": (
            "Learning does not stop at the classroom door. KLB Elimu brings "
            "teachers, learners, schools and educational resources together in "
            "one place, making it easier to teach, discover, practise and grow."
        ),
        "primaryLabel": "Explore KLB Elimu",
        "primaryHref": "/#introduction",
        "secondaryLabel": "School Registration",
        "secondaryHref": "/contact?category=School%20registration",
        "supportingStatement": "Built around learning. Designed for Kenyan schools.",
        "highlights": [
            "Learning resources, classroom activities and assessments",
            "A place for teachers, learners, schools and families",
            "More ways to make every learning moment count",
        ],
        "imageSrc": "/images/hero-community.png",
        "imageAlt": "Students and teachers in a school learning space",
        "imageCaption": (
            "One school record, with the right view for every learner, teacher "
            "and guardian."
        ),
    },
    "announcement": {
        "text": (
            "The KLB Digital Library brings selected educational publications and "
            "supplementary resources into your learning environment."
        ),
        "actionLabel": "Explore the Library",
        "actionHref": "/library",
    },
    "quickLinks": {
        "title": "On this page",
        "links": [
            {"label": "Introduction", "href": "/#introduction"},
            {"label": "What you can do", "href": "/#capabilities"},
            {"label": "Digital Library", "href": "/#library"},
            {"label": "Teachers", "href": "/#teachers"},
            {"label": "Learners", "href": "/#learners"},
            {"label": "Parents", "href": "/#parents"},
            {"label": "How it works", "href": "/#how-it-works"},
            {"label": "Questions", "href": "/#faq"},
        ],
    },
    "introduction": {
        "overline": "A better-connected way to learn",
        "title": "A better-connected way to learn.",
        "paragraphs": [
            (
                "A school day is made up of hundreds of learning moments. A question "
                "asked in class. A new concept discovered in a textbook. An "
                "assignment completed after school. A teacher finding a better way "
                "to explain a difficult topic."
            ),
            "KLB Elimu brings these moments closer together.",
            (
                "It provides schools with a shared digital environment for organising "
                "learning, accessing educational resources, managing assessments and "
                "following learner progress."
            ),
            (
                "Whether you are a teacher preparing tomorrow's lesson, a learner "
                "revisiting today's topic or a parent following your child's progress, "
                "there is a place for you here."
            ),
        ],
    },
    "capabilities": {
        "overline": "What can you do with KLB Elimu?",
        "title": "Everything learning needs, brought closer.",
        "cards": [
            {
                "key": "school",
                "title": "Manage your school",
                "copy": (
                    "Give your school a central place to manage learners, teachers, "
                    "classes, subjects and academic activities."
                ),
                "actionLabel": "Explore School Management",
                "actionHref": "/for-schools",
            },
            {
                "key": "teacher",
                "title": "Make lessons count",
                "copy": (
                    "Prepare lessons, share learning materials, create assignments "
                    "and follow learners' progress from one teaching workspace."
                ),
                "actionLabel": "Discover Teacher Tools",
                "actionHref": "/for-teachers",
            },
            {
                "key": "learner",
                "title": "Learn beyond the classroom",
                "copy": (
                    "Access learning materials, digital books, practice activities "
                    "and assessments in one convenient place."
                ),
                "actionLabel": "Explore Learning",
                "actionHref": "/for-learners",
            },
            {
                "key": "parent",
                "title": "Keep families connected",
                "copy": (
                    "Help parents follow attendance, assessment results, teacher "
                    "feedback and important school announcements."
                ),
                "actionLabel": "Explore Parent Access",
                "actionHref": "/for-parents",
            },
        ],
    },
    "libraryFeature": {
        "overline": "The KLB Digital Library",
        "title": "A good book can take learning further.",
        "paragraphs": [
            "The right learning resource can turn a difficult concept into a moment of understanding.",
            (
                "The KLB Digital Library brings educational books and supplementary "
                "learning materials closer to teachers and learners. Explore available "
                "digital publications, revision resources, audio content and other "
                "approved educational materials."
            ),
            "Find a resource, discover a new idea and make more of every learning opportunity.",
        ],
        "primaryLabel": "Explore the Digital Library",
        "primaryHref": "/library",
        "secondaryLabel": "Browse Learning Resources",
        "secondaryHref": "/library#resources",
    },
    "audiences": {
        "teachers": {
            "overline": "For teachers",
            "title": "Less time organising. More time teaching.",
            "paragraphs": [
                (
                    "A teacher's work goes well beyond the lesson on the timetable. "
                    "There are resources to prepare, assignments to mark, learners to "
                    "guide and progress to follow."
                ),
                (
                    "KLB Elimu gives teachers practical tools to organise their "
                    "classes, prepare learning activities, share resources and keep "
                    "assessment records together."
                ),
                "Your attention belongs in the classroom. Your tools should make the work easier.",
            ],
            "actionLabel": "Explore the Teacher Portal",
            "actionHref": "/for-teachers",
        },
        "learners": {
            "overline": "For learners",
            "title": "Your next discovery starts here.",
            "paragraphs": [
                (
                    "Some lessons make sense immediately. Others need another "
                    "explanation, a little practice or a different approach."
                ),
                (
                    "With KLB Elimu, learners can revisit learning materials, complete "
                    "activities, explore digital books and follow their own learning "
                    "progress."
                ),
                "There is always more to discover.",
            ],
            "actionLabel": "Explore the Learner Portal",
            "actionHref": "/for-learners",
        },
        "parents": {
            "overline": "For parents",
            "title": "Be part of the learning journey.",
            "paragraphs": [
                (
                    "A child's education is not only about the final examination "
                    "result. It is also about attendance, effort, improvement, "
                    "confidence and the small steps that happen along the way."
                ),
                (
                    "KLB Elimu gives parents a convenient way to follow relevant "
                    "school updates, review learning progress and stay connected with "
                    "their children's education."
                ),
            ],
            "actionLabel": "Explore Parent Access",
            "actionHref": "/for-parents",
        },
    },
    "steps": {
        "overline": "How it works",
        "title": "Getting started is straightforward.",
        "steps": [
            {
                "title": "Register your school",
                "copy": (
                    "Create a school account and provide the information needed for "
                    "verification and approval."
                ),
            },
            {
                "title": "Set up your learning environment",
                "copy": "Configure your academic year, classes, subjects, teachers and learners.",
            },
            {
                "title": "Bring learning resources together",
                "copy": "Add your own teaching materials and explore available KLB digital publications.",
            },
            {
                "title": "Start teaching and learning",
                "copy": "Teachers publish lessons and activities. Learners access materials, participate and complete assignments.",
            },
            {
                "title": "Follow the progress",
                "copy": "Review attendance, assessment feedback and learning reports to understand how learners are progressing.",
            },
        ],
    },
    "closingCta": {
        "overline": "Begin with KLB Elimu",
        "title": "Make room for more learning.",
        "copy": (
            "Whether you are preparing a school for its next academic term or "
            "looking for better ways to support everyday learning, KLB Elimu gives "
            "you a place to begin."
        ),
        "primaryLabel": "Register Your School",
        "primaryHref": "/contact?category=School%20registration",
        "secondaryLabel": "Sign In to KLB Elimu",
        "secondaryHref": "/login",
    },
    "trust": {
        "overline": "Why schools choose KLB Elimu",
        "title": "Built for the way schools work",
        "items": [
            {
                "key": "connected",
                "title": "One connected record",
                "copy": (
                    "Courses, attendance, assessments and books share the same "
                    "school information."
                ),
            },
            {
                "key": "roles",
                "title": "The right view for every role",
                "copy": (
                    "Learners, guardians and teachers each see the tools and "
                    "records they need."
                ),
            },
            {
                "key": "modest",
                "title": "Useful on modest connections",
                "copy": "Simple pages and clear actions keep everyday school work moving.",
            },
        ],
    },
    "workspaces": {
        "overline": "What the platform does",
        "title": "Three connected ways to use KLB Elimu",
        "cards": [
            {
                "key": "learning",
                "label": "Learning workspace",
                "index": "01",
                "title": "Learning in one place",
                "copy": (
                    "Courses, assignments, quizzes and a textbook library "
                    "share the same school records."
                ),
                "image": "/images/workspace-skill.jpg",
                "imageAlt": "Learner practising a school skill",
            },
            {
                "key": "school",
                "label": "School day",
                "index": "02",
                "title": "Records that stay connected",
                "copy": (
                    "Attendance, timetables, assessments and class records "
                    "share one school database with the learner portal."
                ),
                "image": "/images/workspace-education.jpg",
                "imageAlt": "Education and school records in use",
            },
            {
                "key": "publishing",
                "label": "Digital publishing",
                "index": "03",
                "title": "Curriculum tied to the classroom",
                "copy": (
                    "Textbooks, chapters, resources and competency based "
                    "outcomes stay linked to the lessons teachers use."
                ),
                "image": "/images/digital-library.jpg",
                "imageAlt": "Library shelves holding reference books",
            },
        ],
    },
    "routines": {
        "overline": "A day in the ecosystem",
        "title": "Small routines, one shared record",
        "description": (
            "The same information follows the school day, from planning a lesson "
            "to reviewing progress."
        ),
        "items": [
            {
                "key": "plan",
                "title": "Plan a lesson",
                "copy": "Teachers prepare courses, materials and assessments in one place.",
            },
            {
                "key": "record",
                "title": "Record the day",
                "copy": "Attendance, submissions and class notes stay linked to the learner.",
            },
            {
                "key": "review",
                "title": "Review progress",
                "copy": "Feedback, results and reports help the next lesson start with context.",
            },
        ],
    },
    "access": {
        "overline": "Clear boundaries",
        "title": "Who sees what",
        "description": (
            "Access follows the permissions set by the school. This short guide "
            "explains the everyday view for each role."
        ),
        "columns": ["Role", "Sees", "Can do"],
        "rows": [
            {
                "role": "Learners",
                "sees": "Their courses, work and results",
                "actions": "Submit work and read feedback",
            },
            {
                "role": "Guardians",
                "sees": "Linked learners' attendance and results",
                "actions": "Follow progress and read school messages",
            },
            {
                "role": "Teachers",
                "sees": "Their classes and curriculum tools",
                "actions": "Plan lessons, mark work and record attendance",
            },
        ],
    },
    "journey": {
        "overline": "A simple first week",
        "title": "Start with three clear steps",
        "description": (
            "No technical setup is needed to explore the platform. Choose your "
            "path, open your workspace and build a routine that fits your school."
        ),
        "steps": [
            {
                "index": "01",
                "title": "Choose your path",
                "copy": "Compare the learner, guardian and teacher views before you sign in.",
            },
            {
                "index": "02",
                "title": "Open your workspace",
                "copy": (
                    "Use the account issued by your school, or register where your "
                    "role allows it."
                ),
            },
            {
                "index": "03",
                "title": "Find what you need",
                "copy": (
                    "Move between courses, records and the digital library without "
                    "leaving the ecosystem."
                ),
            },
        ],
        "checklistTitle": "Have these ready",
        "checklist": [
            "The role you are signing in as",
            "The account issued by your school",
            "A browser with a steady connection",
        ],
    },
    "insights": {
        "overline": "Progress and insight",
        "title": "A clearer picture of learning",
        "description": (
            "School information is most useful when it is easy to read. The "
            "same records used for daily work also feed the dashboards and "
            "reports that teachers, managers and guardians rely on."
        ),
        "points": [
            {"title": "Attendance", "copy": "Daily registers stay linked to the class and learner record."},
            {"title": "Assessments", "copy": "Marks and feedback sit beside the courses they assess."},
            {"title": "Course activity", "copy": "Lessons, resources and submissions share one academic timeline."},
        ],
        "chip": "Attendance, assessments and courses",
        "caption": "Illustrative view of records already captured by the school.",
        "imageSrc": "/images/insight-success.jpg",
        "imageAlt": "A learner celebrating academic progress",
    },
    "accessibility": {
        "overline": "Designed for everyone",
        "title": "Easy to use, by design",
        "items": [
            {
                "key": "keyboard",
                "title": "Keyboard friendly",
                "copy": "Every action has a visible focus and an accessible name.",
            },
            {
                "key": "motion",
                "title": "Motion you control",
                "copy": "Animations respect the reduced-motion setting.",
            },
            {
                "key": "bandwidth",
                "title": "Kind to connections",
                "copy": "Simple pages stay usable on modest bandwidth.",
            },
        ],
    },
    "spotlight": {
        "overline": "Digital library",
        "title": "Find the right resource faster",
        "description": (
            "Start with a title, a learning area or a collection. The public "
            "catalogue shows what is available before you sign in, while full "
            "textbook access stays with your school licence."
        ),
        "actionLabel": "Search the library",
        "actionHref": "/library",
        "imageSrc": "/images/hero-students.jpg",
        "imageAlt": "Students studying together with books and notebooks",
        "imageCaption": "Browse published titles and learning resources.",
    },
    "roles": {
        "overline": "Choose your path",
        "title": "Where do you fit?",
        "description": (
            "Pick the area that sounds like you. We will show what you can "
            "open, what you can do and where to start."
        ),
        "previewLabel": "Access preview",
        "rightsTitle": "What you can do",
        "contentTitle": "What you will see",
        "cards": [
            {
                "key": "learners",
                "label": "Students & learners",
                "title": "Learn at your own pace",
                "copy": (
                    "Open your courses, assignments, quizzes and digital "
                    "books, all linked to your school record."
                ),
                "to": "/login?role=LEARNER",
                "action": "Learner workspace",
                "rights": [
                    "Work only inside your own learner record",
                    "Open your courses, assignments and quizzes",
                    "Track feedback and results in one place",
                    "Read your results, progress report and messages",
                ],
                "content": [
                    "My courses and textbook library",
                    "Assignments and quizzes",
                    "Learning resources",
                    "Progress report and school messages",
                ],
            },
            {
                "key": "guardians",
                "label": "Parents & guardians",
                "title": "Stay close to progress",
                "copy": (
                    "See attendance, results and school messages for the "
                    "learners linked to you, with clear updates that are "
                    "easy to follow."
                ),
                "to": "/login?role=GUARDIAN",
                "action": "Guardian workspace",
                "rights": [
                    "View progress for the learners linked to you",
                    "Read attendance, results and school messages",
                    "Update your own guardian profile",
                    "No staff or administration permissions",
                ],
                "content": [
                    "Linked learner progress",
                    "Attendance and assessment results",
                    "School messages",
                    "Guardian profile",
                ],
            },
            {
                "key": "teachers",
                "label": "Teachers",
                "title": "Plan, teach and assess",
                "copy": (
                    "Plan lessons, keep class records, mark work and use "
                    "curriculum tools in one calm workspace."
                ),
                "to": "/login?role=TEACHER",
                "action": "Teacher workspace",
                "rights": [
                    "Prepare courses, lessons, assignments and quizzes",
                    "Record attendance and manage class results",
                    "View learner records for your classes",
                    "No user administration or staff appointment permissions",
                ],
                "content": [
                    "Courses, modules and lessons",
                    "Assignments, submissions and question bank",
                    "Timetable, attendance and exams",
                    "Learners and curriculum tools",
                ],
            },
        ],
    },
    "support": {
        "overline": "Need a hand?",
        "title": "Help starts with your school",
        "description": (
            "Your school administrator can confirm accounts, permissions and "
            "access to digital books."
        ),
        "primaryLabel": "Read common questions",
        "primaryHref": "/#faq",
        "secondaryLabel": "See role access",
        "secondaryHref": "/#access",
    },
    "faq": {
        "overline": "Good to know",
        "title": "Questions people ask first",
        "description": (
            "Short answers about accounts, access and the way information is "
            "shared across the platform."
        ),
        "items": [
            {
                "question": "Do I need an invitation to register?",
                "answer": (
                    "Learner, guardian and teacher accounts start at the public "
                    "registration page. Teacher accounts wait for school approval, "
                    "while administrator accounts always use a secure invitation."
                ),
            },
            {
                "question": "Can a guardian follow more than one learner?",
                "answer": (
                    "Yes. The school links guardians to the right learners, and the "
                    "guardian workspace shows attendance, results and messages for "
                    "those links."
                ),
            },
            {
                "question": "What happens if a save does not work?",
                "answer": (
                    "This is a normal web app. A failed save stays unsaved, shows a "
                    "clear error and leaves the last saved information in place so "
                    "you can try again."
                ),
            },
            {
                "question": "Who can see a learner's records?",
                "answer": (
                    "Access follows the permissions set by the school. Learners see "
                    "their own records, guardians see linked learners and staff see "
                    "only the classes and tools their role allows."
                ),
            },
        ],
    },
    "publicPages": {
        "about": {
            "pageTitle": "About KLB Elimu",
            "title": "Learning deserves a thoughtful digital home.",
            "introduction": [
                (
                    "KLB Elimu is a proposed digital learning ecosystem developed "
                    "around the needs of Kenyan schools and the people who make "
                    "learning possible."
                ),
                (
                    "The platform brings together school administration, teaching "
                    "and learning activities, assessments and digital educational "
                    "resources."
                ),
                (
                    "It is designed to give teachers practical tools, learners easier "
                    "access to knowledge, parents a clearer view of learning progress "
                    "and schools a more organised way to manage academic activities."
                ),
            ],
            "brandMessage": [
                "A good lesson should not end when the bell rings.",
                (
                    "There is always another question to explore, another idea to "
                    "understand and another opportunity to grow."
                ),
                (
                    "KLB Elimu brings learning resources, classroom activities, "
                    "assessments and educational publishing together in one place, "
                    "giving teachers and learners more ways to make every learning "
                    "moment count."
                ),
            ],
            "approachTitle": "Our approach",
            "approach": [
                {
                    "title": "Learning first",
                    "copy": (
                        "Technology should support teaching and learning, not become "
                        "another obstacle for teachers and learners."
                    ),
                },
                {
                    "title": "Knowledge should be accessible",
                    "copy": (
                        "Educational resources should be easy to find and convenient "
                        "to use, including in environments where internet access is "
                        "limited."
                    ),
                },
                {
                    "title": "Every learner matters",
                    "copy": (
                        "The platform should support different education levels, "
                        "learning needs and individual learning journeys."
                    ),
                },
                {
                    "title": "Better organisation, better insight",
                    "copy": (
                        "Good records help schools understand attendance, "
                        "participation, assessment outcomes and areas where learners "
                        "need more support."
                    ),
                },
            ],
            "commitmentTitle": "Our commitment",
            "commitment": (
                "KLB Elimu is being designed with attention to educational value, "
                "responsible technology use, accessibility, data protection and the "
                "realities of schools across Kenya."
            ),
        },
        "schools": {
            "pageTitle": "A digital home for your school.",
            "title": "A digital home for your school.",
            "introduction": [
                (
                    "Running a school involves keeping many things moving at once. "
                    "Learner records, teachers, classes, subjects, attendance, "
                    "academic activities and school communication all need attention."
                ),
                "KLB Elimu helps bring essential learning and school records into one organised environment.",
            ],
            "benefitsTitle": "Benefits",
            "benefits": [
                {
                    "title": "Organised learner records",
                    "copy": (
                        "Keep learner profiles, admission details, class placements "
                        "and academic information accessible to authorised school staff."
                    ),
                },
                {
                    "title": "Connected teaching teams",
                    "copy": (
                        "Assign teachers to classes and learning areas, making "
                        "responsibilities easier to follow."
                    ),
                },
                {
                    "title": "Learning visibility",
                    "copy": (
                        "See which activities are taking place, how learners are "
                        "performing and where additional support may be needed."
                    ),
                },
                {
                    "title": "Useful reporting",
                    "copy": (
                        "Generate attendance, assessment and performance reports "
                        "without having to assemble every record manually."
                    ),
                },
                {
                    "title": "Learning resources",
                    "copy": (
                        "Connect classroom activities to available digital textbooks "
                        "and supplementary KLB resources."
                    ),
                },
            ],
            "actionLabel": "Register Your School",
            "actionHref": "/contact?category=School%20registration",
        },
        "teachers": {
            "pageTitle": "Your teaching workspace.",
            "title": "Your teaching workspace.",
            "introduction": [
                (
                    "Teaching takes preparation, patience and good judgement. KLB "
                    "Elimu gives teachers a workspace for the practical work that "
                    "supports a lesson, before, during and after the classroom session."
                )
            ],
            "featuresTitle": "Features",
            "features": [
                "Prepare and organise lessons.",
                "Access available learning resources.",
                "Create assignments and assessments.",
                "Review learner submissions.",
                "Record marks, feedback and assessment evidence.",
                "Track class participation and attendance.",
                "View individual and class progress.",
            ],
            "closing": (
                "Spend less time searching for scattered teaching materials and more "
                "time guiding learners towards understanding."
            ),
            "actionLabel": "Access Teacher Portal",
            "actionHref": "/login?role=TEACHER",
        },
        "learners": {
            "pageTitle": "Your learning journey, in one place.",
            "title": "Your learning journey, in one place.",
            "introduction": [
                "A lesson is the beginning, not the end.",
                (
                    "KLB Elimu gives learners a place to find learning materials, "
                    "revisit difficult topics, complete assignments, take assessments "
                    "and follow their progress."
                ),
            ],
            "featuresTitle": "What learners can do",
            "features": [
                "Find lessons and subjects.",
                "Read available digital textbooks.",
                "Download permitted learning materials.",
                "Watch or listen to educational resources.",
                "Submit assignments.",
                "Complete practice activities.",
                "Take assigned assessments.",
                "Review results and teacher feedback.",
            ],
            "closing": (
                "Ask questions. Practise what you learn. Return to the topics that "
                "challenge you. Every step forward counts."
            ),
            "actionLabel": "Access Learner Portal",
            "actionHref": "/login?role=LEARNER",
        },
        "parents": {
            "pageTitle": "A closer connection to school.",
            "title": "A closer connection to school.",
            "introduction": [
                "Being involved in a child's education begins with knowing how things are going.",
                (
                    "KLB Elimu gives parents an authorised view of their children's "
                    "learning activities, attendance, assessment feedback and school "
                    "announcements."
                ),
            ],
            "featuresTitle": "Parent features",
            "features": [
                "View linked learner profiles.",
                "Follow attendance records.",
                "Review available assessment results.",
                "Read teacher feedback.",
                "Receive school announcements.",
                "View relevant progress reports.",
            ],
            "closing": (
                "The most helpful conversation about school often begins with "
                "knowing what happened there today."
            ),
            "actionLabel": "Access Parent Portal",
            "actionHref": "/login?role=GUARDIAN",
        },
        "library": {
            "pageTitle": "The KLB Digital Library",
            "title": "Find the next resource that makes a difference.",
            "introduction": [
                (
                    "Explore a growing collection of available educational "
                    "publications and learning resources from KLB and other approved "
                    "content providers."
                ),
                (
                    "Browse by education level, grade, subject, language and resource "
                    "type to find material relevant to your learning needs."
                ),
            ],
            "categoriesTitle": "Library categories",
            "categories": [
                "Textbooks",
                "Revision materials",
                "Supplementary readers",
                "Teacher resources",
                "Audio learning",
                "Video learning",
                "Practice activities",
                "Assessment resources",
            ],
            "searchPlaceholder": "Search by book title, subject, grade or keyword...",
            "filters": [
                "Education level",
                "Grade",
                "Subject",
                "Language",
                "Content type",
                "Publisher",
                "Access availability",
            ],
            "accessLabels": [
                "Included in your subscription",
                "Available for purchase",
                "School licensed",
                "Teacher access",
                "Preview available",
                "Not currently available",
            ],
            "pricingNote": (
                "Do not display a purchase price until a resource has an approved "
                "price and currency."
            ),
        },
        "contact": {
            "pageTitle": "Let's talk about learning.",
            "title": "Let's talk about learning.",
            "introduction": [
                (
                    "Have a question about KLB Elimu, registering your school or "
                    "accessing learning resources? Send us a message and tell us how "
                    "we can help."
                )
            ],
            "fields": [
                "Full name",
                "Email address",
                "Phone number",
                "Organisation or school",
                "Enquiry category",
                "Subject",
                "Message",
            ],
            "categories": [
                "School registration",
                "Account access",
                "Digital library",
                "Teacher support",
                "Subscription enquiries",
                "Technical assistance",
                "Partnership enquiries",
                "General enquiries",
            ],
            "actionLabel": "Send Enquiry",
            "confirmation": (
                "Thank you for getting in touch. Your enquiry has been received. "
                "Keep your reference number for any follow-up communication."
            ),
            "note": "Do not promise a response time until KLB has approved a service-level commitment.",
        },
        "help": {
            "pageTitle": "A little help goes a long way.",
            "title": "A little help goes a long way.",
            "introduction": [
                (
                    "Find practical guidance for using KLB Elimu. Whether you are "
                    "setting up a school, preparing lessons, accessing a digital book "
                    "or managing an account, start here."
                )
            ],
            "searchPlaceholder": "What would you like help with?",
            "suggestedSearches": [
                "I cannot sign in.",
                "How do I register my school?",
                "How do I add learners?",
                "Where can I find digital books?",
                "How do I submit an assignment?",
            ],
            "categories": [
                {
                    "title": "Getting Started",
                    "items": [
                        "How to access KLB Elimu.",
                        "How to register a school.",
                        "How to activate an account.",
                        "How to reset a password.",
                        "How to navigate your dashboard.",
                    ],
                },
                {
                    "title": "School Administration",
                    "items": [
                        "How to register learners.",
                        "How to generate admission numbers.",
                        "How to create classes and streams.",
                        "How to register teachers.",
                        "How to assign teachers.",
                        "How to link parents to learners.",
                        "How to manage attendance.",
                    ],
                },
                {
                    "title": "Teaching and Learning",
                    "items": [
                        "How to create a lesson.",
                        "How to access digital resources.",
                        "How to create assignments.",
                        "How to prepare an assessment.",
                        "How to mark learner submissions.",
                        "How to view progress reports.",
                    ],
                },
                {
                    "title": "Digital Library",
                    "items": [
                        "How to search for a book.",
                        "How to preview a resource.",
                        "How to access licensed content.",
                        "How to download permitted resources.",
                        "How to use the digital reader.",
                    ],
                },
                {
                    "title": "Parents and Learners",
                    "items": [
                        "How to access learning materials.",
                        "How to submit an assignment.",
                        "How to review teacher feedback.",
                        "How to link a parent account.",
                        "How to follow learning progress.",
                    ],
                },
                {
                    "title": "Account and Security",
                    "items": [
                        "How to change a password.",
                        "How to manage account information.",
                        "How to protect an account.",
                        "How to report suspicious activity.",
                    ],
                },
            ],
            "supportTitle": "Still need a hand?",
            "supportCopy": (
                "Some questions need a little more attention. Send the support team "
                "a request and include as much relevant detail as possible."
            ),
            "actionLabel": "Contact Support",
            "actionHref": "/contact?category=Technical%20assistance",
        },
        "faq": {
            "pageTitle": "Frequently Asked Questions",
            "title": "Frequently Asked Questions",
            "introduction": [
                "Short answers about accounts, access and the way information is shared across the platform."
            ],
            "groups": [
                {
                    "title": "General",
                    "items": [
                        {
                            "question": "What is KLB Elimu?",
                            "answer": (
                                "KLB Elimu is a proposed digital learning ecosystem "
                                "that brings together school management, teaching and "
                                "learning activities, assessments and digital "
                                "educational resources."
                            ),
                        },
                        {
                            "question": "Who can use KLB Elimu?",
                            "answer": (
                                "The initial platform is intended for schools, "
                                "teachers, learners, parents and authorised KLB "
                                "administrators."
                            ),
                        },
                        {
                            "question": "Can any school register?",
                            "answer": (
                                "Schools can submit registration applications. Access "
                                "should be activated after the applicable verification "
                                "and approval process."
                            ),
                        },
                        {
                            "question": "Can I use KLB Elimu on a phone?",
                            "answer": (
                                "The platform is designed to work on computers, "
                                "tablets and smartphones through a responsive interface."
                            ),
                        },
                    ],
                },
                {
                    "title": "Schools",
                    "items": [
                        {
                            "question": "Can my school register multiple classes?",
                            "answer": (
                                "Yes. An authorised school administrator can create "
                                "and manage the classes and streams supported by the "
                                "school's approved account configuration."
                            ),
                        },
                        {
                            "question": "Can I upload learner details in bulk?",
                            "answer": (
                                "The system should provide an approved spreadsheet "
                                "template to help schools import learner records."
                            ),
                        },
                        {
                            "question": "Can a school have multiple administrators?",
                            "answer": (
                                "Yes. A school can assign appropriate administrative "
                                "roles to authorised staff, with permissions managed "
                                "separately."
                            ),
                        },
                    ],
                },
                {
                    "title": "Teachers",
                    "items": [
                        {
                            "question": "Can teachers upload their own learning materials?",
                            "answer": (
                                "Teachers should be able to upload permitted teaching "
                                "materials to their assigned classes, subject to file "
                                "restrictions and school permissions."
                            ),
                        },
                        {
                            "question": "Can I reuse an assignment?",
                            "answer": (
                                "Teachers should be able to duplicate their own "
                                "reusable activities and assessments where permitted."
                            ),
                        },
                        {
                            "question": "Can learners submit assignments online?",
                            "answer": (
                                "Yes. The platform should support the submission "
                                "formats enabled for each assignment."
                            ),
                        },
                    ],
                },
                {
                    "title": "Learners",
                    "items": [
                        {
                            "question": "Can I read books online?",
                            "answer": (
                                "You can access the digital books and learning "
                                "materials available to your account."
                            ),
                        },
                        {
                            "question": "Can I study without internet access?",
                            "answer": (
                                "Some resources can be made available offline where "
                                "downloading and offline use are permitted. Access "
                                "and synchronisation depend on the resource format and "
                                "licence conditions."
                            ),
                        },
                        {
                            "question": "Can I see my assessment results?",
                            "answer": (
                                "You can view the results and feedback that your "
                                "teacher or school has made available."
                            ),
                        },
                    ],
                },
                {
                    "title": "Parents",
                    "items": [
                        {
                            "question": "Can I link more than one child to my account?",
                            "answer": (
                                "The platform should support verified parent accounts "
                                "linked to multiple learner records."
                            ),
                        },
                        {
                            "question": "Can I view my child's marks?",
                            "answer": (
                                "You can view assessment information and reports made "
                                "available to parents by the school."
                            ),
                        },
                        {
                            "question": "Can I change my child's admission details?",
                            "answer": (
                                "Protected school records should be updated by "
                                "authorised school administrators. Contact the school "
                                "if you notice incorrect information."
                            ),
                        },
                    ],
                },
                {
                    "title": "Digital content",
                    "items": [
                        {
                            "question": "Are all digital books free?",
                            "answer": (
                                "Not necessarily. Access depends on the resource's "
                                "licensing and subscription conditions. Each book "
                                "should clearly indicate its access requirements."
                            ),
                        },
                        {
                            "question": "Can I download every book?",
                            "answer": (
                                "Download options depend on the relevant publishing "
                                "and licensing conditions."
                            ),
                        },
                        {
                            "question": "Can I share my account with someone else?",
                            "answer": (
                                "Accounts should only be used by the authorised user. "
                                "Sharing account credentials can compromise personal "
                                "information and access rights."
                            ),
                        },
                    ],
                },
            ],
        },
        "accessibility": {
            "pageTitle": "Make Learning Work for You",
            "title": "Make Learning Work for You",
            "introduction": [
                (
                    "People learn and interact with digital content in different "
                    "ways. KLB Elimu should provide practical accessibility options "
                    "that help users navigate the platform comfortably."
                )
            ],
            "settingsTitle": "Accessibility settings",
            "settings": [
                "Text size",
                "High contrast",
                "Reduced motion",
                "Improved text spacing",
                "Keyboard navigation",
                "Screen-reader compatibility",
                "Captions, where available",
                "Audio learning, where available",
            ],
            "message": (
                "Choose the display settings that make the platform easier for you "
                "to use. Your preferences should be saved to your account where "
                "supported."
            ),
            "specialSupportTitle": "Special support",
            "specialSupport": (
                "Where a learner requires additional support, schools should be able "
                "to make appropriate arrangements without unnecessarily exposing "
                "sensitive personal information."
            ),
        },
        "privacy": {
            "pageTitle": "Your information deserves care.",
            "title": "Your information deserves care.",
            "introduction": [
                (
                    "KLB Elimu is intended to support learning while respecting the "
                    "privacy and security of the people who use it."
                ),
                (
                    "Information should only be collected for legitimate purposes, "
                    "made available to authorised users and handled according to "
                    "applicable data protection requirements."
                ),
                (
                    "Parents, teachers, learners and school administrators should "
                    "understand what information is collected and how it is used."
                ),
            ],
            "acceptableUseTitle": "Acceptable use",
            "acceptableUse": [
                "Protect their account credentials.",
                "Respect other users.",
                "Use educational resources in accordance with their access rights.",
                "Avoid uploading inappropriate or unauthorised content.",
                "Report suspicious activity.",
                "Follow school and platform rules.",
            ],
            "principlesTitle": "Important privacy principles",
            "principles": [
                "Collect only necessary information.",
                "Apply role-based access.",
                "Restrict access to children's records.",
                "Provide appropriate parent or guardian safeguards.",
                "Maintain audit records.",
                "Protect data during storage and transmission.",
                "Support appropriate retention and deletion processes.",
            ],
            "note": (
                "The final Privacy Notice, Terms of Use, Children's Data Policy and "
                "other legal documents must be reviewed and approved by KLB's legal "
                "and data protection teams before publication."
            ),
        },
    },
    "messages": {
        "pageIntroductions": {
            "overview": "Here is a summary of the activities and information available to your account.",
            "records": "View, manage and update the information associated with this section.",
            "reports": "Explore the available records and reports to understand activity and progress.",
            "settings": "Manage the preferences and account details available to your role.",
            "notifications": "Keep track of important updates and messages relevant to your account.",
        },
        "searchPlaceholders": {
            "schools": "Search schools by name or registration number...",
            "learners": "Search learners by name or admission number...",
            "teachers": "Search teachers by name or staff number...",
            "resources": "Search resources by title, subject or grade...",
            "lessons": "Search lessons by topic or learning area...",
            "announcements": "Search announcements...",
            "transactions": "Search transactions by reference number...",
        },
        "globalActions": [
            "Add New",
            "Create Record",
            "Edit Details",
            "View Details",
            "Save Changes",
            "Save as Draft",
            "Publish",
            "Submit",
            "Approve",
            "Reject",
            "Download",
            "Export",
            "Print",
            "Archive",
            "Restore",
            "Cancel",
            "Close",
        ],
        "loading": [
            "Preparing your dashboard...",
            "Retrieving school records...",
            "Opening your learning resources...",
            "Saving your changes...",
            "Submitting your assignment...",
            "Preparing your report...",
            "Checking your account...",
            "Synchronising your offline activity...",
        ],
        "success": {
            "recordSaved": "Your changes have been saved successfully.",
            "schoolCreated": "The school record has been created. You can now continue with the verification process.",
            "learnerAdded": "The learner has been added to the school register.",
            "teacherInvited": "The invitation has been sent successfully.",
            "lessonPublished": "Your lesson is now available to the selected class.",
            "assignmentCreated": "Your assignment has been created and is available according to its publication settings.",
            "resourceUploaded": "Your resource has been uploaded. It will remain in draft or review status until it is approved for publication.",
            "reportGenerated": "Your report is ready. You can now view or download it.",
        },
        "errors": {
            "invalidLogin": "We could not verify those sign-in details. Check your username and password and try again.",
            "accountLocked": "Your account has been temporarily locked following repeated unsuccessful sign-in attempts. Follow the account recovery instructions or contact your administrator.",
            "sessionExpired": "Your session has ended. Sign in again to continue.",
            "noPermission": "Your account does not have permission to perform this action.",
            "duplicateAdmission": "This admission number is already assigned to another learner. Review the number before continuing.",
            "requiredMissing": "Some required fields have not been completed. Review the highlighted fields and try again.",
            "fileTooLarge": "This file exceeds the permitted upload size. Choose a smaller file or an approved alternative format.",
            "unsupportedFile": "This file type is not supported. Check the permitted formats and upload the resource again.",
            "connectionInterrupted": "We lost the connection while processing your request. Check your internet connection before trying again.",
            "submissionFailed": "Your submission could not be completed. Check its status before submitting again.",
            "somethingWrong": "We could not complete that action. Try again, or contact support if the problem continues. Include the reference number shown on this page.",
        },
        "confirmations": {
            "deleteRecord": "Are you sure you want to delete this record? This action may affect related information. Check the details before proceeding.",
            "suspendSchool": "Suspending this school will restrict access according to the platform's suspension policy. Existing academic records should remain protected.",
            "publishContent": "You are about to make this resource available to the selected audience. Confirm that its description, content and access rights have been reviewed.",
            "restoreBackup": "Restoring this backup may replace current platform information. Confirm the backup scope and follow the recovery procedure before proceeding.",
        },
        "emptyStates": {
            "schools": {
                "title": "No schools registered yet",
                "message": "Schools will appear here once their registration details have been submitted.",
            },
            "learners": {
                "title": "Your learner register is empty",
                "message": "Add your first learner or import an existing register to get started.",
            },
            "teachers": {
                "title": "Your teaching team is waiting",
                "message": "Invite teachers and assign them to their relevant classes.",
            },
            "classes": {
                "title": "No classes have been created",
                "message": "Set up your classes and streams to begin organising learners.",
            },
            "lessons": {
                "title": "No lessons yet",
                "message": "Your teachers' published lessons will appear here.",
            },
            "assignments": {
                "title": "Nothing to submit right now",
                "message": "New assignments will appear here when your teachers publish them.",
            },
            "assessments": {
                "title": "No assessments available",
                "message": "Check again when your teacher assigns an assessment.",
            },
            "resources": {
                "title": "No resources found",
                "message": "Try changing your search or exploring another category.",
            },
            "reports": {
                "title": "No reports available yet",
                "message": "Reports will appear when sufficient records have been created.",
            },
            "messages": {
                "title": "Your inbox is clear",
                "message": "New school and learning messages will appear here.",
            },
            "notifications": {
                "title": "You're all caught up",
                "message": "Important updates will appear here when they arrive.",
            },
        },
        "firstTime": {
            "schoolRegistration": "Your school is not just creating an account. It is preparing a learning environment. Begin by confirming the official school details.",
            "learnerRegistration": "Start building your learner register. You can add learners individually or import multiple records using the approved template.",
            "teacherRegistration": "Invite the teachers who will prepare lessons, manage learning activities and guide your learners.",
            "digitalLibrary": "Your library is ready to receive learning resources. Start by exploring the resources already available to your account.",
        },
        "notifications": {
            "schoolApproved": "Your school registration has been approved. You can now sign in and begin setting up your school's learning environment.",
            "teacherCreated": "A new teacher account has been created for your school. The teacher can complete the account activation process using the invitation sent to their registered contact.",
            "learnerRegistered": "A new learner has been added to your school records. Review the learner's profile to confirm that the class placement and contact details are correct.",
            "incompleteSetup": "Your school's initial setup is not yet complete. Review the outstanding items to prepare the learning environment for teachers and learners.",
            "subscriptionReminder": "Your school's subscription is approaching its renewal date. Review your current package and plan the next renewal.",
            "newClass": "You have been assigned to [Class Name]. Open your class dashboard to review the learners and assigned learning areas.",
            "newLearner": "A new learner has joined [Class Name]. Review the updated class register.",
            "submissionReceived": "[Learner Name] has submitted the assignment \"[Assignment Title]\". It is now available for review.",
            "deadlineApproaching": "The submission deadline for \"[Assignment Title]\" is approaching. Review the outstanding submissions from your class.",
            "resourcePublished": "A new learning resource relevant to your teaching area is available in the digital library.",
            "markingReminder": "There are submitted assessments awaiting your review. Visit your assessment workspace to continue marking.",
            "newLesson": "Your teacher has added a new lesson to [Learning Area]. Open it and see what you will explore next.",
            "newAssignment": "There is a new assignment waiting for you in [Subject]. Read the instructions and check the submission date.",
            "assignmentReminder": "Remember to complete \"[Assignment Title]\" before its due date.",
            "feedbackAvailable": "Your teacher has reviewed your work. Open the assignment to see the feedback and suggestions.",
            "newAssessment": "A new assessment has been assigned to you. Read the instructions and check when it is available.",
            "lessonCompleted": "You have completed \"[Lesson Title]\". Take a moment to review what you have learned before moving on.",
            "schoolAnnouncement": "Your child's school has shared a new announcement. Sign in to read the details.",
            "assessmentResult": "A new assessment result for [Learner Name] is available for your review.",
            "attendanceUpdate": "A new attendance record has been made available by the school for [Learner Name].",
            "parentFeedback": "New teacher feedback has been shared for [Learner Name]. Sign in to view the available information.",
            "academicReport": "A new academic report for [Learner Name] is available.",
            "maintenance": "KLB Elimu will undergo scheduled maintenance on [Date] between [Start Time] and [End Time]. Some services may be temporarily unavailable during this period.",
            "newFeature": "We have introduced an improvement to KLB Elimu. Visit the platform to explore the updated feature.",
            "securityNotice": "A security-related change has been made to your account. Review your account activity and contact support if you do not recognise the activity.",
        },
    },
    "library": {
        "overline": "Public library",
        "title": "Find books and learning resources",
        "description": (
            "Explore a growing collection of available educational publications "
            "and learning resources from KLB and other approved content providers. "
            "Browse by education level, grade, subject, language and resource type."
        ),
        "booksOverline": "Textbook catalogue",
        "booksTitle": "Books to explore",
        "booksDescription": (
            "See published titles from the catalogue. Full book access "
            "depends on your school licence and is managed by your "
            "administrator."
        ),
        "resourcesOverline": "Learning resources",
        "resourcesTitle": "Find learning resources",
        "resourcesDescription": (
            "Browse published resources by level, learning area, collection "
            "and keyword. Start with a textbook topic, a document or a "
            "curated collection."
        ),
    },
    "auth": {
        "login": {
            "publicHeading": "Welcome back.",
            "adminHeading": "Welcome back.",
            "storyCopy": (
                "Your classroom, learning resources and school activities are just "
                "a sign-in away."
            ),
            "storyImageSrc": "/images/signin-time.jpg",
            "footnote": (
                "A proposed digital learning initiative associated with Kenya "
                "Literature Bureau PLC, subject to organisational approval."
            ),
            "publicIntro": "New to KLB Elimu? Your school administrator can help you get access to the platform.",
            "adminIntro": "Use an administrator account issued by your institution or platform administrator.",
        },
        "register": {
            "overline": "Create your account",
            "heading": "Choose your role, then fill in only what applies.",
            "copy": (
                "Learner and guardian accounts are ready to use straight "
                "away. Teacher accounts wait for approval by the school. "
                "Administrator accounts need a secure invitation and are "
                "never created through this form."
            ),
            "notice": "The school database is shared, so accounts created here appear in the administration portal for the same institution.",
            "storyImageSrc": "/images/register-learn.jpg",
            "steps": [
                "Choose account type",
                "Add your details",
                "Complete your role setup",
            ],
            "roleOptions": [
                {"value": "LEARNER", "label": "Learner", "note": "Courses, assignments and results"},
                {"value": "GUARDIAN", "label": "Parent / Guardian", "note": "Follow a learner's progress"},
                {"value": "TEACHER", "label": "Teacher", "note": "Created pending school approval"},
            ],
        },
        "admin": {
            "overline": "Administration portal",
            "heading": "Administrator accounts use invitations only.",
            "copy": (
                "A platform or school administrator must issue a secure, "
                "single use invitation token. The token fixes the role and "
                "school. This form cannot grant administrator privileges by "
                "itself. Each token works once and expires after seven days."
            ),
            "warning": (
                "Do not share invitation tokens or passwords over unsecured "
                "channels. If you do not have a token, contact your "
                "platform administrator."
            ),
        },
    },
    "portal": {
        "tutorImageSrc": "/images/tutor-brain.jpg",
        "tutorImageAlt": "A learner thinking through a problem",
    },
    "app": {
        "adminBrand": "KLB Elimu",
        "portalBrand": "KLB Elimu",
        "portalNav": [
            {"key": "home", "label": "Home"},
            {"key": "courses", "label": "My courses"},
            {"key": "textbooks", "label": "Textbook library"},
            {"key": "resources", "label": "Resources"},
            {"key": "documents", "label": "Documents"},
            {"key": "assignments", "label": "Assignments"},
            {"key": "quizzes", "label": "Quizzes"},
            {"key": "reports", "label": "Progress report"},
            {"key": "remediation", "label": "My support tasks"},
            {"key": "fees", "label": "Fees"},
            {"key": "tutor", "label": "Ask the tutor"},
            {"key": "communications", "label": "Messages"},
            {"key": "profile", "label": "My profile"},
        ],
    },
    "styles": default_site_styles(),
}


IMAGE_KEYS = {"image", "imageSrc", "storyImageSrc", "tutorImageSrc"}
LINK_KEYS = {
    "href", "linkHref", "primaryHref", "secondaryHref", "signInHref", "to",
    "actionHref", "primaryCtaHref",
} | IMAGE_KEYS
MAX_TEXT_LENGTH = 4000
MAX_LIST_LENGTH = 60
RETIRED_ROLE_KEYS = {"content"}
RETIRED_NAV_KEYS = {"sync"}
RETIRED_OFFLINE_COPY = {
    "Courses, assignments, quizzes and a textbook library in one place. "
    "Changes wait safely on the device and sync when the connection returns.": (
        "Courses, assignments, quizzes and a textbook library share the same "
        "school records."
    ),
    "Open your courses, assignments, quizzes and digital books. Your work "
    "waits safely on the device and syncs when you are back online.": (
        "Open your courses, assignments, quizzes and digital books, all linked "
        "to your school record."
    ),
    ". It is built for competency based learning and works when the network "
    "is not.": ", built for competency based learning.",
    "Lessons that continue offline": "Learning in one place",
    "Submit work while offline and sync on reconnect": "Track feedback and results in one place",
}


def _without_retired_role_cards(content):
    """Drop the retired content manager preview, even from old saved data."""
    if not isinstance(content, dict):
        return content
    roles = content.get("roles")
    cards = roles.get("cards") if isinstance(roles, dict) else None
    if not isinstance(cards, list):
        return content
    kept = [
        card for card in cards
        if isinstance(card, dict)
        and card.get("key") not in RETIRED_ROLE_KEYS
        and "content manager" not in str(card.get("label", "")).lower()
    ]
    if len(kept) == len(cards):
        return content
    updated = dict(content)
    updated["roles"] = {**roles, "cards": kept}
    return updated


def _without_retired_nav_items(content):
    """Drop the retired offline queue link, even from old saved data."""
    if not isinstance(content, dict):
        return content
    app = content.get("app")
    nav = app.get("portalNav") if isinstance(app, dict) else None
    if not isinstance(nav, list):
        return content
    kept = [
        item for item in nav
        if isinstance(item, dict) and item.get("key") not in RETIRED_NAV_KEYS
    ]
    if len(kept) == len(nav):
        return content
    updated = dict(content)
    updated["app"] = {**app, "portalNav": kept}
    return updated


def _replace_retired_offline_copy(value):
    """Replace known offline-era wording in saved edits as well as defaults."""
    if isinstance(value, str):
        for old, new in RETIRED_OFFLINE_COPY.items():
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [_replace_retired_offline_copy(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _replace_retired_offline_copy(item)
            for key, item in value.items()
        }
    return value


def _strip_retired_content(content):
    content = _without_retired_nav_items(_without_retired_role_cards(content))
    return _replace_retired_offline_copy(content)


def default_site_content():
    """Return a fresh copy so callers never mutate the module constant."""
    return deep_merge(DEFAULT_SITE_CONTENT, {})


def deep_merge(template, overrides):
    """Copy the template, replacing only the keys present in overrides."""
    if isinstance(template, dict):
        result = {key: deep_merge(value, None) for key, value in template.items()}
        if isinstance(overrides, dict):
            for key, value in overrides.items():
                if key in template:
                    result[key] = deep_merge(template[key], value)
        return result
    if isinstance(template, list):
        if isinstance(overrides, list):
            return overrides
        return [deep_merge(item, None) for item in template]
    return overrides if isinstance(overrides, type(template)) else template


def _normalise_styles(value):
    """Validate section-scoped colours and layout choices."""
    if not isinstance(value, dict):
        raise ValidationError({"styles": "Section styles must be an object."})
    result = {}
    for section in STYLE_SECTION_KEYS:
        section_value = value.get(section, {})
        if not isinstance(section_value, dict):
            raise ValidationError({f"styles.{section}": "This section must be an object."})
        clean = {}
        for field in STYLE_COLOUR_KEYS:
            colour = section_value.get(field, "")
            if colour in ("", None):
                clean[field] = ""
            elif not isinstance(colour, str) or not HEX_COLOUR.fullmatch(colour):
                raise ValidationError({
                    f"styles.{section}.{field}": "Enter a six-digit hex colour such as #FFFFFF."
                })
            else:
                clean[field] = colour.upper()
        for field, choices in STYLE_CHOICES.items():
            choice = section_value.get(field, "")
            if choice not in choices:
                raise ValidationError({
                    f"styles.{section}.{field}": "Choose one of the supplied options."
                })
            clean[field] = choice
        background = clean["background"]
        text = clean["text"]
        if background and text and contrast_ratio(background, text) < MIN_TEXT_CONTRAST:
            raise ValidationError({
                f"styles.{section}.text": (
                    "This text colour has less than 4.5:1 contrast on the section "
                    "background. Choose a lighter or darker colour."
                )
            })
        result[section] = clean
    return result


def _safe_link(value, path):
    text = str(value or "")
    if text.startswith("/") and not text.startswith("//"):
        return text
    parsed = urlparse(text)
    if parsed.scheme == "https" and parsed.netloc:
        return text
    raise ValidationError({path: "Use a site path or a full HTTPS address."})


def _normalise(value, template, path):
    if isinstance(template, str):
        if not isinstance(value, str) or len(value) > MAX_TEXT_LENGTH:
            raise ValidationError({path: "Enter text of 4000 characters or fewer."})
        key = path.rsplit(".", 1)[-1]
        if key in IMAGE_KEYS and value == "":
            return ""
        return _safe_link(value, path) if key in LINK_KEYS else value
    if isinstance(template, dict):
        if not isinstance(value, dict):
            raise ValidationError({path: "This section must be an object."})
        result = {}
        for key, child_template in template.items():
            child_path = f"{path}.{key}" if path else key
            if key in value:
                result[key] = _normalise(value[key], child_template, child_path)
            else:
                result[key] = deep_merge(child_template, None)
        return result
    if isinstance(template, list):
        if not isinstance(value, list) or len(value) > MAX_LIST_LENGTH:
            raise ValidationError({path: f"Use a list of {MAX_LIST_LENGTH} items or fewer."})
        def item_path(index):
            return f"{path}.{index}" if path else str(index)

        if not template:
            return [_normalise(item, "", item_path(index)) for index, item in enumerate(value)]
        item_template = template[0]
        if isinstance(item_template, dict):
            result = []
            for index, item in enumerate(value):
                if not isinstance(item, dict):
                    raise ValidationError({path: f"Item {index + 1} must be an object."})
                result.append(_normalise(item, item_template, item_path(index)))
            return result
        return [
            _normalise(item, item_template, item_path(index))
            for index, item in enumerate(value)
        ]
    return value


def normalise_site_content(value):
    """Validate an admin edit and strip keys that are not in the schema."""
    if not isinstance(value, dict):
        raise ValidationError({"content": "Site content must be an object."})
    normalised = _normalise(value, DEFAULT_SITE_CONTENT, "")
    normalised["styles"] = _normalise_styles(normalised.get("styles", {}))
    return _strip_retired_content(normalised)


def public_site_content(overrides=None):
    """Merge stored overrides onto defaults for a safe public response."""
    merged = _strip_retired_content(deep_merge(DEFAULT_SITE_CONTENT, overrides or {}))
    try:
        merged["styles"] = _normalise_styles(merged.get("styles", {}))
    except ValidationError:
        # A stale saved value must never break the public page.
        merged["styles"] = default_site_styles()
    return merged
