import os
import re
import json
import urllib.request
import urllib.error
import socket
from database.db import (
    search_resources,
    get_all_subjects,
    get_all_education_levels,
    get_all_departments,
    get_connection,
)


def get_ollama_base_url():
    """Retrieve the Ollama base URL (defaults to http://localhost:11434)."""
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")


def get_model_name():
    """Retrieve the configured Ollama model name (defaults to llama3.2:3b)."""
    return os.getenv("OLLAMA_MODEL", "llama3.2:3b").strip() or "llama3.2:3b"


def check_ollama_status():
    """
    Checks if Ollama is running on the local system and if the configured model is installed.
    Returns a dictionary with connectivity, model availability, and details.
    """
    base_url = get_ollama_base_url()
    target_model = get_model_name()
    tags_url = f"{base_url}/api/tags"

    try:
        req = urllib.request.Request(tags_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "") for m in data.get("models", [])]

            target_prefix = target_model.split(":")[0]
            model_available = any(
                m == target_model or m == f"{target_model}:latest" or m.startswith(f"{target_prefix}:")
                for m in models
            )

            return {
                "connected": True,
                "model_available": model_available,
                "model": target_model,
                "installed_models": models,
                "url": base_url,
            }
    except (urllib.error.URLError, socket.timeout, ConnectionRefusedError, OSError) as e:
        return {
            "connected": False,
            "model_available": False,
            "model": target_model,
            "installed_models": [],
            "url": base_url,
            "error": str(e),
        }


# -----------------------------------------------------------------------------
# Language Detection & Response Templates (English & Kannada)
# -----------------------------------------------------------------------------

KANNADA_REGEX = re.compile(r"[\u0C80-\u0CFF]")


def is_kannada_text(text: str) -> bool:
    """Check if the text contains Kannada characters."""
    if not text or not isinstance(text, str):
        return False
    return bool(KANNADA_REGEX.search(text))


def detect_language(text: str) -> str:
    """Returns 'Kannada' if Kannada script is detected, else 'English'."""
    return "Kannada" if is_kannada_text(text) else "English"


OUT_OF_DOMAIN_MESSAGE_EN = (
    "I'm your AI Library Assistant. I can help you find books, "
    "study materials, and learning resources across all school and college educational levels (1st Standard to University). "
    "Please ask an academic or library-related question."
)

OUT_OF_DOMAIN_MESSAGE_KN = (
    "ನಾನು ನಿಮ್ಮ AI ಲೈಬ್ರರಿ ಸಹಾಯಕ. 1ನೇ ತರಗತಿಯಿಂದ ವಿಶ್ವವಿದ್ಯಾಲಯ ಮಟ್ಟದವರೆಗಿನ ಪುಸ್ತಕಗಳು, "
    "ಪಠ್ಯ ಸಾಮಗ್ರಿಗಳು ಮತ್ತು ಅಧ್ಯಯನ ಸಂಪನ್ಮೂಲಗಳನ್ನು ಹುಡುಕಲು ನಾನು ನಿಮಗೆ ಸಹಾಯ ಮಾಡಬಲ್ಲೆ. "
    "ದಯವಿಟ್ಟು ಶೈಕ್ಷಣಿಕ ಅಥವಾ ಗ್ರಂಥಾಲಯ ಸಂಬಂಧಿತ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ."
)

OUT_OF_DOMAIN_MESSAGE = OUT_OF_DOMAIN_MESSAGE_EN

NO_MATCHING_BOOKS_NOTE_EN = "No matching books are currently available in our catalogue."
NO_MATCHING_BOOKS_NOTE_KN = "ನಮ್ಮ ಗ್ರಂಥಾಲಯ ಕ್ಯಾಟಲಾಗ್‌ನಲ್ಲಿ ಪ್ರಸ್ತುತ ಯಾವುದೇ ಹೊಂದಾಣಿಕೆಯ ಪುಸ್ತಕಗಳು ಲಭ್ಯವಿಲ್ಲ."


# -----------------------------------------------------------------------------
# Universal Domain Validation Patterns
# -----------------------------------------------------------------------------

