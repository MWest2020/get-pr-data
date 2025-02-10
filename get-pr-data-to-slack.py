#!/usr/bin/env python3

import json
import os
import requests

def get_repo_owner_and_name(repo_url):
    """
    Haalt de owner en de repo-naam op uit een GitHub URL.
    Bijvoorbeeld: https://github.com/organisatie/voorbeeldrepo1 -> ('organisatie', 'voorbeeldrepo1')
    """
    repo_url = repo_url.rstrip('/')
    parts = repo_url.split('/')
    if len(parts) < 5:
        raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
    owner = parts[-2]
    repo_name = parts[-1]
    return owner, repo_name

def get_open_prs(owner, repo_name, github_token=None):
    """
    Haalt de open pull requests op via de GitHub API.
    """
    api_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls?state=open"
    headers = {}
    if github_token:
        headers['Authorization'] = f"token {github_token}"
    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        print(f"Fout bij ophalen PR's voor {owner}/{repo_name}: {response.status_code}")
        return []
    return response.json()

def format_slack_message(pr_data):
    """
    Bouwt een bericht op met het overzicht van open pull requests per repository.
    """
    message_lines = ["*Overzicht open pull requests*"]
    for repo_name, prs in pr_data.items():
        if prs:
            message_lines.append(f"\n*{repo_name}* ({len(prs)} open):")
            for pr in prs:
                title = pr.get("title", "Geen titel")
                pr_url = pr.get("html_url", "")
                message_lines.append(f"- <{pr_url}|{title}>")
        else:
            message_lines.append(f"\n*{repo_name}*: Geen open PR's.")
    return "\n".join(message_lines)

def post_to_slack(webhook_url, message):
    """
    Verstuurd het bericht naar Slack via de webhook.
    """
    payload = {"text": message}
    response = requests.post(webhook_url, json=payload)
    if response.status_code != 200:
        print(f"Fout bij verzenden naar Slack: {response.status_code}, {response.text}")
    else:
        print("Bericht succesvol verzonden naar Slack.")

def main():
    # Laad de configuratie van de repositories uit repos.json
    config_path = os.path.join(os.path.dirname(__file__), 'repos.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    repos = config.get("repos", [])
    if not repos:
        print("Geen repositories gevonden in configuratie.")
        return

    # Optioneel: gebruik een GitHub-token voor geauthenticeerde API-aanvragen
    github_token = os.environ.get("GITHUB_TOKEN", None)
    # Slack-webhook URL moet worden ingesteld als environment variable
    slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not slack_webhook_url:
        print("SLACK_WEBHOOK_URL is niet ingesteld.")
        return

    pr_data = {}
    for repo in repos:
        name = repo.get("name")
        url = repo.get("url")
        if not name or not url:
            print("Ongeldige repository configuratie, sla over.")
            continue
        try:
            owner, repo_name = get_repo_owner_and_name(url)
        except ValueError as e:
            print(e)
            continue
        
        prs = get_open_prs(owner, repo_name, github_token)
        pr_data[name] = prs

    slack_message = format_slack_message(pr_data)
    post_to_slack(slack_webhook_url, slack_message)

if __name__ == "__main__":
    main()
