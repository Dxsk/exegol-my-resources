#!/usr/bin/env python3
import os
import sys
import argparse
import logging
import colorama
from smb.SMBConnection import SMBConnection
from smb.smb_structs import OperationFailure

# Initialize colorama for terminal colors
colorama.init()

# Color definitions
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': colorama.Fore.BLUE,
        'INFO': colorama.Fore.GREEN,
        'WARNING': colorama.Fore.YELLOW,
        'ERROR': colorama.Fore.RED,
        'CRITICAL': colorama.Fore.RED + colorama.Style.BRIGHT
    }

    def format(self, record):
        log_message = super().format(record)
        return self.COLORS.get(record.levelname, colorama.Fore.WHITE) + log_message + colorama.Style.RESET_ALL

# Configure logging with colors
formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

file_handler = logging.FileHandler("smb_script.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, stream_handler]
)
logger = logging.getLogger("SMBScript")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Script to connect to SMB share, list directory structure and download all files")
    parser.add_argument("-u", "--user", required=True, help="SMB username")
    parser.add_argument("-p", "--password", required=True, help="SMB password")
    parser.add_argument("-d", "--domain", required=True, help="SMB domain")
    parser.add_argument("-s", "--server", required=True, help="SMB server IP or hostname")
    parser.add_argument("-o", "--output", default="smb_downloads", help="Output directory for downloads (default: smb_downloads)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode (more details)")
    parser.add_argument("-f", "--folder", help="Specific folder to download (relative path to share)")
    parser.epilog = "Example usage: python smb_downloads.py -u \"$USER\" -p \"$PASSWORD\" -d \"$DOMAIN\" -s \"$TARGET\""
    return parser.parse_args()

def connect_to_smb(user, password, domain, server):
    try:
        logger.info(f"Attempting to connect to {server} with user {domain}\\{user}")
        
        if user.lower() == "guest":
            password = ""
        
        configs = [
            {"domain": domain, "use_ntlm_v2": True, "is_direct_tcp": True},
            {"domain": "", "use_ntlm_v2": True, "is_direct_tcp": True},
            {"domain": domain, "use_ntlm_v2": True, "is_direct_tcp": False},
            {"domain": "", "use_ntlm_v2": True, "is_direct_tcp": False},
            {"domain": domain, "use_ntlm_v2": False, "is_direct_tcp": False},
            {"domain": "", "use_ntlm_v2": False, "is_direct_tcp": False}
        ]
        
        for config in configs:
            try:
                smb_version = "SMBv3" if config["is_direct_tcp"] else ("SMBv2" if config["use_ntlm_v2"] else "SMBv1")
                domain_info = f"with domain '{config['domain']}'" if config['domain'] else "without domain"
                
                logger.info(f"Trying to connect using {smb_version} {domain_info}")
                conn = SMBConnection(user, password, "client", server, **config)
                
                if conn.connect(server, 445):
                    logger.info(f"Connection successful to {server} with user {user} using {smb_version} {domain_info} on port 445")
                    return conn
                
                if not config["is_direct_tcp"]:
                    if conn.connect(server, 139):
                        logger.info(f"Connection successful to {server} with user {user} using {smb_version} {domain_info} on port 139")
                        return conn
            
            except Exception as e:
                logger.debug(f"Connection attempt failed using {smb_version} {domain_info}: {str(e)}")
                continue
        
        logger.error(f"Failed to connect to {server} after trying all SMB versions")
        return None
    
    except ConnectionResetError:
        logger.error(f"Connection reset by server. Check your credentials or server availability.")
        return None
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        logger.debug(f"Tip: Verify that credential format matches what's used in nxc/smbclient-ng")
        return None

def list_shares(conn):
    try:
        logger.info("Listing available shares")
        shares = conn.listShares()
        logger.info("Available shares:")
        for share in shares:
            logger.info(f"- {share.name} ({share.comments})")
        return [share.name for share in shares]
    except Exception as e:
        logger.error(f"Error listing shares: {str(e)}")
        return []

def list_path(conn, share, path="", indent=0):
    try:
        files = conn.listPath(share, path)
        for file in files:
            if file.filename in ['.', '..']:
                continue
            
            full_path = os.path.join(path, file.filename) if path else file.filename
            logger.debug(f"{'    ' * indent}{'[D]' if file.isDirectory else '[F]'} {file.filename}")
            
            if file.isDirectory:
                list_path(conn, share, full_path, indent + 1)
    except OperationFailure as e:
        logger.warning(f"Access denied: {path} in {share}")
    except Exception as e:
        logger.error(f"Error listing {path} in {share}: {str(e)}")

def download_files(conn, share, path="", local_base="", indent=0):
    try:
        files = conn.listPath(share, path)
        for file in files:
            if file.filename in ['.', '..']:
                continue
            
            full_path = os.path.join(path, file.filename) if path else file.filename
            local_path = os.path.join(local_base, share, full_path)
            
            if file.isDirectory:
                os.makedirs(local_path, exist_ok=True)
                download_files(conn, share, full_path, local_base, indent + 1)
            else:
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                try:
                    with open(local_path, 'wb') as file_obj:
                        conn.retrieveFile(share, full_path, file_obj)
                    logger.info(f"Downloaded: {full_path} -> {local_path}")
                except Exception as e:
                    logger.error(f"Failed to download {full_path}: {str(e)}")
    except OperationFailure as e:
        logger.warning(f"Access denied: {path} in {share}")
    except Exception as e:
        logger.error(f"Error downloading from {path} in {share}: {str(e)}")

def explore_share(conn, share, folder=None):
    try:
        logger.info(f"Exploring directory structure of share {share}")
        
        if folder:
            logger.info(f"Exploration limited to folder: {folder}")
            list_path(conn, share, folder)
        else:
            list_path(conn, share)
        return True
    except Exception as e:
        logger.error(f"Error exploring share {share}: {str(e)}")
        return False

def download_share(conn, share, folder=None, output_dir=""):
    try:
        if folder:
            logger.info(f"Downloading files from folder {folder} in share {share}")
            download_files(conn, share, folder, output_dir)
        else:
            logger.info(f"Downloading files from share {share}")
            download_files(conn, share, "", output_dir)
        return True
    except Exception as e:
        logger.error(f"Error downloading from share {share}: {str(e)}")
        return False

def main():
    args = parse_arguments()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info("Starting script")
    
    conn = connect_to_smb(args.user, args.password, args.domain, args.server)
    if not conn:
        logger.error("Unable to connect to SMB server. Stopping script.")
        sys.exit(1)
    
    shares = list_shares(conn)
    
    for share in shares:
        explore_share(conn, share, args.folder)
    
    os.makedirs(args.output, exist_ok=True)
    
    for share in shares:
        download_share(conn, share, args.folder, args.output)
    
    conn.close()
    logger.info("Script completed successfully")

if __name__ == "__main__":
    main()

