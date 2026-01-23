import os
import sys
import paramiko
from paramiko import SSHClient, AutoAddPolicy

# Set the project root 
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

# Local path
DEFAULT_LOCAL_DIR = os.path.join(ROOT_DIR, "data/raw")
LOCAL_DIR = os.getenv("LOCAL_DIR", DEFAULT_LOCAL_DIR)
os.makedirs(LOCAL_DIR, exist_ok=True)

# Get credentials from environment variables
SFTP_HOST = os.getenv("SFTP_HOST")
SFTP_PORT = int(os.getenv("SFTP_PORT", "22"))
SFTP_USERNAME = os.getenv("SFTP_USERNAME")
SFTP_PASSWORD = os.getenv("SFTP_PASSWORD")
REMOTE_DIR = os.getenv("REMOTE_DIR", "/remote/path/to/csvs/")


def get_ssh_client():
    """Create and configure SSH client with host key verification."""
    client = SSHClient()
    
    # Option A: Use known_hosts file
    known_hosts_path = os.path.expanduser('~/.ssh/known_hosts')
    if os.path.exists(known_hosts_path):
        client.load_host_keys(known_hosts_path)
        print(f"✓ Loaded host keys from {known_hosts_path}")
    
    # Option B: Use host key from environment (CI/CD)
    elif os.getenv("SFTP_HOST_KEY"):
        import tempfile
        host_key = os.getenv("SFTP_HOST_KEY")
        temp_known_hosts = os.path.join(tempfile.gettempdir(), 'known_hosts')
        with open(temp_known_hosts, 'w') as f:
            f.write(f"{os.getenv('SFTP_HOST')} {host_key}\n")
        client.load_host_keys(temp_known_hosts)
        print("✓ Using host key from environment")
    
    else:
        print("✗ No host key verification available")
        print(f"  Run: ssh-keyscan {os.getenv('SFTP_HOST')} >> ~/.ssh/known_hosts")
        sys.exit(1)
    
    # Reject unknown hosts (secure)
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    
    return client


def fetch_csv_files():
    """Download CSV files using Paramiko."""
    # Get credentials
    SFTP_HOST = os.getenv("SFTP_HOST")
    SFTP_PORT = int(os.getenv("SFTP_PORT", "22"))
    SFTP_USERNAME = os.getenv("SFTP_USERNAME")
    SFTP_PASSWORD = os.getenv("SFTP_PASSWORD")
    REMOTE_DIR = os.getenv("REMOTE_DIR", "/remote/path/to/csvs/")
    LOCAL_DIR = os.getenv("LOCAL_DIR", "./data/raw/")
    
    if not all([SFTP_HOST, SFTP_USERNAME, SFTP_PASSWORD]):
        print("✗ Missing SFTP credentials")
        return 1
    
    os.makedirs(LOCAL_DIR, exist_ok=True)
    
    try:
        # Create SSH client
        client = get_ssh_client()
        
        # Connect
        client.connect(
            hostname=SFTP_HOST,
            port=SFTP_PORT,
            username=SFTP_USERNAME,
            password=SFTP_PASSWORD
        )
        print(f"✓ Connected to {SFTP_HOST}")
        
        # Open SFTP session
        sftp = client.open_sftp()
        
        try:
            # Change to remote directory
            sftp.chdir(REMOTE_DIR)
            print(f"✓ Changed to remote directory: {REMOTE_DIR}")
            
            # List CSV files
            csv_files = [f for f in sftp.listdir() if f.endswith('.csv')]
            
            if not csv_files:
                print(f"⚠ No CSV files found in {REMOTE_DIR}")
                return 0
            
            print(f"Found {len(csv_files)} CSV file(s): {csv_files}")
            
            # Download each CSV
            success_count = 0
            for file in csv_files:
                local_path = os.path.join(LOCAL_DIR, file)
                try:
                    print(f"Downloading {file} -> {local_path}")
                    sftp.get(file, local_path)
                    
                    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                        print(f"✓ Successfully downloaded {file}")
                        success_count += 1
                    else:
                        print(f"✗ Download failed or file is empty: {file}")
                except Exception as e:
                    print(f"✗ Error downloading {file}: {e}")
            
            print(f"Download complete: {success_count}/{len(csv_files)} files successful")
            
            return 0 if success_count == len(csv_files) else 1
            
        finally:
            sftp.close()
            
    except Exception as e:
        print(f"✗ SFTP connection failed: {e}")
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    exit_code = fetch_csv_files()
    sys.exit(exit_code)
