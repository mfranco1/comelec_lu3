import json
from collections import defaultdict
from csv import DictReader


def load_data(fname: str) -> dict:
    data = defaultdict(lambda: defaultdict(int))
    with open(fname, "r") as f:
        for row in DictReader(f):
            for k, v in row.items():
                if k in ["Timestamp", "Email Address", "Name"]:
                    continue
                values = [word.strip() for word in v.split(",")]
                for value in values:
                    data[k][value] += 1
    return data


def main() -> None:
    data = load_data(fname="votes.csv")
    with open("votes.json", "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    main()