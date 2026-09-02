from miner.core import uses_github_agentic_workflows

def test_uses_gh_aw():
    # report.md + report.lock.yml -> utiliza GH-AW
    assert uses_github_agentic_workflows(["report.md", "report.lock.yml"]) is True
    
    # report.md solamente -> no utiliza GH-AW
    assert uses_github_agentic_workflows(["report.md"]) is False
    
    # report.lock.yml solamente -> no utiliza GH-AW
    assert uses_github_agentic_workflows(["report.lock.yml"]) is False
    
    # report.md + other.lock.yml -> no utiliza GH-AW
    assert uses_github_agentic_workflows(["report.md", "other.lock.yml"]) is False
    
    # Empty list
    assert uses_github_agentic_workflows([]) is False
    
    # Complex case with multiple files
    assert uses_github_agentic_workflows(["README.md", "script.py", "workflow.md", "workflow.lock.yml", "test.md"]) is True
    assert uses_github_agentic_workflows(["workflow.md", "test.lock.yml"]) is False
