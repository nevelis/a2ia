"""Team roster data and mock card data for A2IA.

This data is used by the team roster tools to provide quick access to team information
without requiring API calls.
"""

TEAMS = {
    "it": [
        "Charles Black",
        "Jee Grover",
    ],
    "vp": [
        "Brett Collinson",
        "James Brown",
    ],
    "exec": [
        "Alan Miegel",
        "Derek Watson",
        "Sandra Leon",
    ],
    "cs": [
        "Norway Manalaysay",
        "Lisa Dempsey",
        "Hunter Koch",
        "Tiffany Greenhill",
        "Kathy Fitzgerald",
        "Theresa Hatcher",
        "Jose Lopez",
        "Stacey Freeman",
        "Keith Fortier",
        "Emily Gerhard",
    ],
    "product": [
        "Ben Willard",
    ],
    "platform": [
        "John Terry",
        "Chris Parkinson",
        "Dylan Kappler",
        "Aaron Sinclair",
        "Valentin Parshikov",
        "Evan Schoening",
    ],
    "datahub": [
        "Andrew Oreshko",
        "Diego Contreras",
        "Vitali Mishur",
        "Joseph Lee",
        "Vasyl Skrihunets",
        "Spencer Chastain",
        "Carter Harrington",
    ],
    "marketpricing": [
        "Nadzeya Tryvashkevich",
        "Carlos Ramirez",
        "Julia Martinovich",
        "Yauheniya Bahamya",
        "Alexey Kalachik",
        "Dmitry Bogomua",
        "Viktar Kaniushyk",
        "Maksim Zubov",
    ],
    "sales": [
        "Josh Bordes",
        "Allison Cyphers",
    ],
    "marketing": [
        "Alice Kirchhoff",
    ],
    "unrostered": [
        "Patrick Conner",
        "Nick Kropp",
        "Vanessa Michaels",
        "Jenna Starkey",
        "Christine Berrios",
        "Derek Schlicker",
        "Sean Thompson",
        "Jenny Berkedal Wilkins",
        "Evans Lusuli",
        "Christopher Bonanni",
        "Sumaiya Mahmud",
        "Cooper Yelton",
        "Caren East",
        "Erin Norman",
        "Jill Siciliano",
        "Peter O'Reilly",
        "Kevin Coogan",
        "Rachel Anzalone",
        "John Koopman",
        "Veronica Arrizon",
        "Dima Yarashuk",
        "Mary Castillo",
        "Jon Tannesen",
        "Sam Cooke",
        "Brittany Williams",
        "Christian Creek",
        "Erika Parisi",
        "Finnian Burke",
        "Joe Watson",
        "Rebeckah Flatt",
        "Anton Pavlovsky",
        "Carrie Gumina",
        "Steven Dunston",
        "Jenna Morin",
        "Denis Dudar",
        "Tetiana Bondarchuk",
        "Janet Cheung",
        "Daria Karavaieva",
        "Patryk Kaplan",
        "Oliver Wu",
        "Andrea Higgins",
        "Quinn Fang",
        "Brian Browning",
    ]
}

# Card data structure - kept as mock data for testing/demo purposes
CARDS = {
    "12345": {
        "id": "12345",
        "title": "Implement Survey Orchestration",
        "status": "In Progress",
        "assignee": "Andrew Oreshko",
        "team": "datahub",
        "description": "Core survey orchestration component",
        "parent_card": None,
        "blockers": ["23456"],
        "estimate": "5 days",
        "value": "Last component for Survey Orchestration roadmap"
    },
    "23456": {
        "id": "23456",
        "title": "Fix E2E tests in stage",
        "status": "Blocked",
        "assignee": "Aaron Sinclair",
        "team": "platform",
        "description": "E2E tests failing in stage environment",
        "parent_card": None,
        "blockers": [],
        "estimate": "2 days",
        "value": "Blocking all development branches"
    }
}


