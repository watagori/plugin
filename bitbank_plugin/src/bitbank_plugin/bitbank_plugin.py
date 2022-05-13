import datetime

from senkalib.chain.transaction import Transaction
from senkalib.token_original_id_table import TokenOriginalIdTable
from senkalib.caaj_journal import CaajJournal


class BitbankPlugin:
    chain = "bitbank"
    platform = "bitbank"

    @classmethod
    def can_handle(cls, transaction: Transaction) -> bool:
        chain_type = transaction.get_transaction_data_type()
        return cls.chain in chain_type

    @classmethod
    def get_caajs(
        cls, transaction: Transaction, token_table: TokenOriginalIdTable
    ) -> list:
        caaj = []

        datetime_jst = datetime.datetime.strptime(
            transaction.get_timestamp(), "%Y/%m/%d %H:%M:%S"
        )
        datetime_utc = (datetime_jst - datetime.timedelta(hours=9)).strftime(
            "%Y/%m/%d %H:%M:%S%z"
        )
        amount_get = transaction.get_amount()
        amount_lose = transaction.get_amount() ** transaction.get_price()
        token_pair = transaction.get_token_pair().split("_")
        token_symbol_get = token_pair[0]
        token_symbol_lose = token_pair[1]

        caaj_journal_from = CaajJournal(
            datetime_utc,
            cls.chain,
            cls.platform,
            "exchange",
            transaction.get_transaction_id(),
            transaction.get_trade_uuid(),
            "lose",
            amount_lose,
            token_symbol_lose,
            token_original_id_from,
            token_original_uuid_from,
            "self",
            "bitbank",
            "",
        )

        caaj.append(caaj_journal_from)

        return caaj
