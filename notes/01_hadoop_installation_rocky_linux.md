# Installing Apache Hadoop on Rocky Linux 10

> **Note:** If your VM has no network connectivity, see [VM No Network Connection Fix](vm-no-network-fix.md) before proceeding.

## Purpose

This guide provides step-by-step instructions for installing and configuring Apache Hadoop on Rocky Linux 10 in pseudo-distributed mode. This setup simulates a multi-node Hadoop cluster on a single machine, making it ideal for development, testing, and learning purposes.

**Important:** This guide does not cover Kerberos authentication or production security configurations. For production deployments, ensure proper security measures are implemented.

## Prerequisites

### Required Software

- **Rocky Linux 10** installed on a virtual machine or physical system
- **EPEL repository** - Extra Packages for Enterprise Linux (required for additional packages)
- **Java 8 (Amazon Corretto)** - Required for running Hadoop (not installed by default)
- **SSH** - For passwordless authentication between Hadoop daemons
- **tar** - For extracting the Hadoop distribution
- **curl or wget** - For downloading Hadoop binaries

### Minimum Requirements

- A running Rocky Linux 10 installation
- User account with sudo privileges
- Internet connection for downloading Hadoop binaries

## Installation Steps

### 1. Install Java 8 (OpenJDK)

**Important:** Java is not installed by default on Rocky Linux. Hadoop requires Java 8 to run. We'll use Amazon Corretto 8, a production-ready distribution of OpenJDK.

Install Amazon Corretto 8:

```bash
sudo rpm --import https://yum.corretto.aws/corretto.key
sudo curl -L -o /etc/yum.repos.d/corretto.repo https://yum.corretto.aws/corretto.repo
sudo yum install java-1.8.0-amazon-corretto-devel -y
```

Verify Java installation:

```bash
java -version
```

You should see output indicating Amazon Corretto version 1.8.0.

**Note:** If you have multiple Java versions installed, you can switch between them using:

```bash
sudo alternatives --config java
```

Select the Amazon Corretto 8 option from the list. Verify the change with `java -version`.

### 2. Install Required Packages

Install tar and curl utilities:

```bash
sudo yum install tar curl -y
```

### 3. Download Hadoop

Download the latest stable Apache Hadoop distribution (version 3.4.2):

```bash
curl -O https://downloads.apache.org/hadoop/common/stable/hadoop-3.4.2.tar.gz
```

Alternatively, you can use wget:

```bash
wget https://downloads.apache.org/hadoop/common/stable/hadoop-3.4.2.tar.gz
```

### 4. Extract Hadoop Distribution

Extract the downloaded Hadoop archive to your home directory:

```bash
tar xvzf hadoop-3.4.2.tar.gz
cd hadoop-3.4.2
```

**Note:** For production environments, it's best practice to install Hadoop in a system directory (e.g., `/opt/hadoop`). For this tutorial, we're installing in the home directory for simplicity.

### 5. Configure Java Environment

#### Set JAVA_HOME

After installing Amazon Corretto 8, configure the JAVA_HOME environment variable. Java is installed at `/usr/lib/jvm/java-1.8.0-amazon-corretto`.

Edit your `~/.bashrc` file:

```bash
vim ~/.bashrc
```

Add the following line:

```bash
export JAVA_HOME=/usr/lib/jvm/java-1.8.0-amazon-corretto
```

Apply the changes:

```bash
source ~/.bashrc
```

#### Verify Java Installation

Test that Java is properly configured:

```bash
$JAVA_HOME/bin/java -version
```

You should see output showing Amazon Corretto version 1.8.0. If you see "missing JAVA_HOME" errors, ensure the JAVA_HOME variable is correctly set and sourced.

### 6. Configure Hadoop for Pseudo-Distributed Mode

Pseudo-distributed mode runs Hadoop as a multi-node system on a single machine, with each daemon running in a separate Java process.

#### Configure core-site.xml

Edit `etc/hadoop/core-site.xml`:

```bash
vim etc/hadoop/core-site.xml
```

Add the following configuration:

```xml
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
    </property>
</configuration>
```

**Important:** Each XML configuration file should have only ONE `<configuration>` block. If a `<configuration>` block already exists in the file, add the `<property>` elements inside it rather than creating a new `<configuration>` block.

