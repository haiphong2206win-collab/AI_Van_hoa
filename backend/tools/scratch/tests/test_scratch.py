"""Unit + synthetic integration tests. NEVER a trained-model quality evaluation."""
import builtins
import gc
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import weakref

from app.ai.scratch_model import ScratchModel, extract_answer, _read_settings, read_manifest


class Error(RuntimeError):
    def __init__(self, status_code, code, message):
        self.status_code, self.code = status_code, code
        super().__init__(message)


class UnitTests(unittest.TestCase):
    def test_import_without_ai(self):
        code = '''import builtins
orig = builtins.__import__
def guarded(name, *a, **kw):
    if name.split('.')[0] in {'torch','torchvision','transformers','PIL'}:
        raise AssertionError('Eager AI import: ' + name)
    return orig(name, *a, **kw)
builtins.__import__ = guarded
from app.ai.scratch_model import ScratchModel
m=ScratchModel(); m.unload(); m.unload()
'''
        result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_answer_extraction(self):
        self.assertEqual(extract_answer(' Giải thích: mẫu. Trả lời: Áo dài. '), 'Áo dài.')
        self.assertEqual(extract_answer(' Xe bò '), 'Xe bò')
        for text in ['', '  ', 'Giải thích: thiếu. Trả lời:  ']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                extract_answer(text)

    def test_missing_artifact_and_not_loaded(self):
        with tempfile.TemporaryDirectory() as temp:
            model = ScratchModel(temp, 'cpu', error_factory=Error)
            self.assertFalse(model.artifacts_present())
            with self.assertLogs('app.ai.scratch_model', level='ERROR'):
                with self.assertRaises(Error) as caught:
                    model.load()
            self.assertEqual((caught.exception.status_code, caught.exception.code), (503,'MODEL_UNAVAILABLE'))
            self.assertNotIn(temp, str(caught.exception))
            with self.assertRaises(Error) as caught:
                model.predict(None, 'Ảnh gì?')
            self.assertEqual(caught.exception.status_code,503)
            model.unload(); model.unload()

    def test_wrong_architecture_metadata(self):
        with self.assertRaises(ValueError):
            _read_settings({'model_state_dict': {}, 'seq2seq_model_name':'xlm-roberta-base'})


class SyntheticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch
        import sentencepiece as spm
        from transformers import T5Config, T5Tokenizer, GenerationConfig
        from tools.scratch.tests import reference_notebook as ref
        from tools.scratch.export_scratch_artifacts import export_scratch_artifacts
        torch.set_num_threads(2)
        torch.manual_seed(42)
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        corpus=cls.root/'corpus.txt'
        corpus.write_text(('Đây là ảnh gì? Trả lời: Áo dài. Xe bò. Văn hóa Việt Nam.\n' * 50), encoding='utf-8')
        spm.SentencePieceTrainer.train(input=str(corpus), model_prefix=str(cls.root/'spiece'),
                                      vocab_size=64, hard_vocab_limit=False, pad_id=0, eos_id=1,
                                      unk_id=2, bos_id=-1, minloglevel=2)
        cls.tokenizer=T5Tokenizer(vocab_file=str(cls.root/'spiece.model'),extra_ids=0,legacy=True)
        cls.config=T5Config(vocab_size=len(cls.tokenizer), d_model=16,d_kv=8,d_ff=32,
                            num_layers=1,num_decoder_layers=1,num_heads=2,dropout_rate=0.0,
                            pad_token_id=0,eos_token_id=1,decoder_start_token_id=0)
        ref.CFG.TEST_CONFIG=cls.config
        reference=ref.VQAGenModel().eval()
        # Force a visible first token in this SYNTHETIC fixture, not in production.
        gen=GenerationConfig.from_model_config(cls.config)
        gen.forced_bos_token_id=cls.tokenizer.encode('Xe',add_special_tokens=False)[-1]
        cls.settings=dict(IMG_SIZE=32,MAX_QUESTION_LEN=16,GEN_MAX_LENGTH=8,GEN_NUM_BEAMS=2,
                          ANSWER_MARKER=' Trả lời: ',USE_KB_CONTEXT=True,USE_RATIONALE=True,
                          NUM_VISUAL_TOKENS=16,SEQ2SEQ_MODEL_NAME='VietAI/vit5-base')
        cls.checkpoint=cls.root/'training.pt'
        torch.save(dict(model_state_dict=reference.state_dict(),config=cls.settings,
                        seq2seq_model_name='VietAI/vit5-base',num_visual_tokens=16),cls.checkpoint)
        cls.bundle=export_scratch_artifacts(cls.checkpoint, cls.tokenizer, cls.config,
                                           cls.root/'bundle', gen)
        del reference
        gc.collect()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def new_adapter(self, device='cpu'):
        return ScratchModel(self.bundle,device,error_factory=Error)

    def test_full_pipeline_and_reference_parity(self):
        import torch
        from PIL import Image
        from torchvision import transforms as T
        from transformers import GenerationConfig
        from tools.scratch.tests import reference_notebook as ref
        model=self.new_adapter()
        # Network calls must fail if anyone accidentally attempts them.
        with patch('socket.socket.connect', side_effect=AssertionError('Network forbidden')):
            with self.assertLogs('app.ai.scratch_model', level='WARNING'):
                model.load()
            old_id=id(model._model)
            model.load()
            self.assertEqual(id(model._model), old_id)
            self.assertFalse(model._model.training)
            self.assertTrue(all(p.device.type=='cpu' for p in model._model.parameters()))
            image=Image.new('RGB',(61,47),(55,120,200))
            question='Đây là ảnh gì?'
            with torch.inference_mode():
                ref_model=ref.VQAGenModel().eval()
                ckpt=torch.load(self.checkpoint,map_location='cpu',weights_only=True)
                ref_model.load_state_dict(ckpt['model_state_dict'],strict=True)
                ref_model.seq2seq.generation_config=GenerationConfig.from_pretrained(self.bundle/'vit5',local_files_only=True)
                eval_transform=T.Compose([T.Resize((32,32)),T.ToTensor(),
                                          T.Normalize([.485,.456,.406],[.229,.224,.225])])
                img=eval_transform(image).unsqueeze(0)
                self.assertTrue(torch.equal(img,model._transform(image).unsqueeze(0)))
                enc=self.tokenizer(question,padding='max_length',truncation=True,max_length=16,return_tensors='pt')
                a,b=ref_model._combine_encoder_inputs(img,**enc)
                x,y=model._model._combine_encoder_inputs(img,**enc)
                torch.testing.assert_close(a,x,rtol=0,atol=0)
                self.assertTrue(torch.equal(b,y))
                expected_ids=ref_model.generate(img,**enc,max_length=8,num_beams=2)
                actual_ids=model._model.generate(img,**enc,max_length=8,num_beams=2,min_new_tokens=0,do_sample=False,early_stopping=True)
                self.assertTrue(torch.equal(expected_ids,actual_ids))
                expected=extract_answer(self.tokenizer.decode(expected_ids[0],skip_special_tokens=True))
            answer=model.predict(image,question)
            self.assertEqual(answer,expected)
            self.assertTrue(answer.strip())
            self.assertEqual(image.getpixel((0,0)),(55,120,200))
            ref_model=None;ckpt=None
            # Check error handling without replacing actual model implementation.
            with patch.object(model._tokenizer,'decode',return_value='Giải thích. Trả lời: '):
                with self.assertLogs('app.ai.scratch_model',level='ERROR'):
                    with self.assertRaises(Error) as caught:model.predict(image,question)
                self.assertEqual(caught.exception.code,'INFERENCE_FAILED')
            reference=weakref.ref(model._model)
            model.unload();model.unload()
            self.assertFalse(model.loaded)
            self.assertIsNone(reference())
            self.assertEqual(image.getpixel((0,0)),(55,120,200))
            image.close()
            with self.assertLogs('app.ai.scratch_model',level='WARNING'):model.load()
            model.unload()

    def test_mismatched_weights_atomic_failure(self):
        import torch
        model=self.new_adapter()
        checkpoint=torch.load(self.checkpoint,map_location='cpu',weights_only=True)
        checkpoint['model_state_dict'].pop('image_encoder.projector.0.weight')
        with patch('torch.load',return_value=checkpoint):
            with self.assertLogs('app.ai.scratch_model',level='ERROR'):
                with self.assertRaises(Error) as caught:model.load()
        self.assertEqual(caught.exception.code,'MODEL_UNAVAILABLE')
        self.assertFalse(model.loaded)
        self.assertIsNone(model._tokenizer)
        self.assertIsNone(model._device)
        model.unload()

    def test_unsupported_device(self):
        for name in ['mps','invalid-device','cuda:9999']:
            with self.subTest(device=name):
                model=self.new_adapter(name)
                with self.assertLogs('app.ai.scratch_model',level='ERROR'):
                    with self.assertRaises(Error) as caught:model.load()
                self.assertEqual(caught.exception.code,'MODEL_UNAVAILABLE')
                self.assertFalse(model.loaded)

    def test_checksum_missing_and_path_validation(self):
        path=self.bundle/'manifest.json'; original=path.read_text()
        try:
            data=json.loads(original)
            data['sha256']['vit5/config.json']='0'*64
            path.write_text(json.dumps(data))
            model=self.new_adapter()
            with self.assertLogs('app.ai.scratch_model',level='ERROR'):
                with self.assertRaises(Error):model.load()
            data['sha256']['../escape']='0'*64
            path.write_text(json.dumps(data))
            self.assertFalse(model.artifacts_present())
            data=json.loads(original);data['sha256'].pop('vit5/spiece.model')
            path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):read_manifest(self.bundle)
        finally:path.write_text(original)

    def test_standalone_cli(self):
        from PIL import Image
        image=self.root/'input.png'
        with Image.new('RGB',(32,32),(55,120,200)) as source:source.save(image)
        cmd=[sys.executable,'tools/scratch/run_scratch.py','--model-path',str(self.bundle),
             '--device','cpu','--image',str(image),'--question','Đây là ảnh gì?']
        env=dict(os.environ,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        result=subprocess.run(cmd,capture_output=True,text=True,env=env,timeout=90)
        self.assertEqual(result.returncode,0,result.stderr)
        report=json.loads(result.stdout)
        self.assertTrue(report['answer'].strip())
        self.assertTrue(report['unloaded'])
        self.assertGreater(report['process_peak_rss_sampled_mib'],0)
        # Keep real measured diagnostics in test stdout, marked synthetic.
        print('\nSYNTHETIC_CLI_REPORT='+json.dumps(report,ensure_ascii=False))


if __name__=='__main__':unittest.main(verbosity=2)
