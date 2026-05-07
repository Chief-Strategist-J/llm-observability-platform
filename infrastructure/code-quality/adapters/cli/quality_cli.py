import click
import json
from typing import Optional

from application.analysis.trigger_analysis_use_case import TriggerAnalysisUseCase
from application.analysis.check_analysis_status_use_case import CheckAnalysisStatusUseCase
from application.projects.create_project_use_case import CreateProjectUseCase
from application.reporting.generate_quality_report_use_case import GenerateQualityReportUseCase


class QualityCLI:
    
    def __init__(
        self,
        trigger_analysis_use_case: TriggerAnalysisUseCase,
        check_analysis_status_use_case: CheckAnalysisStatusUseCase,
        create_project_use_case: CreateProjectUseCase,
        generate_quality_report_use_case: GenerateQualityReportUseCase
    ):
        self.trigger_analysis_use_case = trigger_analysis_use_case
        self.check_analysis_status_use_case = check_analysis_status_use_case
        self.create_project_use_case = create_project_use_case
        self.generate_quality_report_use_case = generate_quality_report_use_case

    def create_cli(self):
        @click.group()
        def quality():
            """Code Quality Management CLI"""
            pass

        @quality.command()
        @click.argument('project_key')
        @click.argument('name')
        @click.option('--description', default='', help='Project description')
        @click.option('--languages', required=True, help='Comma-separated list of languages')
        def create_project(project_key: str, name: str, description: str, languages: str):
            """Create a new project for code quality analysis"""
            try:
                language_list = [lang.strip() for lang in languages.split(',')]
                project = self.create_project_use_case.execute(project_key, name, description, language_list)
                
                click.echo(f"✅ Project created successfully!")
                click.echo(f"   Key: {project.key}")
                click.echo(f"   Name: {project.name}")
                click.echo(f"   Languages: {', '.join(project.languages)}")
                
            except Exception as e:
                click.echo(f"❌ Error: {str(e)}", err=True)

        @quality.command()
        @click.argument('project_key')
        @click.argument('branch')
        @click.argument('commit_hash')
        def trigger(project_key: str, branch: str, commit_hash: str):
            """Trigger code analysis for a project"""
            try:
                analysis_id = self.trigger_analysis_use_case.execute(project_key, branch, commit_hash)
                
                click.echo(f"✅ Analysis triggered successfully!")
                click.echo(f"   Analysis ID: {analysis_id}")
                click.echo(f"   Project: {project_key}")
                click.echo(f"   Branch: {branch}")
                click.echo(f"   Commit: {commit_hash}")
                
            except Exception as e:
                click.echo(f"❌ Error: {str(e)}", err=True)

        @quality.command()
        @click.argument('analysis_id')
        def status(analysis_id: str):
            """Check the status of an analysis"""
            try:
                analysis = self.check_analysis_status_use_case.execute(analysis_id)
                summary = self.check_analysis_status_use_case.get_analysis_summary(analysis_id)
                quality_score = self.check_analysis_status_use_case.get_quality_score(analysis_id)
                ready_for_merge = self.check_analysis_status_use_case.is_analysis_ready_for_merge(analysis_id)
                
                click.echo(f"📊 Analysis Status: {analysis.status.value}")
                click.echo(f"   Project: {analysis.project_key}")
                click.echo(f"   Branch: {analysis.branch}")
                click.echo(f"   Summary: {summary}")
                click.echo(f"   Quality Score: {quality_score}/100")
                click.echo(f"   Ready for Merge: {'✅' if ready_for_merge else '❌'}")
                
                if analysis.status.value == 'completed':
                    click.echo(f"   Completed: {analysis.completed_at}")
                    
            except Exception as e:
                click.echo(f"❌ Error: {str(e)}", err=True)

        @quality.command()
        @click.argument('analysis_id')
        @click.option('--format', default='table', type=click.Choice(['table', 'json']))
        def issues(analysis_id: str, format: str):
            """Get issues from an analysis"""
            try:
                analysis = self.check_analysis_status_use_case.execute(analysis_id)
                
                if format == 'json':
                    issues_data = []
                    for issue in analysis.issues:
                        issues_data.append({
                            'key': issue.key,
                            'type': issue.type.value,
                            'severity': issue.severity.value,
                            'message': issue.message,
                            'file_path': issue.file_path,
                            'line_number': issue.line_number,
                            'rule': issue.rule
                        })
                    click.echo(json.dumps(issues_data, indent=2))
                else:
                    click.echo(f"🐛 Issues for Analysis {analysis_id}")
                    click.echo("-" * 50)
                    
                    if not analysis.issues:
                        click.echo("✅ No issues found!")
                    else:
                        for issue in analysis.issues:
                            status_icon = "🔴" if issue.is_blocking() else "🟡" if issue.severity.value == 'major' else "🔵"
                            security_icon = "🔒" if issue.is_security_related() else ""
                            
                            click.echo(f"{status_icon} {issue.severity.value.upper()} {issue.type.value.upper()} {security_icon}")
                            click.echo(f"   File: {issue.file_path}:{issue.line_number}")
                            click.echo(f"   Rule: {issue.rule}")
                            click.echo(f"   Message: {issue.message}")
                            click.echo()
                    
            except Exception as e:
                click.echo(f"❌ Error: {str(e)}", err=True)

        @quality.command()
        @click.argument('project_key')
        @click.option('--days', default=30, help='Number of days for the report')
        @click.option('--format', default='table', type=click.Choice(['table', 'json']))
        def report(project_key: str, days: int, format: str):
            """Generate quality report for a project"""
            try:
                report_data = self.generate_quality_report_use_case.execute(project_key, days)
                
                if format == 'json':
                    click.echo(json.dumps(report_data, indent=2))
                else:
                    self._print_report_table(report_data)
                    
            except Exception as e:
                click.echo(f"❌ Error: {str(e)}", err=True)

        def _print_report_table(self, report: dict):
            click.echo(f"📈 Quality Report for {report['project']['name']}")
            click.echo("=" * 60)
            
            summary = report['summary']
            click.echo(f"📊 Summary (Last {report['period']['days']} days)")
            click.echo(f"   Total Analyses: {summary['total_analyses']}")
            click.echo(f"   Successful: {summary['successful_analyses']}")
            click.echo(f"   Failed: {summary['failed_analyses']}")
            click.echo(f"   Average Quality Score: {summary['average_quality_score']}/100")
            
            trends = report['trends']
            if trends.get('trend') != 'insufficient_data':
                trend_icon = "📈" if trends['trend'] == 'improving' else "📉" if trends['trend'] == 'declining' else "➡️"
                click.echo(f"   Trend: {trend_icon} {trends['trend'].title()} ({trends['score_change']:+.1f})")
            
            quality_metrics = report['quality_metrics']
            if quality_metrics:
                click.echo(f"\n🔍 Quality Metrics")
                click.echo(f"   Total Issues: {quality_metrics['total_issues']}")
                click.echo(f"   Critical Issues: {quality_metrics['critical_issues']}")
                click.echo(f"   Security Issues: {quality_metrics['security_issues']}")
                click.echo(f"   Average Coverage: {quality_metrics['average_coverage']}%")
            
            security = report['security_analysis']
            if security.get('requires_immediate_attention'):
                click.echo(f"\n🚨 Security Alert")
                click.echo(f"   High-risk vulnerabilities: {security['high_risk_vulnerabilities']}")
            
            recommendations = report['recommendations']
            if recommendations:
                click.echo(f"\n💡 Recommendations")
                for i, rec in enumerate(recommendations, 1):
                    click.echo(f"   {i}. {rec}")

        return quality
