# 27 November 2026: apply the KLB Elimu content pack to saved public content.
# The pack values are frozen here so later edits to the live defaults cannot
# change the meaning of an already-applied migration. The exact pre-migration
# document is backed up, which makes reversal safe for administrator edits.

from copy import deepcopy

from django.db import migrations

BACKUP_KEY = "public_before_klb_elimu_content_pack"

PACK_SNAPSHOT = {'introduction': {'overline': 'A better-connected way to learn',
                  'title': 'A better-connected way to learn.',
                  'paragraphs': ['A school day is made up of hundreds of learning moments. '
                                 'A question asked in class. A new concept discovered in a '
                                 'textbook. An assignment completed after school. A '
                                 'teacher finding a better way to explain a difficult '
                                 'topic.',
                                 'KLB Elimu brings these moments closer together.',
                                 'It provides schools with a shared digital environment '
                                 'for organising learning, accessing educational '
                                 'resources, managing assessments and following learner '
                                 'progress.',
                                 "Whether you are a teacher preparing tomorrow's lesson, a "
                                 "learner revisiting today's topic or a parent following "
                                 "your child's progress, there is a place for you here."]},
 'capabilities': {'overline': 'What can you do with KLB Elimu?',
                  'title': 'Everything learning needs, brought closer.',
                  'cards': [{'key': 'school',
                             'title': 'Manage your school',
                             'copy': 'Give your school a central place to manage learners, '
                                     'teachers, classes, subjects and academic activities.',
                             'actionLabel': 'Explore School Management',
                             'actionHref': '/for-schools'},
                            {'key': 'teacher',
                             'title': 'Make lessons count',
                             'copy': 'Prepare lessons, share learning materials, create '
                                     "assignments and follow learners' progress from one "
                                     'teaching workspace.',
                             'actionLabel': 'Discover Teacher Tools',
                             'actionHref': '/for-teachers'},
                            {'key': 'learner',
                             'title': 'Learn beyond the classroom',
                             'copy': 'Access learning materials, digital books, practice '
                                     'activities and assessments in one convenient place.',
                             'actionLabel': 'Explore Learning',
                             'actionHref': '/for-learners'},
                            {'key': 'parent',
                             'title': 'Keep families connected',
                             'copy': 'Help parents follow attendance, assessment results, '
                                     'teacher feedback and important school announcements.',
                             'actionLabel': 'Explore Parent Access',
                             'actionHref': '/for-parents'}]},
 'libraryFeature': {'overline': 'The KLB Digital Library',
                    'title': 'A good book can take learning further.',
                    'paragraphs': ['The right learning resource can turn a difficult '
                                   'concept into a moment of understanding.',
                                   'The KLB Digital Library brings educational books and '
                                   'supplementary learning materials closer to teachers '
                                   'and learners. Explore available digital publications, '
                                   'revision resources, audio content and other approved '
                                   'educational materials.',
                                   'Find a resource, discover a new idea and make more of '
                                   'every learning opportunity.'],
                    'primaryLabel': 'Explore the Digital Library',
                    'primaryHref': '/library',
                    'secondaryLabel': 'Browse Learning Resources',
                    'secondaryHref': '/library#resources'},
 'audiences': {'teachers': {'overline': 'For teachers',
                            'title': 'Less time organising. More time teaching.',
                            'paragraphs': ["A teacher's work goes well beyond the lesson "
                                           'on the timetable. There are resources to '
                                           'prepare, assignments to mark, learners to '
                                           'guide and progress to follow.',
                                           'KLB Elimu gives teachers practical tools to '
                                           'organise their classes, prepare learning '
                                           'activities, share resources and keep '
                                           'assessment records together.',
                                           'Your attention belongs in the classroom. Your '
                                           'tools should make the work easier.'],
                            'actionLabel': 'Explore the Teacher Portal',
                            'actionHref': '/for-teachers'},
               'learners': {'overline': 'For learners',
                            'title': 'Your next discovery starts here.',
                            'paragraphs': ['Some lessons make sense immediately. Others '
                                           'need another explanation, a little practice or '
                                           'a different approach.',
                                           'With KLB Elimu, learners can revisit learning '
                                           'materials, complete activities, explore '
                                           'digital books and follow their own learning '
                                           'progress.',
                                           'There is always more to discover.'],
                            'actionLabel': 'Explore the Learner Portal',
                            'actionHref': '/for-learners'},
               'parents': {'overline': 'For parents',
                           'title': 'Be part of the learning journey.',
                           'paragraphs': ["A child's education is not only about the final "
                                          'examination result. It is also about '
                                          'attendance, effort, improvement, confidence and '
                                          'the small steps that happen along the way.',
                                          'KLB Elimu gives parents a convenient way to '
                                          'follow relevant school updates, review learning '
                                          'progress and stay connected with their '
                                          "children's education."],
                           'actionLabel': 'Explore Parent Access',
                           'actionHref': '/for-parents'}},
 'steps': {'overline': 'How it works',
           'title': 'Getting started is straightforward.',
           'steps': [{'title': 'Register your school',
                      'copy': 'Create a school account and provide the information needed '
                              'for verification and approval.'},
                     {'title': 'Set up your learning environment',
                      'copy': 'Configure your academic year, classes, subjects, teachers '
                              'and learners.'},
                     {'title': 'Bring learning resources together',
                      'copy': 'Add your own teaching materials and explore available KLB '
                              'digital publications.'},
                     {'title': 'Start teaching and learning',
                      'copy': 'Teachers publish lessons and activities. Learners access '
                              'materials, participate and complete assignments.'},
                     {'title': 'Follow the progress',
                      'copy': 'Review attendance, assessment feedback and learning reports '
                              'to understand how learners are progressing.'}]},
 'closingCta': {'overline': 'Begin with KLB Elimu',
                'title': 'Make room for more learning.',
                'copy': 'Whether you are preparing a school for its next academic term or '
                        'looking for better ways to support everyday learning, KLB Elimu '
                        'gives you a place to begin.',
                'primaryLabel': 'Register Your School',
                'primaryHref': '/contact?category=School%20registration',
                'secondaryLabel': 'Sign In to KLB Elimu',
                'secondaryHref': '/login'},
 'publicPages': {'about': {'pageTitle': 'About KLB Elimu',
                           'title': 'Learning deserves a thoughtful digital home.',
                           'introduction': ['KLB Elimu is a proposed digital learning '
                                            'ecosystem developed around the needs of '
                                            'Kenyan schools and the people who make '
                                            'learning possible.',
                                            'The platform brings together school '
                                            'administration, teaching and learning '
                                            'activities, assessments and digital '
                                            'educational resources.',
                                            'It is designed to give teachers practical '
                                            'tools, learners easier access to knowledge, '
                                            'parents a clearer view of learning progress '
                                            'and schools a more organised way to manage '
                                            'academic activities.'],
                           'brandMessage': ['A good lesson should not end when the bell '
                                            'rings.',
                                            'There is always another question to explore, '
                                            'another idea to understand and another '
                                            'opportunity to grow.',
                                            'KLB Elimu brings learning resources, '
                                            'classroom activities, assessments and '
                                            'educational publishing together in one place, '
                                            'giving teachers and learners more ways to '
                                            'make every learning moment count.'],
                           'approachTitle': 'Our approach',
                           'approach': [{'title': 'Learning first',
                                         'copy': 'Technology should support teaching and '
                                                 'learning, not become another obstacle '
                                                 'for teachers and learners.'},
                                        {'title': 'Knowledge should be accessible',
                                         'copy': 'Educational resources should be easy to '
                                                 'find and convenient to use, including in '
                                                 'environments where internet access is '
                                                 'limited.'},
                                        {'title': 'Every learner matters',
                                         'copy': 'The platform should support different '
                                                 'education levels, learning needs and '
                                                 'individual learning journeys.'},
                                        {'title': 'Better organisation, better insight',
                                         'copy': 'Good records help schools understand '
                                                 'attendance, participation, assessment '
                                                 'outcomes and areas where learners need '
                                                 'more support.'}],
                           'commitmentTitle': 'Our commitment',
                           'commitment': 'KLB Elimu is being designed with attention to '
                                         'educational value, responsible technology use, '
                                         'accessibility, data protection and the realities '
                                         'of schools across Kenya.'},
                 'schools': {'pageTitle': 'A digital home for your school.',
                             'title': 'A digital home for your school.',
                             'introduction': ['Running a school involves keeping many '
                                              'things moving at once. Learner records, '
                                              'teachers, classes, subjects, attendance, '
                                              'academic activities and school '
                                              'communication all need attention.',
                                              'KLB Elimu helps bring essential learning '
                                              'and school records into one organised '
                                              'environment.'],
                             'benefitsTitle': 'Benefits',
                             'benefits': [{'title': 'Organised learner records',
                                           'copy': 'Keep learner profiles, admission '
                                                   'details, class placements and academic '
                                                   'information accessible to authorised '
                                                   'school staff.'},
                                          {'title': 'Connected teaching teams',
                                           'copy': 'Assign teachers to classes and '
                                                   'learning areas, making '
                                                   'responsibilities easier to follow.'},
                                          {'title': 'Learning visibility',
                                           'copy': 'See which activities are taking place, '
                                                   'how learners are performing and where '
                                                   'additional support may be needed.'},
                                          {'title': 'Useful reporting',
                                           'copy': 'Generate attendance, assessment and '
                                                   'performance reports without having to '
                                                   'assemble every record manually.'},
                                          {'title': 'Learning resources',
                                           'copy': 'Connect classroom activities to '
                                                   'available digital textbooks and '
                                                   'supplementary KLB resources.'}],
                             'actionLabel': 'Register Your School',
                             'actionHref': '/contact?category=School%20registration'},
                 'teachers': {'pageTitle': 'Your teaching workspace.',
                              'title': 'Your teaching workspace.',
                              'introduction': ['Teaching takes preparation, patience and '
                                               'good judgement. KLB Elimu gives teachers a '
                                               'workspace for the practical work that '
                                               'supports a lesson, before, during and '
                                               'after the classroom session.'],
                              'featuresTitle': 'Features',
                              'features': ['Prepare and organise lessons.',
                                           'Access available learning resources.',
                                           'Create assignments and assessments.',
                                           'Review learner submissions.',
                                           'Record marks, feedback and assessment '
                                           'evidence.',
                                           'Track class participation and attendance.',
                                           'View individual and class progress.'],
                              'closing': 'Spend less time searching for scattered teaching '
                                         'materials and more time guiding learners towards '
                                         'understanding.',
                              'actionLabel': 'Access Teacher Portal',
                              'actionHref': '/login?role=TEACHER'},
                 'learners': {'pageTitle': 'Your learning journey, in one place.',
                              'title': 'Your learning journey, in one place.',
                              'introduction': ['A lesson is the beginning, not the end.',
                                               'KLB Elimu gives learners a place to find '
                                               'learning materials, revisit difficult '
                                               'topics, complete assignments, take '
                                               'assessments and follow their progress.'],
                              'featuresTitle': 'What learners can do',
                              'features': ['Find lessons and subjects.',
                                           'Read available digital textbooks.',
                                           'Access permitted learning materials.',
                                           'Watch or listen to educational resources.',
                                           'Submit assignments.',
                                           'Complete practice activities.',
                                           'Take assigned assessments.',
                                           'Review results and teacher feedback.'],
                              'closing': 'Ask questions. Practise what you learn. Return '
                                         'to the topics that challenge you. Every step '
                                         'forward counts.',
                              'actionLabel': 'Access Learner Portal',
                              'actionHref': '/login?role=LEARNER'},
                 'parents': {'pageTitle': 'A closer connection to school.',
                             'title': 'A closer connection to school.',
                             'introduction': ["Being involved in a child's education "
                                              'begins with knowing how things are going.',
                                              'KLB Elimu gives parents an authorised view '
                                              "of their children's learning activities, "
                                              'attendance, assessment feedback and school '
                                              'announcements.'],
                             'featuresTitle': 'Parent features',
                             'features': ['View linked learner profiles.',
                                          'Follow attendance records.',
                                          'Review available assessment results.',
                                          'Read teacher feedback.',
                                          'Receive school announcements.',
                                          'View relevant progress reports.'],
                             'closing': 'The most helpful conversation about school often '
                                        'begins with knowing what happened there today.',
                             'actionLabel': 'Access Parent Portal',
                             'actionHref': '/login?role=GUARDIAN'},
                 'library': {'pageTitle': 'The KLB Digital Library',
                             'title': 'Find the next resource that makes a difference.',
                             'introduction': ['Explore a growing collection of available '
                                              'educational publications and learning '
                                              'resources from KLB and other approved '
                                              'content providers.',
                                              'Browse by education level, grade, subject, '
                                              'language and resource type to find material '
                                              'relevant to your learning needs.'],
                             'categoriesTitle': 'Library categories',
                             'categories': ['Textbooks',
                                            'Revision materials',
                                            'Supplementary readers',
                                            'Teacher resources',
                                            'Audio learning',
                                            'Video learning',
                                            'Practice activities',
                                            'Assessment resources'],
                             'searchPlaceholder': 'Search by book title, subject, grade or '
                                                  'keyword...',
                             'filters': ['Education level',
                                         'Grade',
                                         'Subject',
                                         'Language',
                                         'Content type',
                                         'Publisher',
                                         'Access availability'],
                             'accessLabels': ['Included in your subscription',
                                              'Available for purchase',
                                              'School licensed',
                                              'Teacher access',
                                              'Preview available',
                                              'Not currently available'],
                             'pricingNote': 'Do not display a purchase price until a '
                                            'resource has an approved price and currency.'},
                 'contact': {'pageTitle': "Let's talk about learning.",
                             'title': "Let's talk about learning.",
                             'introduction': ['Have a question about KLB Elimu, '
                                              'registering your school or accessing '
                                              'learning resources? Send us a message and '
                                              'tell us how we can help.'],
                             'fields': ['Full name',
                                        'Email address',
                                        'Phone number',
                                        'Organisation or school',
                                        'Enquiry category',
                                        'Subject',
                                        'Message'],
                             'categories': ['School registration',
                                            'Account access',
                                            'Digital library',
                                            'Teacher support',
                                            'Subscription enquiries',
                                            'Technical assistance',
                                            'Partnership enquiries',
                                            'General enquiries'],
                             'actionLabel': 'Send Enquiry',
                             'confirmation': 'Thank you for getting in touch. Your enquiry '
                                             'has been received. Keep your reference '
                                             'number for any follow-up communication.',
                             'note': 'Do not promise a response time until KLB has '
                                     'approved a service-level commitment.'},
                 'help': {'pageTitle': 'A little help goes a long way.',
                          'title': 'A little help goes a long way.',
                          'introduction': ['Find practical guidance for using KLB Elimu. '
                                           'Whether you are setting up a school, preparing '
                                           'lessons, accessing a digital book or managing '
                                           'an account, start here.'],
                          'searchPlaceholder': 'What would you like help with?',
                          'noResults': 'No help articles match that search. Try another '
                                       'phrase or contact support.',
                          'suggestedSearches': ['I cannot sign in.',
                                                'How do I register my school?',
                                                'How do I add learners?',
                                                'Where can I find digital books?',
                                                'How do I submit an assignment?'],
                          'categories': [{'title': 'Getting Started',
                                          'items': ['How to access KLB Elimu.',
                                                    'How to register a school.',
                                                    'How to activate an account.',
                                                    'How to reset a password.',
                                                    'How to navigate your dashboard.']},
                                         {'title': 'School Administration',
                                          'items': ['How to register learners.',
                                                    'How to generate admission numbers.',
                                                    'How to create classes and streams.',
                                                    'How to register teachers.',
                                                    'How to assign teachers.',
                                                    'How to link parents to learners.',
                                                    'How to manage attendance.']},
                                         {'title': 'Teaching and Learning',
                                          'items': ['How to create a lesson.',
                                                    'How to access digital resources.',
                                                    'How to create assignments.',
                                                    'How to prepare an assessment.',
                                                    'How to mark learner submissions.',
                                                    'How to view progress reports.']},
                                         {'title': 'Digital Library',
                                          'items': ['How to search for a book.',
                                                    'How to preview a resource.',
                                                    'How to access licensed content.',
                                                    'How to access permitted resources.',
                                                    'How to use the digital reader.']},
                                         {'title': 'Parents and Learners',
                                          'items': ['How to access learning materials.',
                                                    'How to submit an assignment.',
                                                    'How to review teacher feedback.',
                                                    'How to link a parent account.',
                                                    'How to follow learning progress.']},
                                         {'title': 'Account and Security',
                                          'items': ['How to change a password.',
                                                    'How to manage account information.',
                                                    'How to protect an account.',
                                                    'How to report suspicious activity.']}],
                          'supportTitle': 'Still need a hand?',
                          'supportCopy': 'Some questions need a little more attention. '
                                         'Send the support team a request and include as '
                                         'much relevant detail as possible.',
                          'actionLabel': 'Contact Support',
                          'actionHref': '/contact?category=Technical%20assistance'},
                 'faq': {'pageTitle': 'Frequently Asked Questions',
                         'title': 'Frequently Asked Questions',
                         'introduction': ['Short answers about accounts, access and the '
                                          'way information is shared across the platform.'],
                         'groups': [{'title': 'General',
                                     'items': [{'question': 'What is KLB Elimu?',
                                                'answer': 'KLB Elimu is a proposed digital '
                                                          'learning ecosystem that brings '
                                                          'together school management, '
                                                          'teaching and learning '
                                                          'activities, assessments and '
                                                          'digital educational resources.'},
                                               {'question': 'Who can use KLB Elimu?',
                                                'answer': 'The initial platform is '
                                                          'intended for schools, teachers, '
                                                          'learners, parents and '
                                                          'authorised KLB administrators.'},
                                               {'question': 'Can any school register?',
                                                'answer': 'Schools can submit registration '
                                                          'applications. Access should be '
                                                          'activated after the applicable '
                                                          'verification and approval '
                                                          'process.'},
                                               {'question': 'Can I use KLB Elimu on a '
                                                            'phone?',
                                                'answer': 'The platform is designed to '
                                                          'work on computers, tablets and '
                                                          'smartphones through a '
                                                          'responsive interface.'}]},
                                    {'title': 'Schools',
                                     'items': [{'question': 'Can my school register '
                                                            'multiple classes?',
                                                'answer': 'Yes. An authorised school '
                                                          'administrator can create and '
                                                          'manage the classes and streams '
                                                          "supported by the school's "
                                                          'approved account '
                                                          'configuration.'},
                                               {'question': 'Can I upload learner details '
                                                            'in bulk?',
                                                'answer': 'The system should provide an '
                                                          'approved spreadsheet template '
                                                          'to help schools import learner '
                                                          'records.'},
                                               {'question': 'Can a school have multiple '
                                                            'administrators?',
                                                'answer': 'Yes. A school can assign '
                                                          'appropriate administrative '
                                                          'roles to authorised staff, with '
                                                          'permissions managed '
                                                          'separately.'}]},
                                    {'title': 'Teachers',
                                     'items': [{'question': 'Can teachers upload their own '
                                                            'learning materials?',
                                                'answer': 'Teachers should be able to '
                                                          'upload permitted teaching '
                                                          'materials to their assigned '
                                                          'classes, subject to file '
                                                          'restrictions and school '
                                                          'permissions.'},
                                               {'question': 'Can I reuse an assignment?',
                                                'answer': 'Teachers should be able to '
                                                          'duplicate their own reusable '
                                                          'activities and assessments '
                                                          'where permitted.'},
                                               {'question': 'Can learners submit '
                                                            'assignments online?',
                                                'answer': 'Yes. The platform should '
                                                          'support the submission formats '
                                                          'enabled for each assignment.'}]},
                                    {'title': 'Learners',
                                     'items': [{'question': 'Can I read books online?',
                                                'answer': 'You can access the digital '
                                                          'books and learning materials '
                                                          'available to your account.'},
                                               {'question': 'Can I study without internet '
                                                            'access?',
                                                'answer': 'Offline downloads and '
                                                          'synchronisation are not part of '
                                                          'this application. Resources are '
                                                          'available through the web '
                                                          'interface where your account '
                                                          'has access.'},
                                               {'question': 'Can I see my assessment '
                                                            'results?',
                                                'answer': 'You can view the results and '
                                                          'feedback that your teacher or '
                                                          'school has made available.'}]},
                                    {'title': 'Parents',
                                     'items': [{'question': 'Can I link more than one '
                                                            'child to my account?',
                                                'answer': 'The platform should support '
                                                          'verified parent accounts linked '
                                                          'to multiple learner records.'},
                                               {'question': "Can I view my child's marks?",
                                                'answer': 'You can view assessment '
                                                          'information and reports made '
                                                          'available to parents by the '
                                                          'school.'},
                                               {'question': "Can I change my child's "
                                                            'admission details?',
                                                'answer': 'Protected school records should '
                                                          'be updated by authorised school '
                                                          'administrators. Contact the '
                                                          'school if you notice incorrect '
                                                          'information.'}]},
                                    {'title': 'Digital content',
                                     'items': [{'question': 'Are all digital books free?',
                                                'answer': 'Not necessarily. Access depends '
                                                          "on the resource's licensing and "
                                                          'subscription conditions. Each '
                                                          'book should clearly indicate '
                                                          'its access requirements.'},
                                               {'question': 'Can I access every book?',
                                                'answer': 'Access depends on the relevant '
                                                          'publishing and licensing '
                                                          'conditions. Each book should '
                                                          'clearly indicate its access '
                                                          'requirements.'},
                                               {'question': 'Can I share my account with '
                                                            'someone else?',
                                                'answer': 'Accounts should only be used by '
                                                          'the authorised user. Sharing '
                                                          'account credentials can '
                                                          'compromise personal information '
                                                          'and access rights.'}]}]},
                 'accessibility': {'pageTitle': 'Make Learning Work for You',
                                   'title': 'Make Learning Work for You',
                                   'introduction': ['People learn and interact with '
                                                    'digital content in different ways. '
                                                    'KLB Elimu should provide practical '
                                                    'accessibility options that help users '
                                                    'navigate the platform comfortably.'],
                                   'settingsTitle': 'Accessibility settings',
                                   'settings': ['Text size',
                                                'High contrast',
                                                'Reduced motion',
                                                'Improved text spacing',
                                                'Keyboard navigation',
                                                'Screen-reader compatibility',
                                                'Captions, where available',
                                                'Audio learning, where available'],
                                   'message': 'Choose the display settings that make the '
                                              'platform easier for you to use. Your '
                                              'preferences should be saved to your account '
                                              'where supported.',
                                   'specialSupportTitle': 'Special support',
                                   'specialSupport': 'Where a learner requires additional '
                                                     'support, schools should be able to '
                                                     'make appropriate arrangements '
                                                     'without unnecessarily exposing '
                                                     'sensitive personal information.'},
                 'terms': {'pageTitle': 'Terms of Use',
                           'title': 'Terms of Use',
                           'introduction': ['These terms set out the expected way to use '
                                            'KLB Elimu while the proposed initiative is '
                                            'being reviewed.'],
                           'usageTitle': 'Using the platform',
                           'usage': ['Use an account only if it was issued to you.',
                                     'Keep account credentials private.',
                                     'Follow the access rules set by your school.',
                                     'Use educational resources in line with their '
                                     'permissions.',
                                     'Report suspicious activity to the appropriate '
                                     'administrator.'],
                           'availabilityTitle': 'Availability',
                           'availability': 'The platform is designed for use on computers, '
                                           'tablets and smartphones. Some services may be '
                                           'temporarily unavailable during maintenance.',
                           'note': 'The final Terms of Use must be reviewed and approved '
                                   "by KLB's legal team before publication."},
                 'acceptableUse': {'pageTitle': 'Acceptable Use Policy',
                                   'title': 'Acceptable Use Policy',
                                   'introduction': ['KLB Elimu is a learning environment. '
                                                    'Everyone who uses it should help keep '
                                                    'that environment safe and '
                                                    'respectful.'],
                                   'rulesTitle': 'Expected conduct',
                                   'rules': ['Protect your account credentials.',
                                             'Respect other users.',
                                             'Use educational resources only in accordance '
                                             'with your access rights.',
                                             'Do not upload inappropriate or unauthorised '
                                             'content.',
                                             'Do not attempt to access records outside '
                                             'your role.',
                                             'Report suspicious activity.',
                                             'Follow school and platform rules.'],
                                   'note': 'The final Acceptable Use Policy must be '
                                           "reviewed and approved by KLB's legal and data "
                                           'protection teams before publication.'},
                 'privacy': {'pageTitle': 'Your information deserves care.',
                             'title': 'Your information deserves care.',
                             'introduction': ['KLB Elimu is intended to support learning '
                                              'while respecting the privacy and security '
                                              'of the people who use it.',
                                              'Information should only be collected for '
                                              'legitimate purposes, made available to '
                                              'authorised users and handled according to '
                                              'applicable data protection requirements.',
                                              'Parents, teachers, learners and school '
                                              'administrators should understand what '
                                              'information is collected and how it is '
                                              'used.'],
                             'acceptableUseTitle': 'Acceptable use',
                             'acceptableUse': ['Protect their account credentials.',
                                               'Respect other users.',
                                               'Use educational resources in accordance '
                                               'with their access rights.',
                                               'Avoid uploading inappropriate or '
                                               'unauthorised content.',
                                               'Report suspicious activity.',
                                               'Follow school and platform rules.'],
                             'principlesTitle': 'Important privacy principles',
                             'principles': ['Collect only necessary information.',
                                            'Apply role-based access.',
                                            "Restrict access to children's records.",
                                            'Provide appropriate parent or guardian '
                                            'safeguards.',
                                            'Maintain audit records.',
                                            'Protect data during storage and transmission.',
                                            'Support appropriate retention and deletion '
                                            'processes.'],
                             'note': "The final Privacy Notice, Terms of Use, Children's "
                                     'Data Policy and other legal documents must be '
                                     "reviewed and approved by KLB's legal and data "
                                     'protection teams before publication.'}},
 'messages': {'pageIntroductions': {'overview': 'Here is a summary of the activities and '
                                                'information available to your account.',
                                    'records': 'View, manage and update the information '
                                               'associated with this section.',
                                    'reports': 'Explore the available records and reports '
                                               'to understand activity and progress.',
                                    'settings': 'Manage the preferences and account '
                                                'details available to your role.',
                                    'notifications': 'Keep track of important updates and '
                                                     'messages relevant to your account.'},
              'searchPlaceholders': {'schools': 'Search schools by name or registration '
                                                'number...',
                                     'learners': 'Search learners by name or admission '
                                                 'number...',
                                     'teachers': 'Search teachers by name or staff '
                                                 'number...',
                                     'resources': 'Search resources by title, subject or '
                                                  'grade...',
                                     'lessons': 'Search lessons by topic or learning '
                                                'area...',
                                     'announcements': 'Search announcements...',
                                     'transactions': 'Search transactions by reference '
                                                     'number...'},
              'globalActions': ['Add New',
                                'Create Record',
                                'Edit Details',
                                'View Details',
                                'Save Changes',
                                'Save as Draft',
                                'Publish',
                                'Submit',
                                'Approve',
                                'Reject',
                                'Download',
                                'Export',
                                'Print',
                                'Archive',
                                'Restore',
                                'Cancel',
                                'Close'],
              'loading': ['Preparing your dashboard...',
                          'Retrieving school records...',
                          'Opening your learning resources...',
                          'Saving your changes...',
                          'Submitting your assignment...',
                          'Preparing your report...',
                          'Checking your account...',
                          'Preparing a lighter view of your work...'],
              'success': {'recordSaved': 'Your changes have been saved successfully.',
                          'schoolCreated': 'The school record has been created. You can '
                                           'now continue with the verification process.',
                          'learnerAdded': 'The learner has been added to the school '
                                          'register.',
                          'teacherInvited': 'The invitation has been sent successfully.',
                          'lessonPublished': 'Your lesson is now available to the selected '
                                             'class.',
                          'assignmentCreated': 'Your assignment has been created and is '
                                               'available according to its publication '
                                               'settings.',
                          'resourceUploaded': 'Your resource has been uploaded. It will '
                                              'remain in draft or review status until it '
                                              'is approved for publication.',
                          'reportGenerated': 'Your report is ready. You can now view or '
                                             'download it.'},
              'errors': {'invalidLogin': 'We could not verify those sign-in details. Check '
                                         'your username and password and try again.',
                         'accountLocked': 'Your account has been temporarily locked '
                                          'following repeated unsuccessful sign-in '
                                          'attempts. Follow the account recovery '
                                          'instructions or contact your administrator.',
                         'sessionExpired': 'Your session has ended. Sign in again to '
                                           'continue.',
                         'noPermission': 'Your account does not have permission to perform '
                                         'this action.',
                         'duplicateAdmission': 'This admission number is already assigned '
                                               'to another learner. Review the number '
                                               'before continuing.',
                         'requiredMissing': 'Some required fields have not been completed. '
                                            'Review the highlighted fields and try again.',
                         'fileTooLarge': 'This file exceeds the permitted upload size. '
                                         'Choose a smaller file or an approved alternative '
                                         'format.',
                         'unsupportedFile': 'This file type is not supported. Check the '
                                            'permitted formats and upload the resource '
                                            'again.',
                         'connectionInterrupted': 'We lost the connection while processing '
                                                  'your request. Check your internet '
                                                  'connection before trying again.',
                         'submissionFailed': 'Your submission could not be completed. '
                                             'Check its status before submitting again.',
                         'somethingWrong': 'We could not complete that action. Try again, '
                                           'or contact support if the problem continues. '
                                           'Include the reference number shown on this '
                                           'page.'},
              'confirmations': {'deleteRecord': 'Are you sure you want to delete this '
                                                'record? This action may affect related '
                                                'information. Check the details before '
                                                'proceeding.',
                                'suspendSchool': 'Suspending this school will restrict '
                                                 "access according to the platform's "
                                                 'suspension policy. Existing academic '
                                                 'records should remain protected.',
                                'publishContent': 'You are about to make this resource '
                                                  'available to the selected audience. '
                                                  'Confirm that its description, content '
                                                  'and access rights have been reviewed.',
                                'restoreBackup': 'Restoring this backup may replace '
                                                 'current platform information. Confirm '
                                                 'the backup scope and follow the recovery '
                                                 'procedure before proceeding.'},
              'emptyStates': {'schools': {'title': 'No schools registered yet',
                                          'message': 'Schools will appear here once their '
                                                     'registration details have been '
                                                     'submitted.'},
                              'learners': {'title': 'Your learner register is empty',
                                           'message': 'Add your first learner or import an '
                                                      'existing register to get started.'},
                              'teachers': {'title': 'Your teaching team is waiting',
                                           'message': 'Invite teachers and assign them to '
                                                      'their relevant classes.'},
                              'classes': {'title': 'No classes have been created',
                                          'message': 'Set up your classes and streams to '
                                                     'begin organising learners.'},
                              'lessons': {'title': 'No lessons yet',
                                          'message': "Your teachers' published lessons "
                                                     'will appear here.'},
                              'assignments': {'title': 'Nothing to submit right now',
                                              'message': 'New assignments will appear here '
                                                         'when your teachers publish '
                                                         'them.'},
                              'assessments': {'title': 'No assessments available',
                                              'message': 'Check again when your teacher '
                                                         'assigns an assessment.'},
                              'resources': {'title': 'No resources found',
                                            'message': 'Try changing your search or '
                                                       'exploring another category.'},
                              'reports': {'title': 'No reports available yet',
                                          'message': 'Reports will appear when sufficient '
                                                     'records have been created.'},
                              'messages': {'title': 'Your inbox is clear',
                                           'message': 'New school and learning messages '
                                                      'will appear here.'},
                              'notifications': {'title': "You're all caught up",
                                                'message': 'Important updates will appear '
                                                           'here when they arrive.'}},
              'firstTime': {'schoolRegistration': 'Your school is not just creating an '
                                                  'account. It is preparing a learning '
                                                  'environment. Begin by confirming the '
                                                  'official school details.',
                            'learnerRegistration': 'Start building your learner register. '
                                                   'You can add learners individually or '
                                                   'import multiple records using the '
                                                   'approved template.',
                            'teacherRegistration': 'Invite the teachers who will prepare '
                                                   'lessons, manage learning activities '
                                                   'and guide your learners.',
                            'digitalLibrary': 'Your library is ready to receive learning '
                                              'resources. Start by exploring the resources '
                                              'already available to your account.'},
              'notifications': {'schoolApproved': 'Your school registration has been '
                                                  'approved. You can now sign in and begin '
                                                  "setting up your school's learning "
                                                  'environment.',
                                'teacherCreated': 'A new teacher account has been created '
                                                  'for your school. The teacher can '
                                                  'complete the account activation process '
                                                  'using the invitation sent to their '
                                                  'registered contact.',
                                'learnerRegistered': 'A new learner has been added to your '
                                                     "school records. Review the learner's "
                                                     'profile to confirm that the class '
                                                     'placement and contact details are '
                                                     'correct.',
                                'incompleteSetup': "Your school's initial setup is not yet "
                                                   'complete. Review the outstanding items '
                                                   'to prepare the learning environment '
                                                   'for teachers and learners.',
                                'subscriptionReminder': "Your school's package is "
                                                        'approaching its review date. '
                                                        'Review the current configuration '
                                                        'with your administrator.',
                                'newClass': 'You have been assigned to [Class Name]. Open '
                                            'your class dashboard to review the learners '
                                            'and assigned learning areas.',
                                'newLearner': 'A new learner has joined [Class Name]. '
                                              'Review the updated class register.',
                                'submissionReceived': '[Learner Name] has submitted the '
                                                      'assignment "[Assignment Title]". It '
                                                      'is now available for review.',
                                'deadlineApproaching': 'The submission deadline for '
                                                       '"[Assignment Title]" is '
                                                       'approaching. Review the '
                                                       'outstanding submissions from your '
                                                       'class.',
                                'resourcePublished': 'A new learning resource relevant to '
                                                     'your teaching area is available in '
                                                     'the digital library.',
                                'markingReminder': 'There are submitted assessments '
                                                   'awaiting your review. Visit your '
                                                   'assessment workspace to continue '
                                                   'marking.',
                                'newLesson': 'Your teacher has added a new lesson to '
                                             '[Learning Area]. Open it and see what you '
                                             'will explore next.',
                                'newAssignment': 'There is a new assignment waiting for '
                                                 'you in [Subject]. Read the instructions '
                                                 'and check the submission date.',
                                'assignmentReminder': 'Remember to complete "[Assignment '
                                                      'Title]" before its due date.',
                                'feedbackAvailable': 'Your teacher has reviewed your work. '
                                                     'Open the assignment to see the '
                                                     'feedback and suggestions.',
                                'newAssessment': 'A new assessment has been assigned to '
                                                 'you. Read the instructions and check '
                                                 'when it is available.',
                                'lessonCompleted': 'You have completed "[Lesson Title]". '
                                                   'Take a moment to review what you have '
                                                   'learned before moving on.',
                                'schoolAnnouncement': "Your child's school has shared a "
                                                      'new announcement. Sign in to read '
                                                      'the details.',
                                'assessmentResult': 'A new assessment result for [Learner '
                                                    'Name] is available for your review.',
                                'attendanceUpdate': 'A new attendance record has been made '
                                                    'available by the school for [Learner '
                                                    'Name].',
                                'parentFeedback': 'New teacher feedback has been shared '
                                                  'for [Learner Name]. Sign in to view the '
                                                  'available information.',
                                'academicReport': 'A new academic report for [Learner '
                                                  'Name] is available.',
                                'maintenance': 'KLB Elimu will undergo scheduled '
                                               'maintenance on [Date] between [Start Time] '
                                               'and [End Time]. Some services may be '
                                               'temporarily unavailable during this '
                                               'period.',
                                'newFeature': 'We have introduced an improvement to KLB '
                                              'Elimu. Visit the platform to explore the '
                                              'updated feature.',
                                'securityNotice': 'A security-related change has been made '
                                                  'to your account. Review your account '
                                                  'activity and contact support if you do '
                                                  'not recognise the activity.'}}}

