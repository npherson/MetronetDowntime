# MetronetDowntime

Reports for understanding how often Metronet is going down for our home and neighbors on the same shelf.
The report is built from an [Uptime Kuma](https://github.com/louislam/uptime-kuma) instance running on a Raspberry Pi.

**View the report:** https://npherson.github.io/MetronetDowntime/

## How it works

Uptime Kuma has two ping monitors, each checking once a minute:

- **Internet Available** pings a public address (8.8.4.4).
- **Default Gateway** pings the home router.

Uptime Kuma 2 keeps every up/down change permanently, so the full outage history can be
rebuilt from its database. An internet outage is left out of the report when the router
was also down from 3 minutes before it started until 3 minutes after it ended, since that
points to a problem inside the house rather than with the ISP.

## Files

| File | What it does |
|---|---|
| `scripts/pull-kuma.ps1` | Copies Uptime Kuma's SQLite database off the Pi over SSH into `data/` (read-only on the Pi). |
| `scripts/remote.sh` | Runs on the Pi: finds the Uptime Kuma container and streams the database out. |
| `analyze.py` | Turns the database into outage lists, a monthly summary and chart data. |
| `build_site.py` | Builds the report page `docs/index.html`. |
| `update.ps1` | Runs all of the above, then commits and pushes the updated page. |
| `docs/` | The published site (GitHub Pages) and the outage CSV. |

`data/` holds the database copy and local-only outputs and is never committed: the
database contains Uptime Kuma's login secret, and `data/all-outages.csv` includes home
network addresses.

## Updating the report

1. Copy `local.config.example.json` to `local.config.json` and fill in the Pi's address and
   SSH username (this file is not committed).
2. From PowerShell in this folder, run:

   ```powershell
   .\update.ps1
   ```

   Enter the Pi password when asked. Use `.\update.ps1 -NoPush` to rebuild without publishing.

Requires Python 3, OpenSSH and git on the Windows PC, and Uptime Kuma 2 with SQLite in Docker on the Pi.
