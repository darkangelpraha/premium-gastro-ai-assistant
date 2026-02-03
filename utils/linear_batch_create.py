#!/usr/bin/env python3
"""
LINEAR_BATCH_CREATE - Create predefined Linear issues for two projects.
This script reads LINEAR_API_KEY from env and creates tasks for the specified projects.
"""
import os
from typing import Dict, List, Optional
import requests

URL = "https://api.linear.app/graphql"
API_KEY = os.getenv("LINEAR_API_KEY")
if not API_KEY:
    raise SystemExit("LINEAR_API_KEY environment variable is required.")

HEADERS = {"Content-Type": "application/json", "Authorization": API_KEY}

PROJECT_1_ID = "9bc140496890"
PROJECT_2_ID = "f51773eb645a"

tasks1 = [
    {"t": "Reset hesla u účtu 'kolega'", "p": 1},
    {"t": "Audit admin práv v Analytics/Ads (přidat Petra)", "p": 1},
    {"t": "Snížit počet seats v Missive", "p": 1},
    {"t": "Spustit Google DMS (kolega -> petr, last 1yr)", "p": 2},
    {"t": "Ověřit migraci (Label v Gmailu)", "p": 2},
    {"t": "Smazat uživatele 'kolega' + Transfer Drive/Calendar", "p": 3},
    {"t": "Vytvořit alias 'kolega@' u Petra", "p": 3},
    {"t": "Setup 'Send-As' v Gmailu", "p": 3},
    {"t": "Reconnect Missive jako aliasy", "p": 4},
    {"t": "Vytvořit Label 'Účtárna' v Missive", "p": 4},
    {"t": "Pozvat účetní jako Guest + sdílet Label", "p": 4},
]

tasks2 = [
    {"t": "Notion: Vytvořit Invoice Master DB (DUZP, účetní kódy)", "p": 1},
    {"t": "Notion: Propojit s Suppliers + Tech Stack (cross-workspace)", "p": 1},
    {"t": "Notion: View 'By Month' (podle DUZP)", "p": 1},
    {"t": "n8n: Analýza emailu (Příloha/Link/Text)", "p": 2},
    {"t": "n8n: Přejmenování (YYYY-MM-DD_Supplier_Subject)", "p": 2},
    {"t": "n8n: Upload GDrive (2025/MM struktura)", "p": 2},
    {"t": "Dry Run (10 emailů)", "p": 3},
    {"t": "Handover účetní", "p": 3},
]

def gql(query: str, variables: Optional[Dict] = None) -> Dict:
    response = requests.post(URL, headers=HEADERS, json={"query": query, "variables": variables})
    response.raise_for_status()
    data = response.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]

def project_uuid(project_id: str) -> Dict[str, str]:
    data = gql("query($pid: String!) { project(id: $pid) { id name } }", {"pid": project_id})
    proj = data.get("project")
    if not proj:
        raise RuntimeError(f"Project {project_id} not found")
    return {"id": proj.get("id", project_id), "name": proj.get("name", project_id)}

def first_team(project_id: str) -> str:
    data = gql("query($pid: String!) { project(id: $pid) { teams { nodes { id name } } } }", {"pid": project_id})
    teams = data["project"]["teams"]["nodes"]
    if not teams:
        raise RuntimeError(f"No teams for project {project_id}")
    return teams[0]["id"]

def create_tasks(pid: str, tid: str, tasks: List[Dict[str, str]]):
    mutation = "mutation($i: IssueCreateInput!) { issueCreate(input: $i) { issue { id title identifier } } }"
    for task in tasks:
        res = gql(mutation, {"i": {"teamId": tid, "projectId": pid, "title": task["t"], "priority": task["p"]}})
        issue = res["issueCreate"]["issue"]
        print(f"Created {issue.get('identifier')} :: {issue.get('title')}")

def main():
    p1 = project_uuid(PROJECT_1_ID)
    p2 = project_uuid(PROJECT_2_ID)
    t1 = first_team(p1["id"])
    t2 = first_team(p2["id"])
    print(f"Creating tasks in project {p1['name']} ({PROJECT_1_ID}) / team {t1}")
    create_tasks(p1["id"], t1, tasks1)
    print(f"Creating tasks in project {p2['name']} ({PROJECT_2_ID}) / team {t2}")
    create_tasks(p2["id"], t2, tasks2)
    print("Done.")

if __name__ == "__main__":
    main()
