import conducto as co
import json
import time


def clear():
    """
    Delete all blocks from `co.data.user`.

    Uses the following methods from `co.data.user`:

    * `list(prefix)` - get all blocks currently in the data store.
    * `delete(path)` - delete the given block from the data store
    """
    base_path = "conducto/demo/btc"
    blocks = co.data.user.list(base_path)
    for block in blocks:
        print("Deleting", block, flush=True)
        co.data.user.delete(block)


def download(start: int, end: int):
    """
    Download all the blocks with `start <= height <= end` and save the result
    to user-scoped storage. Skip any blocks that are already in `co.data.user`.

    Uses the following methods from `co.data.user`:

    * `exists(path)` - check whether the given block exists in the data store.
    * `gets(path)` - fetch the block from the data store so it can be printed.
    * `puts(path, bytes)` - save the serialized block to the data store.
    """
    start = _parse_height(start)
    end = _parse_height(end)
    for height in range(start, end + 1):
        path = f"conducto/demo/btc/height={height}"

        # Check if `co.data.user` already has this block.
        if co.data.user.exists(path):
            print(f"Data already exists for block at height {height}", flush=True)
            data_bytes = co.data.user.gets(path)
            _print_block(height, data_bytes)
            continue

        print(f"Downloading block at height={height}", flush=True)
        data = _download_block(height)

        # Put the data into `co.data.user`.
        data_bytes = json.dumps(data).encode()
        co.data.user.puts(path, data_bytes)


def _parse_height(height):
    """
    Parse the specified height as if the blockchain were Python-like list.
    Negative numbers are interpreted as an offset from end, with the latest
    block having height=-1.
    """
    if height >= 0:
        return height
    else:
        from blockchain import blockexplorer, util
        util.TIMEOUT = 30  # time out after 5 seconds
        return blockexplorer.get_latest_block().height + 1 + height


def _download_block(height):
    from blockchain import blockexplorer, util
    util.TIMEOUT = 30  # time out after 5 seconds
    block = blockexplorer.get_block_height(height)[0]
    n_tx = len([tx for tx in block.transactions])
    n_outs = len([txo for tx in block.transactions for txo in tx.outputs])
    print(f"- Block with height {height} arrived at {time.ctime(block.time)} with "
          f"{n_tx} transactions and a total of {n_outs} outputs.", flush=True)

    return {"t": block.time, "n_tx": n_tx, "n_outs": n_outs}


def _print_block(height, data_bytes):
    data = json.loads(data_bytes)
    print(f"- Block with height {height} arrived at {time.ctime(data['t'])} with "
          f"{data['n_tx']} transactions and a total of {data['n_outs']} outputs.", flush=True)


if __name__ == "__main__":
    co.main()
