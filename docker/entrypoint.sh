#!/bin/sh
# =============================================================================
# repomend-scanner entrypoint
# KS-TRACE: C-P3-08, ADR-013, AC-P3-01, AC-P3-02
# | assumption: --cap-add NET_ADMIN granted by caller (docker_sandbox.py)
# | test: test_docker_sandbox.py::test_network_none_blocks_egress (integration)
#         test_docker_sandbox.py::test_pypi_only_allows_pip_index_query (integration)
#         AC-P3-02: curl to raw non-allowlisted IP must be blocked by iptables
# =============================================================================
#
# SEQUENCE (order is invariant — do not reorder):
#   1. Resolve destination IPs  (needs DNS — must happen BEFORE DROP policy)
#   2. Write /etc/hosts entries  (tools use hosts file, not DNS, after DROP)
#   3. Apply iptables DROP default OUTPUT policy
#   4. Insert ACCEPT rules for resolved IPs on 443/80
#   5. exec "$@"  (replace shell with scanner process)
#
# WHY /etc/hosts (step 2):
#   After DROP is applied, outbound DNS queries are blocked even to Docker's
#   internal resolver at 127.0.0.11 — it does not route through the lo interface
#   and is caught by the DROP default. Without /etc/hosts entries, tools like
#   pip and npm resolve domains themselves and fail with NXDOMAIN / ETIMEDOUT.
#   Writing /etc/hosts before DROP ensures resolution is local and needs no
#   outbound UDP/TCP port 53. iptables ACCEPT rules on the resolved IPs are
#   belt-and-suspenders: /etc/hosts guarantees name→IP mapping, iptables
#   enforces which IPs are actually reachable.
#
# REPOMEND_NETWORK_POLICY is set by docker_sandbox.py via -e flag.
# Values: OFFLINE | PYPI_ONLY | NPM_ONLY
# If unset, defaults to OFFLINE (deny-all).
# =============================================================================

set -e

POLICY="${REPOMEND_NETWORK_POLICY:-OFFLINE}"

# ---------------------------------------------------------------------------
# Step 1 — resolve destination IPs before any egress rules are applied.
# getent hosts returns all A records; awk extracts IP column.
# Failure to resolve is non-fatal: if the host is unreachable the ACCEPT rule
# simply won't exist and the connection will be blocked by the DROP default —
# which is the safe failure mode.
# ---------------------------------------------------------------------------
PYPI_IPS=""
NPM_IPS=""

if [ "$POLICY" = "PYPI_ONLY" ]; then
    PYPI_IPS=$(getent hosts pypi.org files.pythonhosted.org 2>/dev/null | awk '{print $1}' | sort -u || true)
fi

if [ "$POLICY" = "NPM_ONLY" ]; then
    NPM_IPS=$(getent hosts registry.npmjs.org 2>/dev/null | awk '{print $1}' | sort -u || true)
fi

# ---------------------------------------------------------------------------
# Step 2 — write /etc/hosts entries for allowlisted domains.
# This must happen BEFORE DROP is applied (step 3).
# After DROP, outbound DNS is blocked. Tools (pip, npm) use /etc/hosts
# for name resolution — no outbound DNS query required post-DROP.
# ---------------------------------------------------------------------------
if [ "$POLICY" = "PYPI_ONLY" ] && [ -n "$PYPI_IPS" ]; then
    for ip in $PYPI_IPS; do
        printf '%s\t%s\n' "$ip" "pypi.org files.pythonhosted.org" >> /etc/hosts
    done
fi

if [ "$POLICY" = "NPM_ONLY" ] && [ -n "$NPM_IPS" ]; then
    for ip in $NPM_IPS; do
        printf '%s\t%s\n' "$ip" "registry.npmjs.org" >> /etc/hosts
    done
fi

# ---------------------------------------------------------------------------
# Step 3 — apply deny-by-default OUTPUT policy.
# LOOPBACK is always permitted (tools may communicate via 127.0.0.1).
# ESTABLISHED/RELATED allows outbound ACKs/data on already-accepted connections.
# ---------------------------------------------------------------------------
iptables -P OUTPUT DROP                                             2>/dev/null || true
iptables -A OUTPUT -o lo -j ACCEPT                                  2>/dev/null || true
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT  2>/dev/null || true

# ---------------------------------------------------------------------------
# Step 4 — insert ACCEPT rules for policy-specific destinations.
# Operates on resolved IPs from Step 1 — no hostname matching.
# These are belt-and-suspenders with the /etc/hosts entries above.
# ---------------------------------------------------------------------------
if [ "$POLICY" = "PYPI_ONLY" ]; then
    for ip in $PYPI_IPS; do
        iptables -A OUTPUT -d "$ip" -p tcp --dport 443 -j ACCEPT    2>/dev/null || true
        iptables -A OUTPUT -d "$ip" -p tcp --dport 80  -j ACCEPT    2>/dev/null || true
    done
fi

if [ "$POLICY" = "NPM_ONLY" ]; then
    for ip in $NPM_IPS; do
        iptables -A OUTPUT -d "$ip" -p tcp --dport 443 -j ACCEPT    2>/dev/null || true
        iptables -A OUTPUT -d "$ip" -p tcp --dport 80  -j ACCEPT    2>/dev/null || true
    done
fi

# OFFLINE: no ACCEPT rules added — all outbound blocked after Step 3.

# ---------------------------------------------------------------------------
# Step 5 — exec scanner command (replaces this shell process).
# "$@" is the CMD passed to `docker run`.
# ---------------------------------------------------------------------------
exec "$@"