This configures the default filesystem to use HDFS on localhost.

#### Configure hdfs-site.xml

Edit `etc/hadoop/hdfs-site.xml`:

```bash
vim etc/hadoop/hdfs-site.xml
```

Add the following configuration:

```xml
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
</configuration>
```

**Note:** Setting replication to 1 means data is stored only once with no redundancy. This is acceptable for development but not for production. For production clusters, set this to 3 for proper fault tolerance.

### 7. Setup Passwordless SSH

Hadoop requires passwordless SSH to manage daemons across nodes.

#### Test SSH to Localhost

```bash
ssh localhost
```

If prompted for a password, configure passwordless SSH:

#### Generate SSH Key

```bash
ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa
```

#### Add Key to Authorized Keys

```bash
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
```

#### Set Correct Permissions

```bash
chmod 0600 ~/.ssh/authorized_keys
```

**Important:** The permission step is critical. Without proper permissions (0600), passwordless SSH will not work.

#### Verify Passwordless SSH

```bash
ssh localhost
```

You should now be able to SSH to localhost without entering a password. Type `exit` to return to your original session.

### 8. Format the NameNode

Before starting Hadoop for the first time, format the HDFS filesystem:

```bash
bin/hdfs namenode -format
```

**Important:** Only format the namenode on initial installation. Reformatting will delete all data in HDFS.

#### Troubleshooting: Residual Configuration

If you encounter issues with data nodes not starting, you may have residual configuration from a previous installation. To resolve:

1. Stop all Hadoop services:
   ```bash
   sbin/stop-dfs.sh
   ```

2. Remove old Hadoop data directories (this will delete all HDFS data):
   ```bash
   rm -rf /tmp/hadoop-*
   ```

3. Reformat the namenode:
   ```bash
   bin/hdfs namenode -format
   ```

### 9. Start HDFS Services

Start the NameNode and DataNode daemons:

```bash
sbin/start-dfs.sh
```

#### Verify Services are Running

Check that all services started successfully:

```bash
jps
```

You should see:
- NameNode
- DataNode
- SecondaryNameNode

**Note:** The SecondaryNameNode is not a backup NameNode but stores configuration backups and checkpoints.

### 10. Create HDFS User Directory

Create your user directory in HDFS:

```bash
bin/hdfs dfs -mkdir -p /user/<your-username>
```

**Note:** In HDFS, user directories are located at `/user/<username>`, not `/home/<username>` as in Linux.

### 11. Test HDFS Operations

#### Upload a File to HDFS

```bash
bin/hdfs dfs -put LICENSE.txt /user/<your-username>/
```

#### List Files in HDFS

```bash
bin/hdfs dfs -ls /user/<your-username>
```

#### View File Contents

```bash
bin/hdfs dfs -cat /user/<your-username>/LICENSE.txt
```

### 12. Configure YARN (MapReduce Processing)

To run MapReduce jobs, configure YARN (Yet Another Resource Negotiator).

#### Configure mapred-site.xml

Edit `etc/hadoop/mapred-site.xml`:

```bash
vim etc/hadoop/mapred-site.xml
```

Add the following configuration:

```xml
<configuration>
    <property>
        <name>mapreduce.framework.name</name>
        <value>yarn</value>
    </property>
    <property>
        <name>mapreduce.application.classpath</name>
        <value>$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/*:$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/lib/*</value>
    </property>
</configuration>
```

#### Configure yarn-site.xml

Edit `etc/hadoop/yarn-site.xml`:

```bash
vim etc/hadoop/yarn-site.xml
```

Add the following configuration:

```xml
<configuration>
    <property>
        <name>yarn.nodemanager.aux-services</name>
        <value>mapreduce_shuffle</value>
    </property>
    <property>
        <name>yarn.nodemanager.env-whitelist</name>
        <value>JAVA_HOME,HADOOP_COMMON_HOME,HADOOP_HDFS_HOME,HADOOP_CONF_DIR,CLASSPATH_PREPEND_DISTCACHE,HADOOP_YARN_HOME,HADOOP_HOME,PATH,LANG,TZ,HADOOP_MAPRED_HOME</value>
    </property>
</configuration>
```

