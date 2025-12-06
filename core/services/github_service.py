"""
GitHub API service with caching.
Fetches user profile and repository statistics.
"""
import logging

import httpx
from django.core.cache import cache

logger = logging.getLogger(__name__)

GITHUB_API_BASE: str = "https://api.github.com"
CACHE_TIMEOUT: int = 3600  # 1 hour


def get_github_stats(username: str = "mkofoed") -> dict | None:
    """
    Fetch GitHub user stats with caching.
    Returns None if API call fails.
    """
    cache_key = f"github_stats_{username}"
    cached_data = cache.get(cache_key)
    
    if cached_data is not None:
        return cached_data
    
    try:
        with httpx.Client(timeout=10.0) as client:
            # Fetch user profile
            user_response = client.get(
                f"{GITHUB_API_BASE}/users/{username}",
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            user_response.raise_for_status()
            user_data = user_response.json()
            
            # Fetch repositories
            repos_response = client.get(
                f"{GITHUB_API_BASE}/users/{username}/repos",
                params={"per_page": 100, "sort": "updated"},
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            repos_response.raise_for_status()
            repos_data = repos_response.json()
        
        # Calculate stats
        total_stars = sum(repo.get("stargazers_count", 0) for repo in repos_data)
        total_forks = sum(repo.get("forks_count", 0) for repo in repos_data)
        
        # Count languages
        languages = {}
        for repo in repos_data:
            lang = repo.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
        
        # Sort languages by count
        top_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
        
        stats = {
            "username": username,
            "name": user_data.get("name", username),
            "avatar_url": user_data.get("avatar_url"),
            "bio": user_data.get("bio"),
            "public_repos": user_data.get("public_repos", 0),
            "followers": user_data.get("followers", 0),
            "following": user_data.get("following", 0),
            "total_stars": total_stars,
            "total_forks": total_forks,
            "top_languages": top_languages,
            "profile_url": f"https://github.com/{username}",
        }
        
        # Cache the result
        cache.set(cache_key, stats, CACHE_TIMEOUT)
        
        return stats
        
    except httpx.HTTPError as e:
        logger.warning(f"Failed to fetch GitHub stats: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching GitHub stats: {e}")
        return None
