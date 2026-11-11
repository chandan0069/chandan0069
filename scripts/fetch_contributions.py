#!/usr/bin/env python3
"""Fetch the last year of contributions + pinned repos into data/contributions.json.

Uses GITHUB_TOKEN (set automatically in Actions) or, locally, `gh auth token`.
"""
import json
import os
import subprocess
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

USER = os.getenv("PROFILE_USER", "chandan0069")
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    repositories(privacy: PUBLIC, ownerAffiliations: OWNER) { totalCount }
    pinnedItems(first: 6, types: REPOSITORY) {
      nodes { ... on Repository {
        name description url stargazerCount
        primaryLanguage { name }
      } }
    }
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def token() -> str:
    t = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if t:
        return t
    return subprocess.check_output(["gh", "auth", "token"], text=True).strip()


def main():
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=364)
    body = json.dumps({"query": QUERY, "variables": {
        "login": USER,
        "from": start.strftime("%Y-%m-%dT00:00:00Z"),
        "to": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {token()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise SystemExit(f"GraphQL error: {payload['errors']}")
    u = payload["data"]["user"]
    cal = u["contributionsCollection"]["contributionCalendar"]
    days = [{"date": d["date"], "count": d["contributionCount"]}
            for w in cal["weeks"] for d in w["contributionDays"]]
    repos = [{
        "name": n["name"], "description": n["description"] or "", "url": n["url"],
        "stars": n["stargazerCount"],
        "language": (n["primaryLanguage"] or {}).get("name", ""),
    } for n in u["pinnedItems"]["nodes"]]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "username": USER,
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_contributions": cal["totalContributions"],
        "public_repos": u["repositories"]["totalCount"],
        "days": days,
        "repos": repos,
    }, indent=1))
    print(f"✅ {len(days)} days, {cal['totalContributions']} contributions, {len(repos)} pinned repos")


if __name__ == "__main__":
    main()
