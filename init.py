#!/usr/bin/python3.6

import os
import sys
import yaml
import argparse
import getpass
import subprocess
import json
import shutil

def init_database(database, username, password):
    def create_user(username, password):
        query = """
            DO $$ BEGIN
                CREATE USER {username} WITH PASSWORD '{password}';
                EXCEPTION WHEN DUPLICATE_OBJECT THEN RAISE NOTICE 'The user <{username}> already exists.';
            END $$;
        """.format(username=username, password=password)

        command = ["sudo", "-u", "postgres", "psql", "--username", "postgres", "-c", query]
        return subprocess.run(command, stdout=subprocess.DEVNULL).returncode

    def check_database(database):
        query = """
            SELECT 1 FROM pg_database WHERE datname='{}';
        """.format(database)

        command = ["sudo", "-u", "postgres", "psql", "--username", "postgres", "-tAc", query]
        return len(subprocess.check_output(command)) > 0

    def create_database(database, owner):
        query = """
            CREATE DATABASE {} WITH OWNER = '{}';
        """.format(database, owner)

        command = ["sudo", "-u", "postgres", "psql", "--username", "postgres", "-c", query]
        return subprocess.run(command).returncode

    def modify_schema_privileges(database, username):
        query = """
            ALTER SCHEMA public OWNER TO {};
        """.format(username)

        command = ["sudo", "-u", "postgres", "psql", "--username", "postgres", "--dbname", database, "-c", query]
        return subprocess.run(command).returncode

    def modify_largeobject_privileges(database, username):
        query = """
            GRANT SELECT ON pg_largeobject TO {};
        """.format(username)

        command = ["sudo", "-u", "postgres", "psql", "--username", "postgres", "--dbname", database, "-c", query]
        return subprocess.run(command).returncode

    print("Creating database user {}".format(username))
    if(create_user(username, password)):
        print("Could not create database user.")
        exit(1)

    print("Creating database {}".format(database))
    if(check_database(database)):
        print("Database {} already exists.".format(database))
    else:
        if(create_database(database, username)):
            print("Could not create database {} with owner {}".format(database, username))
            exit(1)

    print("Granting schema privileges to {} on {}".format(username, database))
    if(modify_schema_privileges(database, username)):
        print("Could not modify schema privileges for user {} on database {}".format(username, database))
        exit(1)

    print("Granting largeobject privileges to {} on {}".format(username, database))
    if(modify_largeobject_privileges(database, username)):
        print("Could not modify largeobject privileges for user {} on database {}".format(username, database))
        exit(1)

def make_dir(path):
    return subprocess.run(["mkdir", "-p", path]).returncode

def configure_isolate(build_dir, first_uid, first_gid, num_boxes, cg_root):
    conf_dir = os.path.join(build_dir, "cms", "etc")
    print("Creating isolate configuration directory {}".format(conf_dir))
    if(make_dir(conf_dir)):
        print("Could not create isolate configuration directory.")
        exit(1)

    if(make_dir(os.path.join(build_dir, "cms", "lib", "isolate"))):
        print("Could not create isolate box directory.")
        exit(1)

    with open(os.path.join(conf_dir, "isolate.conf"), "w") as f:
        f.write("box_root = {}\n".format(os.path.join(build_dir, "cms", "lib", "isolate")))
        f.write("cg_root = {}\n".format(cg_root))
        f.write("first_uid = {}\n".format(first_uid))
        f.write("first_gid = {}\n".format(first_gid))
        f.write("num_boxes = {}\n".format(num_boxes))

def build_isolate(build_dir, isolate_dir):
    if make_dir(os.path.join(build_dir, "cms", "bin")):
        print("Could not create isolate build directory.")
        exit(1)

    sources = [os.path.join(isolate_dir, x) for x in ["isolate.c", "util.c", "rules.c", "cg.c", "config.c"]]
    command = ["gcc", "-std=c99", "-D_GNU_SOURCE", '-DVERSION="0"', 
            '-DYEAR="0"', '-DBUILD_DATE="0"', '-DBUILD_COMMIT="0"', 
            '-DCONFIG_FILE="{}"'.format(os.path.join(build_dir, "cms", "etc", "isolate.conf")), 
            "-o", os.path.join(build_dir, "cms", "bin", "isolate")] + sources + ["-lcap"]
    return subprocess.run(command).returncode

