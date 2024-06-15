
import argparse
import os
import stat
import base64
import platform
import requests
import sys
from getpass import getpass

HISTORY_FILE = "/var/lib/unapt/history.txt"

# Define BIN_DIR based on platform
if platform.system() == 'Linux':
    BIN_DIR = "/usr/local/bin"
elif platform.system() == 'Android' and 'TERMUX' in os.environ:
    BIN_DIR = "/data/data/com.termux/files/usr/bin"
else:
    print("Unsupported platform.")
    sys.exit(1)

def download_file(base_url, filename):
    url = f"{base_url}/{filename}"
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {filename} successfully.")
    else:
        print(f"Failed to download {filename}. Status code: {response.status_code}")

def install(args):
    base_url = "https://tont-linux.github.io/unapt/unapt"
    filename = args.filename
    download_file(base_url, filename)
    try:
        os.makedirs(BIN_DIR, exist_ok=True)
        os.rename(filename, os.path.join(BIN_DIR, filename))
        file_path = os.path.join(BIN_DIR, filename)
        os.chmod(file_path, os.stat(file_path).st_mode | stat.S_IEXEC)
        print(f"File '{filename}' has been downloaded and moved to '{BIN_DIR}' directory.")
        with open(HISTORY_FILE, "a") as f:
            f.write(f"{filename}\n")
    except Exception as e:
        print(f"An error occurred: {e}")

def update(args):
    base_url = "https://tont-linux.github.io/unapt/unapt"
    filename = args.filename
    try:
        os.remove(os.path.join(BIN_DIR, filename))
    except FileNotFoundError:
        pass
    download_file(base_url, filename)
    try:
        os.makedirs(BIN_DIR, exist_ok=True)
        os.rename(filename, os.path.join(BIN_DIR, filename))
        file_path = os.path.join(BIN_DIR, filename)
        os.chmod(file_path, os.stat(file_path).st_mode | stat.S_IEXEC)
        print(f"File '{filename}' has been updated and moved to '{BIN_DIR}' directory.")
        remove_from_history(filename)
        with open(HISTORY_FILE, "a") as f:
            f.write(f"{filename}\n")
    except Exception as e:
        print(f"An error occurred: {e}")

def remove(args):
    file_name = args.filename
    try:
        os.remove(os.path.join(BIN_DIR, file_name))
        print(f"File '{file_name}' has been removed successfully.")
        remove_from_history(file_name)
    except FileNotFoundError:
        print(f"File '{file_name}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def list_files(args):
    print("List of downloaded files:")
    try:
        with open(HISTORY_FILE, "r") as f:
            for line in f:
                print(line.strip())
    except FileNotFoundError:
        print("No history found.")

def upload(args):
    filename = args.filename
    github_username = input("Enter your GitHub username: ")
    github_password = getpass("Enter your GitHub password: ")
    
    url = "https://api.github.com/repos/Tony-Linux/unapt/contents/unapt/" + filename
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    auth = (github_username, github_password)
    
    try:
        with open(filename, "rb") as file:
            content = base64.b64encode(file.read()).decode()
        
        data = {
            "message": f"Upload {filename}",
            "content": content,
            "branch": "main"
        }
        
        response = requests.put(url, headers=headers, json=data, auth=auth)
        if response.status_code == 201:
            print(f"File '{filename}' uploaded successfully. Now you can wait 24 hours for Linux developers to verify this.")
            
            pull_request_url = "https://api.github.com/repos/Tony-Linux/unapt/pulls"
            pull_request_data = {
                "title": f"Add {filename}",
                "body": f"Add {filename} to the repository",
                "head": "main",
                "base": "main"
            }
            pull_response = requests.post(pull_request_url, headers=headers, json=pull_request_data, auth=auth)
            if pull_response.status_code == 201:
                print("Pull request created successfully.")
            else:
                print("Failed to create pull request.")
        else:
            print(f"Failed to upload file. Status Code: {response.status_code}")
            print("Error reason: ", response.json().get('message', 'Unknown error'))
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def remove_from_history(filename):
    try:
        with open(HISTORY_FILE, "r") as f:
            lines = f.readlines()
        with open(HISTORY_FILE, "w") as f:
            for line in lines:
                if line.strip() != filename:
                    f.write(line)
    except FileNotFoundError:
        pass

def main():
    parser = argparse.ArgumentParser(description="Download or manage files.")
    subparsers = parser.add_subparsers(title="commands", dest="command")

    install_parser = subparsers.add_parser("install", help="Download a file")
    install_parser.add_argument("filename", help="The name of the file to download")

    update_parser = subparsers.add_parser("update", help="Update a file")
    update_parser.add_argument("filename", help="The name of the file to update")

    remove_parser = subparsers.add_parser("remove", help="Remove a file")
    remove_parser.add_argument("filename", help="The name of the file to remove")

    list_parser = subparsers.add_parser("list", help="List installed files")

    upload_parser = subparsers.add_parser("upload", help="Upload a file to the repository")
    upload_parser.add_argument("filename", help="The name of the file to upload")

    parser.add_argument("--help", action="help", help="Show this help message and exit")

    args = parser.parse_args()

    if args.command == "install":
        install(args)
    elif args.command == "update":
        update(args)
    elif args.command == "remove":
        remove(args)
    elif args.command == "list":
        list_files(args)
    elif args.command == "upload":
        upload(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
