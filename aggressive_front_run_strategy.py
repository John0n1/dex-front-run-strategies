import asyncio
import logging
from typing import Dict, Any, Callable, Awaitable

logger = logging.getLogger(__name__)

class AggressiveFrontRunStrategy:
    """
    Aggressive front-run strategy class.

    This strategy is triggered when the risk score of a target transaction
    exceeds a configured threshold. It's designed for scenarios where quick
    action based on simpler risk analysis is preferred.
    """

    def __init__(
        self,
        validate_transaction_func: Callable[..., Awaitable[tuple[bool, dict, str]]],
        calculate_risk_score_func: Callable[..., Awaitable[tuple[float, dict]]],
        front_run_func: Callable[..., Awaitable[bool]],
        get_price_change_24h_func: Callable[[str], Awaitable[float]],
        config: Dict[str, Any]
    ):
        """
        Initializes the AggressiveFrontRunStrategy.

        Args:
            validate_transaction_func: Asynchronous function to validate a transaction.
            calculate_risk_score_func: Asynchronous function to calculate risk score.
            front_run_func: Asynchronous function to execute a front-run.
            get_price_change_24h_func: Asynchronous function to get 24h price change.
            config: Configuration dictionary containing strategy parameters.
        """
        self._validate_transaction = validate_transaction_func
        self._calculate_risk_score = calculate_risk_score_func
        self._front_run = front_run_func
        self._get_price_change_24h = get_price_change_24h_func
        self.config = config
        self.min_value_eth = config.get("AGGRESSIVE_FRONT_RUN_MIN_VALUE_ETH", 0.01) # Default value
        self.risk_score_threshold = config.get("AGGRESSIVE_FRONT_RUN_RISK_SCORE_THRESHOLD", 70) # Default value


    async def execute(self, target_tx: Dict[str, Any]) -> bool:
        """
        Executes the aggressive front-run strategy.

        Args:
            target_tx: The target transaction dictionary.

        Returns:
            True if front-run was executed, False otherwise.
        """
        logger.debug("Initiating Aggressive Front-Run Strategy...")

        valid, decoded_tx, token_symbol = await self._validate_transaction(
            target_tx, "front_run", min_value=self.min_value_eth
        )
        if not valid:
            return False

        price_change_24h = await self._get_price_change_24h(token_symbol)
        risk_score, market_conditions = await self._calculate_risk_score(
            target_tx,
            token_symbol,
            price_change=price_change_24h
        )

        if risk_score >= self.risk_score_threshold:
            logger.debug(f"Executing aggressive front-run (Risk: {risk_score:.2f})")
            return await self._front_run(target_tx)

        return False