NEW_FIELDS = {'header.primaryCtaLabel': 'Get Your School Started',
 'header.primaryCtaHref': '/contact?category=School%20registration',
 'hero.supportingStatement': 'Built around learning. Designed for Kenyan schools.',
 'footer.infoTitle': 'Information',
 'footer.infoLinks': [{'label': 'Privacy Notice', 'href': '/privacy'},
                      {'label': 'Terms of Use', 'href': '/terms'},
                      {'label': 'Acceptable Use Policy', 'href': '/acceptable-use'},
                      {'label': 'Accessibility Statement',
                       'href': '/accessibility-statement'}],
 'footer.supportTitle': 'Contact',
 'footer.supportLinks': [{'label': 'Contact KLB', 'href': '/contact'},
                         {'label': 'School Registration Support',
                          'href': '/contact?category=School%20registration'},
                         {'label': 'Technical Support',
                          'href': '/contact?category=Technical%20assistance'}],
 'footer.closingLine': 'Every lesson opens a door.',
 'footer.disclaimer': 'A proposed digital learning initiative associated with Kenya '
                      'Literature Bureau PLC, subject to organisational approval.',
 'publicPages.terms': {'pageTitle': 'Terms of Use',
                       'title': 'Terms of Use',
                       'introduction': ['These terms set out the expected way to use KLB '
                                        'Elimu while the proposed initiative is being '
                                        'reviewed.'],
                       'usageTitle': 'Using the platform',
                       'usage': ['Use an account only if it was issued to you.',
                                 'Keep account credentials private.',
                                 'Follow the access rules set by your school.',
                                 'Use educational resources in line with their '
                                 'permissions.',
                                 'Report suspicious activity to the appropriate '
                                 'administrator.'],
                       'availabilityTitle': 'Availability',
                       'availability': 'The platform is designed for use on computers, '
                                       'tablets and smartphones. Some services may be '
                                       'temporarily unavailable during maintenance.',
                       'note': 'The final Terms of Use must be reviewed and approved by '
                               "KLB's legal team before publication."},
 'publicPages.acceptableUse': {'pageTitle': 'Acceptable Use Policy',
                               'title': 'Acceptable Use Policy',
                               'introduction': ['KLB Elimu is a learning environment. '
                                                'Everyone who uses it should help keep '
                                                'that environment safe and respectful.'],
                               'rulesTitle': 'Expected conduct',
                               'rules': ['Protect your account credentials.',
                                         'Respect other users.',
                                         'Use educational resources only in accordance '
                                         'with your access rights.',
                                         'Do not upload inappropriate or unauthorised '
                                         'content.',
                                         'Do not attempt to access records outside your '
                                         'role.',
                                         'Report suspicious activity.',
                                         'Follow school and platform rules.'],
                               'note': 'The final Acceptable Use Policy must be reviewed '
                                       "and approved by KLB's legal and data protection "
                                       'teams before publication.'},
 'publicPages.help.noResults': 'No help articles match that search. Try another phrase or '
                               'contact support.'}

