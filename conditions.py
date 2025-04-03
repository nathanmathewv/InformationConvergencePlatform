import json
import pandas as pd
import random

first_names = ["John", "John", "John", "Alice", "Bob", "Charlie", "David", "Emma", "Fiona", "George"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

num_records = 20
data = {
    "CustomerID": [i for i in range(1001, 1001 + num_records)],
    "fname": [random.choice(first_names) for _ in range(num_records)],
    "lname": [random.choice(last_names) for _ in range(num_records)],
}
df1 = pd.DataFrame(data)

customer_ids = random.choices(df1["CustomerID"], k=num_records - 1) + [1002]
customer_ids.append(1002) 

data_orders = {
    "PurchaseOrder/CustomerID": customer_ids,
    "PurchaseOrder/OrderID": [i for i in range(2001, 2001 + num_records + 1)]
}
df2 = pd.DataFrame(data_orders)

with open("query.json", "r") as f:
    json_data = json.load(f)

dbs = [df1, df2]

db = dbs[0]
for i in dbs[1:]:
    db = db.merge(i, how = "cross")

select_ds_names = [entry["DSName"] for entry in json_data["Select"]]
ds_index = dict()
i = 0
for ds_name in select_ds_names:
    ds_index[ds_name] = i
    i += 1

# Get where conditions from the JSON data
where_conditions = json_data.get("Where", [])


new_db = pd.DataFrame(columns = db.columns)
for row in db.iterrows():
    valid = False
    for i in where_conditions:
        valid_in = True
        for literal in i.get("Literals", []):
            v1 = literal["Value1"]
            v2 = literal["Value2"]
            if(v1[:10] == "Constant::"):
                v1 = v1[10:]
            else:
                v1 = v1[v1.index(".") + 1:]
                v1 = row[1][v1]
            if(v2[:10] == "Constant::"):
                v2 = v2[10:]
            else:
                v2 = v2[v2.index(".") + 1:]
                v2 = row[1][v2]
            
            v1 = str(v1)
            v2 = str(v2)
            if(literal["Operator"] == "="):
                if(v1 != v2):
                    valid_in = False
            elif(literal["Operator"] == "<"):
                if(v1 >= v2):
                    valid_in = False
            elif(literal["Operator"] == ">"):
                if(v1 <= v2):
                    valid_in = False
            elif(literal["Operator"] == "<="):
                if(v1 > v2):
                    valid_in = False
            elif(literal["Operator"] == ">="):
                if(v1 < v2):
                    valid_in = False
            elif(literal["Operator"] == "!="):
                if(v1 == v2):
                    valid_in = False
            else:
                print("Invalid operator")
                valid_in = False
        if(valid_in == True):
            valid = True
            break
    if(valid == True):
        new_db = pd.concat([new_db, row[1].to_frame().T], ignore_index=True)

print(new_db)
