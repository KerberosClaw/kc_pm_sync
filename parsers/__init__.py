# Parsers per platform live as sibling modules (azure, redmine, jira, ...).
# Import directly from the module you need, e.g.:
#     from parsers.azure import parse_azure
#
# No re-export here — keeps platforms symmetric (no privileged default).
