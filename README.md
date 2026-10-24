# Hadoop Cluster Lab — HDFS with an Edge Node

A hands-on lab for teaching **how a file travels from a client into HDFS**, how HDFS divides it into blocks, how blocks are replicated, and what happens if a DataNode fails. Everything runs locally in **five Docker containers on one physical computer**.

> **Classroom-only configuration, not production secure.** HDFS authentication and file permissions are not enabled for this lab, and the HDFS services are not hardened. The NameNode web dashboard binds to `127.0.0.1` only. Do not deploy this setup on the public Internet or use real/private data.

## Architecture: 1 client + 1 NameNode + 3 DataNodes

```text
YOUR LAPTOP
   sales.csv
      |
      | docker compose cp  (staging a LOCAL file; not HDFS yet)
      v
  +-----------+      HDFS metadata requests     +-----------+
  | Edge Node | ------------------------------> | NameNode  |
  |  client   | <------------------------------ | metadata  |
  +-----------+     DataNode locations          +-----------+
      |
      | hdfs dfs -put: client sends block bytes DIRECTLY to DataNodes
      v
  +------------+      replication pipeline
  | DataNode 1 |  --------------------->  +------------+
  +------------+                          | DataNode 2 |
                                          +------------+
  +------------+
  | DataNode 3 |   (also stores blocks chosen by HDFS)
  +------------+
```

The illustration shows one *possible* write pipeline. Different blocks can go to different DataNodes. **The NameNode stores metadata, not the uploaded file's contents.** The Edge Node uses the Hadoop CLI as a client; it does **not** run HDFS storage services.

| Service | Count | Purpose |
| --- | ---: | --- |
| `edge-node` | 1 | Submits the CSV and issues HDFS client commands |
| `namenode` | 1 | Maintains namespace, block IDs and block locations |
| `datanode1`, `datanode2`, `datanode3` | 3 | Store and replicate HDFS blocks |

Our HDFS block size is deliberately **1 MiB** to make a small CSV split into many blocks. Replication factor is **2**. Typical production block sizes are much larger (often 128 MiB or more).

## Prerequisites

- Docker Desktop (Windows/macOS) or Docker Engine with Compose v2 (Linux)
- Python 3 on your laptop (to generate the example CSV)
- About 6–8 GB of free RAM recommended for Docker; actual usage varies

Run every `docker compose` command from the **folder containing `docker-compose.yml`**.

## Step 1 — Start the five-container lab

```bash
docker compose up -d
docker compose ps
```

Expected services: `namenode`, `datanode1`, `datanode2`, `datanode3`, `edge-node`.

HDFS daemons may need some time to register. Check the number of DataNodes:

```bash
docker compose exec edge-node hdfs dfsadmin -report
```

Look for **`Live datanodes (3)`**. Open <http://localhost:9870> and click **Datanodes**. If registration fails:

```bash
docker compose logs --tail=100 namenode datanode1 datanode2 datanode3
```

## Step 2 — Create sales.csv on the laptop

This dataset includes several product types, so you can reuse it later for MapReduce word counts or sales aggregation.

```bash
python scripts/generate_sales.py
```

On some Linux or macOS machines you may need to use `python3` instead of `python`.

This creates **`data/sales.csv`** with a header and **500,000 sales records**, roughly 10 MiB. The actual file size can differ slightly by platform because CSV line endings may differ. Use `--rows 1000000` to make it larger.

Peek at it with Excel or another CSV viewer on your laptop. The file is still **outside Hadoop**.

## Step 3 — Copy the CSV into the Edge Node container (still NOT HDFS)

```bash
docker compose cp data/sales.csv edge-node:/tmp/sales.csv
```

This copies the file to the **Edge Node's local filesystem** at `/tmp/sales.csv`. It does **not** send the file to the NameNode and it does **not** distribute or replicate any blocks yet.

Optionally check that the file is there:

```bash
docker compose exec edge-node ls -lh /tmp/sales.csv
```

## Step 4 — Upload into HDFS from the Edge Node

```bash
docker compose exec edge-node hdfs dfs -mkdir -p /demo
docker compose exec edge-node hdfs dfs -put -f /tmp/sales.csv /demo/sales.csv
```

The **HDFS client running on the Edge Node** first contacts the NameNode for metadata and block locations. It then streams the actual CSV contents to DataNodes through the replication pipeline. The NameNode **does not** carry the file bytes.

Confirm the file is in HDFS:

```bash
docker compose exec edge-node hdfs dfs -ls /demo/
docker compose exec edge-node bash -c "hdfs dfs -cat /demo/sales.csv | sed -n '1,6p'"
```

## Step 5 — Show students the block distribution

```bash
docker compose exec edge-node hdfs fsck /demo/sales.csv -files -blocks -locations
```

In the report, discuss the **number of blocks**, **length of each block** and **replica locations**. A 1 MiB block size means the roughly 10 MiB CSV should occupy multiple blocks. Exact block counts and DataNode choices depend on the actual file size and HDFS placement policy. With replication factor 2, each healthy block normally has two copies stored on different DataNodes.

**Key distinction:** HDFS blocks divide *bytes for storage*, not logical CSV rows. Later, MapReduce's `InputFormat` and record reader decide how CSV lines are presented to mapper tasks; an input split is not necessarily identical to an HDFS block.

## Step 6 — Demonstrate fault tolerance

First confirm in the `fsck` output that the file has healthy replicas. Then stop one DataNode:

```bash
docker compose stop datanode1
docker compose exec edge-node hdfs dfsadmin -report
docker compose exec edge-node hdfs fsck /demo/sales.csv -files -blocks -locations
```

Even if some blocks are **under-replicated**, they should stay readable from surviving copies if they were healthy before the failure. Restore the stopped node:

```bash
docker compose start datanode1
```

Do **not** use `docker compose down -v` during the lesson; it deletes all HDFS volumes.

## Step 7 — Stop or reset

```bash
docker compose down
```

Named HDFS data volumes are preserved. To permanently **erase all HDFS data in this local lab** and start over:

```bash
docker compose down -v
```

## Questions for students

1. Why do we copy `sales.csv` to the **Edge Node**, not into the NameNode service?
2. What changes between `docker compose cp` and `hdfs dfs -put`?
3. Does the NameNode store CSV content or only metadata?
4. If the CSV contains 500,000 rows, is each HDFS block guaranteed to contain complete rows?
5. How do replicas help when `datanode1` stops?

## Repository structure

```text
hadoop-classroom/
├── docker-compose.yml
├── config/
│   ├── core-site.xml
│   └── hdfs-site.xml
├── scripts/
│   ├── start-namenode.sh
│   └── generate_sales.py
├── data/
│   └── .gitkeep         # generated CSV is excluded from Git
├── .gitignore
└── README.md
```

## Publishing to GitHub

Create an empty GitHub repository named `hadoop-cluster-lab`, then in this folder run:

```bash
git init
git add .
git commit -m "Add three-DataNode HDFS lab with separate Edge Node"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/hadoop-cluster-lab.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. If you already created a repository, copy these files into it and commit normally instead of running `git init` again.

## Troubleshooting and limitations

- This project uses the official **`apache/hadoop:3.5.0`** image, but its full container startup has **not been tested in this environment**; verify locally before teaching.
- Only port **9870** is published, and only to localhost. Other container services communicate over a private Docker Compose network.
- If `docker compose cp` fails, verify `edge-node` is running with `docker compose ps`.
- If uploads fail, verify there are three live DataNodes and check `docker compose logs --tail=100`.
- **YARN and MapReduce services are not included yet.** This version is intentionally an HDFS-only teaching lab.
