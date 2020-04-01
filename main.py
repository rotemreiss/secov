#!/usr/bin/python
# coding=utf-8
import argparse
import re
import os
import db
import hashlib


def banner():
    print("""                                        

███████╗███████╗ ██████╗ ██████╗ ██╗   ██╗
██╔════╝██╔════╝██╔════╝██╔═══██╗██║   ██║
███████╗█████╗  ██║     ██║   ██║██║   ██║
╚════██║██╔══╝  ██║     ██║   ██║╚██╗ ██╔╝
███████║███████╗╚██████╗╚██████╔╝ ╚████╔╝ 
╚══════╝╚══════╝ ╚═════╝ ╚═════╝   ╚═══╝  
                                          
           # Coded By Rotem Reiss - @2RS3C
    """)


def dir_path(path):
    if os.path.isdir(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"readable_dir:{path} is not a valid path")


def get_code_file_names(path, extensions):
    code_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(extensions):
                 code_files.append(os.path.join(root, file))
    return code_files


def generate_route_uniqid(route):
    unique_route_str = route["file_path"] + "-" + route["route"] + "-" + route["http_method"]
    uniqid = hashlib.md5(unique_route_str.encode())
    return uniqid.hexdigest()


def grep_code_annotations(filepath, regex, base_path):
    res = []
    base_route = ""

    base_path_len = len(base_path)
    with open(filepath, encoding="ISO-8859-1") as f:
        for line in f:
            if regex.search(line):
                is_base_route = line.startswith("@Request")
                clean_ann = line.lstrip(" ").rstrip("\n")

                # Extract the route from the annotation's content
                route = get_route_from_annotation(clean_ann, is_base_route)

                # Save our base route to a variable so it will be later used to replace the base route placeholder
                if is_base_route:
                    base_route = route

                route_dict = {
                    "file_path": filepath[base_path_len:].lstrip('/'),
                    "annotation": clean_ann,
                    # Note that the returned path can be relative to RequestMapping or absolute
                    # "route": get_route_from_annotation(clean_ann) if not is_base_route else "",
                    "route": route,
                    "is_base_route": is_base_route,
                    "http_method": "" if is_base_route else re.search(r'@([a-zA-z]+)Mapping', line).group(1).upper()
                }

                # Generate a uniqid for the route
                route_dict["uniqid"] = generate_route_uniqid(route_dict)

                res.append(route_dict)

    # Replace the [BASEPATH] placeholder with the actual base path
    for ann in res:
        ann["route"] = ann["route"].replace("[BASEPATH]", base_route)

    return res


def grep_test_annotations(filepath, regex):
    res = []

    with open(filepath, encoding="ISO-8859-1") as f:
        for line in f:
            if regex.search(line):
                clean_ann = line.lstrip(" ").rstrip("\n").replace(" ", "")

                # Get the inner content of the annotation and split it to list
                ann_content = clean_ann[14:-1].split(',')

                # Extract the coverage data from the annotation's content
                res.append({
                    "annotation": clean_ann,
                    # Clean anything but the values
                    "route": ann_content[0][6:-1],
                    "http_method": ann_content[1][8:-1].upper()
                })

    return res


# @todo Refactor and remove the ugly type option
def grep_annotations_multiple_files(files_list, regex, base_path, grep_type):
    annotations_list = []
    for f in files_list:
        annotations = []
        if grep_type is "code":
            annotations = grep_code_annotations(f, regex, base_path)
        elif grep_type is "tests":
            annotations = grep_test_annotations(f, regex)

        if annotations:
            annotations_list.extend(annotations)
    return annotations_list


def get_route_annotation_content(annotation):
    # Get the content of the route annotation
    jave_route_content_regex = re.compile(r'@(.)+Mapping(\((.)+\))?')
    content = re.search(jave_route_content_regex, annotation).group(2)

    # If the annotation has no content - return an empty route
    if not content:
        return ""

    # Remove spaces, parenthesis, quotes and curly braces
    return content \
        .replace('(', '') \
        .replace(')', '') \
        .replace('\'', '') \
        .replace('"', '') \
        .replace(' ', '')


def get_first_route(route):
    if route.startswith('{'):
        return route.lstrip('{').rstrip('}').split(',')[0]
    elif route.startswith('/'):
        return route
    else:
        return ""


def get_route_from_annotation(annotation, is_base_route):
    content = get_route_annotation_content(annotation)

    rel_placeholder = "[BASEPATH]" if not is_base_route else ""

    # Now do the heavy lifting - extract the path/s from the content
    value_el = re.search(r'value=((.)+),', content)
    path_el = re.search(r'path=((.)+),', content)
    if value_el:
        # Relative path - return with our placeholder
        return rel_placeholder + get_first_route(value_el.group(1))
    elif path_el:
        # Absolute path, return as is
        return get_first_route(path_el.group(1))
    else:
        # Relative path - return with our placeholder
        return rel_placeholder + get_first_route(content)


def main():
    parser = argparse.ArgumentParser(description='Calculates the security coverage of a Java project.')
    parser.add_argument('-p', '--project', help='A system identifier for the project.', dest='project',
                        required=True)
    parser.add_argument('-d', '--path', help='The project directory to analyze.', type=dir_path, dest='project_dir', default='./')
    parser.add_argument('-ce', '--code-extensions', help='The code files extensions.', default=['java,class'], type=str, dest='code_extensions')
    parser.add_argument('-te', '--test-extensions', help='The test files extensions.', default=['groovy'], type=str, dest='test_extensions')

    args = parser.parse_args()

    # Print our banner
    banner()

    #@todo Extend to support @RequestHeader and @RequestParam

    code_ext = args.code_extensions.split(",") if "," in args.code_extensions else args.code_extensions
    code_files = get_code_file_names(args.project_dir, tuple(code_ext))
    # @todo Split to a mappings file (yaml/json/..)
    java_route_regex = re.compile(r'@(.)+Mapping')

    routes = grep_annotations_multiple_files(code_files, java_route_regex, args.project_dir, 'code')
    # for route in routes:
    #     print(route)

    # Get the tests coverage annotations
    test_annotation_regex = re.compile(r'@CoveredRoute')
    test_ext = args.test_extensions.split(",") if "," in args.test_extensions else args.test_extensions
    test_files = get_code_file_names(args.project_dir, tuple(test_ext))
    test_annotations = grep_annotations_multiple_files(test_files, test_annotation_regex, args.project_dir, 'tests')

    # Init DB.
    db.db_install()
    db.connect()

    pid = db.insert_project(args.project)
    # We are clearing all the data and then adding the new one to simplify things.
    db.clear_project_data(pid)

    # Insert the routes and the tests to the DB
    db.insert_routes(routes, pid)
    db.insert_tests(test_annotations, pid)

    db.close()


if __name__ == "__main__":
    main()