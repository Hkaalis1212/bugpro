"""
Export integrations for GitHub and Jira
Allows exporting bug reports to external issue tracking systems
"""

import json
import requests
from typing import Dict, Optional, List
from datetime import datetime
import base64

class GitHubExporter:
    def __init__(self, token: str, repo_owner: str, repo_name: str):
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
    
    def export_bug_report(self, bug_report: Dict, reproducibility_score: Optional[Dict] = None) -> Dict:
        """Export bug report to GitHub as an issue"""
        
        # Format the issue body
        body = self._format_github_issue_body(bug_report, reproducibility_score)
        
        # Create labels based on reproducibility score
        labels = self._generate_github_labels(bug_report, reproducibility_score)
        
        issue_data = {
            "title": f"[Bug] {bug_report['title']}",
            "body": body,
            "labels": labels
        }
        
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues"
        
        try:
            response = requests.post(url, headers=self.headers, json=issue_data)
            response.raise_for_status()
            
            github_issue = response.json()
            
            # Upload attachments if any
            if bug_report.get('attachments'):
                self._upload_attachments_to_github(github_issue['number'], bug_report['attachments'])
            
            return {
                'success': True,
                'github_url': github_issue['html_url'],
                'issue_number': github_issue['number'],
                'message': f"Bug report exported to GitHub issue #{github_issue['number']}"
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"GitHub export failed: {str(e)}",
                'message': "Failed to export to GitHub"
            }
    
    def _format_github_issue_body(self, bug_report: Dict, reproducibility_score: Optional[Dict]) -> str:
        """Format the GitHub issue body"""
        body = f"""## Bug Description
{bug_report['description']}

## Reproduction Steps
{bug_report.get('parsed_steps', 'See description above')}

## Environment
- **Reported on:** {bug_report.get('created_at', 'Unknown')}
- **Reporter:** {bug_report.get('user_email', 'Anonymous')}

"""
        
        if reproducibility_score:
            body += f"""## Reproducibility Assessment
- **Score:** {reproducibility_score.get('score', 0):.1f}/100
- **Confidence:** {reproducibility_score.get('confidence', 'Unknown')}

### Factors Identified:
{chr(10).join('- ' + factor for factor in reproducibility_score.get('factors', []))}

### Recommendations:
{chr(10).join('- ' + rec for rec in reproducibility_score.get('recommendations', []))}

"""
        
        if bug_report.get('attachments'):
            body += f"""## Attachments
{len(bug_report['attachments'])} file(s) attached to original report.

"""
        
        body += f"""---
*This issue was automatically exported from the Bug Reporting System*
*Original Report ID: {bug_report.get('id', 'Unknown')}*"""
        
        return body
    
    def _generate_github_labels(self, bug_report: Dict, reproducibility_score: Optional[Dict]) -> List[str]:
        """Generate appropriate labels for the GitHub issue"""
        labels = ["bug", "imported"]
        
        if reproducibility_score:
            score = reproducibility_score.get('score', 0)
            confidence = reproducibility_score.get('confidence', '').lower()
            
            if score >= 80:
                labels.append("high-reproducibility")
            elif score >= 50:
                labels.append("medium-reproducibility")
            else:
                labels.append("needs-clarification")
            
            if confidence in ['high', 'very high']:
                labels.append("ready-to-reproduce")
        
        return labels
    
    def _upload_attachments_to_github(self, issue_number: int, attachments: List[Dict]):
        """Upload attachments as comments on the GitHub issue"""
        for attachment in attachments:
            comment_body = f"""### Attachment: {attachment['filename']}
**Size:** {attachment.get('file_size', 'Unknown')} bytes

```
{attachment.get('content', 'Content not available')}
```"""
            
            comment_data = {"body": comment_body}
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}/comments"
            
            try:
                requests.post(url, headers=self.headers, json=comment_data)
            except:
                pass  # Continue if attachment upload fails

