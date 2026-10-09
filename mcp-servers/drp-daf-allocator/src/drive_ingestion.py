from __future__ import annotations
class WorkspaceFetcher:
    def fetch(self, workspace=None):
        workspace = workspace or {"documents": [], "ledger": [], "proposals": []}
        return workspace