UNIVERSAL_DISALLOWED_PATTERNS = [
    # Cooking / recipes / food preparation (English)
    r"\b(cook|cooking|recipe|recipes|biryani|biriyani|bake|baking|cuisine|curry|roast|roasting|fry|frying|saute|ingredients|pasta|pizza|burger|sandwich|delicious|yummy|tasty|kitchen|chef|dinner|lunch|breakfast|tea recipe|coffee recipe)\b",
    r"\bhow to (make|prepare|cook) (food|tea|coffee|biryani|cake|bread|rice|dinner|lunch|breakfast|soup|curry)\b",
    # Cooking / food (Kannada)
    r"(ಅಡುಗೆ|ಬಿರಿಯಾನಿ|ರೆಸಿಪಿ|ಖಾದ್ಯ|ತಯಾರಿಸುವುದು ಹೇಗೆ|ಮಾಡುವುದು ಹೇಗೆ|ಚಹಾ|ಕಾಫಿ|ತಿಂಡಿ|ಊಟ|ಪಾಕವಿಧಾನ)",

    # Sports / scores / tournaments (English)
    r"\b(cricket|football|soccer|ipl|fifa|nba|nfl|baseball|tennis|badminton|hockey|olympics|world cup|wicket|wickets|batsman|bowler|batting|bowling|innings|stadium|penalty shootout)\b",
    r"\b(who won|match score|cricket match|football match|yesterday\'s match|today\'s match|live score|score of .* match)\b",
    r"\b(virat kohli|ms dhoni|sachin tendulkar|lionel messi|cristiano ronaldo|lebron james)\b",
    # Sports (Kannada)
    r"(ಕ್ರಿಕೆಟ್|ಫುಟ್‌ಬಾಲ್|ಪಂದ್ಯ|ಯಾರು ಗೆದ್ದರು|ಸ್ಕೋರ್|ವಿರಾಟ್ ಕೊಹ್ಲಿ|ಧೋನಿ|ವಿಕೆಟ್)",

    # Entertainment / jokes / pop culture (English)
    r"\b(joke|jokes|riddle|riddles|pun|puns|funny story|humor me|standup comedy)\b",
    r"\b(tell me a joke|crack a joke|say a joke)\b",
    r"\b(movie|movies|cinema|box office|hollywood|bollywood|actor|actress|celebrity|gossip|pop star|taylor swift|sing a song|album lyrics)\b",
    # Entertainment / jokes (Kannada)
    r"(ಹಾಸ್ಯ|ತಮಾಷೆ|ಕಾಮಿಡಿ|ಚಲನಚಿತ್ರ|ಸಿನಿಮಾ|ನಟ|ನಟಿ|ಹಾಡು ಹಾಡು|ಹಾಡಿನ ಸಾಲುಗಳು)",

    # Politics / elections (English)
    r"\b(election|elections|political party|politics|politician|politicians|parliament|prime minister|president of|chief minister|democrat|republican|senate|campaign rally|ballot)\b",
    # Politics (Kannada)
    r"(ರಾಜಕೀಯ|ಚುನಾವಣೆ|ಪ್ರಧಾನ ಮಂತ್ರಿ|ಮುಖ್ಯಮಂತ್ರಿ|ಸಂಸತ್ತು|ರಾಜಕಾರಣಿ)",

    # Astrology / dating / non-academic lifestyle (English & Kannada)
    r"\b(horoscope|astrology|zodiac sign|dating advice|find a girlfriend|find a boyfriend)\b",
    r"\b(weight loss|symptoms of fever|headache remedy|crypto trading|buy bitcoin|stock tips|forex)\b",
    r"(ಜಾತಕ|ಜ್ಯೋತಿಷ್ಯ|ತೂಕ ಇಳಿಕೆ)",
]

EDU_LEVEL_PATTERNS = [
    # Primary school: 1st - 5th
    r"\b(1st|2nd|3rd|4th|5th|first|second|third|fourth|fifth)\s+(standard|grade|class)\b",
    r"\b(class|grade|standard)\s+(1|2|3|4|5|i|ii|iii|iv|v)\b",
    r"\b(primary\s+school|primary\s+education|elementary)\b",
    # Middle school: 6th - 8th
    r"\b(6th|7th|8th|sixth|seventh|eighth)\s+(standard|grade|class)\b",
    r"\b(class|grade|standard)\s+(6|7|8|vi|vii|viii)\b",
    r"\b(middle\s+school)\b",
    # High school: 9th - 10th / SSLC
    r"\b(9th|10th|ninth|tenth)\s+(standard|grade|class)\b",
    r"\b(class|grade|standard)\s+(9|10|ix|x)\b",
    r"\b(high\s+school|sslc|secondary\s+school|matriculation|10th\s+board)\b",
    # PUC / 11th - 12th
    r"\b(1st|2nd|first|second)\s+puc\b",
    r"\b(puc|pu\s+college|pre-university|pre\s+university)\b",
    r"\b(11th|12th|eleventh|twelfth)\s+(standard|grade|class)\b",
    r"\b(class|grade|standard)\s+(11|12|xi|xii)\b",
    r"\b(higher\s+secondary|plus\s+two|\+2|cbse\s+12|cbse\s+11|karnataka\s+puc)\b",
    # Diploma / Polytechnic
    r"\b(diploma|polytechnic|applied\s+science)\b",
    # Undergraduate
    r"\b(undergraduate|undergrad|ug|degree|bachelor|bachelors|b\.?e\.?|b\.?tech\.?|b\.?sc\.?|b\.?com\.?|bca|bba|b\.?a\.?)\b",
    # Postgraduate
    r"\b(postgraduate|postgrad|pg|masters?|m\.?tech\.?|m\.?sc\.?|m\.?com\.?|mca|mba|m\.?a\.?|doctorate|phd)\b",
    # Kannada levels & classes
    r"(1ನೇ|2ನೇ|3ನೇ|4ನೇ|5ನೇ|6ನೇ|7ನೇ|8ನೇ|9ನೇ|10ನೇ|೧ನೇ|೨ನೇ|೩ನೇ|೪ನೇ|೫ನೇ|೬ನೇ|೭ನೇ|೮ನೇ|೯ನೇ|೧೦ನೇ)\s*(ತರಗತಿ|ಕ್ಲಾಸ್|ಸ್ಟ್ಯಾಂಡರ್ಡ್)",
    r"(ಪ್ರಾಥಮಿಕ|ಮಾಧ್ಯಮಿಕ|ಪ್ರೌಢಶಾಲೆ|ಎಸ್ಎಸ್ಎಲ್ಸಿ|ಪಿಯುಸಿ|೧ನೇ\s*ಪಿಯುಸಿ|೨ನೇ\s*ಪಿಯುಸಿ|ಡಿಪ್ಲೊಮಾ|ಪಾಲಿಟೆಕ್ನಿಕ್|ಪದವಿ|ಸ್ನಾತಕೋತ್ತರ|ಇಂಜಿನಿಯರಿಂಗ್|ವಿಶ್ವವಿದ್ಯಾಲಯ|ಕಾಲೇಜು|ಶಾಲೆ)",
]

