import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluate import normalize,run
class AdapterTests(unittest.TestCase):
    def test_label_only(self):self.assertEqual(normalize({'label':'todo'}),{'predicted':'todo'})
    def test_invalid_probs(self):
        with self.assertRaises(ValueError):normalize({'label':'todo','probabilities':{'urgent':0,'todo':float('nan'),'valuable':0,'noise':0}})
    def test_baseline_and_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            metrics=run(lambda req:{'label':'noise'},tmp,'constant',repeats=1,kind='baseline')
            self.assertEqual((metrics['correct'],metrics['n']),(16,64));self.assertEqual(metrics['repeat_consistency']['same_label_all_repeats'],64)
            with self.assertRaises(ValueError):run(lambda req:{'label':'noise'},tmp,'constant',1)
    def test_failures_not_dropped(self):
        with tempfile.TemporaryDirectory() as tmp:
            def broken(req):raise RuntimeError('provider is down')
            metrics=run(broken,tmp,'broken',1)
            self.assertEqual((metrics['n'],metrics['errors'],metrics['correct']),(64,64,0))
    def test_mutating_adapter_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            def bad(req):req['state'].clear();return {'label':'noise'}
            metrics=run(bad,tmp,'mutating',1)
            self.assertEqual(metrics['errors'],64)
if __name__=='__main__':unittest.main()
