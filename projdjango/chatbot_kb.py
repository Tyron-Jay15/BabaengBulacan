"""
Chatbot Knowledge Base for BabaengBulacan
Contains FAQ data and training data
"""

# FAQ Knowledge Base
KNOWLEDGE_BASE = [
    {
        "id": 1,
        "question": "Is my report anonymous?",
        "keywords": ["anonymous", "privacy", "confidential", "identity", "protected"],
        "answer": "Yes, you can choose to report anonymously. Your identity will be protected and only authorized personnel will have access to your information. You have full control over your privacy."
    },
    {
        "id": 2,
        "question": "What happens after I report?",
        "keywords": ["after report", "what happens", "follow up", "next steps", "investigation", "process"],
        "answer": "Your report will be reviewed within 24 hours. A case worker will be assigned and you will receive updates on the investigation progress. You can track your case status anytime."
    },
    {
        "id": 3,
        "question": "Are the programs free?",
        "keywords": ["free", "cost", "payment", "fee", "money", "charge"],
        "answer": "Yes, all empowerment programs are completely free for qualified participants. Transportation and meal allowances may be provided. No hidden charges."
    },
    {
        "id": 4,
        "question": "How do I contact emergency services?",
        "keywords": ["emergency", "contact", "call", "help", "immediate", "hotline", "911"],
        "answer": "Call our 24/7 Crisis Hotline: 999-8888. This line is available anytime, day or night. If you are in immediate danger, also call 911 or your local police."
    },
    {
        "id": 5,
        "question": "What is Republic Act 9262?",
        "keywords": ["republic act 9262", "ra 9262", "anti-violence", "women protection", "law"],
        "answer": "Republic Act 9262 is the Anti-Violence Against Women and Their Children Act of 2004. It protects women from physical, sexual, psychological, and economic abuse. You have rights to protection orders, counseling, and legal aid."
    },
    {
        "id": 6,
        "question": "Where are the nearest safe houses?",
        "keywords": ["shelter", "safe house", "location", "address", "where", "find"],
        "answer": "Visit our Service Directory on the Resource Center page to find safe houses, PNP Women's Desks, and counseling centers near you. You can view all locations on an interactive map."
    },
    {
        "id": 7,
        "question": "Can I get legal help?",
        "keywords": ["legal", "lawyer", "attorney", "help", "rights", "court"],
        "answer": "Yes! You can avail of free legal services in criminal, civil, or administrative cases. Contact our legal aid team through the emergency hotline or visit the nearest PNP Women's Desk."
    },
    {
        "id": 8,
        "question": "Do I need proof to report?",
        "keywords": ["proof", "evidence", "documentation", "witness", "record"],
        "answer": "No, you do not need proof to make a report. Your testimony is enough. We will investigate and gather evidence. Your safety and support are our priority."
    },
    {
        "id": 9,
        "question": "Can I withdraw my report?",
        "keywords": ["withdraw", "cancel", "drop", "change mind", "stop"],
        "answer": "Yes, you can withdraw your report at any time. Contact the case worker assigned to your case or call our hotline to discuss your options."
    },
    {
        "id": 10,
        "question": "What support services are available?",
        "keywords": ["support", "counseling", "therapy", "services", "help", "assistance"],
        "answer": "We offer: counseling and psychological support, medical examination and treatment, legal aid, temporary shelter, temporary custody of children, and support for maintenance."
    },
    {
        "id": 11,
        "question": "How do I report online?",
        "keywords": ["online", "report", "form", "submit", "web", "internet"],
        "answer": "You can file an anonymous report through our platform. Go to the Reports section and fill out the Anonymous Report form. Your information will be kept secure and confidential."
    },
    {
        "id": 12,
        "question": "Is counseling free?",
        "keywords": ["counseling", "therapy", "mental health", "free", "cost"],
        "answer": "Yes, all counseling and psychological support services from DSWD and our partners are completely free for victims of violence."
    },
    {
        "id": 13,
        "question": "What is the hotline number?",
        "keywords": ["hotline", "phone", "number", "call", "emergency number"],
        "answer": "Our 24/7 Crisis Hotline is 999-8888. Call anytime for immediate help or information. All calls are confidential."
    },
    {
        "id": 14,
        "question": "Can men report abuse?",
        "keywords": ["men", "male victim", "abuse men", "boys"],
        "answer": "Yes, men and boys can also report abuse. While our primary focus is women and children, we provide support to all victims of violence. Call our hotline for assistance."
    },
    {
        "id": 15,
        "question": "How are my children protected?",
        "keywords": ["children", "kids", "child protection", "custody", "minors"],
        "answer": "Children have full protection under RA 9262. You can obtain temporary custody, support, and maintenance. We provide specialized support for children affected by violence."
    }
]

# Additional training phrases for better understanding
TRAINING_PHRASES = {
    "greeting": [
        "hello", "hi", "hey", "good morning", "good afternoon", "greetings",
        "what can you help", "how can you help"
    ],
    "help": [
        "help", "support", "assist", "need help", "i need", "can you",
        "help me", "how to", "how do i", "how can i"
    ],
    "information": [
        "what is", "tell me", "information", "about", "explain", "describe",
        "know about", "learn about"
    ],
    "location": [
        "where", "location", "address", "find", "nearest", "close by",
        "near me", "in my area"
    ],
    "emergency": [
        "emergency", "urgent", "danger", "help now", "immediate", "911",
        "in danger", "critical"
    ]
}
