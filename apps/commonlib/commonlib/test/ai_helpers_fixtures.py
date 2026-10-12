"""Parametrize tables and helpers shared by ai_helpers_test."""

LISTS_TO_STRING_CASES = [
    ("Java (Spring, Hibernate)", "Java,Spring,Hibernate"),
    ("React (Hooks, Context), Node.js (Express)", "React,Hooks,Context,Node.js,Express"),
    ("Cloud (AWS (EC2, S3), Azure)", "Cloud,AWS,EC2,S3,Azure"),
    ("No parentheses here", "No parentheses here"),
    ("JS (React.js, Vue.js, Node-RED)", "JS,React.js,Vue.js,Node-RED"),
    ("C# (.NET Core, ASP.NET)", "C#,.NET Core,ASP.NET"),
    ("C# (.NET Core,, ASP.NET, ,  ASP.NET)", "C#,.NET Core,ASP.NET"),
    ("None specified", None),
    ("null", None),
    ("Null", None),
]

FLATTEN_STRING_CASES = [
    ("Java,Spring Boot,AWS (RDS, Cognito, ECS),Observability (Grafana, Sentry)",
     ["Java", "Spring Boot", "AWS", "RDS", "Cognito", "ECS", "Observability", "Grafana", "Sentry"]),
    ("Cloud (AWS (EC2, S3), Azure)", ["Cloud", "AWS", "EC2", "S3", "Azure"]),
    ("No parentheses here", ["No parentheses here"]),
    ("Java,Java,AWS (EC2, S3)", ["Java", "AWS", "EC2", "S3"]),
]

FLATTEN_LIST_CASES = [
    (["AWS (RDS, Cognito)", "Java", "Observability (Grafana, Sentry)"],
     ["AWS", "RDS", "Cognito", "Java", "Observability", "Grafana", "Sentry"]),
    (["Cloud (AWS (EC2, S3), Azure)", "Java"], ["Cloud", "AWS", "EC2", "S3", "Azure", "Java"]),
    (["Java", None, "AWS (EC2, S3)", "AWS (EC2, S3)"], ["Java", "AWS", "EC2", "S3"]),
    ([], []),
]

SALARY_CASES = [
    ({"salary": "Competitive String with no numbers"}, None),
    ({"salary": "50k-60k"}, "50k-60k"),
    ({"salary": {"min": 50, "max": 60}}, "50-60"),
    ({"salary": {"amount": 70}}, "70"),
    ({"salary": {"other": "value"}}, None),
    ({"salary": "Sueldo: 50k"}, "50k"),
]

CV_MATCH_CASES = [
    ({"cv_match_percentage": "85"}, "85"),
    ({"cv_match_percentage": "105"}, None),
    ({"cv_match_percentage": "high"}, None),
]

MAP_JOB_CASES = [(b"Markdown", "Markdown\n"), ("MarkdownStr", "MarkdownStr\n")]

MODALITY_CASES = [
    ("REMOTE", "REMOTE"), ("remote", "REMOTE"), ("Hybrid", "HYBRID"),
    ("ON_SITE", "ON_SITE"), ("invalid", None), (None, None), ("", None),
]

EXPAND_CASES = [
    ("Java (Spring, Hibernate)", "Java, Spring, Hibernate"),
    ("React (Hooks, Context), Node.js (Express)", "React, Hooks, Context, Node.js, Express"),
    ("Cloud (AWS (EC2, S3), Azure)", "Cloud, AWS, EC2, S3, Azure"),
    ("No parentheses here", "No parentheses here"),
    ("JS (React.js, Vue.js, Node-RED)", "JS, React.js, Vue.js, Node-RED"),
    ("C# (.NET Core, ASP.NET)", "C#, .NET Core, ASP.NET"),
    ("C# (.NET Core,, ASP.NET, ,  ASP.NET)", "C#, .NET Core, ASP.NET, ASP.NET"),
]

FOOTER_ERROR_CASES = [(set(), 0), ({"error1"}, 1)]

FOOTER_JOB_ELAPSED_CASES = [
    (1668.0, "Time elapsed: 41s (Media: 40s/job)", {"elapsed": "27m 48s", "elapsed_per_job": "40s"}),
    (None, "Time elapsed: 41s", None),
]

LOG_IDLE_TERMINAL_CASES = [
    ("jobs.skipped", "no_pending_jobs"),
    ("ai.retry_wait", "backend_unavailable"),
    ("jobs.skipped", "no_pending_skills"),
]


def completed(records):
    return [r for r in records if r["event"] == "ai.batch_completed"][0]
