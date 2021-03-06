#!/usr/bin/python
# coding=utf-8
import argparse
import re
import os
import hashlib
import shutil
from git import Repo
from secov import db


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


def copytree(src, dst, symlinks=False, ignore=None):
    """ Copy an entire directory.
    Used for cloning our project directory before the parsing starts.
    """
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


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


def clean_multiline_annotations(filepath, regex):
    """ Support multiline annotations.
    Multiline annotations must be cleaned for our parsing to work.
    This is a recursive method that runs until there's nothing else to clean.
    """
    is_multiline_found = False

    updated_code = ""
    # Iterate over the lines and search for unclosed annotations.
    with open(filepath, encoding="ISO-8859-1") as f:
        for line in f:
            if regex.search(line):
                if not line.rstrip().endswith(")"):
                    # Found unclosed annotation - flag it and strip the new line character/s.
                    is_multiline_found = True
                    line = line.rstrip()

            updated_code += line

    # Found multiline annotation - save the updated content to the source code and rerun the clean method.
    if is_multiline_found:
        f = open(filepath, "w")
        f.write(updated_code)
        f.close()

        clean_multiline_annotations(filepath, regex)



def grep_code_annotations(filepath, regex, base_path):
    res = []
    base_route = ""

    clean_multiline_annotations(filepath, regex)

    base_path_len = len(base_path)
    with open(filepath, encoding="ISO-8859-1") as f:
        for line in f:
            if regex.search(line):
                clean_ann = line.lstrip(" ").rstrip("\n").replace("  ", "")
                is_base_route = clean_ann.startswith("@Request")

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
                    "http_method": get_method_from_annotation(clean_ann, is_base_route)
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


def grep_annotations_multiple_files(files_list, regex, base_path, grep_type):
    """
    :todo Refactor and remove the ugly type option
    """
    annotations_list = []
    for f in files_list:
        annotations = []
        if grep_type == "code":
            annotations = grep_code_annotations(f, regex, base_path)
        elif grep_type == "tests":
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


def get_method_from_annotation(annotation, is_base_route):
    http_method = ""
    if is_base_route:
        content = get_route_annotation_content(annotation)
        method_val = re.search(r'method=(.*?),', content)
        http_method = method_val.group(1) if method_val else ""
        # print(http_method)
    else:
        http_method = re.search(r'@([a-zA-z]+)Mapping', annotation).group(1).upper()

    # Make sure that it matches one of the common HTTP methods.
    method_val = re.search(r'GET|HEAD|POST|PUT|DELETE|CONNECT|OPTIONS|TRACE|PATCH', http_method)
    http_method = method_val.group(0) if method_val else ""

    return http_method


def get_route_from_annotation(annotation, is_base_route):
    content = get_route_annotation_content(annotation)

    rel_placeholder = "[BASEPATH]" if not is_base_route else ""

    # Now do the heavy lifting - extract the path/s from the content
    value_el = re.search(r'value=(.*?),', content)
    path_el = re.search(r'path=(.*?),', content)
    if value_el:
        # Relative path - return with our placeholder
        return rel_placeholder + get_first_route(value_el.group(1))
    elif path_el:
        # Absolute path, return as is
        return get_first_route(path_el.group(1))
    else:
        # Relative path - return with our placeholder
        return rel_placeholder + get_first_route(content)


def cleanup_tmp(tmp_project_dir):
    # Cleanup - remove our temp project directory.
    shutil.rmtree(tmp_project_dir, True)


def main(db_path, project, git_repo, git_branch="master", project_dir=False, code_extensions="java,class", test_extensions="groovy"):

    # Print our banner
    banner()

    # Clone repository in case of a git repository instead of a local URI.
    if git_repo:
        if not project_dir:
            base_path = os.path.dirname(os.path.realpath(__file__))
            project_dir = f'{base_path}/../projects'

        # Create a project dir in the projects dir.
        project_dir = f'{project_dir}/{project}'

        # Delete any existing directory if exists.
        shutil.rmtree(project_dir, True)
        Repo.clone_from(git_repo, project_dir, branch=git_branch)

    tmp_project_dir = f'{project_dir}_tmp'
    cleanup_tmp(tmp_project_dir)
    copytree(project_dir, tmp_project_dir)

    #@todo Extend to support @RequestHeader and @RequestParam

    code_ext = code_extensions.split(",") if "," in code_extensions else code_extensions
    code_files = get_code_file_names(tmp_project_dir, tuple(code_ext))

    # @todo Split to a mappings file (yaml/json/..)
    java_route_regex = re.compile(r'@(.)+Mapping')

    routes = grep_annotations_multiple_files(code_files, java_route_regex, tmp_project_dir, 'code')

    # Get the tests coverage annotations
    test_annotation_regex = re.compile(r'@CoveredRoute')
    test_ext = test_extensions.split(",") if "," in test_extensions else test_extensions
    test_files = get_code_file_names(tmp_project_dir, tuple(test_ext))
    test_annotations = grep_annotations_multiple_files(test_files, test_annotation_regex, tmp_project_dir, 'tests')

    # Init DB.
    db.db_install(db_path)
    db.connect()

    pid = db.insert_project(project)
    # We are clearing all the data and then adding the new one to simplify things.
    db.clear_project_data(pid)

    # Insert the routes and the tests to the DB
    db.insert_routes(routes, pid)
    db.insert_tests(test_annotations, pid)

    db.close()

    cleanup_tmp(tmp_project_dir)

    # Print the results
    print("[+] Found and stored {} routes.".format(str(len(routes))))
    print("[+] Found and stored {} tests.".format(str(len(test_annotations))))


def interactive():
    parser = argparse.ArgumentParser(description='Calculates the security coverage of a Java project.')
    parser.add_argument('-p', '--project', help='A system identifier for the project.', dest='project',
                        required=True)
    parser.add_argument('-g', '--git-repo', help='A Git repository URL instead of a local directory.', dest='git_repo')
    parser.add_argument('-b', '--git-branch', help='A specific git branch to clone.', dest='git_branch',
                        default="master")
    parser.add_argument('-d', '--path', help='The project directory to analyze.',
                        type=dir_path,
                        dest='project_dir')

    parser.add_argument('-db', '--database', help='Database file path (absolute path).', dest='db_path',
                        default="/tmp/secov.sqlite")

    parser.add_argument('-ce', '--code-extensions', help='The code files extensions.', default='java,class',
                        type=str,
                        dest='code_extensions')
    parser.add_argument('-te', '--test-extensions', help='The test files extensions.', default='groovy',
                        type=str,
                        dest='test_extensions')

    args = parser.parse_args()

    # Validate some of our args.
    if not args.git_repo and not args.project_dir:
        parser.error('You should use --git-repo or --path, none specified.')

    main(args.db_path, args.project, args.git_repo, args.git_branch, args.project_dir, args.code_extensions, args.test_extensions)


if __name__ == "__main__":
    interactive()
