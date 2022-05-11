import sys

import pandas as pd
from senkalib.chain.osmosis.osmosis_transaction_generator import (
    OsmosisTransactionGenerator,
)
from senkalib.senka_setting import SenkaSetting
from senkalib.token_original_id_table import TokenOriginalIdTable

from osmosis_plugin.osmosis_plugin import OsmosisPlugin

TOKEN_ORIGINAL_IDS_URL = "https://raw.githubusercontent.com/ca3-caaip/token_original_id/master/token_original_id.csv"

if __name__ == "__main__":
    args = sys.argv
    address = args[1]
    caaj = []
    settings = SenkaSetting({})
    token_original_ids = TokenOriginalIdTable(TOKEN_ORIGINAL_IDS_URL)
    transactions = OsmosisTransactionGenerator.get_transactions(
        settings, address, None, {}
    )
    for transaction in transactions:
        if OsmosisPlugin.can_handle(transaction):
            caaj_peace = OsmosisPlugin.get_caajs(
                address, transaction, token_original_ids
            )
            caaj.extend(caaj_peace)

    df = pd.DataFrame(caaj)
    df = df.sort_values("executed_at")
    caaj_csv = df.to_csv(None, index=False)
    print(caaj_csv)
