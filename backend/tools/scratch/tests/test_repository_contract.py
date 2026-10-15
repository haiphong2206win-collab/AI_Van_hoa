"""Verify the adapter against the real backend settings, ABC and error handler."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.ai.base import BaseVIVQAModel
from app.ai.scratch_model import ScratchVIVQAModel
from app.config import Settings
from app.errors import AppError
from app.main import create_app


class RepositoryContractTests(unittest.TestCase):
    def test_reads_shared_dotenv_and_base_interface(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / 'scratch.env'
            env.write_text('AI_DEVICE=cpu\nSCRATCH_MODEL_PATH=custom/scratch\n')
            settings = Settings(_env_file=env)
            with patch('app.ai.scratch_model.get_settings',return_value=settings):
                model = ScratchVIVQAModel()
            self.assertIsInstance(model,BaseVIVQAModel)
            self.assertEqual(model.model_path,settings.resolved_scratch_model_path)
            self.assertEqual(model.device,settings.AI_DEVICE)
            self.assertFalse(model._is_loaded)
            model.unload()

    def test_missing_artifacts_raise_actual_app_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            model = ScratchVIVQAModel(tmp,'cpu')
            with self.assertLogs('app.ai.scratch_model',level='ERROR'):
                with self.assertRaises(AppError) as caught:model.load()
            self.assertEqual(caught.exception.status_code,503)
            self.assertEqual(caught.exception.code,'MODEL_UNAVAILABLE')
            self.assertNotIn(tmp,caught.exception.message)

    def test_actual_handler_preserves_model_error_contract(self):
        app = create_app()
        with tempfile.TemporaryDirectory() as tmp:
            model = ScratchVIVQAModel(tmp,'cpu')
            @app.get('/test-scratch-error')
            def probe():
                model.load()
            with TestClient(app,raise_server_exceptions=False) as client:
                with self.assertLogs('app.ai.scratch_model',level='ERROR'):
                    response = client.get('/test-scratch-error')
            self.assertEqual(response.status_code,503)
            self.assertEqual(response.json(),{'error':{'code':'MODEL_UNAVAILABLE',
                                                     'message':'Model tự xây chưa sẵn sàng.'}})
            self.assertNotIn(tmp,response.text)