PATH_REPLACEMENTS = {'header.links': [{'label': 'Home', 'href': '/'},
                  {'label': 'For Schools', 'href': '/for-schools'},
                  {'label': 'For Teachers', 'href': '/for-teachers'},
                  {'label': 'For Learners', 'href': '/for-learners'},
                  {'label': 'Digital Library', 'href': '/library'},
                  {'label': 'About KLB Elimu', 'href': '/about'},
                  {'label': 'Help Centre', 'href': '/help'}],
 'header.signInLabel': 'Sign In',
 'footer.exploreLinks': [{'label': 'About KLB Elimu', 'href': '/about'},
                         {'label': 'For Schools', 'href': '/for-schools'},
                         {'label': 'For Teachers', 'href': '/for-teachers'},
                         {'label': 'For Learners', 'href': '/for-learners'},
                         {'label': 'For Parents', 'href': '/for-parents'}],
 'footer.learnLinks': [{'label': 'Digital Library', 'href': '/library'},
                       {'label': 'Learning Resources', 'href': '/library#resources'},
                       {'label': 'Help Centre', 'href': '/help'},
                       {'label': 'Frequently Asked Questions', 'href': '/faq'}],
 'hero.title': 'Give every lesson somewhere to go.',
 'hero.description': 'Learning does not stop at the classroom door. KLB Elimu brings '
                     'teachers, learners, schools and educational resources together in '
                     'one place, making it easier to teach, discover, practise and grow.',
 'hero.primaryLabel': 'Explore KLB Elimu',
 'hero.primaryHref': '/#introduction',
 'hero.secondaryLabel': 'School Registration',
 'hero.secondaryHref': '/contact?category=School%20registration',
 'announcement': {'text': 'The KLB Digital Library brings selected educational '
                          'publications and supplementary resources into your learning '
                          'environment.',
                  'actionLabel': 'Explore the Library',
                  'actionHref': '/library'},
 'quickLinks': {'title': 'On this page',
                'links': [{'label': 'Introduction', 'href': '/#introduction'},
                          {'label': 'What you can do', 'href': '/#capabilities'},
                          {'label': 'Digital Library', 'href': '/#library'},
                          {'label': 'Teachers', 'href': '/#teachers'},
                          {'label': 'Learners', 'href': '/#learners'},
                          {'label': 'Parents', 'href': '/#parents'},
                          {'label': 'How it works', 'href': '/#how-it-works'},
                          {'label': 'Questions', 'href': '/#faq'}]},
 'auth.login.storyCopy': 'Your classroom, learning resources and school activities are '
                         'just a sign-in away.',
 'auth.login.publicIntro': 'New to KLB Elimu? Your school administrator can help you get '
                           'access to the platform.'}

