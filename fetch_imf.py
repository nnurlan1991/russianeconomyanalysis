#!/usr/bin/env python3
"""Fetch IMF data for Russia via MCP JSON-RPC. Outputs JSON for the HTML builder."""
import subprocess, json, sys

MCP_BIN = "/Users/market/Downloads/russian economy analysis/.uv-bin/imf-data-mcp"

def mcp_req(proc, method, params=None, req_id=1):
    msg = {"jsonrpc":"2.0","id":req_id,"method":method,"params":params or {}}
    proc.stdin.write(json.dumps(msg)+"\n"); proc.stdin.flush()
    return json.loads(proc.stdout.readline())

def mcp_notify(proc, method, params=None):
    msg = {"jsonrpc":"2.0","method":method,"params":params or {}}
    proc.stdin.write(json.dumps(msg)+"\n"); proc.stdin.flush()

def call_tool(proc, tool_name, args, label=""):
    """Call a tool and print formatted result."""
    r = mcp_req(proc, "tools/call", {"name": tool_name, "arguments": args})
    if "error" in r:
        print(f"\n>>> ERROR [{label}]: {json.dumps(r['error'], ensure_ascii=False)[:500]}")
        return None
    content = r.get("result",{}).get("content",[])
    text = ""
    for c in content:
        if c.get("type")=="text":
            text += c["text"]
    print(f"\n>>> {label} ({len(text)} chars)")
    print(text[:2000])
    return text

proc = subprocess.Popen([MCP_BIN], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, text=True, bufsize=1)

# Init + handshake
r = mcp_req(proc, "initialize", {"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"fetch","version":"1.0"}})
if "error" in r: print("INIT FAIL"); sys.exit(1)
mcp_notify(proc, "notifications/initialized")

# Get Russia country code from CPI
r = mcp_req(proc, "tools/call", {"name":"imf_get_parameter_codes",
    "arguments": {"params": {"database_id":"CPI_2026_JAN_VINTAGE","parameter":"country","search":"russia"}}})
print("\n=== RUSSIA CODE ===")
for c in r.get("result",{}).get("content",[]):
    if c.get("type")=="text": print(c["text"][:1000])

# Try fetching CPI data for Russia (annual, 1990-2030)
r = mcp_req(proc, "tools/call", {"name":"imf_fetch_data",
    "arguments": {"params": {
        "database_id": "CPI_2026_JAN_VINTAGE",
        "start_year": 1990, "end_year": 2030,
        "filters": {"country": ["RU"], "frequency": ["A"]}
    }}})
print("\n=== CPI DATA (RU, annual) ===")
for c in r.get("result",{}).get("content",[]):
    if c.get("type")=="text": print(c["text"][:3000])

proc.terminate()
