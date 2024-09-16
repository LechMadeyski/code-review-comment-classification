import argparse

DEFAULT_SEED = 0
DEFAULT_EPOCHS = 40
DEFAULT_BATCH_SIZE = 4
DEFAULT_FOLDS = 10
DEFAULT_PATH = "dataset.xlsx"


def positive_int(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
    return ivalue


def read_args():
    parser = argparse.ArgumentParser("python -m solution", description="Train a model on the dataset")
    parser.add_argument("-s", "--seed", type=int, default=DEFAULT_SEED, metavar="S",
                        help="Seed for random number generators")
    parser.add_argument("-e", "--epochs", type=positive_int, default=DEFAULT_EPOCHS, metavar="E",
                        help="Number of epochs to train the model")
    parser.add_argument("-b", "--batch_size", type=positive_int, default=DEFAULT_BATCH_SIZE, metavar="B",
                        help="Batch size for training")
    parser.add_argument("-f", "--folds", type=positive_int, default=DEFAULT_FOLDS, metavar="F",
                        help="Number of folds for cross-validation")
    parser.add_argument("-p", "--path", type=argparse.FileType(), default=DEFAULT_PATH, metavar="P",
                        help="Path to the dataset")

    args = parser.parse_args()
    return args.seed, args.epochs, args.batch_size, args.folds, args.path.name