BRAND_VALUES = {'header.brand.mark': 'KLB',
 'header.brand.name': 'Elimu',
 'header.brand.subtitle': 'Every lesson opens a door.',
 'footer.name': 'KLB Elimu',
 'hero.overline': 'KLB Elimu',
 'app.adminBrand': 'KLB Elimu',
 'app.portalBrand': 'KLB Elimu'}

OLD_BRAND_VALUES = {
    "header.brand.mark": ("KLB", "KLB Elimu", "KLB LMS"),
    "header.brand.name": (
        "Digital Learning Ecosystem", "KLB Learning", "KLB LMS", "KLB Elimu",
    ),
    "header.brand.subtitle": (
        "Kenya Literature Bureau", "Digital Education",
        "Kenya Literature Bureau, Digital Education",
    ),
    "footer.name": ("KLB Digital Learning Ecosystem", "KLB Learning", "KLB LMS"),
    "hero.overline": ("KLB Digital Learning Ecosystem", "KLB Learning", "KLB LMS"),
    "app.adminBrand": ("KLB Digital Learning Ecosystem", "KLB Learning", "KLB LMS"),
    "app.portalBrand": ("KLB Digital Learning Ecosystem", "KLB Learning", "KLB LMS"),
}

OLD_PATH_VALUES = {
    "header.links": [
        {"label": "Platform", "href": "/#workspaces"},
        {"label": "How it works", "href": "/#journey"},
        {"label": "Library", "href": "/library"},
        {"label": "Who it's for", "href": "/#roles"},
        {"label": "FAQ", "href": "/#faq"},
    ],
    "header.signInLabel": "Sign in",
    "footer.exploreLinks": [
        {"label": "Platform", "href": "/#workspaces"},
        {"label": "How it works", "href": "/#journey"},
        {"label": "Public library", "href": "/library"},
    ],
    "footer.learnLinks": [
        {"label": "Role guide", "href": "/#roles"},
        {"label": "Who sees what", "href": "/#access"},
        {"label": "Common questions", "href": "/#faq"},
        {"label": "Progress insight", "href": "/#insights"},
    ],
    "hero.title": "Teaching and learning, connected for Kenyan schools.",
    "hero.description": (
        "Courses, school records and digital textbooks now live in one calm "
        "workspace, designed for competency based learning and modest connections."
    ),
    "hero.primaryLabel": "Create an account",
    "hero.primaryHref": "/register",
    "hero.secondaryLabel": "Browse the library",
    "hero.secondaryHref": "/library",
    "announcement": {
        "text": "New this term: role previews make it easier to find your workspace.",
        "actionLabel": "See how it works",
        "actionHref": "/#journey",
    },
    "quickLinks": {
        "title": "On this page",
        "links": [
            {"label": "Workspaces", "href": "/#workspaces"},
            {"label": "Getting started", "href": "/#journey"},
            {"label": "Progress", "href": "/#insights"},
            {"label": "Library", "href": "/#spotlight"},
            {"label": "Roles", "href": "/#roles"},
            {"label": "Questions", "href": "/#faq"},
        ],
    },
    "auth.login.storyCopy": (
        "Built for Kenyan schools with competency based learning, school "
        "administration and a digital publishing library. It works well on "
        "modest connections."
    ),
    "auth.login.publicIntro": (
        "Use the account your school administrator created, or register below."
    ),
}