ACADEMIC_SUBJECT_PATTERNS = [
    # Languages & Literature
    r"\b(kannada|english|hindi|sanskrit|literature|grammar|comprehension|poetry|prose)\b",
    # School core subjects
    r"\b(mathematics|math|maths|arithmetic|algebra|geometry|trigonometry|calculus|statistics)\b",
    r"\b(science|general science|environmental studies|evs|physics|chemistry|biology|botany|zoology)\b",
    r"\b(social science|social studies|history|geography|civics|political science|sociology)\b",
    # College / Engineering subjects
    r"\b(engineering mathematics|m1|m2|m3|m4|discrete mathematics|differential equations|linear algebra|complex analysis|numerical methods)\b",
    r"\b(mechanical engineering|mechanics|thermodynamics|fluid mechanics|strength of materials|heat transfer|machine design|manufacturing)\b",
    r"\b(civil engineering|surveying|structural analysis|concrete technology|geotechnical|hydraulics|environmental engineering)\b",
    r"\b(electrical engineering|circuits|power systems|electrical machines|control systems|electromagnetics|power electronics)\b",
    r"\b(electronics|communication engineering|ece|analog electronics|digital electronics|signals and systems|vlsi|microprocessors|embedded systems)\b",
    r"\b(commerce|accountancy|accounting|business studies|financial accounting|management accounting|corporate accounting|auditing|taxation|gst)\b",
    r"\b(economics|macroeconomics|microeconomics|business economics|public finance|econometrics)\b",
    r"\b(management|marketing|human resource|finance|operations research|business administration|organizational behavior|supply chain)\b",
    # Computer Science & IT
    r"\b(computer science|programming|software engineering|coding|dsa|data structures|algorithms|oop)\b",
    r"\b(python|java|c\+\+|cpp|c\#|csharp|golang|rust|kotlin|swift|php|ruby|sql|nosql|html|css|javascript|typescript)\b",
    r"\b(c\s+(programming|language|code|pointer|pointers|basics|struct)|in\s+c\b|\bc\s+program|pointers?\s+in\s+c\b|learn\s+c\b)\b",
    r"\b(operating systems?|os|kernel|dbms|database|computer networks?|osi model|tcp/ip|network security|cryptography)\b",
    r"\b(artificial intelligence|machine learning|deep learning|neural networks?|nlp|computer vision|ai|ml|dl|llm)\b",
    r"\b(web development|full stack|frontend|backend|flask|django|react|spring boot)\b",
    # Kannada subjects & academic terms
    r"(ಕನ್ನಡ|ಇಂಗ್ಲಿಷ್|ಹಿಂದಿ|ಸಂಸ್ಕೃತ|ವ್ಯಾಕರಣ|ಸಾಹಿತ್ಯ)",
    r"(ಗಣಿತ|ಅಂಕಗಣಿತ|ಬೀಜಗಣಿತ|ರೇಖಾಗಣಿತ|ವಿಜ್ಞಾನ|ಭೌತಶಾಸ್ತ್ರ|ರಸಾಯನಶಾಸ್ತ್ರ|ಜೀವಶಾಸ್ತ್ರ|ಪರಿಸರ)",
    r"(ಸಮಾಜ\s*ವಿಜ್ಞಾನ|ಇತಿಹಾಸ|ಭೂಗೋಳ|ರಾಜ್ಯಶಾಸ್ತ್ರ|ಅರ್ಥಶಾಸ್ತ್ರ|ವಾಣಿಜ್ಯ|ಲೆಕ್ಕಶಾಸ್ತ್ರ|ಖಾತೆ)",
    r"(ಇಂಜಿನಿಯರಿಂಗ್|ಮೆಕ್ಯಾನಿಕಲ್|ಸಿವಿಲ್|ಎಲೆಕ್ಟ್ರಿಕಲ್|ಎಲೆಕ್ಟ್ರಾನಿಕ್ಸ್|ಗಣಕವಿಜ್ಞಾನ|ಕಂಪ್ಯೂಟರ್)",
]