def set_isolate_permissions(build_dir, username):
    command = ["sudo", "chmod", "770", os.path.join(build_dir, "cms", "bin", "isolate")]
    if subprocess.run(command).returncode:
        print("Could not change isolate executable permissions to 770.")
        exit(1)
    
    command = ["sudo", "chown", "root:{}".format(username), os.path.join(build_dir, "cms", "bin", "isolate")]
    if subprocess.run(command).returncode:
        print("Could not change owner of isolate executable.")
        exit(1)

    command = ["sudo", "chmod", "u+s", os.path.join(build_dir, "cms", "bin", "isolate")]
    if subprocess.run(command).returncode:
        print("Could not change isolate executable sticky bit.")
        exit(1)
    return 0

def make_python_env(build_dir, no_index):
    venv_dir = os.path.join(build_dir, "cms", "venv")
    command = ["python3.6", "-m", "venv", venv_dir]
    if subprocess.run(command).returncode:
        print("Could not create python3.6 virtual environment.")
        exit(1)

    packages = ["pip", "setuptools", "wheel", "future", 
            "tornado>=4.5,<4.6",
            "psycopg2>=2.7,<2.8",
            "sqlalchemy>=1.1,<1.2",
            "netifaces>=0.10,<0.11",
            "pycrypto>=2.6,<2.7", 
            "psutil>=5.4,<5.5",
            "requests>=2.18,<2.19",
            "gevent>=1.2,<1.3",
            "werkzeug>=0.14,<0.15",
            "patool>=1.12,<1.13",
            "bcrypt>=3.1,<3.2",
            "chardet>=3.0,<3.1",
            "babel>=2.4,<2.5",
            "pyxdg>=0.25,<0.26",
            "Jinja2>=2.10,<2.11",  
            "pyyaml>=3.12,<3.13"]
    command = [os.path.join(venv_dir, "bin", "pip3"), "install","--upgrade"] + packages + ["--no-binary", "psycopg2"]
    if no_index:
        command += ["--no-index"]
    if subprocess.run(command).returncode:
        print("Could not install packages")
        exit(1)

    def export_variable(f, name, value):
        command = ["echo", "export {}={};".format(name, value)]
        return subprocess.run(command, stdout=f).returncode

    with open(os.path.join(build_dir, "cms", "venv", "bin", "activate"), "a") as f:
        export_variable(f, "CMS_CONFIG", "'{}'".format(os.path.join(build_dir, "cms", "etc", "cms.conf")))
        export_variable(f, "CMS_RANKING_CONFIG", "'{}'".format(os.path.join(build_dir, "cms", "etc", "cms.ranking.conf")))
        export_variable(f, "PATH", r"$PATH:'{}'".format(os.path.join(build_dir, "cms", "bin")))
        export_variable(f, "PATH", r"$PATH:'{}'".format(os.path.join(build_dir, "cms", "lib", "scripts")))
        export_variable(f, "PATH", r"$PATH:'{}'".format(os.path.join(build_dir, "cms", "lib", "cmscontrib")))
        export_variable(f, "PYTHONPATH", r"$PYTHONPATH:'{}'".format(os.path.join(build_dir, "cms", "lib")))

    return 0

def copy_cms_sources(build_dir, cms_dir):
    def copy_dir(dir_from, dir_to):
        command = ["cp", "-rf", dir_from, dir_to]
        return subprocess.run(command).returncode

    def src_to_build(dir_from):
        return copy_dir(os.path.join(cms_dir, dir_from), os.path.join(build_dir, "cms", "lib"))

    for x in ["cms", "cmscommon", "cmscontrib", "cmsranking", "cmstaskenv", "cmstestsuite", "scripts", 
            "setup.cfg", "setup.py", "babel_mapping.cfg"]:
        src_to_build(x)

def make_cms_ranking_conf(build_dir, rank_conf):
    conf = dict()
    conf["bind_address"] = ""
    conf["http_port"] = rank_conf.get("port")
    conf["username"] = rank_conf.get("username")
    conf["password"] = rank_conf.get("password")

    with open(os.path.join(build_dir, "cms", "etc", "cms.ranking.conf"), "w") as f:    
        json.dump(conf, f, indent=2) 

