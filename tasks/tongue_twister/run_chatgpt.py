"""
@Desc:
@Reference:
- logger and WandLogger
Weights and Biases is a third-party logger
https://pytorch-lightning.readthedocs.io/en/latest/common/loggers.html
@Notes:

"""

import sys
import json
import numpy as np
from pathlib import Path

from tqdm import tqdm

FILE_PATH = Path(__file__).absolute()
BASE_DIR = FILE_PATH.parent.parent.parent
sys.path.insert(0, str(BASE_DIR))  # run code in any path

from src.configuration.tongue_twister.config_args import parse_args_for_config
from src.utils.file_utils import copy_file_or_dir, output_obj_to_file, pickle_save, pickle_load
from src.utils import nlg_eval_utils
from src.utils.tongue_twister import tt_eval_utils
from train import TongueTwisterTrainer
from src.utils.string_utils import rm_extra_spaces

class ChatGPTTester(object):
    def __init__(self, hparams):
        self.hparams = hparams
        self.data_dir = Path(self.hparams.data_dir)
        self.resource_dir = Path(self.hparams.resource_dir)
        self.output_dir = Path(self.hparams.output_dir)
        self.experiment_name = self.hparams.experiment_name
        self.experiment_output_dir = self.output_dir.joinpath(self.experiment_name)
        self.experiment_output_dir = Path(hparams.output_dir)
        self.generation_dir = self.experiment_output_dir / "gen_result"
        self.generation_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir = self.experiment_output_dir / "cache_dir"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.src_data_file = self.data_dir.joinpath("test.source.txt")
        self.tgt_data_file = self.data_dir.joinpath("test.target.txt")
        self.src_data = self._read_clean_lines(self.src_data_file)
        self.tgt_data = self._read_clean_lines(self.tgt_data_file)

    def load_cache(self):
        pass

    def save_cache(self):
        pass


    def _read_clean_lines(self, file_path):
        data = []
        with open(file_path, "r", encoding="utf-8") as fr:
            for line in fr:
                line = rm_extra_spaces(line)
                if len(line) > 0:
                    data.append(line)
        return data


    def generate(self):


        preds = self.test_output["preds"]
        targets = self.tgt_data
        tgt_lines_toks, pred_lines_toks = \
            [self.tokenizer.tokenize(t) for t in targets], [self.tokenizer.tokenize(c) for c in preds]

        metrics = {}
        # calculate bleu score
        nlg_eval_utils.calculate_bleu(ref_lines=tgt_lines_toks, gen_lines=pred_lines_toks, metrics=metrics)
        # calculate rouge score
        rouge_metrics = nlg_eval_utils.calculate_rouge(pred_lines=preds, tgt_lines=targets)
        metrics.update(**rouge_metrics)
        phoneme_metrics = tt_eval_utils.compute_phonemes(keywords=preds, predictions=targets)
        metrics.update(**phoneme_metrics)
        bertscore_metrics = tt_eval_utils.compute_bert_score(predictions=preds, references=targets)
        metrics.update(**bertscore_metrics)
        gen_len = np.mean(list(map(len, preds)))
        metrics["gen_len"] = gen_len
        metrics["ppl"] = round(np.exp(metrics["loss"]), 2)
        key = sorted(metrics.keys())
        for k in key:
            print(k, metrics[k])
        print("=" * 10)

        print(f"model {self.model.model_name} eval {self.gen_file}")
        output_obj_to_file(json.dumps(metrics, indent=4), self.eval_file)
        return metrics

if __name__ == '__main__':
    hparams = parse_args_for_config()
    tester = chatgpt_generate_responses(hparams)