STUDY_AND_LIBRARY_PATTERNS = [
    r"\b(book|books|textbook|textbooks|resource|resources|material|materials|reference|references)\b",
    r"\b(catalogue|catalog|reading list|syllabus|curriculum|handbook|guide|guides|tutorial|tutorials|notes|notes for)\b",
    r"\b(study|studying|study plan|study schedule|learning path|roadmap|learn|learning|revision|exam|exams|semester|preparation|prepare|homework|assignment)\b",
    r"\b(recommend|recommendation|recommendations|suggest|suggestion|suggestions|explain|what is|how does|solve|derivation|theorem)\b",
    r"\b(beginner|intermediate|advanced|school|college|university|student|teacher)\b",
    # Kannada study/library terms
    r"(ಪುಸ್ತಕ|ಪುಸ್ತಕಗಳು|ಪಠ್ಯಪುಸ್ತಕ|ಗ್ರಂಥಾಲಯ|ಕ್ಯಾಟಲಾಗ್|ಪಠ್ಯಕ್ರಮ|ಟಿಪ್ಪಣಿಗಳು|ಅಧ್ಯಯನ|ಕಲಿಯಿರಿ|ಕಲಿಯಲು)",
    r"(ಶಿಫಾರಸು|ಸಲಹೆ|ವಿವರಿಸಿ|ಅರ್ಥಮಾಡಿಕೊಳ್ಳಿ|ಪರೀಕ್ಷೆ|ಸಿದ್ಧತೆ|ವೇಳಾಪಟ್ಟಿ|ಯೋಜನೆ|ಮಾರ್ಗದರ್ಶಿ)",
]

GREETINGS_OR_META_PATTERNS = [
    r"^\s*(hi|hello|hey|good\s+(morning|afternoon|evening)|greetings|howdy|help|namaste|namaskara)\b",
    r"\b(who are you|what are you|what can you do|what do you do|how can you help|how do you work|what is your purpose|what can i ask|what subjects|available subjects|guide me)\b",
    r"^\s*(thank\s+you|thanks|thanks\s+a\s+lot|bye|goodbye)\b",
    # Kannada greetings
    r"(ನಮಸ್ಕಾರ|ಹಲೋ|ಹಾಯ್|ನೀವು ಯಾರು|ನಿಮ್ಮ ಕೆಲಸ ಏನು|ಏನು ಸಹಾಯ ಮಾಡಬಹುದು|ಧನ್ಯವಾದ|ಶುಭೋದಯ)",
]


def is_in_domain(message: str, history: list = None) -> bool:
    """
    Validates whether a user query falls within the Universal Educational Library Assistant domain.
    Supports students from 1st Standard to University level across all subjects and departments,
    in both Kannada and English.
    Strictly rejects unrelated topics (cooking, recipes, biryani, cricket scores, entertainment,
    jokes, politics, etc.).
    """
    if not message or not isinstance(message, str):
        return False

    clean_message = message.strip().lower()
    if not clean_message:
        return False

    # 1. Negative Filter: Reject disallowed topics unconditionally (English & Kannada)
    for pat in UNIVERSAL_DISALLOWED_PATTERNS:
        if re.search(pat, clean_message):
            return False

    # 2. Positive Filter: Check greetings or meta inquiries
    for pat in GREETINGS_OR_META_PATTERNS:
        if re.search(pat, clean_message):
            return True

    # 3. Positive Filter: Check educational levels / classes
    for pat in EDU_LEVEL_PATTERNS:
        if re.search(pat, clean_message):
            return True

    # 4. Positive Filter: Check academic subjects across school and college
    for pat in ACADEMIC_SUBJECT_PATTERNS:
        if re.search(pat, clean_message):
            return True

    # 5. Positive Filter: Check general study, library, and learning keywords
    for pat in STUDY_AND_LIBRARY_PATTERNS:
        if re.search(pat, clean_message):
            return True

    # 6. Contextual dialogue follow-ups (if history exists and previous turns were in-domain)
    if history and isinstance(history, list) and len(history) > 0:
        follow_up_cues = [
            r"\b(next|more|explain|summarize|detail|shorter|longer|schedule|plan|days?|weeks?|first|second|third|step|why|how)\b",
            r"(ಇನ್ನಷ್ಟು|ವಿವರಿಸಿ|ಸಂಕ್ಷೇಪಿಸಿ|ಮುಂದೆ|ಹೇಗೆ|ಏಕೆ)",
        ]
        is_follow_up = any(re.search(pat, clean_message) for pat in follow_up_cues)
        if is_follow_up:
            history_text = " ".join(
                str(turn.get("content", "")).lower()
                for turn in history[-4:]
                if isinstance(turn, dict)
            )
            for pat in EDU_LEVEL_PATTERNS + ACADEMIC_SUBJECT_PATTERNS + STUDY_AND_LIBRARY_PATTERNS:
                if re.search(pat, history_text):
                    return True

    return False


# -----------------------------------------------------------------------------
# Intelligent Catalogue Relevance Matching
# -----------------------------------------------------------------------------

