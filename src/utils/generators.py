import uuid
import random
from datetime import datetime
from faker import Faker
import itertools
fake = Faker()


def generate_static(dataset):
    return dataset["fields"] * dataset.get("record_count", 1)


def generate_dynamic(dataset):
    records = []
    for _ in range(dataset["record_count"]):
        row = {}
        for f in dataset["fields"]:
            if f["type"] == "uuid":
                row[f["name"]] = str(uuid.uuid4())

            elif f["type"] == "string" and f.get("generator") == "name":
                row[f["name"]] = fake.name()

            elif f["type"] == "string" and f.get("generator") == "email":
                row[f["name"]] = fake.email()

            elif f["type"] == "integer":
                row[f["name"]] = random.randint(f["min"], f["max"])

            elif f["type"] == "float":
                row[f["name"]] = round(random.uniform(f["min"], f["max"]), 2)

            elif f["type"] == "boolean":
                row[f["name"]] = random.random() < f.get("probability_true", 0.5)
            elif f["type"] == "datetime":
                start_dt = datetime.strptime(f['start'], "%Y-%m-%d")
                end_dt = datetime.strptime(f['end'], "%Y-%m-%d")
                row[f["name"]] = fake.date_between(start_date=start_dt, end_date=end_dt).strftime(f['format'])


        records.append(row)

    return records


def generate_boundary(dataset):
    keys = [f["name"] for f in dataset["fields"]]
    values = [f["values"] for f in dataset["fields"]]

    records = []
    for combo in zip(*values):
        records.append(dict(zip(keys, combo)))

    return records


def generate_combinational(dataset):
    keys = [f["name"] for f in dataset["fields"]]
    values = [f["values"] for f in dataset["fields"]]

    records = []
    for combo in itertools.product(*values):
        records.append(dict(zip(keys, combo)))

    return records