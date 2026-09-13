"""The evidence-access audit is reproducible and does not fabricate model runs."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'analyses/scenario-1/graph-access'
spec=importlib.util.spec_from_file_location('graph_access',HERE/'run_analysis.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
spec=importlib.util.spec_from_file_location('graph_access_verifier',HERE/'verify_runs.py')
verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)


class GraphAccessTests(unittest.TestCase):
    def test_fresh_audit_and_archived_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)/'audit'
            result=audit.run(ROOT,directory,'fixture')
            self.assertEqual(result['model_calls'],0)
            self.assertTrue(result['evidence_equivalence_checked'])
            self.assertEqual(len(result['metrics']),6)
            self.assertEqual({m['distinct_offers'] for m in result['metrics']},{177,140})
            self.assertEqual(verifier.verify(directory),{'status':'verified','model_calls':0,'query_count':27})
            self.assertFalse((directory/'outcome.json').exists())
            with self.assertRaisesRegex(ValueError,'Output exists'):
                audit.run(ROOT,directory,'fixture')


if __name__=='__main__':unittest.main()