class JiraExporter:
    def __init__(self, base_url: str, username: str, api_token: str, project_key: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.project_key = project_key
        self.auth = (username, api_token)
        self.headers = {"Content-Type": "application/json"}
    
    def export_bug_report(self, bug_report: Dict, reproducibility_score: Optional[Dict] = None) -> Dict:
        """Export bug report to Jira as an issue"""
        
        # Format the description
        description = self._format_jira_description(bug_report, reproducibility_score)
        
        # Determine priority based on reproducibility score
        priority = self._determine_jira_priority(reproducibility_score)
        
        issue_data = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": f"[Bug] {bug_report['title']}",
                "description": description,
                "issuetype": {"name": "Bug"},
                "priority": {"name": priority}
            }
        }
        
        # Add custom fields if reproducibility score is available
        if reproducibility_score:
            issue_data["fields"]["customfield_reproducibility_score"] = reproducibility_score.get('score', 0)
        
        url = f"{self.base_url}/rest/api/2/issue"
        
        try:
            response = requests.post(url, auth=self.auth, headers=self.headers, json=issue_data)
            response.raise_for_status()
            
            jira_issue = response.json()
            issue_key = jira_issue['key']
            
            # Upload attachments if any
            if bug_report.get('attachments'):
                self._upload_attachments_to_jira(issue_key, bug_report['attachments'])
            
            return {
                'success': True,
                'jira_url': f"{self.base_url}/browse/{issue_key}",
                'issue_key': issue_key,
                'message': f"Bug report exported to Jira issue {issue_key}"
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"Jira export failed: {str(e)}",
                'message': "Failed to export to Jira"
            }
    
    def _format_jira_description(self, bug_report: Dict, reproducibility_score: Optional[Dict]) -> str:
        """Format the Jira issue description"""
        description = f"""h2. Bug Description
{bug_report['description']}

h2. Reproduction Steps
{bug_report.get('parsed_steps', 'See description above')}

h2. Environment Information
* *Reported on:* {bug_report.get('created_at', 'Unknown')}
* *Reporter:* {bug_report.get('user_email', 'Anonymous')}

"""
        
        if reproducibility_score:
            description += f"""h2. Reproducibility Assessment
* *Score:* {reproducibility_score.get('score', 0):.1f}/100
* *Confidence:* {reproducibility_score.get('confidence', 'Unknown')}

h3. Factors Identified:
{chr(10).join('* ' + factor for factor in reproducibility_score.get('factors', []))}

h3. Recommendations:
{chr(10).join('* ' + rec for rec in reproducibility_score.get('recommendations', []))}

"""
        
        if bug_report.get('attachments'):
            description += f"""h2. Attachments
{len(bug_report['attachments'])} file(s) will be attached to this issue.

"""
        
        description += f"""----
_This issue was automatically exported from the Bug Reporting System_
_Original Report ID: {bug_report.get('id', 'Unknown')}_"""
        
        return description
    
    def _determine_jira_priority(self, reproducibility_score: Optional[Dict]) -> str:
        """Determine Jira priority based on reproducibility score"""
        if not reproducibility_score:
            return "Medium"
        
        score = reproducibility_score.get('score', 0)
        
        if score >= 80:
            return "High"
        elif score >= 60:
            return "Medium"
        elif score >= 30:
            return "Low"
        else:
            return "Lowest"
    
    def _upload_attachments_to_jira(self, issue_key: str, attachments: List[Dict]):
        """Upload attachments to the Jira issue"""
        url = f"{self.base_url}/rest/api/2/issue/{issue_key}/attachments"
        
        for attachment in attachments:
            try:
                # Create a temporary file for the attachment
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w+b', suffix=f"_{attachment['filename']}", delete=False) as temp_file:
                    # Decode base64 content if present
                    content = attachment.get('content', '')
                    if content:
                        try:
                            decoded_content = base64.b64decode(content)
                            temp_file.write(decoded_content)
                        except:
                            temp_file.write(content.encode('utf-8'))
                    
                    temp_file.flush()
                    
                    # Upload to Jira
                    files = {'file': (attachment['filename'], open(temp_file.name, 'rb'))}
                    headers = {"X-Atlassian-Token": "no-check"}
                    
                    requests.post(url, auth=self.auth, headers=headers, files=files)
                    
                    # Clean up
                    files['file'][1].close()
                    import os
                    os.unlink(temp_file.name)
                    
            except Exception as e:
                print(f"Failed to upload attachment {attachment['filename']}: {e}")

class ExportManager:
    def __init__(self):
        self.github_exporter = None
        self.jira_exporter = None
    
    def configure_github(self, token: str, repo_owner: str, repo_name: str):
        """Configure GitHub integration"""
        self.github_exporter = GitHubExporter(token, repo_owner, repo_name)
    
    def configure_jira(self, base_url: str, username: str, api_token: str, project_key: str):
        """Configure Jira integration"""
        self.jira_exporter = JiraExporter(base_url, username, api_token, project_key)
    
    def export_to_platform(self, platform: str, bug_report: Dict, reproducibility_score: Optional[Dict] = None) -> Dict:
        """Export bug report to specified platform"""
        if platform.lower() == 'github' and self.github_exporter:
            return self.github_exporter.export_bug_report(bug_report, reproducibility_score)
        elif platform.lower() == 'jira' and self.jira_exporter:
            return self.jira_exporter.export_bug_report(bug_report, reproducibility_score)
        else:
            return {
                'success': False,
                'error': f"Platform {platform} not configured or not supported",
                'message': f"Cannot export to {platform}"
            }