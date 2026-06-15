import re

with open('README.md', 'r', encoding='utf-8') as f:
    readme = f.read()

with open('WorkFlow.md', 'r', encoding='utf-8') as f:
    workflow = f.read()

# Extract from Phase 0 onwards in WorkFlow.md
match = re.search(r'(## Phase 0:.*)', workflow, re.DOTALL)
if match:
    workflow_content = match.group(1)
    
    # Replace the short section in README.md
    readme_new = re.sub(
        r'## Live demo workflow and screenshots\n\nSee \[WorkFlow\.md\]\(WorkFlow\.md\) for the full live demo walkthrough and \[docs/demo_captures/\]\(docs/demo_captures/\) for captured screenshots\.',
        '## Live demo workflow\n\n' + workflow_content,
        readme
    )
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_new)
    print("Successfully added workflow to README.md")
else:
    print("Could not find Phase 0 in WorkFlow.md")