CLASS_PATTERNS = [
    (r"\b(1st|first|1)\s+(standard|grade|class)\b|\bclass\s+1\b|\b1ನೇ\s*(ತರಗತಿ|ಕ್ಲಾಸ್)", "Class 1"),
    (r"\b(2nd|second|2)\s+(standard|grade|class)\b|\bclass\s+2\b|\b2ನೇ\s*(ತರಗತಿ|ಕ್ಲಾಸ್)", "Class 2"),
    (r"\b(3rd|third|3)\s+(standard|grade|class)\b|\bclass\s+3\b|\b3ನೇ\s*(ತರಗತಿ|ಕ್ಲಾಸ್)", "Class 3"),
    (r"\b(4th|fourth|4)\s+(standard|grade|class)\b|\bclass\s+4\b|\b4ನೇ\s*(ತರಗತಿ|ಕ್ಲಾಸ್)", "Class 4"),
    (r"\b(5th|fifth|5)\s+(standard|grade|class)\b|\bclass\s+5\b|\b5ನೇ\s*(ತರಗತಿ|ಕ್ಲಾಸ್)", "Class 5"),
    (r"\b(6th|sixth|6)\s+(standard|grade|class)\b|\bclass\s+6\b|\b6ನೇ\s*(ತರಗತಿ|ಕ್ಲಾಸ್)", "Class 6"),
    (r"\b(7th|seventh|7)\s+(standard|grade|class)\b|\bclass\s+7\b|\b7ನೇ\s*(ತರಗತಿ|ಕ್ಲಾಸ್)", "Class 7"),
    (r"\b(8th|eighth|8)\s+(standard|grade|class)\b|\bclass\s+8\b|\b8ನೇ\s*(ತರಗತಿ|ಕ್ಲಾಸ್)", "Class 8"),
    (r"\b(9th|ninth|9)\s+(standard|grade|class)\b|\bclass\s+9\b|\b9ನೇ\s*(ತರಗತಿ|ಕ್ಲಾಸ್)", "Class 9"),
    (r"\b(10th|tenth|10)\s+(standard|grade|class)\b|\bclass\s+10\b|\bsslc\b|\b10ನೇ\s*(ತರಗತಿ|ಕ್ಲಾಸ್)", "Class 10"),
    (r"\b(1st\s+puc|class\s+11|11th\s+standard|11th\s+grade)\b|\b1ನೇ\s*ಪಿಯುಸಿ", "1st PUC"),
    (r"\b(2nd\s+puc|class\s+12|12th\s+standard|12th\s+grade)\b|\b2ನೇ\s*ಪಿಯುಸಿ", "2nd PUC"),
]

SPECIFIC_EDU_PATTERNS = [
    (r"\b(primary\s+school|primary|1st\s+to\s+5th)\b|ಪ್ರಾಥಮಿಕ", "Primary School"),
    (r"\b(middle\s+school|6th\s+to\s+8th)\b|ಮಾಧ್ಯಮಿಕ", "Middle School"),
    (r"\b(high\s+school|9th\s+to\s+10th|sslc)\b|ಪ್ರೌಢಶಾಲೆ", "High School"),
    (r"\b(puc|pre-university|pre\s+university|11th|12th|\+2|plus\s+two)\b|ಪಿಯುಸಿ", "PUC"),
    (r"\b(diploma|polytechnic)\b|ಡಿಪ್ಲೊಮಾ|ಪಾಲಿಟೆಕ್ನಿಕ್", "Diploma"),
    (r"\b(undergraduate|ug|degree|bachelor|b\.?e|b\.?tech|b\.?sc|b\.?com|bca|bba)\b|ಪದವಿ", "Undergraduate"),
    (r"\b(postgraduate|pg|master|m\.?tech|m\.?sc|m\.?com|mca|mba)\b|ಸ್ನಾತಕೋತ್ತರ", "Postgraduate"),
]

COURSE_CODE_PATTERNS = [
    (r"\b(m-?1|mat-?101|engg\s+math\s+1|math\s+1|engineering\s+mathematics\s+1)\b", "M1"),
    (r"\b(m-?2|mat-?201|engg\s+math\s+2|math\s+2|engineering\s+mathematics\s+2)\b", "M2"),
    (r"\b(m-?3|mat-?301|engg\s+math\s+3|math\s+3|engineering\s+mathematics\s+3)\b", "M3"),
    (r"\b(m-?4|mat-?401|engg\s+math\s+4|math\s+4|engineering\s+mathematics\s+4)\b", "M4"),
]

