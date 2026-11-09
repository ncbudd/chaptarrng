## Hardcover-only manual imports

Selecting only Hardcover in Metadata Provider settings now routes selected `hc:` author and edition IDs to the native Hardcover catalog during manual import. Previously this path still queried the metadata server unless the separate legacy `HARDCOVER=true` environment mode was set, so an available Hardcover edition could be reported missing from the author catalog. The explicit legacy environment mode and `HARDCOVER_NATIVE=false` override retain their behavior.
