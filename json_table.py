# /// script
# requires-python = ">=3.13"
# dependencies = ["faker"]
# ///
import json
import os
from faker import Faker
from pathlib import Path

seed_value = int(os.environ.get("TDS_RANDOM_SEED", 42))
fake = Faker()
fake.seed_instance(seed_value)

Path("json_table").mkdir(exist_ok=True)

for i in range(1, 51):
    data = [
        {
            "number": fake.random_int(),
            "word": fake.word(),
            "sentence": fake.sentence(),
            "name": fake.name(),
            "address": fake.address(),
            "email": fake.email(),
            "company": fake.company(),
            "date": fake.date(),
            "boolean": fake.boolean(),
            "url": fake.url(),
        }
        for _ in range(100)
    ]
    Path(f"json_table/{i}.json").write_text(json.dumps({"data": data}, indent=2))

print("Generated json_table/*.json")