SPECIFIC_SUBJECT_PATTERNS = [
    (r"\b(python|python\s+programming)\b", "Python Programming"),
    (r"\b(java|java\s+programming)\b", "Java Programming"),
    (r"\b(dsa|data\s+structures|algorithms|algorithm)\b", "Data Structures and Algorithms"),
    (r"\b(dbms|database|databases|sql)\b", "Database Management Systems"),
    (r"\b(operating\s+systems?|\bos\b)\b", "Operating Systems"),
    (r"\b(computer\s+networks?|networking)\b", "Computer Networks"),
    (r"\b(artificial\s+intelligence|\bai\b|machine\s+learning|\bml\b)\b", "Artificial Intelligence"),
    (r"\b(web\s+development|javascript|html|css|web\s+dev)\b", "Web Development"),
    (r"\b(physics|ಭೌತಶಾಸ್ತ್ರ)\b", "Physics"),
    (r"\b(chemistry|ರಸಾಯನಶಾಸ್ತ್ರ)\b", "Chemistry"),
    (r"\b(biology|ಜೀವಶಾಸ್ತ್ರ)\b", "Biology"),
    (r"\b(engineering\s+mathematics|m1|m2|m3|m4)\b", "Engineering Mathematics"),
    (r"\b(mathematics|math|maths|ಗಣಿತ)\b", "Mathematics"),
    (r"\b(applied\s+science)\b", "Applied Science"),
    (r"\b(science|ವಿಜ್ಞಾನ)\b", "Science"),
    (r"\b(social\s+science|social\s+studies|ಸಮಾಜ\s*ವಿಜ್ಞಾನ)\b", "Social Science"),
    (r"\b(kannada|ಕನ್ನಡ)\b", "Kannada"),
    (r"\b(english|ಇಂಗ್ಲಿಷ್)\b", "English"),
    (r"\b(hindi|ಹಿಂದಿ)\b", "Hindi"),
    (r"\b(history|ಇತಿಹಾಸ)\b", "History"),
    (r"\b(economics|ಅರ್ಥಶಾಸ್ತ್ರ)\b", "Economics"),
    (r"\b(commerce|accountancy|accounting|ಲೆಕ್ಕಶಾಸ್ತ್ರ|ಖಾತೆ)\b", "Accountancy"),
    (r"\b(mechanical\s+engineering|fluid\s+mechanics|thermodynamics)\b", "Mechanical Engineering"),
    (r"\b(civil\s+engineering|surveying)\b", "Civil Engineering"),
    (r"\b(electrical\s+engineering|electronics|circuits)\b", "Electrical and Electronics Engineering"),
]


def find_relevant_resources(message: str, history: list = None) -> list:
    """
    Intelligently finds verified library resources matching the user query.
    Enforces strict class, education level, and subject alignment to eliminate
    unrelated book recommendations.
    Returns empty list [] if no genuine catalogue match is found.
    """
    text_to_scan = message.lower()
    if history and isinstance(history, list):
        for turn in history[-2:]:
            if isinstance(turn, dict):
                text_to_scan += " " + str(turn.get("content", "")).lower()

    # 1. Detect Class / Grade
    detected_class = None
    for pat, cls in CLASS_PATTERNS:
        if re.search(pat, text_to_scan, re.IGNORECASE):
            detected_class = cls
            break

    # 2. Detect Education Level
    detected_edu = None
    for pat, edu in SPECIFIC_EDU_PATTERNS:
        if re.search(pat, text_to_scan, re.IGNORECASE):
            detected_edu = edu
            break

    # Infer Education Level from Class
    if detected_class:
        if detected_class in ["Class 1", "Class 2", "Class 3", "Class 4", "Class 5"]:
            detected_edu = detected_edu or "Primary School"
        elif detected_class in ["Class 6", "Class 7", "Class 8"]:
            detected_edu = detected_edu or "Middle School"
        elif detected_class in ["Class 9", "Class 10"]:
            detected_edu = detected_edu or "High School"
        elif detected_class in ["1st PUC", "2nd PUC"]:
            detected_edu = detected_edu or "PUC"

    # 3. Detect Course Codes (M1, M2, M3, M4)
    detected_course_codes = []
    for pat, code in COURSE_CODE_PATTERNS:
        if re.search(pat, text_to_scan, re.IGNORECASE):
            detected_course_codes.append(code)

    # 4. Detect Specific Academic Subjects
    detected_subjects = set()
    for pat, subj in SPECIFIC_SUBJECT_PATTERNS:
        if re.search(pat, text_to_scan, re.IGNORECASE):
            detected_subjects.add(subj)

    # If "Engineering Mathematics" or M1/M2/M3 is detected, adjust subject & level
    if "Engineering Mathematics" in detected_subjects or detected_course_codes:
        detected_subjects.discard("Mathematics")
        detected_subjects.add("Engineering Mathematics")
        if not detected_edu or detected_edu in ["Primary School", "Middle School", "High School"]:
            detected_edu = "Undergraduate"

    # If "Kannada mathematics" or "5th Kannada math", Kannada is medium/language, subject is Mathematics
    if "Mathematics" in detected_subjects and "Kannada" in detected_subjects and detected_class:
        # Keep Mathematics as primary subject, Kannada as language preference
        detected_subjects.discard("Kannada")

    is_kannada = is_kannada_text(message)

    # Fetch all candidate resources from database
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, title, author, publisher, subject, level, education_level,
                   class_grade, department, language, description, resource_type, url
            FROM resources
        """).fetchall()

    scored = []
    for row in rows:
        r = dict(row)
        score = 0
        r_title = (r["title"] or "").lower()
        r_desc = (r["description"] or "").lower()
        r_subj = (r["subject"] or "").lower()
        r_edu = (r["education_level"] or "").lower()
        r_class = (r["class_grade"] or "").lower()
        r_lang = (r["language"] or "").lower()

        # Subject Filter (Strict Disqualification)
        if detected_subjects:
            target_subjs_lower = [s.lower() for s in detected_subjects]
            if r_subj not in target_subjs_lower:
                # Unless it's an exact course code match (e.g. M2 in description)
                if not (detected_course_codes and any(c.lower() in r_desc for c in detected_course_codes)):
                    continue
            score += 35

        # Class / Grade Matching (Strict Disqualification)
        if detected_class:
            if detected_class.lower() == r_class:
                score += 40
            elif r_class not in ["all classes", ""]:
                # Mismatched specific class -> Disqualify
                continue

        # Education Level Matching (Strict Disqualification)
        if detected_edu:
            if detected_edu.lower() == r_edu:
                score += 25
            else:
                # If specific level was requested, do not show wrong educational level
                if detected_edu in ["Primary School", "Middle School", "High School", "PUC", "Diploma"]:
                    continue

        # Course Code Matching (e.g. M1, M2, M3)
        if detected_course_codes:
            matched_code = False
            for code in detected_course_codes:
                code_lower = code.lower()
                if code_lower in r_desc or code_lower in r_title:
                    score += 50
                    matched_code = True
            if not matched_code and "engineering mathematics" in r_subj:
                score += 15

        # Language Matching
        if is_kannada:
            if r_lang == "kannada":
                score += 30
            elif r_lang == "bilingual":
                score += 15
        elif "kannada" in text_to_scan:
            if r_lang == "kannada":
                score += 30

        # Meaningful keyword relevance in title and description
        words = re.findall(r"\w+", text_to_scan)
        meaningful_words = [
            w for w in words
            if len(w) > 3 and w not in [
                "book", "books", "recommend", "recommendation", "recommendations",
                "suggest", "want", "please", "help", "with", "from", "give"
            ]
        ]
        for w in meaningful_words:
            if w in r_title:
                score += 10
            elif w in r_desc:
                score += 5

        # Only retain matches that pass the strict relevance threshold
        if score >= 25:
            scored.append((score, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:6]]


# -----------------------------------------------------------------------------
# System Prompt Builder with Dual-Language and Educational Level Guidance
# -----------------------------------------------------------------------------

def build_system_prompt(relevant_resources, query_language="English", detected_level=None):
    """
    Constructs the system prompt instructing Ollama (Llama 3.2 3B) to act as a
    Universal AI Library Assistant for students of all ages, classes, and educational levels,
    supporting Kannada and English.
    """
    if relevant_resources:
        catalogue_text = "CURRENT MATCHING VERIFIED RESOURCES IN THE LIBRARY CATALOGUE:\n"
        for r in relevant_resources:
            url_part = f" | Link: {r['url']}" if r.get("url") else ""
            pub_part = f" | Publisher: {r['publisher']}" if r.get("publisher") else ""
            catalogue_text += (
                f"- [ID {r['id']}] \"{r['title']}\" by {r['author']} "
                f"({r.get('education_level', '')}, {r.get('class_grade', '')}, {r.get('subject', '')}{pub_part}) - {r.get('level', '')}\n"
                f"  Description: {r.get('description', '')}{url_part}\n"
            )
    else:
        catalogue_text = (
            "CATALOGUE STATUS: No matching books are currently available in the library catalogue for this specific query.\n"
            "You MUST state: 'No matching books are currently available in our catalogue.' "
            "(In Kannada: 'ನಮ್ಮ ಗ್ರಂಥಾಲಯ ಕ್ಯಾಟಲಾಗ್‌ನಲ್ಲಿ ಪ್ರಸ್ತುತ ಯಾವುದೇ ಹೊಂದಾಣಿಕೆಯ ಪುಸ್ತಕಗಳು ಲಭ್ಯವಿಲ್ಲ.')\n"
            "You can still provide general conceptual explanations, learning roadmaps, and study advice, "
            "but clearly indicate that this is general advice and that the specific textbook is not in the library catalogue.\n"
        )

    lang_instruction = ""
    if query_language == "Kannada":
        lang_instruction = """
