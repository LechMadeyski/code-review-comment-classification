import torch
from torch import nn, concat
from transformers import RobertaModel
from sklearn.metrics import classification_report, matthews_corrcoef, precision_score, accuracy_score, f1_score, recall_score
from tqdm import tqdm

from solution.data import partition_data

LSTM_DIM = 50


class Model(nn.Module):
    def __init__(self, metrics_dim):
        super(Model, self).__init__()

        self.codebert_comment = RobertaModel.from_pretrained(
            'microsoft/codebert-base')
        self.codebert_code = RobertaModel.from_pretrained(
            'microsoft/codebert-base')

        self.lstm_comment = nn.LSTM(768, LSTM_DIM)
        self.lstm_code = nn.LSTM(768, LSTM_DIM)

        self.dropout_comment = nn.Dropout(0.3)
        self.dropout_code = nn.Dropout(0.3)

        self.dense = nn.Linear(2 * LSTM_DIM + metrics_dim, 25)  # 50x2 from LSTMs, rest from metrics
        self.relu1 = nn.ReLU()
        self.dense1 = nn.Linear(25, 5)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, comment_input_ids, comment_attention_masks, code_input_ids, code_attention_masks, metrics):
        comment = self.codebert_comment(input_ids=comment_input_ids,
                                        attention_mask=comment_attention_masks)[0]
        code = self.codebert_code(input_ids=code_input_ids,
                                  attention_mask=code_attention_masks)[0]

        comment, _ = self.lstm_comment(comment)
        code, _ = self.lstm_code(code)

        comment = comment[:, -1]
        code = code[:, -1]

        comment = self.dropout_comment(comment)
        code = self.dropout_code(code)

        combined = concat((comment, code), dim=1)
        combined = concat((combined, metrics), dim=1)
        dense = self.dense(combined)
        dense1 = self.dense1(self.relu1(dense))
        return self.softmax(dense1)

    # stop fine-tuning the codebert models
    # for debugging purposes
    def freeze_codeberts(self, freeze=True):
        for param in self.codebert_comment.parameters():
            param.requires_grad = not freeze
        for param in self.codebert_code.parameters():
            param.requires_grad = not freeze


def __to_tensor(x, device): return {key: torch.tensor(value).to(device) for key, value in x.items()}


def train(model, device, optimizer, epochs, batch_size, X_train_set, Y_train_set, X_val_set, Y_val_set):

    X_train_set, Y_train_set = __to_tensor(X_train_set, device), torch.tensor(Y_train_set).to(device)
    X_val_set, Y_val_set = __to_tensor(X_val_set, device), torch.tensor(Y_val_set).to(device)

    for epoch in range(epochs):
        print(f"Epoch {epoch + 1}/{epochs}")

        model.train()
        for i in tqdm(range(0, len(Y_train_set), batch_size)):
            batch_X = partition_data(X_train_set, slice(i, i + batch_size))
            batch_Y = Y_train_set[i:i + batch_size,]

            optimizer.zero_grad()
            output = model(**batch_X)
            loss = nn.functional.cross_entropy(
                output, torch.argmax(batch_Y.to(torch.long), 1))
            loss.backward()
            optimizer.step()

        print(f"Evaulating epoch {epoch + 1}/{epochs} on validation set")
        model.eval()
        with torch.no_grad():
            output = model(**X_val_set)
            loss = nn.functional.cross_entropy(
                output, torch.argmax(Y_val_set.to(torch.long), 1))

            print(f"Validation loss: {loss.item()}")

            accuracy = torch.sum(torch.argmax(output, 1)
                                 == torch.argmax(Y_val_set.to(torch.long), 1)).item() / len(Y_val_set)
            print(f"Validation accuracy: {accuracy}")


def evaluate(model, device, X_test_set, Y_test_set, metrics):
    X_test_set, Y_test_set = __to_tensor(X_test_set, device), torch.tensor(Y_test_set).to(device)

    model.eval()
    with torch.no_grad():
        output = model(**X_test_set)

        true_class = torch.argmax(Y_test_set.to(torch.long), 1).cpu().numpy()
        predicted_class = torch.argmax(output, 1).cpu().numpy()
        print("Test set results: ")
        print(classification_report(true_class,
              predicted_class, zero_division=0.0))

    return {metric: metric_function(true_class, predicted_class) for metric, metric_function in metrics.items()}
