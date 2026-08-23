#!/usr/bin/env python3
"""Generate a sing-box rule-set from the Steam Datagram Relay config."""

from __future__ import annotations

import argparse
import ipaddress
import json
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_URL = "https://api.steampowered.com/ISteamApps/GetSDRConfig/v1?appid=730"


def fetch_config(url: str, attempts: int = 4, timeout: int = 30) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "steam-sdr-rule-generator/1.0"},
    )
    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.load(response)
            if not isinstance(payload, dict):
                raise ValueError("Steam API returned a non-object JSON value")
            return payload
        except (OSError, ValueError, json.JSONDecodeError) as error:
            last_error = error
            if attempt + 1 < attempts:
                time.sleep(2**attempt)

    raise RuntimeError(f"failed to download Steam SDR config: {last_error}")


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        payload = json.load(source)
    if not isinstance(payload, dict):
        raise ValueError("input JSON must contain an object")
    return payload


def generate_rule_set(config: dict[str, Any]) -> dict[str, Any]:
    if config.get("success") is not True:
        raise ValueError("Steam API response does not contain success=true")

    pops = config.get("pops")
    if not isinstance(pops, dict) or not pops:
        raise ValueError("Steam API response does not contain any POPs")

    relay_networks: set[ipaddress.IPv4Network | ipaddress.IPv6Network] = set()
    address_count = 0

    for pop_name, pop in sorted(pops.items()):
        if not isinstance(pop, dict):
            raise ValueError(f"POP {pop_name!r} is not an object")
        relays = pop.get("relays", [])
        if not isinstance(relays, list):
            raise ValueError(f"POP {pop_name!r} has an invalid relays value")

        for relay in relays:
            if not isinstance(relay, dict):
                raise ValueError(f"POP {pop_name!r} contains an invalid relay")
            for field in ("ipv4", "ipv6"):
                value = relay.get(field)
                if value is None:
                    continue
                try:
                    address = ipaddress.ip_address(value)
                except ValueError as error:
                    raise ValueError(
                        f"POP {pop_name!r} contains an invalid {field} address: {value!r}"
                    ) from error
                if address.version != int(field[-1]):
                    raise ValueError(f"POP {pop_name!r} has {address} in the {field} field")
                relay_networks.add(
                    ipaddress.ip_network((address, address.max_prefixlen), strict=False)
                )
                address_count += 1

    if address_count == 0:
        raise ValueError("Steam API response does not contain any relay addresses")

    networks: list[str] = []
    for version in (4, 6):
        same_version = (network for network in relay_networks if network.version == version)
        networks.extend(str(network) for network in ipaddress.collapse_addresses(same_version))

    return {"version": 4, "rules": [{"ip_cidr": networks}]}


def write_rule_set(rule_set: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp")
    with temporary.open("w", encoding="utf-8") as destination:
        json.dump(rule_set, destination, ensure_ascii=False, indent=2)
        destination.write("\n")
    temporary.replace(output)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--url", default=DEFAULT_URL, help="Steam SDR config URL")
    source.add_argument("--input", type=Path, help="read the SDR config from a local file")
    parser.add_argument("--output", type=Path, default=Path("steam-ip.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.input) if args.input else fetch_config(args.url)
        rule_set = generate_rule_set(config)
        write_rule_set(rule_set, args.output)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    count = len(rule_set["rules"][0]["ip_cidr"])
    print(f"wrote {count} networks to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
