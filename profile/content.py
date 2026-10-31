"""Single source of truth for everything written on the profile.

Edit this file, run ``python profile/build.py`` and commit the regenerated
``assets/``. The README only arranges the images; the words live here.
"""

NAME = "Tony Tabwa"
LOGIN = "ProlificTMontana"
ROLES = ("Penetration Tester", "Full-Stack Engineer")
LOCATION = "Pretoria, South Africa"
STATUS = "OPEN TO ENGAGEMENTS & COLLABORATION"

TAGLINES = (
    "breaking systems to make them stronger.",
    "recon → exploit → report → remediate.",
    "shipping secure SaaS from Pretoria to the world.",
)

LINKS = {
    "portfolio": ("Portfolio", "https://tony-github-io.vercel.app"),
    "company": ("Tony Link Technologies", "https://tonylinktech.co.za"),
    "linkedin": ("LinkedIn", "https://www.linkedin.com/in/tony-tabwa-7145b0140"),
    "email": ("Email", "mailto:tabwatony7@gmail.com"),
}

# neofetch-style profile ------------------------------------------------------
FETCH = (
    ("Role", "Penetration Tester · Full-Stack Engineer"),
    ("Location", "Pretoria, South Africa"),
    ("Company", "Tony Link Technologies"),
    ("Focus", "Red teaming · Secure SaaS · Security automation"),
    ("Learning", "Blue teaming · Digital forensics · DevSecOps"),
    ("Certs", "Cisco Ethical Hacker · Junior Cybersecurity Analyst"),
    ("", "Blue Team Junior Analyst Pathway"),
    ("Education", "National Diploma in Information Technology"),
    ("Training", "TryHackMe · freeCodeCamp"),
    ("Mindset", "Prevent, don't just patch."),
)

# Toolchain: (label, simple-icons slug or None, monogram fallback) -------------
ARSENAL = (
    ("Offensive Security", (
        ("Kali Linux", "kalilinux", None),
        ("Metasploit", "metasploit", None),
        ("Burp Suite", "burpsuite", None),
        ("Nmap", None, "Nm"),
        ("Wireshark", "wireshark", None),
        ("OWASP", "owasp", None),
        ("MITRE ATT&CK", None, "AT"),
        ("NIST CSF", None, "NI"),
        ("TryHackMe", "tryhackme", None),
    )),
    ("Frontend", (
        ("React", "react", None),
        ("Next.js", "nextdotjs", None),
        ("React Native", "react", None),
        ("TypeScript", "typescript", None),
        ("JavaScript", "javascript", None),
        ("Tailwind CSS", "tailwindcss", None),
        ("HTML5", "html5", None),
        ("CSS", "css", None),
    )),
    ("Backend & Data", (
        ("Node.js", "nodedotjs", None),
        ("FastAPI", "fastapi", None),
        ("PHP", "php", None),
        ("Supabase", "supabase", None),
        ("Firebase", "firebase", None),
        ("PostgreSQL", "postgresql", None),
        ("Redis", "redis", None),
        ("Celery", "celery", None),
    )),
    ("Cloud & DevOps", (
        ("Docker", "docker", None),
        ("GitHub Actions", "githubactions", None),
        ("Git", "git", None),
        ("Vercel", "vercel", None),
        ("Linux", "linux", None),
        ("Azure AD", None, "Az"),
        ("Microsoft 365", None, "M"),
    )),
    ("Languages", (
        ("Python", "python", None),
        ("TypeScript", "typescript", None),
        ("Java", "openjdk", None),
        ("C++", "cplusplus", None),
        ("C#", None, "C#"),
        ("VB.NET", "dotnet", None),
        ("Bash", "gnubash", None),
    )),
)

