import json

from senkalib.chain.bitbank.bitbank_transaction import BitbankTransaction

from bitbank_plugin.bitbank_plugin import BitbankPlugin


class TestBitbankPlugin:
    def test_can_handle_bitbank(self):
        test_data = TestBitbankPlugin._get_test_data(
            "tests/data/bitbank_sample_with_data_type.json"
        )
        transaction = BitbankTransaction(test_data)
        chain_type = BitbankPlugin.can_handle(transaction)
        assert chain_type

    @staticmethod
    def _get_test_data(filename: str):
        json_load = json.load(open(filename))
        return json_load[0]
