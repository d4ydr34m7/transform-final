import os
import requests

GITHUB_API = "https://api.github.com"


def list_user_repos():
    token = os.environ.get("GITHUB_TOKEN")
    user = os.environ.get("GITHUB_USER")

    if not token or not user:
        raise RuntimeError("GITHUB_TOKEN or GITHUB_USER not set")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    repos = []
    page = 1

    while True:
        resp = requests.get(
            f"{GITHUB_API}/users/{user}/repos",
            headers=headers,
            params={"per_page": 100, "page": page},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        if not data:
            break

        for r in data:
            repos.append(
                {
                    "full_name": r["full_name"],  # user/repo
                    "private": r["private"],
                }
            )

        page += 1

    return repos
