import json
import csv

csvFilePath = "src/data/bitbank_sample.csv"
jsonFilePath = "src/data/bitbank_sample.json"


def read_csv(file, json_file):
    csv_rows = []
    with open(file, encoding="utf8") as csvfile:
        reader = csv.DictReader(csvfile)
        field = reader.fieldnames
        for row in reader:
            csv_rows.extend([{field[i]: row[field[i]] for i in range(len(field))}])
            convert_write_json(csv_rows, json_file)


def convert_write_json(data, json_file):
    with open(json_file, "w", encoding="utf-8") as f:
        f.write(
            json.dumps(
                data,
                sort_keys=False,
                indent=4,
                ensure_ascii=False,
                separators=(",", ": "),
            )
        )
        f.write(json.dumps(data))


if __name__ == "__main__":
    read_csv(csvFilePath, jsonFilePath)
