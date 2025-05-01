from collections import defaultdict
from saxonche import PySaxonProcessor
import os
import glob
import pandas as pd
from lxml import etree
import xmltodict
import json

def initialize_xml(root, jsonquery, data_dict, namespace):
    xml_root_dict = {}
    xml_location_dict = {}

    for entity in root.findall('ns:entity_type', namespace):
        if entity.get('type') == 'XML':
            name = entity.find('ns:name', namespace).text
            ds = entity.find('ns:ds', namespace)
            root_tag = ds.find('ns:root', namespace).text
            xml_root_dict[name] = root_tag
            location = ds.find('ns:FolderName', namespace).text
            xml_location_dict[name] = location
    
    xml_ds_names = [entry["DSName"] for entry in jsonquery["Select"] if data_dict.get(entry["DSName"]) == "XML"]
    xml_files = defaultdict(list)
    xml_roots = {}

    for data in xml_ds_names:
        xml_files[data] = glob.glob(os.path.join(xml_location_dict[data], "*.xml"))
        xml_roots[data] = xml_root_dict.get(data)

    return xml_ds_names, xml_files, xml_root_dict

def generate_xquery_string(conditions, fields, ds_name, root_name):
    where_clauses = []

    for cond_group in conditions:
        literals = cond_group.get("Literals", [])
        group_clauses = []
        for lit in literals:
            left = lit["Value1"].split("::")[-1].replace(f'{ds_name}.{root_name}/', "")
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
        f"<{f.replace('/', '_')}>{{ $p/{f.replace(f'{root_name}/', '')} }}</{f.replace('/', '_')}>"
        for f in fields
    ])

    return_fields =[]
    for f in fields:
        if f == root_name:
            return_fields.append("{ $p }")
        else:
            return_fields.append(f"<{f.replace('/', '_')}>{{ $p/{f.replace(f'{root_name}/', '')} }}</{f.replace('/', '_')}>")
        
    return_fields = "\n".join(return_fields)

    xquery = f"""
    for $p in /{root_name}
    where {where_expr}
    return <result>{return_fields}</result>
    """
    print(ds_name,f"query:\n{xquery.strip()}","\n")
    return xquery.strip()

def run_xml_query(conditions, xml_files, ds_name, root_name, fields):
    records = []

    xquery_str = generate_xquery_string(conditions, fields, ds_name, root_name)

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
                error_flag = 0

                for entry_dom in doc.findall("result"):
                    row = {}

                    for field in fields:
                        tag = field.replace("/", "_")
                        display_column = ds_name + "." + field
                        container_nodes = entry_dom.findall(f".//{tag}")

                        if not container_nodes:
                            row[field] = None
                            continue

                        values = []
                        # print(container_nodes)
                        for cn in container_nodes:
                            # print(f"cn: {etree.tostring(cn)}")
                            elem_dict = xmltodict.parse(etree.tostring(cn))
                            if(field == root_name):
                                elem_dict = {root_name: elem_dict}
                            elem_root = list(elem_dict.values())[0]
                            # print(f"elem_dict: {elem_dict}")
                            
                                
                            # print(elem_root)
                            child_entries = []
                            if(elem_root is None):
                                error_flag = 1
                                raise Exception(f"Empty element found in {xml_file} for {field}")
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
                                            break
                            values.extend(child_entries)
                        # print(f"values: {values}")
                        row[display_column] = values
                    records.append(row)

            except Exception as e:
                if(error_flag == 1):
                    raise e
                print(f"Warning file {xml_file} not read. Error: {e}")
    # print(records)
    return pd.DataFrame(records)