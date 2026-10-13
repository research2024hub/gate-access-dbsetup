# Host this MySQL database on EC2

This guide hosts **MySQL on one EC2 server** using Docker, with a persistent data
volume. This folder has models and migrations but no web/API server, so there is
no website port or HTTP process to start. Hosting your actual backend requires
its code and entrypoint. For production availability and managed backups, evaluate
Amazon RDS for MySQL separately; this single-server setup requires you to maintain
backups, updates, monitoring, disk capacity, and recovery.

## 1. Launch an EC2 instance

In AWS Console → EC2 → Instances → Launch instances:

- Name: `gate-access-mysql`.
- AMI: Ubuntu Server 24.04 LTS, 64-bit x86.
- Initial learning/small-workload size: `t3.small` (2 GiB RAM). Size from actual
  database size and traffic for production; monitor memory and CPU credits.
- Create/download an SSH key pair, e.g. `gate-access.pem`. Store it privately.
- Use an encrypted gp3 EBS root volume, initially at least 30 GiB for a small DB;
  allow more for the source data, indexes, Docker images, and backups. For important
  data, use a separate encrypted data volume and arrange its lifecycle explicitly.
- Put the instance in your selected VPC/subnet with connectivity for package/image
  downloads. For this introductory SSH setup, use a public IPv4 address and an
  internet gateway route. Production can use a private subnet and Systems Manager.
- Security group: inbound TCP **22 only from your current public IP /32**.
  Do not add public 3306, HTTP, or HTTPS rules for this database-only project.
- Require IMDSv2 in instance metadata settings. Launch and wait for status checks.

EC2, EBS, public IPv4, snapshots, and data transfer can incur charges. Check the
AWS estimate for your region; do not assume this instance is free-tier eligible.
Stopping EC2 does not remove EBS storage charges.

See [AWS security group guidance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-rules-reference.html)
and [SSH connection methods](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/connect.html).

## 2. Connect from your Mac

Replace `EC2_PUBLIC_IP` with the address shown in the console:

```bash
chmod 400 ~/Downloads/gate-access.pem
ssh -i ~/Downloads/gate-access.pem ubuntu@EC2_PUBLIC_IP
```

Use `ubuntu` for this Ubuntu AMI. Verify the host key fingerprint when connecting.
If SSH times out, check your current public IP, inbound rule, public address,
subnet route, and instance status.

## 3. Install Docker and Python on EC2

