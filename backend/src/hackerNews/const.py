ALGOLIA_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
ALGOLIA_SEARCH_BY_DATE = "https://hn.algolia.com/api/v1/search_by_date"

import re
URL_RE = re.compile(r"(https?://[^\s)>\]]+)", re.IGNORECASE)