LANGUAGE REQUIREMENT (CRITICAL):
- The student's query is in KANNADA.
- You MUST answer COMPLETELY in fluent, grammatically correct, natural KANNADA (ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸಿ).
- Use clear Kannada terminology familiar to Karnataka students (e.g., ಗಣಿತ, ವಿಜ್ಞಾನ, ಅಧ್ಯಯನ ಯೋಜನೆ).
- You may include English book titles in parentheses if helpful.
"""
    else:
        lang_instruction = """
LANGUAGE REQUIREMENT:
- The student's query is in ENGLISH. Answer in clear, concise, fluent English.
"""

    system_prompt = f"""You are the Universal AI Library Assistant, running locally with Ollama (Llama 3.2 3B).
You help students of ALL AGES, CLASSES, DEPARTMENTS, AND EDUCATIONAL LEVELS (from 1st Standard to University and Postgraduate level).

CORE DOMAIN BOUNDARIES:
- You ONLY answer questions related to library resources, books, academic subjects, syllabus, learning roadmaps, and study plans across all educational levels (Primary, Middle, High School / SSLC, PUC, Diploma, Undergraduate, and Postgraduate).
- Strictly REJECT questions about cooking, recipes, biryani, cricket scores, entertainment, jokes, politics, elections, and non-academic topics.

{lang_instruction}

