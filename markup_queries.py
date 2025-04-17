from collections import defaultdict
from saxonche import PySaxonProcessor
import os
import glob
import pandas as pd
from lxml import etree

def initialize_xml(jsonquery,data_dict,datasource):
    xml_ds_names = [entry["DSName"] for entry in jsonquery["Select"] if data_dict.get(entry["DSName"]) == "XML"]
    xml_files = defaultdict(list)
    for data in xml_ds_names:
        folder = os.path.join(datasource, data)
        xml_files[data] = glob.glob(os.path.join(folder, "*.xml"))
    return xml_ds_names, xml_files

def run_xml_query(conditions, xml_files,ds_name,fields):
    print("hawoiduha\n\n",fields)
    records = []
    for xml_file in xml_files[ds_name]:
        print(xml_file)
        try:
            tree = etree.parse(xml_file)
        except Exception as e:
            print(f"Error parsing {xml_file}: {e}")
            continue
        record = {}
        for field in fields:
            value = tree.xpath(f"string(//{field})")
            record[field] = value

        record = {f"{ds_name}.{k}": v for k, v in record.items()}
        records.append(record)

    df = pd.DataFrame(records)
    return df


def generate_xquery_string(conditions, fields):
    where_clauses = []
    for cond_group in conditions:
        literals = cond_group.get("Literals", [])
        group_clauses = []
        for lit in literals:
            left = lit["Value1"].split("::")[-1]
            right = lit["Value2"].split("::")[-1]
            op = lit["Operator"]
            if not right.isnumeric():
                right = f"'{right}'"
            group_clauses.append(f"$p/{left} {op} {right}")
        if group_clauses:
            where_clauses.append(f"({' and '.join(group_clauses)})")
    where_expr = " and ".join(where_clauses) if where_clauses else "true()"

    return_fields = "\n".join([
        f"<{f.replace('/', '_')}>{{ $p/{f} }}</{f.replace('/', '_')}>"
        for f in fields
    ])

    xquery = f"""
    for $p in /PurchaseOrder
    where {where_expr}
    return <result>{return_fields}</result>
    """
    return xquery.strip()


# def run_xml_query(conditions, xml_files, ds_name, fields):
#     records = []
#     xquery_str = generate_xquery_string(conditions, fields)

#     with PySaxonProcessor(license=False) as proc:
#         xq_proc = proc.new_xquery_processor()

#         for xml_file in xml_files[ds_name]:
#             try:
#                 xq_proc.set_context(xdm_item=proc.parse_xml(xml_file_name=xml_file))
#                 xq_proc.set_query_content(xquery_str)

#                 result_seq = xq_proc.run_query_to_value()
#                 if result_seq is None:
#                     continue

#                 for i in range(result_seq.count):
#                     entry = result_seq.item_at(i)
#                     entry_dom = proc.parse_xml(xml_text=entry.string_value)
#                     record = {}
#                     for field in fields:
#                         tag = field.replace('/', '_')
#                         val = entry_dom.xpath(f"string(//{tag})")
#                         record[f"{ds_name}.{field}"] = val
#                     records.append(record)

#             except Exception as e:
#                 print(f"Error processing {xml_file}: {e}")
#                 continue

#     return pd.DataFrame(records)

