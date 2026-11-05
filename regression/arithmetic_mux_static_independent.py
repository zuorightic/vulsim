"""New independent P4 admission is gated by validated frozen static choices."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse.model_m2_mux_static_tests import prepare


class StaticIndependentGate(unittest.TestCase):
    def test_failed_validation_rejected_before_folder_or_measurement(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'not-created'
            with patch('experiments.arithmetic_dse.model_m2_mux_collection.verify',return_value={}), \
                 patch('experiments.arithmetic_dse.model_m2_mux_static_fit.verify_fit',return_value={'grt_validation_ready':False}):
                with self.assertRaisesRegex(ValueError,'validation freeze'):prepare(Path(td),Path('/selection'),target)
            self.assertFalse(target.exists())
    def test_wrong_collection_rejected_before_folder_or_measurement(self):
        with tempfile.TemporaryDirectory() as td:
            parent=Path(td);(parent/'admission.json').write_text('{}');target=parent/'not-created'
            with patch('experiments.arithmetic_dse.model_m2_mux_collection.verify',return_value={}), \
                 patch('experiments.arithmetic_dse.model_m2_mux_static_fit.verify_fit',return_value={'grt_validation_ready':True,'collection_admission_sha256':'changed'}):
                with self.assertRaisesRegex(ValueError,'validation freeze'):prepare(parent,Path('/selection'),target)
            self.assertFalse(target.exists())


if __name__=='__main__':unittest.main()
