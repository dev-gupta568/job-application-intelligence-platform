import re
from collections import Counter
from decimal import Decimal

ALGORITHM_VERSION = "rule-based-v1"

SKILL_PATTERNS: dict[str, tuple[str, ...]] = {
    "Accessibility": ("accessibility", "a11y"),
    "Agile": ("agile",),
    "Amazon Web Services": ("amazon web services", "aws"),
    "Angular": ("angular",),
    "API design": ("api design", "rest api", "restful api"),
    "Application security": ("application security", "app security"),
    "Azure": ("azure", "microsoft azure"),
    "Bash": ("bash", "shell scripting"),
    "C": ("c language",),
    "C#": ("c#", "c sharp"),
    "C++": ("c++", "cpp"),
    "CI/CD": ("ci/cd", "continuous integration", "continuous delivery", "continuous deployment"),
    "Cloud computing": ("cloud computing", "cloud platform"),
    "Communication": ("communication", "communicate"),
    "CSS": ("css", "css3"),
    "Data analysis": ("data analysis", "data analytics"),
    "Data engineering": ("data engineering",),
    "Data visualization": ("data visualization",),
    "Django": ("django",),
    "Docker": ("docker", "containerization"),
    "Express": ("express", "express.js"),
    "FastAPI": ("fastapi", "fast api"),
    "Figma": ("figma",),
    "Flask": ("flask",),
    "Git": ("git", "version control"),
    "GitHub Actions": ("github actions",),
    "Go": ("golang",),
    "GraphQL": ("graphql",),
    "HTML": ("html", "html5"),
    "Java": ("java",),
    "JavaScript": ("javascript", "js"),
    "Jenkins": ("jenkins",),
    "Jest": ("jest",),
    "Kotlin": ("kotlin",),
    "Kubernetes": ("kubernetes", "k8s"),
    "Linux": ("linux",),
    "Machine learning": ("machine learning", "ml"),
    "Microsoft Excel": ("microsoft excel", "excel"),
    "MongoDB": ("mongodb", "mongo db"),
    "MySQL": ("mysql", "my sql"),
    "Next.js": ("next.js", "nextjs"),
    "Node.js": ("node.js", "nodejs", "node js"),
    "NoSQL": ("nosql", "no sql"),
    "OAuth": ("oauth", "oauth 2.0", "oauth2"),
    "PHP": ("php",),
    "Playwright": ("playwright",),
    "PostgreSQL": ("postgresql", "postgres", "postgre sql"),
    "Power BI": ("power bi",),
    "Problem solving": ("problem solving", "problem-solving"),
    "Project management": ("project management",),
    "Python": ("python",),
    "Pytest": ("pytest",),
    "React": ("react", "react.js", "reactjs"),
    "Redis": ("redis",),
    "Redux": ("redux",),
    "Responsive design": ("responsive design",),
    "Ruby": ("ruby",),
    "Ruby on Rails": ("ruby on rails", "rails"),
    "Rust": ("rust",),
    "SASS": ("sass", "scss"),
    "SQL": ("sql",),
    "SQLite": ("sqlite",),
    "Software testing": ("software testing", "test automation"),
    "Spring Boot": ("spring boot",),
    "Tailwind CSS": ("tailwind css", "tailwind"),
    "Teamwork": ("teamwork", "collaboration"),
    "Technical writing": ("technical writing",),
    "Terraform": ("terraform",),
    "TypeScript": ("typescript", "ts"),
    "UI design": ("ui design", "user interface design"),
    "UX design": ("ux design", "user experience design"),
    "Vue.js": ("vue.js", "vuejs", "vue"),
    "Web development": ("web development",),
}

def normalize_skill(value: str) -> str:
    normalized = " ".join(value.casefold().strip().split())
    for canonical, aliases in SKILL_PATTERNS.items():
        if normalized == canonical.casefold() or normalized in {
            alias.casefold() for alias in aliases
        }:
            return canonical
    return normalized


def _phrase_pattern(phrase: str) -> re.Pattern[str]:
    if phrase.casefold() == "js":
        return re.compile(r"(?<![\w.])js(?![\w.])", re.IGNORECASE)
    if phrase.casefold() == "go":
        return re.compile(
            r"\bgolang\b|\bgo(?=\s+(?:developer|engineer|programming|language))",
            re.IGNORECASE,
        )
    flexible_phrase = r"\s+".join(re.escape(part) for part in phrase.split())
    return re.compile(rf"(?<!\w){flexible_phrase}(?!\w)", re.IGNORECASE)


def analyze_skills(
    job_description: str,
    user_skills: list[str],
    declared_requirements: list[str],
) -> dict:
    candidates: dict[str, list[str]] = {}
    for canonical, aliases in SKILL_PATTERNS.items():
        candidates[canonical] = list(dict.fromkeys((canonical, *aliases)))
    for skill in (*user_skills, *declared_requirements):
        cleaned = " ".join(skill.strip().split())
        if cleaned:
            canonical = normalize_skill(cleaned)
            candidates.setdefault(canonical, [cleaned])

    occurrences: list[tuple[int, str, int]] = []
    text_counts: Counter[str] = Counter()
    for canonical, phrases in candidates.items():
        matches_by_span = {
            (match.start(), match.end())
            for phrase in phrases
            for match in _phrase_pattern(phrase).finditer(job_description)
        }
        matches = sorted(matches_by_span)
        if matches:
            occurrences.append((matches[0][0], canonical, len(matches)))
            text_counts[canonical] = len(matches)

    found_keywords = [name for _, name, _ in sorted(occurrences)]
    for requirement in declared_requirements:
        normalized_requirement = normalize_skill(requirement)
        if normalized_requirement and normalized_requirement not in found_keywords:
            found_keywords.append(normalized_requirement)
    normalized_user_skills = {normalize_skill(skill) for skill in user_skills if skill.strip()}
    matched = [skill for skill in found_keywords if skill in normalized_user_skills]
    missing = [skill for skill in found_keywords if skill not in normalized_user_skills]

    declared = {normalize_skill(skill) for skill in declared_requirements if skill.strip()}
    important = [
        skill for skill in found_keywords
        if text_counts[skill] > 1 or skill in declared
    ]
    percentage = (
        (Decimal(len(matched)) * 100 / Decimal(len(found_keywords))).quantize(Decimal("0.01"))
        if found_keywords
        else Decimal("0.00")
    )

    learn = missing[:5]
    checklist = [
        "Tailor your summary to the role using accurate, evidence-backed experience.",
        "Use the posting's important terms naturally in relevant project or experience bullets.",
        "Support each listed skill with a concrete result, project, or example.",
    ]
    if missing:
        checklist.append(
            "Address missing skills only when you have genuine experience; otherwise plan learning instead of claiming them."
        )
    else:
        checklist.append("No recognized missing skills; prioritize role-specific evidence and measurable outcomes.")

    return {
        "job_keywords": found_keywords,
        "user_skills": list(dict.fromkeys(normalize_skill(skill) for skill in user_skills if skill.strip())),
        "matching_skills": matched,
        "missing_skills": missing,
        "important_keywords": important,
        "match_percentage": percentage,
        "suggested_skills_to_learn": learn,
        "resume_checklist": checklist,
        "algorithm_version": ALGORITHM_VERSION,
    }
