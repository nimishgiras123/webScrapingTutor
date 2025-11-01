"""
Configuration settings for Jira scraper
"""

JIRA_BASE_URL = "https://issues.apache.org/jira/rest/api/2"

PROJECTS = [
    "KAFKA",
    "SPARK",
    "HADOOP"
]

MAX_RESULTS_PER_PAGE = 100
MAX_RETRIES = 5
RETRY_WAIT_MIN = 2
RETRY_WAIT_MAX = 60

DATA_DIR = "data"
RAW_DATA_DIR = f"{DATA_DIR}/raw"
PROCESSED_DATA_DIR = f"{DATA_DIR}/processed"
CHECKPOINT_DIR = f"{DATA_DIR}/checkpoints"

JIRA_FIELDS = [
    "summary",
    "description",
    "status",
    "priority",
    "assignee",
    "reporter",
    "created",
    "updated",
    "resolutiondate",
    "labels",
    "comment"
]
