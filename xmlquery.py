import json
import pandas as pd
import os
import glob
from lxml import etree


with open('query.json', 'r') as file:
    data = json.load(file)

datasources = ['Datasources/PurchaseOrders']
results = {}

for select_item in data.get("Select", []):
    ds_name = select_item["DSName"]
    fields = select_item["Fields"]
    # Assume XML files are in "Datasources/<DSName>" folder
    folder = os.path.join("Datasources", ds_name)
    xml_files = glob.glob(os.path.join(folder, "*.xml"))
    records = []
    for xml_file in xml_files:
        try:
            tree = etree.parse(xml_file)
        except Exception as e:
            print(f"Error parsing {xml_file}: {e}")
            continue
        record = {}
        for field in fields:
            value = tree.xpath(f"string(//{field})")
            record[field.split('/')[-1]] = value  # use last part as column name
        records.append(record)
    df = pd.DataFrame(records)

print(df)