Run on the EC2 shell (the Docker repository setup follows the
[official Ubuntu installation guide](https://docs.docker.com/engine/install/ubuntu/)):

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl python3-venv
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF_DOCKER
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: noble
Components: stable
Architectures: amd64
Signed-By: /etc/apt/keyrings/docker.asc
EOF_DOCKER
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
mkdir -p ~/gate_access_dbsetup
```

## 4. Upload project files

In a **new terminal on your Mac**, run from the project folder:

```bash
cd ~/Downloads/gate_access_dbsetup
rsync -av -e 'ssh -i ~/Downloads/gate-access.pem' \
  --exclude='.env*' --exclude='venv/' --exclude='.venv/' \
  --exclude='archive/' --exclude='__pycache__/' --exclude='.git/' \
  --exclude='.aider*' --exclude='.repomap*' --exclude='.claude/' \
  --exclude='.DS_Store' \
  ./ ubuntu@EC2_PUBLIC_IP:~/gate_access_dbsetup/
scp -i ~/Downloads/gate-access.pem .env.example \
  ubuntu@EC2_PUBLIC_IP:~/gate_access_dbsetup/.env.example
```

This excludes local credentials and the Mac virtual environment. On **EC2**:

```bash
cd ~/gate_access_dbsetup
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-transfer.txt
cp .env.example .env
chmod 600 .env
nano .env
```

Set MYSQL_PASSWORD and MYSQL_ROOT_PASSWORD to different random passwords. Generate
values with `openssl rand -hex 32`. Leave MYSQL_HOST=127.0.0.1 and MYSQL_PORT=3306.
Set SOURCE_DATABASE_URL to the PostgreSQL source for transfer, using the editor.
The source must be reachable from EC2 and accept the connection; use its TLS
settings and restrict any source firewall rule to the EC2 address/security group.
Do not expose PostgreSQL publicly just to perform the copy. An alternative is to
run the transfer from your Mac through the MySQL SSH tunnel in step 7.

## 5. Start MySQL and transfer records

On EC2, in the project folder with the virtual environment active:

```bash
sudo docker compose up -d --wait
python -m alembic upgrade head
python -m scripts.transfer_postgres --check
```

For your existing database, complete the backup/write-freeze steps in the
[transfer guide](MYSQL_MIGRATION.md), then:

```bash
python -m scripts.transfer_postgres --copy
python -m alembic current
```

Expected migration revision: `mysql_0001`. Do not seed the target before transfer.
If intentionally starting fresh instead, use `python -m scripts.seed` in place
of the transfer. Do not run both paths.

## 6. Understand persistence and access

`compose.yaml` binds MySQL to **127.0.0.1:3306**, accessible only from EC2 itself
or through an SSH tunnel. The `mysql_data` Docker volume retains records across
container replacement and instance restarts. Docker and the MySQL container are
configured to restart automatically. The volume normally lives on the root EBS
volume; if that EBS volume is deleted, these records are lost too.

Do not run `docker compose down -v`, remove the data volume, or terminate an
instance whose only database copy is on a volume scheduled for deletion. Keep the
project directory/name stable because Compose uses it to identify the volume.
Changing `.env` passwords after initial database creation does not change MySQL
accounts; rotate with `ALTER USER`, then update dependent configuration.

A backend on this same EC2 host can use 127.0.0.1:3306. A backend in another
container should use the MySQL service name on a shared private Docker network.
For a backend on another EC2 instance, design private VPC access, bind to the
appropriate private interface, restrict 3306 to the backend security group, and
configure TLS. The supplied Compose file intentionally does not enable that path.

## 7. Access MySQL from your Mac

Keep this terminal running:

```bash
ssh -i ~/Downloads/gate-access.pem -N \
  -L 13306:127.0.0.1:3306 ubuntu@EC2_PUBLIC_IP
```

MySQL Workbench settings: host `127.0.0.1`, port `13306`, username `gate_access`,
password from the EC2 `.env`, database `gate_access`. Traffic travels through SSH;
no public 3306 rule is needed.

To run the transfer on your Mac, set its MYSQL_PORT=13306 and its MYSQL_PASSWORD
to the EC2 database password, while retaining the Mac's SOURCE_DATABASE_URL.
Ensure no DATABASE_URL override points elsewhere, then follow the transfer guide.

## 8. Back up and check recovery

Run on EC2. `mysqldump` runs inside the container, so no host MySQL client is needed:

```bash
cd ~/gate_access_dbsetup
mkdir -p ~/db-backups
chmod 700 ~/db-backups
umask 077
backup_file="$HOME/db-backups/gate_access_$(date -u +%Y%m%dT%H%M%SZ).sql"
sudo docker compose exec -T mysql sh -c \
  'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqldump -uroot --single-transaction --routines --triggers --events --no-tablespaces --set-gtid-purged=OFF "$MYSQL_DATABASE"' \
  > "$backup_file"
```

Check the command succeeds and the file is nonempty. Copy backups off the EC2
server (for example to an encrypted, private S3 bucket using an EC2 IAM role).
A local backup disappears with the disk. Schedule daily backups and EBS snapshots
according to your recovery needs, with retention and failure alerts. Avoid schema
changes during a single-transaction dump. Test restoring into a separate disposable
MySQL 8.4 instance before relying on a backup:

```bash
# Run against a SEPARATE recovery instance/project, never over your live DB.
sudo docker compose exec -T mysql sh -c \
  'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot "$MYSQL_DATABASE"' < /path/to/backup.sql
```

The dump contains data and triggers; restore into an empty recovery database,
without first installing tables with Alembic. It also includes alembic_version.

## 9. Routine checks

```bash
sudo docker compose ps
sudo docker compose logs --tail=100 mysql
df -h
python -m alembic current
```

Monitor disk, memory, CPU, and backup success. Test MySQL image updates and future
migrations on a restored copy first. `mysql:8.4` follows the 8.4 release line; pin a
verified image digest in production when reproducible rollouts are required.

If deploying the actual API later, supply its repository, start command, domain,
and device connection requirements. Its HTTP/TLS/service configuration is a
separate deployment from this database setup.

## Recover from MySQL error 1419 during the initial migration

If CREATE TRIGGER fails with error 1419, binary logging is enabled and the
schema-scoped migration user cannot create triggers under the server's default
policy. The supplied compose.yaml now enables log_bin_trust_function_creators
for this dedicated MySQL 8.4 instance. This trusts users who already have routine
or trigger creation privileges; it does not grant SUPER or turn off binary logging.
The setting is deprecated but supported in MySQL 8.4; reevaluate for future versions.

For an existing Gate Access container using Compose project name `gate-access`,
apply the setting without restarting the server:

```bash
sudo docker compose -p gate-access exec -T mysql sh -c \
  'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot -e "SET PERSIST log_bin_trust_function_creators = ON; SELECT @@GLOBAL.log_bin_trust_function_creators;"'
```

Use this only with the Gate Access Compose file/project, not another project's
MySQL container. Keep the new command option in compose.yaml for future instances.
SET PERSIST also saves this setting in the current instance's data volume.

Because MySQL DDL auto-commits, error 1419 may leave all tables but no triggers and
an empty alembic_version. Do not stamp an incomplete migration. If and only if
this is an unused target, verify every table is empty and the table names belong
to this project before removing its partial schema and rerunning Alembic. Preserve
any populated target and investigate it separately. Keep applications disconnected
throughout an empty-schema rebuild. No source PostgreSQL action is required.

Reference: https://dev.mysql.com/doc/refman/8.4/en/replication-options-binary-log.html
