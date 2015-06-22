"""
The RKEY_PREFIX can be used to set a common prefix to every key stored.
SEP defines the separator used to create fake namespaces in key names.

The entries in RKEY are used to both document what's available and
reduce code rewrite just to rename keys.
"""

SEP = '_'

RKEY = {
    # the two sides of the merged orderbook stored as sorted sets
    'book_bid': 'book' + SEP + 'bid',
    'book_ask': 'book' + SEP + 'ask',
    # helper to produce one of the two keys above
    'book_side': 'book' + SEP + '%s',

    # members in the sorted are built based on the price, timestamp, amount (volume)
    # and an order id, e.g. book_member % (price, time.time(), 3.2, order_id)
    # This ordering is designed to take advantage of the Lexicographical scores sorting.
    'book_member': '%s' + SEP + '%s' + SEP + '%s' + SEP + '%s',

    'ticker': 'ticker'  # ticker based on the latest book
}

# publishes our internal index, an index generated based on
# tickers alone, and warning=True in case of divergences
INDEX_EXTERNAL_CHANNEL = 'index_external'