def make_cms_conf(build_dir, db_conf, cms_conf, rank_conf):
    make_dir(os.path.join(build_dir, "cms", "submissions"))

    conf = dict()
    conf["temp_dir"] = "/tmp"
    conf["backdoor"] = False
    conf["cmsuser"] = getpass.getuser()

    services = dict()
    services["LogService"] = [["localhost", cms_conf.get("log_service_port")]]
    services["ScoringService"] = [["localhost", cms_conf.get("scoring_service_port")]]
    services["Checker"] = [["localhost", cms_conf.get("checker_service_port")]]
    services["EvaluationService"] = [["localhost", cms_conf.get("evaluation_service_port")]]
    services["ContestWebServer"] = [["localhost", cms_conf.get("contest_web_server_port")]]
    services["AdminWebServer"] = [["localhost", cms_conf.get("admin_web_server_port")]]
    services["ResourceService"] = [["localhost", cms_conf.get("resource_service_port")]]

    services["Worker"] = []
    for i in range(cms_conf.get("num_workers")):
        port0 = cms_conf.get("worker_service_port_begin")
        services["Worker"].append(["localhost", port0 + i])

    services["ProxyService"] = []
    for i in range(cms_conf.get("num_proxies")):
        port0 = cms_conf.get("proxy_service_port_begin")
        services["ProxyService"].append(["localhost", port0 + i])

    conf["core_services"] = services

    conf["other_services"] = { "TestFileCacher": [] }

    conf["contest_listen_address"] = [""]
    conf["contest_listen_port"] = [cms_conf.get("contest_listen_port")]
    conf["admin_listen_address"] = ""
    conf["admin_listen_port"] = cms_conf.get("admin_listen_port")
    conf["admin_cookie_duration"] = cms_conf.get("admin_cookie_duration")

    ranking_username = rank_conf.get("username")
    ranking_password = rank_conf.get("password")
    ranking_port = rank_conf.get("port")
    conf["rankings"] = [ "http://{}:{}@localhost:{}".format(ranking_username, ranking_password, ranking_port)]
    conf["https_certificate"] = None

    database_username = db_conf.get("user")
    database_password = db_conf.get("password")
    database_name = db_conf.get("name")
    conf["database"] = "postgresql+psycopg2://{}:{}@localhost:5432/{}".format(database_username, database_password, database_name)
    conf["database_debug"] = False
    conf["twophase_commit"] = False
    conf["keep_sandbox"] = False
    conf["max_file_size"] = cms_conf.get("max_file_size")
    conf["secret_key"] = cms_conf.get("secret_key")
    conf["tornado_debug"] = False
    conf["cookie_duration"] = cms_conf.get("cookie_duration")
    conf["submit_local_copy"] = cms_conf.get("submit_local_copy")
    conf["submit_local_copy_path"] = os.path.join(build_dir, "cms", "submissions")
    conf["num_proxies_used"] = 0
    conf["max_submission_length"] = cms_conf.get("max_submission_length")
    conf["max_input_length"] = cms_conf.get("max_input_length")
    conf["stl_path"] = cms_conf.get("stl_path")
    conf["max_print_length"] = 1000000
    conf["printer"] = None
    conf["paper_size"] = "A4"
    conf["max_pages_per_job"] = 10
    conf["max_jobs_per_user"] = 10
    conf["pdf_printing_allowed"] = False

    with open(os.path.join(build_dir, "cms", "etc", "cms.conf"), "w") as f:    
        json.dump(conf, f, indent=2) 

def drop_db_schema(build_dir):
    venv_bin = os.path.join(build_dir, "cms", "venv", "bin")
    command = "source {}/activate; cd {}; ./scripts/cmsDropDB -y".format(venv_bin, 
            os.path.join(build_dir, "cms", "lib"))
    subprocess.call(command, shell=True, executable="/bin/bash")

def init_db_schema(build_dir):
    venv_bin = os.path.join(build_dir, "cms", "venv", "bin")
    command = "source {}/activate; cd {}; ./scripts/cmsInitDB".format(venv_bin,
            os.path.join(build_dir, "cms", "lib"))
    subprocess.call(command, shell=True, executable="/bin/bash")

def make_scripts(build_dir):
    script = """
        #!/bin/bash
        bash -c 'source {}/activate; cd {}; ./scripts/cmsRankingWebServer;'
    """.format(os.path.join(build_dir, "cms", "venv", "bin"), os.path.join(build_dir, "cms/lib"))
    with open(os.path.join(build_dir, "cms_start_ranking.sh"), "w") as f:
        f.write(script)

    script = """
        #!/bin/bash
        bash -c "source {}/activate; cd {}; ./scripts/cmsResourceService $*;"
    """.format(os.path.join(build_dir, "cms", "venv", "bin"), os.path.join(build_dir, "cms", "lib"))
    with open(os.path.join(build_dir, "cms_start_resources.sh"), "w") as f:
        f.write(script)

    script = """
        #!/bin/bash
        pkill -f cmsRankingWebServer;
        pkill -f cmsResourceService;
    """
    with open(os.path.join(build_dir, "cms_stop.sh"), "w") as f:
        f.write(script)

    script_dir = os.path.join(build_dir, "cms", "lib", "cmscontrib")
    script = """
        #!/bin/bash
        bash -c "source {}/activate; {}/ImportContest.py $*"
    """.format(os.path.join(build_dir, "cms", "venv", "bin"), script_dir)
    with open(os.path.join(build_dir, "cms_import_contest.sh"), "w") as f:
        f.write(script)

    subprocess.run(["sudo", "chmod", "+x", os.path.join(build_dir, "cms_start_ranking.sh")])
    subprocess.run(["sudo", "chmod", "+x", os.path.join(build_dir, "cms_start_resources.sh")])
    subprocess.run(["sudo", "chmod", "+x", os.path.join(build_dir, "cms_stop.sh")])
    subprocess.run(["sudo", "chmod", "+x", os.path.join(build_dir, "cms_import_contest.sh")])