# Featured work -----------------------------------------------------------------
# accent: one of primary | neon | soft (see THEMES in design.py)
PROJECTS = (
    {
        "slug": "accrediq",
        "mark": "AQ",
        "name": "AccredIQ",
        "kind": "SaaS · Compliance",
        "status": "LIVE",
        "accent": "primary",
        "desc": (
            "Compliance system of record for QCTO-accredited skills providers: accreditation scope, "
            "staff credentials, assessment, moderation and certification in one auditable, multi-tenant platform."
        ),
        "stack": ("Next.js", "TypeScript", "Supabase", "RLS"),
        "url": "https://accrediq.co.za",
        "label": "accrediq.co.za",
    },
    {
        "slug": "red-team-toolkit",
        "mark": "RT",
        "name": "Red Team Automation Toolkit",
        "kind": "Offensive Tooling",
        "status": "OPEN SOURCE",
        "accent": "neon",
        "desc": (
            "Operator platform for automating red team ops: CIDR scope enforcement, async Nmap recon "
            "with findings extraction, role-based access and OPSEC-safe audit logging."
        ),
        "stack": ("FastAPI", "Celery", "Redis", "Next.js", "Docker"),
        "url": "https://github.com/ProlificTMontana/red_team_automation_toolkit",
        "label": "github.com/…/red_team_automation_toolkit",
    },
    {
        "slug": "osint",
        "mark": "OS",
        "name": "OSINT Automation Tool",
        "kind": "Reconnaissance",
        "status": "OPEN SOURCE",
        "accent": "neon",
        "desc": (
            "Plugin-driven OSINT recon: Shodan host intelligence, HaveIBeenPwned breach checks and "
            "username enumeration across major social platforms, in a single Streamlit console."
        ),
        "stack": ("Python", "Streamlit", "Shodan API", "HIBP API"),
        "url": "https://github.com/ProlificTMontana/OSINT-Automation-Tool",
        "label": "github.com/…/OSINT-Automation-Tool",
    },
    {
        "slug": "autoreserve",
        "mark": "AR",
        "name": "AutoReserve Africa",
        "kind": "Marketplace · Cross-border",
        "status": "LIVE",
        "accent": "primary",
        "desc": (
            "Vehicle reservation and export marketplace connecting verified South African dealers with "
            "buyers in Zimbabwe, Zambia, Namibia, Botswana and beyond."
        ),
        "stack": ("Next.js", "TypeScript", "Supabase"),
        "url": "https://autoreserve-africa.com",
        "label": "autoreserve-africa.com",
    },
)

# Career progression, oldest → newest -------------------------------------------
EXPERIENCE = (
    {
        "role": "I.T Support Intern",
        "tag": "Foundations",
        "summary": "First-line support for 100+ users. Microsoft 365 and Azure AD administration, firewall rules, network segmentation and Wi-Fi hardening.",
        "bullets": (
            "Provided first-line technical support to over 100 users, ensuring minimal downtime.",
            "Managed Microsoft 365 and Azure AD accounts, streamlining user access and security.",
            "Configured firewalls, implemented network segmentation, and enhanced Wi-Fi security protocols.",
        ),
    },
    {
        "role": "Red Team Intern",
        "tag": "Offense",
        "summary": "Simulated cyber-attacks to surface weaknesses, analysed traffic with Wireshark and co-authored remediation plans with defenders.",
        "bullets": (
            "Conducted simulated cyber-attacks to identify and fortify system vulnerabilities.",
            "Performed network traffic analysis using tools like Wireshark to detect and patch security gaps.",
            "Collaborated with teams to develop and implement security remediation plans.",
        ),
    },
    {
        "role": "Freelance Tech Admin & Web Developer",
        "tag": "Independent",
        "summary": "Ran Microsoft 365 for small businesses, delivered remote IT support and shipped secure web apps through CI/CD.",
        "bullets": (
            "Administered Microsoft 365 environments for small businesses, optimizing workflows and security.",
            "Delivered remote IT support, resolving issues efficiently for diverse clients.",
            "Designed and deployed secure web applications using modern CI/CD pipelines and Git for version control.",
        ),
    },
    {
        "role": "Full-Stack Engineer",
        "tag": "Product",
        "summary": "Building and deploying full-stack platforms for businesses with hardened CI/CD and Microsoft 365 API integrations.",
        "bullets": (
            "Implemented CI/CD pipelines with Git for version control in secure web app deployments, streamlining development cycles and reducing downtime.",
            "Developed and deployed full-stack web applications for small businesses, integrating Microsoft 365 APIs to optimize workflows and enhance data security.",
        ),
    },
)

IMPACT = (
    ("100+", "users supported with", "minimal downtime"),
    ("−30%", "IT resolution time", "via task automation"),
    ("+20%", "operational efficiency", "for an SMB client"),
)

OPEN_TO = (
    "Open-source security & web projects",
    "Penetration testing engagements",
    "Secure full-stack builds",
)

QUOTE = (
    "Cybersecurity is more than a job — it's a mindset.",
    "I don't just solve problems, I prevent them.",
)
