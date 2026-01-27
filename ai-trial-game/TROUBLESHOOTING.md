# Troubleshooting

## Voting stuck or no tx hash

1) Verify Anvil is running and RPC is healthy:

```bash
python -c "import json,urllib.request;payload={'jsonrpc':'2.0','method':'eth_blockNumber','params':[],'id':1};req=urllib.request.Request('http://127.0.0.1:8545',data=json.dumps(payload).encode('utf-8'),headers={'Content-Type':'application/json'});print(urllib.request.urlopen(req,timeout=2).read().decode('utf-8'))"
```

2) Check timeout/confirmations:

- `VOTING_TX_TIMEOUT` (seconds)
- `VOTING_TX_CONFIRMATIONS` (blocks)

3) Review Anvil logs:

- Set `ANVIL_LOG_PATH=anvil.log` in `backend/.env`
- Re-run `python start.py` and inspect `anvil.log`

## spoon-core import failure

1) Ensure the local dependency exists:

- Expected path: `../spoon-core-main/spoon-core-main`

2) Install editable into the venv:

```bash
python -m pip install -e ..\\spoon-core-main\\spoon-core-main
```

On macOS/Linux:

```bash
python -m pip install -e ../spoon-core-main/spoon-core-main
```

3) Verify import:

```bash
python -c "import spoon_ai; print('spoon-core OK')"
```

4) If you want to skip SpoonOS:

- Set `USE_SPOON_AGENT=false` in `backend/.env`

## Port already in use

1) Change `SERVER_PORT` in `backend/.env`

2) Identify the process:

Windows:

```bash
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

macOS/Linux:

```bash
lsof -i :8080
kill -9 <PID>
```