def copy_loaders(build_dir, loaders_dir):
    for filename in os.listdir(loaders_dir):
        shutil.copy(os.path.join(loaders_dir, filename), os.path.join(build_dir, "cms", "lib", "cmscontrib", "loaders", filename))

def install_cms(build_dir):
    venv_bin = os.path.join(build_dir, "cms", "venv", "bin")
    lib_dir = os.path.join(build_dir, "cms", "lib")
    command = "source {}/activate; cd {}; ./setup.py install".format(venv_bin, lib_dir)
    subprocess.call(command, shell=True, executable="/bin/bash", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    SCRIPT_PATH = os.path.dirname(__file__)
    parser = argparse.ArgumentParser(description="Initialize a cms instance.")
    parser.add_argument("--config", help="Path to the yaml configuration file.", 
            dest="config", default=os.path.join(SCRIPT_PATH,"conf.yaml"))
    parser.add_argument("--build_dir", help="Build directory.", dest="build_dir", default=".")
    parser.add_argument("--isolate_source", help="Isolate source directory.", 
            default=os.path.join(SCRIPT_PATH, "src/isolate"), dest="isolate_source")
    parser.add_argument("--cms_source", help="CMS-DEV source directory.",
            default=os.path.join(SCRIPT_PATH, "src/cms"), dest = "cms_source")
    parser.add_argument("--dropdb", help="If selected, resets the database instance.",
            default=False, dest="dropdb", action="store_true")
    parser.add_argument("--loaders", help="Loaders directory.",
            default=os.path.join(SCRIPT_PATH, "loaders"), dest="loaders")
    parser.add_argument("--no-index", help="Don't usre pip3 index", 
            default=False, dest="noindex", action="store_true")

    parsed_args = parser.parse_args(sys.argv[1:])
    try:
        conf = yaml.load(open(parsed_args.config, "r"), Loader=yaml.Loader)
    except IOError:
        print("Config file not found.")

    database_name = conf.get("database").get("name", getpass.getuser())
    database_user = conf.get("database").get("user", getpass.getuser())
    database_pass = conf.get("database").get("password", getpass.getuser())

    init_database(database_name, database_user, database_pass)

    build_directory = os.path.abspath(parsed_args.build_dir)
    isolate_first_uid = conf.get("isolate").get("first_uid")
    isolate_first_gid = conf.get("isolate").get("first_gid")
    isolate_num_boxes = conf.get("isolate").get("num_boxes")
    isolate_cg_root = conf.get("isolate").get("cg_root")

    print("Creating isolate configuration.")
    configure_isolate(build_directory, isolate_first_uid, isolate_first_gid, isolate_num_boxes, isolate_cg_root)

    print("Building isolate.")
    isolate_source_directory = os.path.abspath(parsed_args.isolate_source)
    build_isolate(build_directory, isolate_source_directory)

    print("Changing isolate executable permissions.")
    set_isolate_permissions(build_directory, getpass.getuser())

    print("Creating python3.6 virtual env.")
    make_python_env(build_directory, parsed_args.noindex)

    cms_source_directory = os.path.abspath(parsed_args.cms_source)

    print("Copying cms sources")
    copy_cms_sources(build_directory, cms_source_directory)

    print("Compiling configuration files")
    make_cms_ranking_conf(build_directory, conf.get("rankings"))
    make_cms_conf(build_directory, conf.get("database"), conf.get("cms"), conf.get("rankings"))

    if parsed_args.dropdb:
        print("Dropping DB schema")
        drop_db_schema(build_directory)

    print("Creating DB schema")
    init_db_schema(build_directory)

    print("Creating start script")
    make_scripts(build_directory)

    loaders_directory = os.path.abspath(parsed_args.loaders)

    print("Copying loaders")
    copy_loaders(build_directory, loaders_directory)

    print("Installing cms in build directory")
    install_cms(build_directory)

if __name__ == "__main__":
    main()

