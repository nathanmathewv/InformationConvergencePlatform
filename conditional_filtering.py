import json
import pandas as pd
import random

# first_names = ["John", "John", "John", "Alice", "Bob", "Charlie", "David", "Emma", "Fiona", "George"]
# last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

# num_records = 20
# data = {
#     "CustomerID": [i for i in range(1001, 1001 + num_records)],
#     "fname": [random.choice(first_names) for _ in range(num_records)],
#     "lname": [random.choice(last_names) for _ in range(num_records)],
# }
# df1 = pd.DataFrame(data)

# customer_ids = random.choices(df1["CustomerID"], k=num_records - 1) + [1002]
# customer_ids.append(1002) 

# data_orders = {
#     "PurchaseOrder/CustomerID": customer_ids,
#     "PurchaseOrder/OrderID": [i for i in range(2001, 2001 + num_records + 1)]
# }
# df2 = pd.DataFrame(data_orders)
# dbs = [df1, df2]

def get_ds_specific_query(jsonquery):
    #go through "Select" and get the DSName of each entry
    ds_names = [entry["DSName"] for entry in jsonquery["Select"]]

    fields = dict()
    for ds in ds_names:
        fields[ds] = [entry["Fields"] for entry in jsonquery["Select"] if entry["DSName"]==ds]
        fields[ds] = fields[ds][0]

    where_conditions = jsonquery.get("Where", [])
    conditions = dict()
    for ds_name in ds_names:
        conditions[ds_name] = []
        for i in where_conditions:
            temp_literals = []
            for literal in i.get("Literals", []):
                v1 = literal["Value1"]
                v2 = literal["Value2"]
                v1_cond = (v1[:10] == "Constant::" or v1[:v1.index(".")] == ds_name)
                v2_cond = (v2[:10] == "Constant::" or v2[:v2.index(".")] == ds_name)
                if(v1_cond and v2_cond):
                    temp_literals.append(literal)
            conditions[ds_name].append({"Literals": temp_literals})
    return conditions, fields         
        

def resolve_queries(jsonquery, dbs):
    db = dbs[0]
    print(db,"\n\n\n\n")
    for i in dbs[1:]:
        print(i,"\n\n\n\n")
        db = db.merge(i, how = "cross")
    

    select_ds_names = [entry["DSName"] for entry in jsonquery["Select"]]
    ds_index = dict()
    i = 0
    for ds_name in select_ds_names:
        ds_index[ds_name] = i
        i += 1

    # Get where conditions from the JSON data
    where_conditions = jsonquery.get("Where", [])


    new_db = pd.DataFrame(columns = db.columns)
    for row in db.iterrows():
        valid = False
        # print(row)
        for i in where_conditions:
            valid_in = True
            for literal in i.get("Literals", []):
                v1 = literal["Value1"]
                v2 = literal["Value2"]
                
                if(v1[:10] == "Constant::"):
                    v1 = v1[10:]
                else:
                    v1 = row[1][v1]
                if(v2[:10] == "Constant::"):
                    v2 = v2[10:]
                else:
                    v2 = row[1][v2]
                
                flag1 = 0
                if(isinstance(v1,list)):
                    # print("HELLOOOO")
                    if(len(v1) > 1):
                        flag1 = 1
                    else:
                        v1 = str(v1[0])
                else:
                    v1 = str(v1)
                flag2 = 0
                if(isinstance(v2,list)):
                    if(len(v2) > 1):
                        flag2 = 1
                    else:
                        v2 = v2[0]
                        v2 = str(v2)
                else:
                    v2 = str(v2)
                if(literal["Operator"] in ["<", ">", "<=", ">=", "=", "!="]):
                    if(flag1  == 1 or flag2 == 1):
                        raise Exception(f'Invalid operator {literal["Operator"]} between {v1} and {v2}')
                if(literal["Operator"] in "IN"):
                    if(flag1 == 1):
                        raise Exception(f'Invalid operator {literal["Operator"]} between {v1} and {v2}')
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
                elif(literal["Operator"] == "IN"):
                    if(v1 not in v2):
                        valid_in = False
                else:
                    print("Invalid operator")
                    valid_in = False
            if(valid_in == True):
                valid = True
                break
        if(valid == True):
            new_db = pd.concat([new_db, row[1].to_frame().T], ignore_index=True)


    return new_db

#print(get_ds_specific_query(jsonquery))
