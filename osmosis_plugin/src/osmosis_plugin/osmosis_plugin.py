import re
import uuid
from decimal import Decimal
from typing import Union

from senkalib.caaj_journal import CaajJournal
from senkalib.chain.transaction import Transaction
from senkalib.token_original_id_table import TokenOriginalIdTable

MEGA = 10**6
EXA = 10**18


class OsmosisPlugin:
    chain = "osmosis"
    PLATFORM = "osmosis"

    @classmethod
    def can_handle(cls, transaction: Transaction) -> bool:
        chain_type = transaction.get_transaction()["header"]["chain_id"]
        return OsmosisPlugin.chain in chain_type

    @classmethod
    def get_caajs(
        cls, address: str, transaction: Transaction, token_table: TokenOriginalIdTable
    ) -> list:
        caaj = []
        if transaction.get_transaction()["data"]["code"] != 0:
            return caaj

        transaction_type = transaction.get_transaction()["data"]["tx"]["body"][
            "messages"
        ][0]["@type"].split(".")[-1]

        if transaction_type in [
            "MsgSwapExactAmountIn",
            "MsgJoinSwapExternAmountIn",
        ]:
            caaj.extend(OsmosisPlugin._get_caaj_swap(transaction, token_table))

        elif transaction_type in "MsgTransfer":
            caaj.extend(OsmosisPlugin._get_caaj_transfer(transaction, token_table))

        elif transaction_type == "MsgJoinPool":
            caaj.extend(OsmosisPlugin._get_caaj_join_pool(transaction, token_table))

        elif transaction_type in ["MsgSend", "MsgLockTokens"]:
            caaj.extend(OsmosisPlugin._get_caaj_lock_token(transaction, token_table))

        elif transaction_type == "MsgExitPool":
            caaj.extend(OsmosisPlugin._get_caaj_exit_pool(transaction, token_table))

        elif transaction_type == "MsgDelegate":
            caaj.extend(
                OsmosisPlugin._get_caaj_delegate(address, transaction, token_table)
            )

        elif transaction_type == "MsgUpdateClient":
            caaj.extend(
                OsmosisPlugin._get_caaj_update_client(address, transaction, token_table)
            )
            return caaj  # it ignores fee because this address does not pay fee in case of MsgUpdateClient.
        else:
            raise Exception(
                f"This type of transaction is not defined. transaction_id: {transaction.get_transaction_id()}"
            )

        transaction_fee = transaction.get_transaction_fee()
        if transaction_fee != 0:
            caaj_fee = OsmosisPlugin._get_caaj_fee(address, transaction, token_table)
            caaj.extend(caaj_fee)

        return caaj

    @classmethod
    def _get_caaj_swap(
        cls, transaction: Transaction, token_table: TokenOriginalIdTable
    ) -> list:
        caaj = []
        attributes_list = OsmosisPlugin._get_attributes_list(transaction, "transfer")
        for attribute in attributes_list:
            caaj_to = OsmosisPlugin._get_attribute_data(attribute, "sender")[0]["value"]
            caaj_from = OsmosisPlugin._get_attribute_data(attribute, "recipient")[0][
                "value"
            ]

            amounts = OsmosisPlugin._get_attribute_data(attribute, "amount")
            amount_to = OsmosisPlugin._get_token_amount(amounts[0]["value"])
            token_original_id_to = OsmosisPlugin._get_token_original_id(
                amounts[0]["value"]
            )
            token_symbol_to = token_table.get_symbol(
                OsmosisPlugin.chain, token_original_id_to
            )
            symbol_uuid_to = token_table.get_symbol_uuid(
                OsmosisPlugin.chain, token_original_id_to
            )

            amount_from = OsmosisPlugin._get_token_amount(amounts[1]["value"])
            token_original_id_from = OsmosisPlugin._get_token_original_id(
                amounts[1]["value"]
            )

            token_symbol_from = token_table.get_symbol(
                OsmosisPlugin.chain, token_original_id_from
            )
            symbol_uuid_from = token_table.get_symbol_uuid(
                OsmosisPlugin.chain, token_original_id_from
            )

            trade_uuid = OsmosisPlugin._get_uuid()

            caaj_journal_get = CaajJournal(
                transaction.get_timestamp(),
                cls.chain,
                cls.PLATFORM,
                "swap",
                transaction.get_transaction_id(),
                trade_uuid,
                "lose",
                amount_to,
                token_symbol_to,
                token_original_id_to,
                symbol_uuid_to,
                caaj_to,
                caaj_from,
                "",
            )

            caaj_journal_lose = CaajJournal(
                transaction.get_timestamp(),
                cls.chain,
                cls.PLATFORM,
                "swap",
                transaction.get_transaction_id(),
                trade_uuid,
                "get",
                amount_from,
                token_symbol_from,
                token_original_id_from,
                symbol_uuid_from,
                caaj_from,
                caaj_to,
                "",
            )
            caaj.append(caaj_journal_get)
            caaj.append(caaj_journal_lose)
        return caaj

    @classmethod
    def _get_caaj_transfer(
        cls, transaction: Transaction, token_table: TokenOriginalIdTable
    ) -> list:
        caaj = []
        message = transaction.get_transaction()["data"]["tx"]["body"]["messages"][0]
        token_original_id = message["token"]["denom"]
        symbol = token_table.get_symbol(OsmosisPlugin.chain, token_original_id)
        symbol_uuid = token_table.get_symbol_uuid(
            OsmosisPlugin.chain, token_original_id
        )

        caaj_journal_lose = CaajJournal(
            transaction.get_timestamp(),
            cls.chain,
            cls.PLATFORM,
            cls.chain,
            transaction.get_transaction_id(),
            None,
            "send",
            str(Decimal(message["token"]["amount"]) / Decimal(MEGA)),
            symbol,
            token_original_id,
            symbol_uuid,
            message["sender"],
            message["receiver"],
            "",
        )
        caaj.append(caaj_journal_lose)
        return caaj

    @classmethod
    def _get_caaj_join_pool(
        cls, transaction: Transaction, token_table: TokenOriginalIdTable
    ) -> list:
        caaj = []
        attributes_list = OsmosisPlugin._get_attributes_list(transaction, "transfer")
        for attribute in attributes_list:
            senders = OsmosisPlugin._get_attribute_data(attribute, "sender")
            recipients = OsmosisPlugin._get_attribute_data(attribute, "recipient")
            amounts = OsmosisPlugin._get_attribute_data(attribute, "amount")
            amount_one = OsmosisPlugin._get_token_amount(
                amounts[0]["value"].split(",")[0]
            )
            amount_two = OsmosisPlugin._get_token_amount(
                amounts[0]["value"].split(",")[1]
            )

            token_original_id_one = OsmosisPlugin._get_token_original_id(
                amounts[0]["value"].split(",")[0]
            )
            token_original_id_two = OsmosisPlugin._get_token_original_id(
                amounts[0]["value"].split(",")[1]
            )

            token_symbol_one = token_table.get_symbol(
                OsmosisPlugin.chain, token_original_id_one
            )
            symbol_uuid_one = token_table.get_symbol_uuid(
                OsmosisPlugin.chain, token_original_id_one
            )
            token_symbol_two = token_table.get_symbol(
                OsmosisPlugin.chain, token_original_id_two
            )
            symbol_uuid_two = token_table.get_symbol_uuid(
                OsmosisPlugin.chain, token_original_id_two
            )

            trade_uuid = OsmosisPlugin._get_uuid()

            caaj_journal_lose_one = CaajJournal(
                transaction.get_timestamp(),
                cls.chain,
                cls.PLATFORM,
                "liquidity",
                transaction.get_transaction_id(),
                trade_uuid,
                "deposit",
                str(Decimal(amount_one)),
                token_symbol_one,
                OsmosisPlugin._get_token_original_id(amounts[0]["value"].split(",")[0]),
                symbol_uuid_one,
                senders[0]["value"],
                recipients[0]["value"],
                "",
            )
            caaj_journal_lose_two = CaajJournal(
                transaction.get_timestamp(),
                cls.chain,
                cls.PLATFORM,
                "liquidity",
                transaction.get_transaction_id(),
                trade_uuid,
                "deposit",
                str(Decimal(amount_two)),
                token_symbol_two,
                OsmosisPlugin._get_token_original_id(amounts[0]["value"].split(",")[1]),
                symbol_uuid_two,
                senders[0]["value"],
                recipients[0]["value"],
                "",
            )
            caaj.append(caaj_journal_lose_one)
            caaj.append(caaj_journal_lose_two)

            token_original_id_liquidity = OsmosisPlugin._get_token_original_id(
                amounts[1]["value"]
            )

            amount_liquidity = OsmosisPlugin._get_token_amount(amounts[1]["value"])

            caaj_journal_get_liquidity = CaajJournal(
                transaction.get_timestamp(),
                cls.chain,
                cls.PLATFORM,
                "liquidity",
                transaction.get_transaction_id(),
                trade_uuid,
                "get_bonds",
                amount_liquidity,
                None,
                token_original_id_liquidity,
                None,
                senders[1]["value"],
                recipients[1]["value"],
                "",
            )
            caaj.append(caaj_journal_get_liquidity)
        return caaj

    @classmethod
    def _get_caaj_lock_token(
        cls, transaction: Transaction, token_table: TokenOriginalIdTable
    ) -> list:
        caaj = []
        attributes_list = OsmosisPlugin._get_attributes_list(transaction, "transfer")
        for attribute in attributes_list:
            senders = OsmosisPlugin._get_attribute_data(attribute, "sender")
            recipients = OsmosisPlugin._get_attribute_data(attribute, "recipient")
            amounts = OsmosisPlugin._get_attribute_data(attribute, "amount")

            token_original_id_liquidity = OsmosisPlugin._get_token_original_id(
                amounts[0]["value"]
            )

            token_symbol_liquidity = token_table.get_symbol(
                OsmosisPlugin.chain, token_original_id_liquidity
            )
            symbol_uuid_liquidity = token_table.get_symbol_uuid(
                OsmosisPlugin.chain, token_original_id_liquidity
            )
            amount_liquidity = OsmosisPlugin._get_token_amount(amounts[0]["value"])

            caaj_journal_get_liquidity = CaajJournal(
                transaction.get_timestamp(),
                cls.chain,
                cls.PLATFORM,
                "staking",
                transaction.get_transaction_id(),
                OsmosisPlugin._get_uuid(),
                "deposit",
                amount_liquidity,
                token_symbol_liquidity,
                token_original_id_liquidity,
                symbol_uuid_liquidity,
                senders[0]["value"],
                recipients[0]["value"],
                "",
            )
            caaj.append(caaj_journal_get_liquidity)
        return caaj

    @classmethod
    def _get_caaj_exit_pool(
        cls, transaction: Transaction, token_table: TokenOriginalIdTable
    ) -> list:
        caaj = []
        attributes_list = OsmosisPlugin._get_attributes_list(transaction, "transfer")
        for attribute in attributes_list:
            senders = OsmosisPlugin._get_attribute_data(attribute, "sender")
            recipients = OsmosisPlugin._get_attribute_data(attribute, "recipient")
            amounts = OsmosisPlugin._get_attribute_data(attribute, "amount")
            amount_one = OsmosisPlugin._get_token_amount(
                amounts[0]["value"].split(",")[0]
            )

            token_original_id_one = OsmosisPlugin._get_token_original_id(
                amounts[0]["value"].split(",")[0]
            )
            token_symbol_one = token_table.get_symbol(
                OsmosisPlugin.chain, token_original_id_one
            )
            symbol_uuid_one = token_table.get_symbol_uuid(
                OsmosisPlugin.chain, token_original_id_one
            )

            trade_uuid = OsmosisPlugin._get_uuid()

            caaj_journal_lose_one = CaajJournal(
                transaction.get_timestamp(),
                cls.chain,
                cls.PLATFORM,
                "liquidity",
                transaction.get_transaction_id(),
                trade_uuid,
                "withdraw",
                str(Decimal(amount_one)),
                token_symbol_one,
                token_original_id_one,
                symbol_uuid_one,
                senders[0]["value"],
                recipients[0]["value"],
                "",
            )
            caaj.append(caaj_journal_lose_one)

            amount_two = OsmosisPlugin._get_token_amount(
                amounts[0]["value"].split(",")[1]
            )

            token_original_id_two = OsmosisPlugin._get_token_original_id(
                amounts[0]["value"].split(",")[1]
            )
            token_symbol_two = token_table.get_symbol(
                OsmosisPlugin.chain, token_original_id_two
            )
            symbol_uuid_two = token_table.get_symbol_uuid(
                OsmosisPlugin.chain, token_original_id_two
            )

            caaj_journal_lose_two = CaajJournal(
                transaction.get_timestamp(),
                cls.chain,
                cls.PLATFORM,
                "liquidity",
                transaction.get_transaction_id(),
                trade_uuid,
                "withdraw",
                str(Decimal(amount_two)),
                token_symbol_two,
                token_original_id_two,
                symbol_uuid_two,
                senders[0]["value"],
                recipients[0]["value"],
                "",
            )
            caaj.append(caaj_journal_lose_two)

            token_original_id_liquidity = OsmosisPlugin._get_token_original_id(
                amounts[1]["value"]
            )

            token_symbol_liquidity = token_table.get_symbol(
                OsmosisPlugin.chain, token_original_id_liquidity
            )
            symbol_uuid_liquidity = token_table.get_symbol_uuid(
                OsmosisPlugin.chain, token_original_id_liquidity
            )
            amount_liquidity = OsmosisPlugin._get_token_amount(amounts[1]["value"])

            caaj_journal_get_liquidity = CaajJournal(
                transaction.get_timestamp(),
                cls.chain,
                cls.PLATFORM,
                "liquidity",
                transaction.get_transaction_id(),
                trade_uuid,
                "lose_bonds",
                amount_liquidity,
                token_symbol_liquidity,
                token_original_id_liquidity,
                symbol_uuid_liquidity,
                senders[1]["value"],
                recipients[1]["value"],
                "",
            )
            caaj.append(caaj_journal_get_liquidity)
        return caaj

    @classmethod
    def _get_caaj_delegate(
        cls, address: str, transaction: Transaction, token_table: TokenOriginalIdTable
    ) -> list:
        caaj = []

        attributes_list_delegate = OsmosisPlugin._get_attributes_list(
            transaction, "delegate"
        )
        for attribute in attributes_list_delegate:
            caaj_to = OsmosisPlugin._get_attribute_data(attribute, "validator")[0][
                "value"
            ]
            amounts = OsmosisPlugin._get_attribute_data(attribute, "amount")
            caaj_from = address

            token_original_id_staking = OsmosisPlugin._get_token_original_id(
                amounts[0]["value"]
            )
            token_symbol_staking = token_table.get_symbol(
                OsmosisPlugin.chain, token_original_id_staking
            )
            symbol_uuid_staking = token_table.get_symbol_uuid(
                OsmosisPlugin.chain, token_original_id_staking
            )
            amount_liquidity = OsmosisPlugin._get_token_amount(amounts[0]["value"])

            caaj_journal_get_liquidity = CaajJournal(
                transaction.get_timestamp(),
                cls.chain,
                cls.PLATFORM,
                "staking",
                transaction.get_transaction_id(),
                OsmosisPlugin._get_uuid(),
                "deposit",
                amount_liquidity,
                token_symbol_staking,
                token_original_id_staking,
                symbol_uuid_staking,
                caaj_from,
                caaj_to,
                "",
            )
            caaj.append(caaj_journal_get_liquidity)
        return caaj

    @classmethod
    def _get_caaj_update_client(
        cls, address: str, transaction: Transaction, token_table: TokenOriginalIdTable
    ) -> list:
        caaj = []
        logs = transaction.get_transaction()["data"]["logs"]
        for log in logs:
            fungible_token_packet_list = list(
                filter(
                    lambda event: event["type"] == "fungible_token_packet",
                    log["events"],
                )
            )
            if not fungible_token_packet_list:
                pass
            else:
                success = OsmosisPlugin._get_attribute_data(
                    fungible_token_packet_list[0]["attributes"], "success"
                )[0]["value"]

                receiver = OsmosisPlugin._get_attribute_data(
                    fungible_token_packet_list[0]["attributes"], "receiver"
                )[0]["value"]

                if success == "true" and receiver == address:
                    transfer_list = list(
                        filter(
                            lambda event: event["type"] == "transfer",
                            log["events"],
                        )
                    )

                    recipients = OsmosisPlugin._get_attribute_data(
                        transfer_list[0]["attributes"], "recipient"
                    )

                    senders = OsmosisPlugin._get_attribute_data(
                        transfer_list[0]["attributes"], "sender"
                    )

                    amounts = OsmosisPlugin._get_attribute_data(
                        transfer_list[0]["attributes"], "amount"
                    )

                    caaj_from = senders[0]["value"]
                    caaj_to = recipients[0]["value"]

                    token_original_id_liquidity = OsmosisPlugin._get_token_original_id(
                        amounts[0]["value"]
                    )

                    token_symbol_liquidity = token_table.get_symbol(
                        OsmosisPlugin.chain, token_original_id_liquidity
                    )
                    symbol_uuid_liquidity = token_table.get_symbol_uuid(
                        OsmosisPlugin.chain, token_original_id_liquidity
                    )
                    amount_liquidity = OsmosisPlugin._get_token_amount(
                        amounts[0]["value"]
                    )

                    caaj_journal_get_liquidity = CaajJournal(
                        transaction.get_timestamp(),
                        cls.chain,
                        cls.PLATFORM,
                        cls.chain,
                        transaction.get_transaction_id(),
                        OsmosisPlugin._get_uuid(),
                        "receive",
                        amount_liquidity,
                        token_symbol_liquidity,
                        token_original_id_liquidity,
                        symbol_uuid_liquidity,
                        caaj_from,
                        caaj_to,
                        "",
                    )
                    caaj.append(caaj_journal_get_liquidity)
        return caaj

    @classmethod
    def _get_caaj_fee(
        cls, address: str, transaction: Transaction, token_table: TokenOriginalIdTable
    ) -> list:
        caaj = []
        caaj_journal_get = CaajJournal(
            transaction.get_timestamp(),
            cls.chain,
            cls.PLATFORM,
            cls.chain,
            transaction.get_transaction_id(),
            None,
            "lose",
            str(transaction.get_transaction_fee() / Decimal(MEGA)),
            "osmo",
            None,
            "c0c8e177-53c3-c408-d8bd-067a2ef41ea7",
            address,
            "fee",
            "",
        )
        caaj.append(caaj_journal_get)
        return caaj

    @classmethod
    def _get_token_amount(cls, value: str) -> str:
        token_amount_original = re.search(r"\d+", value)
        if token_amount_original is None:
            raise ValueError("token_amount_original is None")

        if "pool" in value:
            token_amount = str(Decimal(token_amount_original.group()) / Decimal(EXA))

        else:
            token_amount = str(Decimal(token_amount_original.group()) / Decimal(MEGA))
        return token_amount

    @classmethod
    def _get_uuid(cls) -> str:
        return str(uuid.uuid4())

    @classmethod
    def _get_token_original_id(cls, value: str) -> Union[str, None]:
        token_original_id_original = re.search(r"\d+", value)
        if token_original_id_original is None:
            raise ValueError("token_original_id_original is None")

        token_original_id = value[token_original_id_original.end() :]
        if token_original_id == "uosmo" or token_original_id == "":
            token_original_id = None
        elif token_original_id == "uion":
            token_original_id = None
        return token_original_id

    @classmethod
    def _get_attribute_data(cls, attribute: dict, attribute_key: str) -> list:
        attribute_data = list(
            filter(lambda attribute: attribute["key"] == attribute_key, attribute)
        )

        return attribute_data

    @classmethod
    def _get_attributes_list(cls, transaction: Transaction, event_type: str) -> list:
        logs = transaction.get_transaction()["data"]["logs"]
        events_list = []
        for log in logs:
            events = list(
                filter(lambda event: event["type"] == event_type, log["events"])
            )
            if len(events) > 0:
                events_list.append(*events)

        attributes_list = list(map(lambda event: event["attributes"], events_list))

        return attributes_list
