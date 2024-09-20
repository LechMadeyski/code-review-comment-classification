import pandas as pd
import numpy as np
from transformers import RobertaTokenizerFast

from solution.comment_groups import add_comment_group_metrics

COLUMNS_TO_DROP = ["meta.comment_id", "meta.url", "meta.start_line",
                   "meta.end_line", "comment.side", "code.context.text"]
Y_COLUMN = "meta.label"
COMMENT_COLUMN = "comment.text"
CODE_COLUMN = "code.range.text"

tokenizer = RobertaTokenizerFast.from_pretrained('microsoft/codebert-base')


def get_data(path):
    df = pd.read_excel(path)
    df = add_comment_group_metrics(df)

    Y = np.array(pd.get_dummies(df[Y_COLUMN]).values.tolist())

    code = df[CODE_COLUMN]
    comment = df[COMMENT_COLUMN]

    code_input_ids, code_attention_masks = tokenize_dataframe(code)
    comment_input_ids, comment_attention_masks = tokenize_dataframe(comment)

    X = {
        "comment_input_ids": comment_input_ids,
        "comment_attention_masks": comment_attention_masks,
        "code_input_ids": code_input_ids,
        "code_attention_masks": code_attention_masks,
        "metrics": df.drop(columns=[*COLUMNS_TO_DROP, COMMENT_COLUMN, CODE_COLUMN, Y_COLUMN]).to_numpy(dtype=np.float32)
    }

    return X, Y


def tokenize_dataframe(df):
    input_ids = []
    attention_masks = []

    for sentence in df:
        # NOTE: When tokenizing sentences that are too long, they will be truncated. This is not ideal.
        tokens = tokenizer(str(sentence), truncation=True, padding="max_length")
        input_ids.append(tokens["input_ids"])
        attention_masks.append(tokens["attention_mask"])

    return np.array(input_ids, dtype=np.int32), np.array(attention_masks, dtype=np.int32)


def partition_data(data, idx):
    return {key: value[idx] for key, value in data.items()}
