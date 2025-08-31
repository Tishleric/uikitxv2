#!/usr/bin/env python
"""Run the Actant CLI Bridge for spot_risk:prices_full (on Actant machine)."""

import logging

from .bridge import ActantCLIBridgeService


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    svc = ActantCLIBridgeService()
    svc.run_forever()


if __name__ == "__main__":
    main()