def _get(content, path):
    current = content
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _set(content, path, value):
    parts = path.split(".")
    current = content
    for part in parts[:-1]:
        if not isinstance(current, dict):
            return False
        current = current.setdefault(part, {})
    if not isinstance(current, dict):
        return False
    current[parts[-1]] = deepcopy(value)
    return True


def _delete(content, path):
    parts = path.split(".")
    current = content
    for part in parts[:-1]:
        if not isinstance(current, dict):
            return False
        current = current.get(part)
    if isinstance(current, dict) and parts[-1] in current:
        del current[parts[-1]]
        return True
    return False


def apply_content_pack(apps, schema_editor):
    SiteContent = apps.get_model("theming", "SiteContent")
    for record in SiteContent.objects.filter(key="public"):
        original = deepcopy(record.content or {})
        # One immutable backup lets reversal restore exactly what was replaced.
        SiteContent.objects.get_or_create(
            key=BACKUP_KEY, defaults={"content": original},
        )
        content = deepcopy(original)
        changed = False

        for path, value in BRAND_VALUES.items():
            if _get(content, path) in OLD_BRAND_VALUES[path]:
                changed = _set(content, path, value) or changed
        for path, old_value in OLD_PATH_VALUES.items():
            if _get(content, path) == old_value:
                changed = _set(content, path, PATH_REPLACEMENTS[path]) or changed
        for section, value in PACK_SNAPSHOT.items():
            if _get(content, section) is None:
                changed = _set(content, section, value) or changed
        for path, value in NEW_FIELDS.items():
            if _get(content, path) is None:
                changed = _set(content, path, value) or changed

        if changed:
            record.content = content
            record.save(update_fields=["content", "updated_at"])


def revert_content_pack(apps, schema_editor):
    SiteContent = apps.get_model("theming", "SiteContent")
    backup = SiteContent.objects.filter(key=BACKUP_KEY).first()
    for record in SiteContent.objects.filter(key="public"):
        if backup is not None:
            record.content = deepcopy(backup.content or {})
        else:
            # Safety net for databases where the backup record was removed.
            content = deepcopy(record.content or {})
            for section in PACK_SNAPSHOT:
                if _get(content, section) == PACK_SNAPSHOT[section]:
                    _delete(content, section)
            for path, value in NEW_FIELDS.items():
                if _get(content, path) == value:
                    _delete(content, path)
            for path, old_value in OLD_PATH_VALUES.items():
                if _get(content, path) == PATH_REPLACEMENTS[path]:
                    _set(content, path, old_value)
            record.content = content
        record.save(update_fields=["content", "updated_at"])
    if backup is not None:
        backup.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("theming", "0008_add_public_homepage_extras"),
    ]

    operations = [
        migrations.RunPython(apply_content_pack, revert_content_pack),
    ]
