from collections import defaultdict
from saxonche import PySaxonProcessor
import os
import glob
import pandas as pd
from lxml import etree
import xmltodict
import json

def initialize_xml(jsonquery,data_dict,datasource):
    xml_ds_names = [entry["DSName"] for entry in jsonquery["Select"] if data_dict.get(entry["DSName"]) == "XML"]
    xml_files = defaultdict(list)
    for data in xml_ds_names:
        folder = os.path.join(datasource, data)
        xml_files[data] = glob.glob(os.path.join(folder, "*.xml"))
    return xml_ds_names, xml_files

def generate_xquery_string(conditions, fields):
    where_clauses = []

    for cond_group in conditions:
        literals = cond_group.get("Literals", [])
        group_clauses = []
        for lit in literals:
            left = lit["Value1"].split("::")[-1].replace("PurchaseOrders.PurchaseOrder/", "")
            right = lit["Value2"].split("::")[-1]
            op = lit["Operator"]
            if not right.isnumeric():
                right = f"'{right}'"
            group_clauses.append(f"$p/{left} {op} {right}")
        if group_clauses:
            where_clauses.append(f"({' and '.join(group_clauses)})")

    where_expr = " and ".join(where_clauses) if where_clauses else "true()"
    if {'Literals': []} in conditions:
        where_expr = "true()"

    return_fields = "\n".join([
        f"<{f.replace('/', '_')}>{{ $p/{f.replace('PurchaseOrder/', '')} }}</{f.replace('/', '_')}>"
        for f in fields
    ])

    xquery = f"""
    for $p in /PurchaseOrder
    where {where_expr}
    return <result>{return_fields}</result>
    """
    print(xquery.strip())
    return xquery.strip()

def run_xml_query(conditions, xml_files, ds_name, fields):
    records = []

    xquery_str = generate_xquery_string(conditions, fields)

    with PySaxonProcessor(license=False) as proc:
        xq_proc = proc.new_xquery_processor()

        for xml_file in xml_files[ds_name]:
            try:
                xq_proc.set_context(xdm_item=proc.parse_xml(xml_file_name=xml_file))
                xq_proc.set_query_content(xquery_str)
                serialized = xq_proc.run_query_to_string()
                if not serialized:
                    continue

                serialized = serialized.replace('<?xml version="1.0" encoding="UTF-8"?>', "")
                wrapped = f"<root>{serialized}</root>"
                doc = etree.fromstring(wrapped.encode("utf-8"))

                for entry_dom in doc.findall("result"):
                    row = {}

                    for field in fields:
                        tag = field.replace("/", "_")
                        container_nodes = entry_dom.findall(f".//{tag}")

                        if not container_nodes:
                            row[field] = None
                            continue

                        values = []
                        for cn in container_nodes:
                            elem_dict = xmltodict.parse(etree.tostring(cn))
                            elem_root = list(elem_dict.values())[0]
                            # print(f"elem_root: {elem_root}")

                            child_entries = []
                            for k, v in elem_root.items():
                                if isinstance(v,str):
                                    child_entries.append(v)
                                elif isinstance(v, list):
                                    child_entries.extend(v)
                                else:
                                    for m,n in v.items():
                                        if isinstance(n, list):
                                            for i in n:
                                                child_entries.append({m: i})
                                        else:
                                            child_entries.append(v)
                            values.extend(child_entries)
                        # print(f"values: {values}")
                        row[field] = values
                    records.append(row)

            except Exception as e:
                print(f"Error processing {xml_file}: {e}")

    return pd.DataFrame(records)


# def run_xml_query(conditions, xml_files, ds_name, fields):
#     records = []

#     # 1) Build XQuery
#     xquery_str = generate_xquery_string(conditions, fields)

#     with PySaxonProcessor(license=False) as proc:
#         xq_proc = proc.new_xquery_processor()

#         for xml_file in xml_files[ds_name]:
#             try:
#                 # 2) Run XQuery and get serialized XML
#                 xq_proc.set_context(xdm_item=proc.parse_xml(xml_file_name=xml_file))
#                 xq_proc.set_query_content(xquery_str)
#                 serialized = xq_proc.run_query_to_string()
#                 if not serialized:
#                     continue
#                 serialized = serialized.replace('<?xml version="1.0" encoding="UTF-8"?>', "")

#                 # 3) Wrap & parse once

#                 doc = etree.fromstring(serialized.encode("utf-8"))

#                 # 4) Parse XML to dict
#                 dict = xmltodict.parse(serialized)
#                 if dict.get("result") is not None:
#                     json_data = json.dumps(dict)

#                     print(json_data)
#                     records.append(json_data)



#                 # 4) For each <result> …
#                 for entry_dom in doc.findall("result"):
#                     lists_of_vals = []
#                     for field in fields:
#                         tag = field.replace("/", "_")
#                         container_nodes = entry_dom.findall(f".//{tag}")

#                         vals = []
#                         for cn in container_nodes:
#                             # if there are child elems, collect each child.text
#                             children = list(cn)
#                             if children:
#                                 for child in children:
#                                     text = (child.text or "").strip()
#                                     if text:
#                                         vals.append(text)
#                             else:
#                                 text = (cn.text or "").strip()
#                                 if text:
#                                     vals.append(text)

#                         if not vals:
#                             vals = [""]
#                         lists_of_vals.append(vals)

#                     # 5) Cross‑product → one row each
#                     # for combo in itertools.product(*lists_of_vals):
#                     #     row = {
#                     #         f"{ds_name}.{field}": val
#                     #         for field, val in zip(fields, combo)
#                     #     }
#                     #     records.append(row)

#             except Exception as e:
#                 print(f"Error processing {xml_file}: {e}")

#     return pd.DataFrame(records)