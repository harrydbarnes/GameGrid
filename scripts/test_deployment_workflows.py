#!/usr/bin/env python3
"""Contract tests for the split catalogue and Pages deployment workflows."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DeploymentWorkflowTests(unittest.TestCase):
    def read(self, name):
        return (ROOT / '.github' / 'workflows' / name).read_text(encoding='utf-8')

    def test_catalogue_workflow_publishes_a_retained_bundle(self):
        source = self.read('catalogue.yml')
        for required in (
            "schedule:",
            "workflow_dispatch:",
            "build_catalog_v3.py",
            "enrich_covers.py",
            "validate_catalog.py",
            "actions/upload-artifact@v4",
            "name: gamegrid-catalogue",
            "retention-days: 90",
        ):
            self.assertIn(required, source)

    def test_pages_workflow_reuses_catalogue_artifact(self):
        source = self.read('pages.yml')
        for required in (
            "workflow_run:",
            "Publish GameGrid catalogue",
            "actions/download-artifact@v4",
            "name: gamegrid-catalogue",
            "run-id:",
            "actions: read",
            "- '*.js'",
        ):
            self.assertIn(required, source)
        self.assertNotIn('build_catalog_v3.py', source)
        self.assertNotIn('enrich_covers.py', source)
        self.assertNotIn('schedule:', source)


if __name__ == '__main__':
    unittest.main()