AGE & EDUCATIONAL LEVEL ADAPTATION:
- Primary School (1st to 5th Standard): Use simple, friendly words, short sentences, and fun, encouraging explanations.
- Middle School (6th to 8th Standard): Provide clear definitions, practical everyday examples, and easy study tips.
- High School (9th & 10th / SSLC): Focus on key board syllabus concepts, step-by-step problem-solving, and exam preparation tips.
- PUC / Higher Secondary (1st & 2nd PUC / 11th & 12th): Balance theoretical clarity with formulas, derivations, diagrams, and board/competitive exam orientation.
- Diploma / Polytechnic: Focus on practical application, industry relevance, step-by-step technical procedures, and applied science.
- Undergraduate & Postgraduate (BA, BSc, BCom, BCA, BBA, BE, BTech, MA, MSc, MCom, MCA, MBA, MTech): Provide deep academic rigor, mathematical foundations, standard university textbook references, and research perspectives.

CATALOGUE GROUNDING RULES:
1. When matching catalogue items are listed below, cite their EXACT Title and Author.
2. NEVER invent book titles, authors, or fake library entries.
3. If no matching books are listed, clearly include the note:
   "No matching books are currently available in our catalogue." (or in Kannada: "ನಮ್ಮ ಗ್ರಂಥಾಲಯ ಕ್ಯಾಟಲಾಗ್‌ನಲ್ಲಿ ಪ್ರಸ್ತುತ ಯಾವುದೇ ಹೊಂದಾಣಿಕೆಯ ಪುಸ್ತಕಗಳು ಲಭ್ಯವಿಲ್ಲ.")
4. Clearly distinguish between verified catalogue books available in our library and general conceptual advice or learning tips.

{catalogue_text}
"""
    return system_prompt


# -----------------------------------------------------------------------------
# Ollama Chat Generation
# -----------------------------------------------------------------------------

def generate_chat_response(message: str, history: list = None) -> dict:
    """
    Interacts with local Ollama API using conversation history and catalogue grounding.
    Returns a dictionary with response details or friendly error status.
    """
    base_url = get_ollama_base_url()
    model = get_model_name()
    query_language = detect_language(message)

    # 1. Pre-generation domain validation check
    if not is_in_domain(message, history):
        reject_reply = OUT_OF_DOMAIN_MESSAGE_KN if query_language == "Kannada" else OUT_OF_DOMAIN_MESSAGE_EN
        return {
            "success": True,
            "reply": reject_reply,
            "recommended_resources": [],
            "catalogue_note": None,
            "language": query_language,
            "model": model,
            "status_code": 200,
        }

    # 2. Intelligent Catalogue Search
    relevant_resources = find_relevant_resources(message, history)
    catalogue_note = None
    if len(relevant_resources) == 0:
        catalogue_note = NO_MATCHING_BOOKS_NOTE_KN if query_language == "Kannada" else NO_MATCHING_BOOKS_NOTE_EN

    # 3. Build System Prompt with Language & Level Context
    system_prompt = build_system_prompt(relevant_resources, query_language=query_language)

    # 4. Format messages array
    messages = [{"role": "system", "content": system_prompt}]

    if history and isinstance(history, list):
        for turn in history[-8:]:
            if isinstance(turn, dict) and turn.get("role") in ("user", "assistant"):
                content = str(turn.get("content", "")).strip()
                if content:
                    messages.append({"role": turn["role"], "content": content})

    messages.append({"role": "user", "content": message.strip()})

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.6,
        },
    }

    chat_url = f"{base_url}/api/chat"
    data_bytes = json.dumps(payload).encode("utf-8")

    try:
        req = urllib.request.Request(
            chat_url,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=120) as resp:
            response_data = json.loads(resp.read().decode("utf-8"))
            reply_msg = response_data.get("message", {}).get("content", "").strip()

            return {
                "success": True,
                "reply": reply_msg,
                "recommended_resources": relevant_resources,
                "catalogue_note": catalogue_note,
                "language": query_language,
                "model": model,
                "status_code": 200,
            }

    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            pass

        if e.code == 404 or "not found" in error_body.lower():
            return {
                "success": False,
                "error_type": "model_missing",
                "message": (
                    f"The model '{model}' was not found in your Ollama installation. "
                    f"Please run 'ollama run {model}' or 'ollama pull {model}' in your terminal to download it."
                ),
                "status_code": 503,
            }
        return {
            "success": False,
            "error_type": "ollama_http_error",
            "message": f"Ollama service returned error HTTP {e.code}: {e.reason}",
            "status_code": 502,
        }

    except (urllib.error.URLError, ConnectionRefusedError, OSError) as e:
        return {
            "success": False,
            "error_type": "ollama_not_running",
            "message": (
                f"Ollama is not running locally at {base_url}. "
                "Please make sure Ollama is installed and started (run 'ollama serve' in your terminal or launch the Ollama app). "
                "You can still search and browse all library catalogue books below."
            ),
            "status_code": 503,
        }

    except (socket.timeout, TimeoutError):
        return {
            "success": False,
            "error_type": "timeout",
            "message": (
                "The local AI model took too long to generate a response. "
                "Please ensure your system has available CPU/RAM resources and try again."
            ),
            "status_code": 504,
        }

    except Exception as e:
        return {
            "success": False,
            "error_type": "unexpected_error",
            "message": f"An unexpected error occurred while communicating with Ollama: {str(e)}",
            "status_code": 500,
        }
