import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.kafka.clients.kafka_transaction_client import (
    TransactionalConfig,
    TransactionState
)
from infrastructure.orchestrator.kafka.clients.kafka_producer_client import ProducerConfig


class TestKafkaTransactions:
    def test_transactional_config_creation(self):
        config = TransactionalConfig(
            transactional_id="test-transaction",
            transaction_timeout_ms=120000
        )
        
        assert config.transactional_id == "test-transaction"
        assert config.transaction_timeout_ms == 120000
    
    def test_transactional_config_defaults(self):
        config = TransactionalConfig(transactional_id="test-transaction")
        
        assert config.transaction_timeout_ms == 60000
        assert config.producer_config is None
    
    def test_transactional_config_with_producer_config(self):
        producer_config = ProducerConfig(
            bootstrap_servers=["localhost:9092"],
            transactional_id="test-transaction"
        )
        
        txn_config = TransactionalConfig(
            transactional_id="test-transaction",
            producer_config=producer_config
        )
        
        assert txn_config.producer_config is not None
        assert txn_config.producer_config.transactional_id == "test-transaction"
    
    def test_transaction_state_enum(self):
        states = [
            TransactionState.READY,
            TransactionState.IN_TRANSACTION,
            TransactionState.COMMITTING,
            TransactionState.ABORTING,
            TransactionState.ABORTED,
            TransactionState.COMMITTED
        ]
        
        assert len(states) == 6
        assert TransactionState.READY.value == "ready"
        assert TransactionState.IN_TRANSACTION.value == "in_transaction"
        assert TransactionState.COMMITTED.value == "committed"
    
    @pytest.mark.parametrize("timeout_ms", [30000, 60000, 120000, 300000])
    def test_transactional_config_timeout_variations(self, timeout_ms):
        config = TransactionalConfig(
            transactional_id="test-transaction",
            transaction_timeout_ms=timeout_ms
        )
        
        assert config.transaction_timeout_ms == timeout_ms