### 13. Start YARN Services

Start the ResourceManager and NodeManager:

```bash
sbin/start-yarn.sh
```

#### Verify YARN Services

```bash
jps
```

You should now see:
- NameNode
- DataNode
- SecondaryNameNode
- ResourceManager
- NodeManager

**Note:** 
- **ResourceManager** acts as a directory service for job scheduling
- **NodeManager** executes the actual MapReduce tasks

### 14. Run a MapReduce Example

#### Create Input Directory

```bash
bin/hdfs dfs -mkdir input
```

#### Upload Input Files

```bash
bin/hdfs dfs -put etc/hadoop/*.xml input
```

#### Run the Grep Example

```bash
bin/hadoop jar share/hadoop/mapreduce/hadoop-mapreduce-examples-3.4.2.jar grep input output 'dfs[a-z.]+'
```

This example searches all XML files for lines starting with "dfs".

#### View Output

```bash
bin/hdfs dfs -ls output
```

You should see:
- `_SUCCESS` - Zero-byte file indicating successful completion
- `part-r-00000` - Output file containing results

#### View Results

```bash
bin/hdfs dfs -cat output/*
```

Expected output:
```
1       dfsadmin
1       dfs.replication
```

### 15. Managing Hadoop Services

#### Start All Services

To start both HDFS and YARN services:

```bash
sbin/start-all.sh
```

#### Stop All Services

**Important:** Always stop Hadoop services properly before shutting down your system to avoid configuration corruption.

```bash
sbin/stop-all.sh
```

#### Stop Individual Services

Stop HDFS only:
```bash
sbin/stop-dfs.sh
```

Stop YARN only:
```bash
sbin/stop-yarn.sh
```

#### Verify Services are Stopped

```bash
jps
```

Only the `Jps` process itself should be listed.

### 16. Web Interfaces

Hadoop provides web interfaces for monitoring:

- **NameNode:** http://localhost:9870/
- **ResourceManager:** http://localhost:8088/

## Common Issues and Troubleshooting

### Data Nodes Not Starting

**Symptoms:** `jps` shows NameNode but no DataNode

**Solution:**
1. Check logs in `logs/` directory
2. Look for cluster ID mismatch errors
3. Stop services, remove `/tmp/hadoop-*` directories
4. Reformat namenode and restart

### Passwordless SSH Not Working

**Symptoms:** Services fail to start, password prompts appear

**Solution:**
1. Verify `~/.ssh/authorized_keys` has correct permissions (0600)
2. Ensure SSH key was properly generated and added
3. Test with `ssh localhost`

### JAVA_HOME Not Set

**Symptoms:** "missing JAVA_HOME" errors

**Solution:**
1. Verify JAVA_HOME in `~/.bashrc`
2. Run `source ~/.bashrc`
3. Test with `echo $JAVA_HOME`

### Port Already in Use

**Symptoms:** Services fail to start with "address already in use" errors

**Solution:**
1. Check if Hadoop is already running: `jps`
2. Stop existing services: `sbin/stop-all.sh`
3. Verify ports 9000, 9870, 8088 are free

## Best Practices

1. **Always stop services properly** before system shutdown
2. **Never reformat namenode** on a running cluster with data
3. **Use proper replication** (3) in production environments
4. **Monitor logs** in `$HADOOP_HOME/logs/` for issues
5. **Backup HDFS data** regularly in production
6. **Implement Kerberos** authentication for production clusters

## Next Steps

- Explore additional MapReduce examples in `share/hadoop/mapreduce/`
- Learn HDFS commands: `bin/hdfs dfs -help`
- Set up a fully-distributed multi-node cluster
- Integrate with Hive, Pig, or Spark
- Implement proper security with Kerberos

## Summary

You now have a working Hadoop installation on Rocky Linux 10 running in pseudo-distributed mode. This setup includes:

- **HDFS** for distributed storage (NameNode, DataNode, SecondaryNameNode)
- **YARN** for resource management and job scheduling (ResourceManager, NodeManager)
- **MapReduce** framework for distributed data processing

This environment is suitable for development, testing, and learning Hadoop concepts before deploying to a production cluster.
